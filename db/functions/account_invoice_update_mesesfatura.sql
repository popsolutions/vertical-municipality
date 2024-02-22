CREATE OR REPLACE FUNCTION public.account_invoice_update_mesesfatura(_anomesinicial integer = 202401)
 RETURNS void
 LANGUAGE plpgsql
AS $function$
declare sum_price_total numeric;
declare _residual numeric;
declare _state varchar(30);
begin
 /*
 task-430-Criar campos para mostrar ano/meses contido na fatura
 */
  with x as (
  SELECT ai.id,
         string_agg(DISTINCT anomes_text(ail.anomes_vencimento, 5), ', '::text) mesesfatura,
         count(DISTINCT ail.anomes_vencimento) mesesfaturaqtde
    FROM account_invoice ai join account_invoice_line ail on ail.invoice_id = ai.id
   where anomes(ai.date_due) >= _anomesinicial
  group by 1
  order by 3 desc
  )
  update account_invoice ai
     set mesesfaturaqtde = x.mesesfaturaqtde,
         mesesfatura = x.mesesfatura
    from x
   where ai.id = x.id;
END;
$function$
;
