CREATE OR REPLACE VIEW public.vw_account_invoice_move_line
AS SELECT ai.id AS invoice_id,
    ai.amount_total AS invoice_amount_total,
    ai.state AS invoice_state,
    ai.vendor_display_name,
    ai.date_due AS invoice_date_due,
    COALESCE(cre.real_payment_date, aml.date, ai.date_payment) AS datapagamento_real,
    COALESCE(cre.occurrence_date, aml.date, ai.date_payment) AS datapagamento_ocorrencia,
    ai.date_payment AS invoice_datapagamento_sisa,
    aml.credit AS valorpago,
    cre.interest_fee_value AS valorpago_juros,
    am.id AS move_id,
    am.is_cnab AS move_is_cnab,
    aml.id AS move_line_id,
    aml.debit AS move_line_debit,
    aml.credit AS move_line_credit,
    aml.account_id AS move_line_account_id,
    aa.name AS move_line_account_name,
    aml.journal_id AS move_line_journal_id,
    aj.name AS move_line_journal_name,
    aml.date AS move_line_date,
    aml.date_maturity AS move_line_date_maturity,
    aml.journal_entry_ref AS move_line_journal_entry_ref,
    aml.payment_id AS move_line_payment_id,
    cre.id AS cnab_id,
    cre.cnab_return_log_id,
    cre.bank_payment_line_id AS cnab_bank_payment_line_id,
    cre.real_payment_date AS cnab_real_payment_date,
    cre.occurrence_date AS cnab_occurrence_date,
    cre.due_date AS cnab_due_date,
    cre.company_title_identification AS cnab_company_title_identification,
    cre.interest_fee_value AS cnab_interest_fee_value,
    cre.own_number AS cnab_own_number,
    cre.occurrences AS cnab_occurrences,
    cre.your_number AS cnab_your_number,
    cre.title_value AS cnab_title_value,
    cre.payment_value AS cnab_payment_value,
    ai.partner_id,
    ai.accumulated
   FROM account_invoice ai
     LEFT JOIN account_invoice_account_move_line_rel aiam ON aiam.account_invoice_id = ai.id
     LEFT JOIN account_move_line aml_rel ON aml_rel.id = aiam.account_move_line_id
     LEFT JOIN account_move am ON am.id = aml_rel.move_id
     LEFT JOIN account_move_line aml ON aml.move_id = am.id
     LEFT JOIN account_account aa ON aa.id = aml.account_id
     LEFT JOIN account_journal aj ON aj.id = aml.journal_id
     LEFT JOIN account_account_type aat ON aat.id = aml.user_type_id
     LEFT JOIN account_payment ap ON ap.id = aml.payment_id
     LEFT JOIN l10n_br_cnab_return_event cre ON cre.invoice_id = ai.id AND cre.occurrences::text = '06-Liquidação Normal *'::text
  WHERE aiam.account_invoice_id IS NOT NULL;


-----------------------------

