update account_invoice_line ail
   set land_id = (select aci.land_id from account_invoice aci where aci.id = ail.invoice_id)
 where land_id is null;


