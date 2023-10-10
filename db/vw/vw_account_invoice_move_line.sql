create or replace view vw_account_invoice_move_line as
select ai.id invoice_id,
       ai.amount_total invoice_amount_total,
       ai.state invoice_state,
       ai.vendor_display_name,
       ai.date_due invoice_date_due,
       COALESCE(cre.real_payment_date, aml."date", ai.date_payment) datapagamento_real,
       COALESCE(cre.occurrence_date, aml."date", ai.date_payment) datapagamento_ocorrencia,
       ai.date_payment invoice_datapagamento_sisa,
       aml.credit valorpago,
       cre.interest_fee_value valorpago_juros,
       am.id move_id,
       am.is_cnab move_is_cnab,
       aml.id move_line_id,
       aml.debit move_line_debit,
       aml.credit move_line_credit,
       aml.account_id move_line_account_id,
       aa."name" move_line_account_name,
       aml.journal_id move_line_journal_id,
       aj.name move_line_journal_name,
       aml."date" move_line_date,
       aml.date_maturity move_line_date_maturity,
       aml.journal_entry_ref move_line_journal_entry_ref,
       aml.payment_id move_line_payment_id,
       cre.id cnab_id,
       cre.cnab_return_log_id,
       cre.bank_payment_line_id cnab_bank_payment_line_id,
       cre.real_payment_date cnab_real_payment_date,
       cre.occurrence_date cnab_occurrence_date,
       cre.due_date cnab_due_date,
       cre.company_title_identification cnab_company_title_identification,
       cre.interest_fee_value cnab_interest_fee_value,
       cre.own_number cnab_own_number,
       cre.occurrences cnab_occurrences,
       cre.your_number cnab_your_number,
       cre.title_value cnab_title_value,
       cre.payment_value cnab_payment_value,
       ai.partner_id
  from account_invoice ai
  left join account_invoice_account_move_line_rel aiam on aiam.account_invoice_id = ai.id
  left join account_move_line aml_rel on aml_rel.id = aiam.account_move_line_id
  left join account_move am on am.id = aml_rel.move_id
  left join account_move_line aml on aml.move_id = am.id
  left join account_account aa on aa.id = aml.account_id
  left join account_journal aj on aj.id = aml.journal_id
  left join account_account_type aat on aat.id = aml.user_type_id
  left join account_payment ap on ap.id = aml.payment_id
  left join l10n_br_cnab_return_event cre ON cre.invoice_id = ai.id AND cre.occurrences::text = '06-Liquidação Normal *'::text
  where aiam.account_invoice_id is not null