create or replace view vw_account_invoice_move_sum as
select t.invoice_id,
       t.invoice_amount_total,
       t.invoice_state,
       t.vendor_display_name,
       t.invoice_date_due,
       t.datapagamento_real_max,
       t.datapagamento_ocorrencia_max,
       t.invoice_datapagamento_sisa,
       t.invoice_amount_total valorfatura_odoo,
       t.cnab_title_value valorfatura_cnab,
       t.valorpago,
       t.valorpago_juros,
       coalesce(t.invoice_amount_total, 0) - coalesce(t.valorpago, 0) saldo_fatura,
       t.cnab_payment_value valorpago_cnab,
       t.move_line_credit valorpago_odoo,
       t.move_line_debit valorfatura_contabil,
       t.cnab_interest_fee_value valorjuros_cnab,
       t.cnab_semcnab,
       t.move_line_debit,
       t.move_line_credit,
       t.move_line_account_ids,
       t.move_line_account_names,
       t.move_line_journal_ids,
       t.move_line_journal_names,
       t.move_line_date_max,
       t.move_line_date_maturity_max,
       t.cnab_ids,
       t.cnab_return_log_ids,
       t.cnab_bank_payment_line_ids,
       t.cnab_real_payment_date_max,
       t.cnab_occurrence_date_max,
       t.cnab_due_date_max,
       t.cnab_interest_fee_value,
       t.cnab_own_numbers,
       t.cnab_occurrencess,
       t.cnab_your_numbers,
       t.cnab_title_value,
       t.cnab_payment_value,
       t.count_move,
       t.count_move_line,
       t.count_cnab_id,
       t.land_id,
       t.land,
       case when cnab_semcnab in ('cnab', 'cnab-manual') then
         case when exists
           (select 1
              from res_partner_bank rpb
             where rpb.partner_id = t.partner_id
               and rpb.acc_number is not null
           ) then 'A'
           else 'B'
         end
       when coalesce(t.accumulated, false) then 'C' /*Acumulado*/
       else
         'D'
       end tipocob__automatico_boleto_dinheiro --A-> Débito automático, B -> boleto, D -> Dinheiro, C -> Acumulado
  from (select aiml.invoice_id,
               aiml.invoice_amount_total,
               aiml.invoice_state,
               aiml.accumulated,
               aiml.vendor_display_name,
               aiml.invoice_date_due,
               aiml.invoice_datapagamento_sisa,
               aiml.datapagamento_real_max,
               aiml.datapagamento_ocorrencia_max,
               aiml.valorpago,
               aiml.valorpago_juros,
               aiml.cnab_semcnab,
               aiml.move_line_debit,
               aiml.move_line_credit,
               aiml.move_line_account_ids,
               aiml.move_line_account_names,
               aiml.move_line_journal_ids,
               aiml.move_line_journal_names,
               aiml.move_line_date_max,
               aiml.move_line_date_maturity_max,
               aiml.count_move,
               aiml.count_move_line,
               string_agg(distinct cre.id::varchar, ',') cnab_ids,
               string_agg(distinct cre.cnab_return_log_id::varchar, ',') cnab_return_log_ids,
               string_agg(distinct cre.bank_payment_line_id::varchar, ',') cnab_bank_payment_line_ids,
               max(cre.real_payment_date) cnab_real_payment_date_max,
               max(cre.occurrence_date) cnab_occurrence_date_max,
               max(cre.due_date) cnab_due_date_max,
               sum(cre.interest_fee_value) cnab_interest_fee_value,
               string_agg(distinct cre.own_number, ',') cnab_own_numbers,
               string_agg(distinct cre.occurrences, ',') cnab_occurrencess,
               string_agg(distinct cre.your_number, ',') cnab_your_numbers,
               sum(cre.title_value) cnab_title_value,
               sum(cre.payment_value) cnab_payment_value,
               count(distinct cre.id) count_cnab_id,
               ai.land_id,
               vpl.module_code__block_code__lot_code2 land,
               ai.partner_id
          from (select aiml.invoice_id,
                       aiml.invoice_amount_total,
                       aiml.invoice_state,
                       aiml.accumulated,
                       aiml.vendor_display_name,
                       aiml.invoice_date_due,
                       aiml.invoice_datapagamento_sisa,
                       max(aiml.datapagamento_real) datapagamento_real_max,
                       max(aiml.datapagamento_ocorrencia) datapagamento_ocorrencia_max,
                       sum(valorpago) valorpago,
                       sum(valorpago_juros) valorpago_juros,
                       string_agg(distinct case when aiml.move_is_cnab then 'cnab' WHEN aiml.move_line_journal_id = 7 THEN 'cnab-manual' else 'sem cnab' end, ',') cnab_semcnab,
                       sum(aiml.move_line_debit) move_line_debit,
                       sum(aiml.move_line_credit) move_line_credit,
                       string_agg(distinct aiml.move_line_account_id::varchar, ',') move_line_account_ids,
                       string_agg(distinct aiml.move_line_account_name, ',') move_line_account_names,
                       string_agg(distinct aiml.move_line_journal_id::varchar, ',') move_line_journal_ids,
                       string_agg(distinct aiml.move_line_journal_name, ',') move_line_journal_names,
                       max(aiml.move_line_date) move_line_date_max,
                       max(aiml.move_line_date_maturity) move_line_date_maturity_max,
                       count(distinct aiml.move_id) count_move,
                       count(distinct aiml.move_line_id) count_move_line
                  from vw_account_invoice_move_line aiml
                group by
                      aiml.invoice_id,
                      aiml.invoice_amount_total,
                      aiml.invoice_state,
                      aiml.accumulated,
                      aiml.vendor_display_name,
                      aiml.invoice_date_due,
                      aiml.invoice_datapagamento_sisa
              ) aiml
              left join l10n_br_cnab_return_event cre ON cre.invoice_id = aiml.invoice_id AND cre.occurrences::text = '06-Liquidação Normal *'::text
              join account_invoice ai on ai.id = aiml.invoice_id
              left join vw_property_land vpl on vpl.id = ai.land_id
        group by
              aiml.invoice_id,
              aiml.invoice_amount_total,
              aiml.invoice_state,
              aiml.accumulated,
              aiml.vendor_display_name,
              aiml.invoice_date_due,
              aiml.invoice_datapagamento_sisa,
              aiml.datapagamento_real_max,
              aiml.datapagamento_ocorrencia_max,
              aiml.valorpago,
              aiml.valorpago_juros,
              aiml.cnab_semcnab,
              aiml.move_line_debit,
              aiml.move_line_credit,
              aiml.move_line_account_ids,
              aiml.move_line_account_names,
              aiml.move_line_journal_ids,
              aiml.move_line_journal_names,
              aiml.move_line_date_max,
              aiml.move_line_date_maturity_max,
              aiml.count_move,
              aiml.count_move_line,
              ai.land_id,
              vpl.module_code__block_code__lot_code2,
              ai.partner_id
      ) t;