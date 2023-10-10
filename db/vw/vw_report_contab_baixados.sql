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