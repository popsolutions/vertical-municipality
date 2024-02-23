CREATE OR REPLACE FUNCTION public.account_invoice_update_mesesfatura(_anomesinicial integer = 202401, _invoice_id integer = null)
 RETURNS void
 LANGUAGE plpgsql
AS $function$
begin
/*
 2024-02-23
 task-430-Criar campos para mostrar ano/meses contido na fatura

 ** obs: manter sincronização entre as rotinas duplicasdas: public.func_trg_account_invoice_update_mesesfatura e public.account_invoice_update_mesesfatura
*/
  with x as (
  SELECT ai.id,
         string_agg(DISTINCT anomes_text(ail.anomes_vencimento, 5), ', '::text) mesesfatura,
         count(DISTINCT ail.anomes_vencimento) mesesfaturaqtde
    FROM account_invoice ai join account_invoice_line ail on ail.invoice_id = ai.id
   where ((_invoice_id IS not NULL) or (anomes(ai.date_due) >= _anomesinicial))
     AND ((_invoice_id IS NULL) OR (ai.id = _invoice_id))
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
