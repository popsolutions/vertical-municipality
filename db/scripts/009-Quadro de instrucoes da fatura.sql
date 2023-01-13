CREATE OR REPLACE FUNCTION public.func_account_invoice_JurosDiario(invoice_id int4)
 RETURNS TABLE(amount_total numeric, juros_mensal numeric, juros_diario numeric, multa_diaria numeric)
 LANGUAGE plpgsql
AS $function$
begin
  select aci.amount_total,
         apm.boleto_interest_perc juros_mensal,
         round(apm.boleto_interest_perc / 30, 2) juros_diario,
         round(aci.amount_total * apm.boleto_interest_perc / 30 / 100, 2) multa_diaria
    from account_invoice aci join account_payment_mode apm on apm.id = aci.payment_mode_id
   where aci.id = invoice_id
    into amount_total, juros_mensal, juros_diario, multa_diaria;

    return next;
end
$function$
;
