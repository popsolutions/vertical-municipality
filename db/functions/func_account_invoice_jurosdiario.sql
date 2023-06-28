CREATE OR REPLACE FUNCTION public.func_account_invoice_jurosdiario(_invoice_id integer)
 RETURNS TABLE(amount_total numeric, juros_mensal numeric, juros_diario numeric, multa_diaria numeric)
 LANGUAGE plpgsql
AS $function$
begin
  /*
  versão=2023.06.28-acrescentado filtro para incluir no cálculo apenas Contrib. Mensal, Água/Esgoto, Tx Captação, Área verde
  */
  select ail.amount_total,
         apm.boleto_interest_perc juros_mensal,
         round(apm.boleto_interest_perc / 30, 2) juros_diario,
         round(ail.amount_total * apm.boleto_interest_perc / 30 / 100, 2) multa_diaria
    from (
          select ai.payment_mode_id,
                 sum(ail.price_total) amount_total
            from account_invoice ai,
                 account_invoice_line ail
           where ai.id = _invoice_id
             and ail.invoice_id = ai.id
             and ail.product_id in (1, 7, 9, 10) /*Contrib. Mensal, Água/Esgoto, Tx Captação, Área verde*/  
             and ail.anomes_vencimento = anomes(ai.date_due)
            group by 1 
         ) ail
    join account_payment_mode apm on apm.id = ail.payment_mode_id
    into amount_total, juros_mensal, juros_diario, multa_diaria;

  return next;
end
$function$
;