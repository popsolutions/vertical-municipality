CREATE OR REPLACE FUNCTION func_trg_account_invoice_update_mesesfatura()
RETURNS trigger AS $$
declare mesesfatura integer;
declare mesesfaturaqtde integer;
begin
  --task-430-Criar campos para mostrar ano/meses contido na fatura
  --** obs: manter sincronização entre as rotinas duplicasdas: public.func_trg_account_invoice_update_mesesfatura e public.account_invoice_update_mesesfatura

  SELECT string_agg(DISTINCT anomes_text(ail.anomes_vencimento, 5), ', '::text) mesesfatura,
         count(DISTINCT ail.anomes_vencimento) mesesfaturaqtde
    FROM account_invoice ai join account_invoice_line ail on ail.invoice_id = ai.id
   where ai.id = new.id
    into new.mesesfatura,
         new.mesesfaturaqtde;
RETURN NEW;
END;
$$
LANGUAGE plpgsql;