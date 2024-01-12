CREATE OR REPLACE VIEW public.vw_bank_payment_line
AS SELECT apo.id AS account_payment_order_id,
          bpl.id AS bank_payment_line_id,
          bpl.own_number AS bank_payment_line_own_number,
          apl.id AS account_payment_line,
          ai.id AS account_invoice_id,
          ai.amount_total,
          ai.land_id,
          vpl.module_code__block_code__lot_code,
          rp.id AS res_partner_id,
          apo.state AS account_payment_order_state,
          ai.date_due,
          bpl.partner_id,
          rp.name,
          rp.display_name,
          rp.legal_name,
          rp.street_name,
          rp.city_id,
          cre.title_value AS cnabret_title_value,
          cre.interest_fee_value AS cnabret_interest_fee_value,
          cre.payment_value AS cnabret_payment_value,
          cre.real_payment_date AS cnabret_real_payment_date,
          cre.occurrence_date AS cnabret_occurrence_date,
          cre.occurrences AS cnabret_occurrences,
          cre.cnab_return_log_id,
          cre.id AS l10n_br_cnab_return_event_id
     FROM bank_payment_line bpl
          LEFT JOIN account_payment_order apo ON apo.id = bpl.order_id
          LEFT JOIN account_payment_line apl ON apl.bank_line_id = bpl.id
          LEFT JOIN account_invoice ai ON ai.id = apl.invoice_id
          LEFT JOIN res_partner rp ON rp.id = ai.partner_id
          LEFT JOIN vw_property_land vpl ON vpl.id = ai.land_id
          LEFT JOIN l10n_br_cnab_return_event cre ON cre.bank_payment_line_id = bpl.id;