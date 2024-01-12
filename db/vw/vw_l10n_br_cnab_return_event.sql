create or replace view vw_l10n_br_cnab_return_event as
select cre.id,
       cre.cnab_return_log_id,
       cre.create_date dt_importacao,
       cre.real_payment_date,
       cre.occurrence_date,
       cre.due_date,
       cre.favored_bank_account_id,
       cre.invoice_id,
       cre.interest_fee_value,
       cre.own_number,
       cre.occurrences,
       cre.your_number,
       cre.str_motiv_a,
       cre.str_motiv_b,
       cre.str_motiv_c,
       cre.str_motiv_d,
       cre.str_motiv_e,
       cre.tariff_charge,
       cre.title_value,
       cre.rebate_value,
       cre.discount_value,
       cre.iof_value,
       cre.payment_value,
       rp_user.name user_name,
       ai.id AS account_invoice_id,
       ai.amount_total,
       ai.land_id,
       vpl.module_code__block_code__lot_code land,
       rp.id AS res_partner_id,
       ai.date_due,
       ai.state,
       rp.name partner_name,
       rp.street_name,
       rp.city_id
  from l10n_br_cnab_return_event cre
       LEFT JOIN account_invoice ai ON ai.id = cre.invoice_id
       LEFT JOIN res_partner rp ON rp.id = ai.partner_id
       LEFT JOIN vw_property_land vpl ON vpl.id = ai.land_id
       left join res_users ru on ru.id = cre.create_uid
       left join res_partner rp_user on rp_user.id = ru.partner_id;