CREATE TRIGGER trg_account_invoice_update_mesesfatura
before insert or update ON account_invoice
    FOR EACH ROW EXECUTE PROCEDURE func_trg_account_invoice_update_mesesfatura();