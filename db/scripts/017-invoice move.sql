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
  where aiam.account_invoice_id is not null;


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
       case when cnab_semcnab = 'cnab' then
         case when exists
           (select 1
              from res_partner_bank rpb
             where rpb.partner_id = t.partner_id
               and rpb.acc_number is not null
           ) then 'A'
           else 'B'
         end
       else
         'D'
       end tipocob__automatico_boleto_dinheiro --A-> Débito automático, B -> boleto, D -> Dinheiro
  from (select aiml.invoice_id,
               aiml.invoice_amount_total,
               aiml.invoice_state,
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
                       aiml.vendor_display_name,
                       aiml.invoice_date_due,
                       aiml.invoice_datapagamento_sisa,
                       max(aiml.datapagamento_real) datapagamento_real_max,
                       max(aiml.datapagamento_ocorrencia) datapagamento_ocorrencia_max,
                       sum(valorpago) valorpago,
                       sum(valorpago_juros) valorpago_juros,
                       string_agg(distinct case when aiml.move_is_cnab then 'cnab' else 'sem cnab' end, ',') cnab_semcnab,
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

ALTER VIEW public.vw_report_contab_baixados TO vw_report_contab_baixados_old_20231010;

DROP VIEW public.vw_report_contab_baixados;

create or replace view vw_report_contab_baixados as
select ims.invoice_id,
    vpl.id AS land_id,
    vpl.module_code,
    vpl.block_code,
    lpad(vpl.lot_code, 3, '0') AS lot_code,
    ("substring"(t.anomes_vencimento::varchar, 5, 2) || '/'::text) || "substring"(t.anomes_vencimento::varchar, 1, 4) AS referencia,
    t.total_agua,
    t.total_contribuicaomensal,
    t.total_taxas,
    t.jurosproporcional_valor,
    t.total_areaverde,
    t.juros_areaverde,
    t.total_taxacaptacao,
    t.descontos,
    t.price_total,
    ims.datapagamento_ocorrencia_max occurrence_date,
    ims.datapagamento_real_max real_payment_date,
    t.tipocobranca,
    '' observacao,
    ims.invoice_date_due due_date,
    t.anomes_vencimento,
    rp.id res_id,
    rp.name res_name,
    vpl.module_code__block_code__lot_code2 AS land,
    t.product_id,
    t.product_name,
    t.price_total_sum,
    t.total_juros,
    t.jurosproporcional_perc,
    t.price_total + t.jurosproporcional_valor AS price_total_juros,
    ims.tipocob__automatico_boleto_dinheiro
   FROM vw_account_invoice_move_sum ims
     join account_invoice ai on ai.id = ims.invoice_id
     join vw_property_land vpl on vpl.id = ai.land_id
     join res_partner rp on rp.id = ai.partner_id
     left join func_report_contab_baixados(ims.invoice_id) t on true
   where ( true or
         ('' = 'versão-2023-10-09')
         );