ALTER TABLE public.product_template ADD juros boolean NULL;

commit;

update product_template pt
  set juros = pt.id in (13, 12, 18, 19, 20);

commit;

CREATE OR REPLACE FUNCTION public.func_trg_account_invoice_update_mesesfatura()
 RETURNS trigger
 LANGUAGE plpgsql
AS $function$
declare mesesfatura integer;
declare mesesfaturaqtde integer;
begin
  --task-434-func_trg_account_invoice_update_mesesfatura não podem incluir juros. Função account_invoice_update_mesesfatura não precisa mais existir
  --task-430-Criar campos para mostrar ano/meses contido na fatura

  SELECT string_agg(DISTINCT anomes_text(ail.anomes_vencimento, 5), ', '::text) mesesfatura,
         count(DISTINCT ail.anomes_vencimento) mesesfaturaqtde
    FROM account_invoice ai
         join account_invoice_line ail on ail.invoice_id = ai.id
         join product_template pt on pt.id = ail.product_id and (not coalesce(pt.juros, false))
   where ai.id = new.id
    into new.mesesfatura,
         new.mesesfaturaqtde;
RETURN NEW;
END;
$function$
;

DROP FUNCTION public.account_invoice_update_mesesfatura(int4, int4);

