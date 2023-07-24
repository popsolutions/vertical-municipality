create or replace view vw_report_contab_baixados as
select t.invoice_id,
       vpl.id land_id,
       vpl.module_code,
       vpl.block_code,
       lpad(vpl.lot_code, 3, '0') lot_code,
       substring(t.anomes_vencimento::varchar, 5, 2) || '/' || substring(t.anomes_vencimento::varchar, 1, 4) referencia,
       t.total_agua,
       t.total_contribuicaomensal,
       t.total_taxas,
       t.jurosproporcional_valor,
       t.total_areaverde,
       t.juros_areaverde,
       t.total_taxacaptacao,
       t.descontos,
       t.price_total,
       cre.occurrence_date,
       t.tipocobranca,
       '' observacao,
       cre.real_payment_date,
       cre.due_date,
       t.anomes_vencimento,
       rp.id res_id,
       rp."name" res_name,
       vpl.module_code__block_code__lot_code2 land,
       t.product_id,
       t.product_name,
       t.price_total_sum,
       t.total_juros,
       t.jurosproporcional_perc
  from l10n_br_cnab_return_event cre
       join account_invoice ai on ai.id = cre.invoice_id
       join vw_property_land vpl on vpl.id = ai.land_id
       join res_partner rp on rp.id = ai.partner_id
       left join func_report_contab_baixados(cre.invoice_id) t on true
 where true
   and cre.invoice_id is not null
   and ( true or
        ('' = 'versão-2023-07-20')
       )
 order by
       t.invoice_id,
       t.anomes_vencimento