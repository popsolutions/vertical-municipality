-->>>>>>>>>>>>>>>>>>>>>>>
--deletando dependências...

drop MATERIALIZED VIEW if exists public.x_bi_sql_view_items_fatura_cont_riv;

drop MATERIALIZED VIEW if exists public.x_bi_sql_view_contabil_riviera_baixados;

drop view if exists public.invoice_product_report;

drop view if exists public.vw_vs_vw_l10n_br_cnab_return_event__vw_report_contab_baixados;

drop MATERIALIZED VIEW if exists task_439_contab.vw_contab_odoo_vs_sisa_m; --view momentâneas de desenvolvimento

drop MATERIALIZED VIEW if exists task_439_contab.vw_contab_odoo_vs_sisa_m_2; --view momentâneas de desenvolvimento

drop view if exists task_439_contab.vw_contab_odoo_vs_sisa;

drop materialized view if exists dev.vw_task_345_paidinvoice_tipocobranca_diferencas;

drop view if exists vw_report_contab_baixados_old_20231010;

drop view if exists vw_report_contab_baixados_old_20231116;

drop view if exists vw_report_contab_baixados_old_20240317;

drop function if exists public.func_report_contab_baixados_20240317;

commit;
--<<<<<<<<<<<<<<<<<<<<<<<

drop view if exists public.vw_report_contab_baixados;

drop function if exists public.func_report_contab_baixados;

commit;

CREATE OR REPLACE FUNCTION public.func_report_contab_baixados(_invoice_id integer)
 RETURNS TABLE(invoice_id integer,
               func_sequence integer,
               anomes_vencimento integer,
               product_id integer,
               product_name character varying,
               price_total_sum numeric, --Valor total pago
               juros numeric, -- Juros total da fatura
               taxaPermanencia numeric, -- Taxa de permanencia total da fatura
               total_juros numeric,  -- Juros total + taxa de permanência da fatura
               juros_anomes numeric,
               txpermanencia_anomes numeric,
               jurostotal_anomes numeric,
               jurosproporcional_perc numeric,
               jurosproporcional_valor numeric,
               juros_areaverde numeric,
               jurosproporcional_total numeric,
               price_total numeric,
               price_total_anomes numeric,
               total_agua numeric,
               total_contribuicaomensal numeric,
               total_taxas numeric,
               total_areaverde numeric,
               total_taxacaptacao numeric,
               descontos numeric)
 LANGUAGE plpgsql
AS $function$
  declare _ai_anomesVencimentoInicial integer;
  declare _pt_juros bool;
  declare _anomes_vencimento_count integer;
  declare _anomes_vencimento_current integer;
  declare _anomes_vencimento_index integer;
  declare _jurosProporcionalJaDiluido_Anomes numeric = 0; --esta variável vai acumular o total de juros que já foi diluído para ano/mês
begin
/*
  versão=2024-03-23
    task-445-paid_invoice - reconstrução de func_report_contab_baixados
  versao=2023-10-13
*/
  invoice_id = _invoice_id;
  txpermanencia_anomes = 0;

  select sum(aims.valorjuros_cnab::numeric) taxa_permanencia,
         sum(aims.valorpago) price_total_sum
    from vw_account_invoice_move_sum aims
   where aims.invoice_id = _invoice_id
    into taxaPermanencia,
         price_total_sum;

  select anomes(ai.date_due_initial) ai_anomesVencimentoInicial
    from account_invoice ai
   where ai.id = _invoice_id
    into _ai_anomesVencimentoInicial;

--  raise notice 'taxaPermanencia %, _ai_anomesVencimentoInicial %', taxaPermanencia, _ai_anomesVencimentoInicial;

  func_sequence = 1;

  for anomes_vencimento,
      product_id,
      product_name,
      _pt_juros,
      price_total,
      price_total_anomes,
      juros,
      _anomes_vencimento_count,
      total_agua,
      total_contribuicaomensal,
      total_areaverde,
      total_taxacaptacao,
      total_taxas
   in select t.anomes_vencimento,
             t.product_id,
             t.product_name,
             t.pt_juros,
             t.price_total,
             sum(t.price_total) filter(where not t.pt_juros) over(partition by t.anomes_vencimento) price_total_anomes,
             sum(t.price_total) filter(where     t.pt_juros) over() juros,
             t.anomes_vencimento_count,
             t.total_agua,
             t.total_contribuicaomensal,
             t.total_areaverde,
             t.total_taxacaptacao,
             t.total_taxas
        from (select ail.anomes_vencimento,
                     ail.product_id_tranformado product_id,
                     pt."name" product_name,
                     coalesce(pt.juros, false) pt_juros,
                     sum(ail.price_total) price_total,
                     sum(case when ail.product_id = 7 then ail.price_total else 0 end) total_agua,
                     sum(case when ail.product_id = 1 then ail.price_total else 0 end) total_contribuicaomensal,
                     sum(case when ail.product_id = 10 then ail.price_total else 0 end) total_areaverde,
                     sum(case when ail.product_id = 9 then ail.price_total else 0 end) total_taxacaptacao,
                     sum(case when ail.product_id_tranformado = 33 then ail.price_total else 0 end) total_taxas,
                     count(0) over(partition by ail.anomes_vencimento) anomes_vencimento_count
                from (select ail2.anomes_vencimento,
                             case when ail2.product_id = 9/*Taxa Captação*/ then 7/*água*/
                                  when coalesce(pt.juros, false) then 12 /*Multa, Juros e correção monetária*/
                                  when ((ail2.product_id not in (1, 7, 10, 9)) and (not coalesce(pt.juros, false))) then 33 /*Taxas*/
                                  else ail2.product_id
                             end product_id_tranformado,
                             ail2.product_id,
                             ail2.price_total
                        from account_invoice_line ail2 join product_template pt on pt.id = ail2.product_id
                       where ail2.invoice_id = _invoice_id
                     ) ail join product_template pt on pt.id = ail.product_id_tranformado
               group by
                     ail.anomes_vencimento,
                     ail.product_id_tranformado,
                     pt."name",
                     coalesce(pt.juros, false)
               order by
                     ail.anomes_vencimento,
                     case when coalesce(pt.juros, false) then 0 else 1 end,
                     price_total
              ) t
  loop
     if (func_sequence = 1) then
       total_juros = juros + taxaPermanencia;
     end if;

     if (_anomes_vencimento_current is distinct from anomes_vencimento) then
       --Mudou ano/mês
--       raise notice 'Novo ano/mês de % para % ', _anomes_vencimento_current, anomes_vencimento;
       _anomes_vencimento_current = anomes_vencimento;
       juros_anomes = 0;
       txpermanencia_anomes = 0;

--       raise notice 'anomes_vencimento %, _ai_anomesVencimentoInicial %', anomes_vencimento, _ai_anomesVencimentoInicial;

       if (anomes_vencimento = _ai_anomesVencimentoInicial) then
         txpermanencia_anomes = coalesce(taxaPermanencia, 0);
--         raise notice 'txpermanencia_anomes %, taxaPermanencia %', txpermanencia_anomes, taxaPermanencia;
       end if;

       if (_pt_juros) then
         juros_anomes = price_total;
       end if;

       jurostotal_anomes = juros_anomes + txpermanencia_anomes;
       _anomes_vencimento_index = 0;
      _jurosProporcionalJaDiluido_Anomes = 0;

       if (_pt_juros) then
         _anomes_vencimento_index = _anomes_vencimento_index + 1;
         continue;
       end if;
     end if;

--     raise notice 'func_sequence %, product_name %, anomes_vencimento %, juros_anomes % ', func_sequence, product_name, anomes_vencimento, juros_anomes;

     descontos = 0;

     if (total_taxas < 0) then
       descontos = total_taxas;
       total_taxas = 0;
     end if;

     _anomes_vencimento_index = _anomes_vencimento_index + 1;

     jurosproporcional_perc = price_total / price_total_anomes;

     if (_anomes_vencimento_index = _anomes_vencimento_count) then
       --É o último registro do ano/mês. Vou jogar diretamente a diferença de juros que falta
       jurosproporcional_total = jurostotal_anomes - _jurosProporcionalJaDiluido_Anomes;
     else
       jurosproporcional_total = round(jurosproporcional_perc * jurostotal_anomes, 2);
     end if;

     _jurosProporcionalJaDiluido_Anomes = _jurosProporcionalJaDiluido_Anomes + jurosproporcional_total;

     if (product_id = 10) then
       juros_areaverde = jurosproporcional_total;
       jurosproporcional_valor = 0;
     else
       juros_areaverde = 0;
       jurosproporcional_valor = jurosproporcional_total;
     end if;


     return next;
--     raise notice '-------------------';
     func_sequence = func_sequence + 1;
  end loop;
end
$function$
;

commit;

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
    ims.tipocob__automatico_boleto_dinheiro::character varying AS tipocobranca,
    case
        when ims.cnab_semcnab = 'cnab-manual'::text then 'cnab-manual'::text
        else ''::text
    end AS observacao,
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
    t.price_total + t.jurosproporcional_total AS price_total_juros,
    ims.tipocob__automatico_boleto_dinheiro,
    ims.cnab_semcnab
   FROM vw_account_invoice_move_sum ims
     join account_invoice ai on ai.id = ims.invoice_id
     join vw_property_land vpl on vpl.id = ai.land_id
     join res_partner rp on rp.id = ai.partner_id
     left join func_report_contab_baixados(ims.invoice_id) t on true
   where ( true or
         ('' = 'versão-2024-02-19-task-422')
         );


commit;
-->>>>>>>>>>>>>>>>>>>>>>>
--Recriando dependências...


CREATE OR REPLACE VIEW public.vw_vs_vw_l10n_br_cnab_return_event__vw_report_contab_baixados
AS SELECT
        CASE
            WHEN cnab.cnab = 1 AND contab.contab = 1 THEN 'ambos'::text
            WHEN cnab.cnab = 1 THEN 'cnab'::text
            WHEN contab.contab = 1 THEN 'contab'::text
            ELSE NULL::text
        END AS existe,
    cnab.cnab_id,
    COALESCE(cnab.invoice_id, contab.invoice_id) AS invoice_id,
    COALESCE(cnab.occurrence_date, contab.occurrence_date) AS occurrence_date,
    cnab.dt_importacao AS cnab_dt_importacao,
    cnab.payment_value AS cnab_valor,
    contab.price_total_juros AS contab_valor,
    COALESCE(cnab.payment_value, 0::numeric) - COALESCE(contab.price_total_juros, 0::numeric) AS dif_valor,
    abs(COALESCE(cnab.payment_value, 0::numeric) - COALESCE(contab.price_total_juros, 0::numeric)) AS dif_valorabs,
    contab.tipocob__automatico_boleto_dinheiro AS contab_tipocob__automatico_boleto_dinheiro,
    cnab.occurrence_date AS cnab_occurrence_date,
    contab.occurrence_date AS contab_occurrence_date,
    cnab.invoice_id AS cnab_invoice_id,
    contab.invoice_id AS contab_invoice_id
   FROM ( SELECT 1 AS cnab,
            e.id AS cnab_id,
            e.invoice_id,
            e.occurrence_date,
            e.dt_importacao,
            e.payment_value::numeric AS payment_value
           FROM vw_l10n_br_cnab_return_event e
          WHERE e.occurrences::text = '06-Liquidação Normal *'::text AND e.occurrence_date = '2024-02-14'::date) cnab
     FULL JOIN ( SELECT 1 AS contab,
            b.invoice_id,
            b.occurrence_date,
            b.tipocob__automatico_boleto_dinheiro,
            round(sum(b.price_total_juros), 2) AS price_total_juros
           FROM vw_report_contab_baixados b
          WHERE (b.tipocob__automatico_boleto_dinheiro = ANY (ARRAY['A'::text, 'B'::text])) AND b.occurrence_date = '2024-02-14'::date
          GROUP BY 1::integer, b.invoice_id, b.occurrence_date, b.tipocob__automatico_boleto_dinheiro) contab ON contab.invoice_id = cnab.invoice_id AND contab.occurrence_date = cnab.occurrence_date;

-- public.invoice_product_report source

CREATE OR REPLACE VIEW public.invoice_product_report
AS SELECT ail.invoice_id AS id,
    ail.invoice_id,
    ail.land_id,
    ail.module_code,
    ail.block_code,
    ail.lot_code,
    ail.referencia,
    ail.total_agua,
    ail.total_contribuicaomensal,
    ail.total_taxas,
    ail.jurosproporcional_valor,
    ail.total_areaverde,
    ail.juros_areaverde,
    ail.total_taxacaptacao,
    ail.descontos,
    ail.price_total,
    ail.occurrence_date,
    ail.tipocobranca,
    ail.observacao,
    ail.real_payment_date,
    ail.due_date,
    ail.anomes_vencimento,
    ail.res_id,
    ail.res_name,
    ail.land,
    ail.product_id,
    ail.product_name,
    ail.price_total_sum,
    ail.total_juros,
    ail.jurosproporcional_perc,
    ail.price_total_juros
   FROM vw_report_contab_baixados ail;

-- public.x_bi_sql_view_contabil_riviera_baixados source
-- aparentemente desnecessária esta recriação (e demorada) - Será provisoriamente comentada
/*
CREATE MATERIALIZED VIEW public.x_bi_sql_view_contabil_riviera_baixados
TABLESPACE pg_default
AS SELECT row_number() OVER ()::integer AS id,
    NULL::timestamp without time zone AS create_date,
    NULL::integer AS create_uid,
    NULL::timestamp without time zone AS write_date,
    NULL::integer AS write_uid,
    my_query.x_invoice_id,
    my_query.x_land_id,
    my_query.x_module_code,
    my_query.x_block_code,
    my_query.x_lot_code,
    my_query.x_referencia,
    my_query.x_total_agua,
    my_query.x_total_contribuicaomensal,
    my_query.x_total_taxas,
    my_query.x_jurosproporcional_valor,
    my_query.x_total_areaverde,
    my_query.x_juros_areaverde,
    my_query.x_total_taxacaptacao,
    my_query.x_descontos,
    my_query.x_price_total,
    my_query.x_occurrence_date,
    my_query.x_real_payment_date,
    my_query.x_tipocobranca,
    my_query.x_observacao,
    my_query.x_due_date,
    my_query.x_anomes_vencimento,
    my_query.x_res_id,
    my_query.x_res_name,
    my_query.x_land,
    my_query.x_product_id,
    my_query.x_product_name,
    my_query.x_price_total_sum,
    my_query.x_total_juros,
    my_query.x_jurosproporcional_perc,
    my_query.x_price_total_juros,
    my_query.x_tipocob__automatico_boleto_dinheiroo
   FROM ( SELECT v.invoice_id AS x_invoice_id,
            v.land_id AS x_land_id,
            v.module_code AS x_module_code,
            v.block_code AS x_block_code,
            v.lot_code AS x_lot_code,
            v.referencia AS x_referencia,
            v.total_agua AS x_total_agua,
            v.total_contribuicaomensal AS x_total_contribuicaomensal,
            v.total_taxas AS x_total_taxas,
            v.jurosproporcional_valor AS x_jurosproporcional_valor,
            v.total_areaverde AS x_total_areaverde,
            v.juros_areaverde AS x_juros_areaverde,
            v.total_taxacaptacao AS x_total_taxacaptacao,
            v.descontos AS x_descontos,
            v.price_total AS x_price_total,
            v.occurrence_date AS x_occurrence_date,
            v.real_payment_date AS x_real_payment_date,
            v.tipocobranca AS x_tipocobranca,
            v.observacao AS x_observacao,
            v.due_date AS x_due_date,
            v.anomes_vencimento AS x_anomes_vencimento,
            v.res_id AS x_res_id,
            v.res_name AS x_res_name,
            v.land AS x_land,
            v.product_id AS x_product_id,
            v.product_name AS x_product_name,
            v.price_total_sum AS x_price_total_sum,
            v.total_juros AS x_total_juros,
            v.jurosproporcional_perc AS x_jurosproporcional_perc,
            v.price_total_juros AS x_price_total_juros,
            v.tipocob__automatico_boleto_dinheiro AS x_tipocob__automatico_boleto_dinheiroo
           FROM vw_report_contab_baixados v) my_query
WITH DATA;

*/

commit;

-- public.x_bi_sql_view_items_fatura_cont_riv source
-- aparentemente desnecessária esta recriação (e demorada) - Será provisoriamente comentada
/*

CREATE MATERIALIZED VIEW public.x_bi_sql_view_items_fatura_cont_riv
TABLESPACE pg_default
AS SELECT row_number() OVER ()::integer AS id,
    NULL::timestamp without time zone AS create_date,
    NULL::integer AS create_uid,
    NULL::timestamp without time zone AS write_date,
    NULL::integer AS write_uid,
    my_query.x_invoice_id,
    my_query.x_land_id,
    my_query.x_module_code,
    my_query.x_block_code,
    my_query.x_lot_code,
    my_query.x_referencia,
    my_query.x_total_agua,
    my_query.x_total_contribuicaomensal,
    my_query.x_total_taxas,
    my_query.x_jurosproporcional_valor,
    my_query.x_total_areaverde,
    my_query.x_juros_areaverde,
    my_query.x_total_taxacaptacao,
    my_query.x_descontos,
    my_query.x_price_total,
    my_query.x_occurrence_date,
    my_query.x_real_payment_date,
    my_query.x_tipocobranca,
    my_query.x_observacao,
    my_query.x_due_date,
    my_query.x_anomes_vencimento,
    my_query.x_res_id,
    my_query.x_res_name,
    my_query.x_land,
    my_query.x_product_id,
    my_query.x_product_name,
    my_query.x_price_total_sum,
    my_query.x_total_juros,
    my_query.x_jurosproporcional_perc,
    my_query.x_price_total_juros,
    my_query.x_tipocob__automatico_boleto_dinheiro
   FROM ( SELECT vw_report_contab_baixados.invoice_id AS x_invoice_id,
            vw_report_contab_baixados.land_id AS x_land_id,
            vw_report_contab_baixados.module_code AS x_module_code,
            vw_report_contab_baixados.block_code AS x_block_code,
            vw_report_contab_baixados.lot_code AS x_lot_code,
            vw_report_contab_baixados.referencia AS x_referencia,
            vw_report_contab_baixados.total_agua AS x_total_agua,
            vw_report_contab_baixados.total_contribuicaomensal AS x_total_contribuicaomensal,
            vw_report_contab_baixados.total_taxas AS x_total_taxas,
            vw_report_contab_baixados.jurosproporcional_valor AS x_jurosproporcional_valor,
            vw_report_contab_baixados.total_areaverde AS x_total_areaverde,
            vw_report_contab_baixados.juros_areaverde AS x_juros_areaverde,
            vw_report_contab_baixados.total_taxacaptacao AS x_total_taxacaptacao,
            vw_report_contab_baixados.descontos AS x_descontos,
            vw_report_contab_baixados.price_total AS x_price_total,
            vw_report_contab_baixados.occurrence_date AS x_occurrence_date,
            vw_report_contab_baixados.real_payment_date AS x_real_payment_date,
            vw_report_contab_baixados.tipocobranca AS x_tipocobranca,
            vw_report_contab_baixados.observacao AS x_observacao,
            vw_report_contab_baixados.due_date AS x_due_date,
            vw_report_contab_baixados.anomes_vencimento AS x_anomes_vencimento,
            vw_report_contab_baixados.res_id AS x_res_id,
            vw_report_contab_baixados.res_name AS x_res_name,
            vw_report_contab_baixados.land AS x_land,
            vw_report_contab_baixados.product_id AS x_product_id,
            vw_report_contab_baixados.product_name AS x_product_name,
            vw_report_contab_baixados.price_total_sum AS x_price_total_sum,
            vw_report_contab_baixados.total_juros AS x_total_juros,
            vw_report_contab_baixados.jurosproporcional_perc AS x_jurosproporcional_perc,
            vw_report_contab_baixados.price_total_juros AS x_price_total_juros,
            vw_report_contab_baixados.tipocob__automatico_boleto_dinheiro AS x_tipocob__automatico_boleto_dinheiro
           FROM vw_report_contab_baixados) my_query
WITH DATA;

commit;

*/
-- task_439_contab.vw_contab_odoo_vs_sisa source
create or replace view task_439_contab.vw_contab_odoo_vs_sisa as
select case when sisa.land_id is not null and odoo.land_id is not null then 'Ambos'
            when sisa.land_id is not null then 'Sisa'
            when odoo.land_id is not null then 'Odoo'
       end existe,
       coalesce(sisa.land_id, odoo.land_id) land_id,
       coalesce(sisa.modulo, odoo.modulo) modulo,
       coalesce(sisa.quadra, odoo.quadra) quadra,
       coalesce(sisa.lote, odoo.lote) lote,
       vpl.module_code__block_code__lot_code2 land,
       'XXXXXXX1' XXXXXXX1,
       sisa.agua_sisa,
       odoo.agua_odoo,
       coalesce(sisa.agua_sisa, 0) - coalesce(odoo.agua_odoo, 0) agua_dif,
       sisa.ctm_sisa,
       odoo.ctm_odoo,
       coalesce(sisa.ctm_sisa, 0) - coalesce(odoo.ctm_odoo, 0) ctm_dif,
       sisa.taxas_sisa,
       odoo.taxas_odoo,
       coalesce(sisa.taxas_sisa, 0) - coalesce(odoo.taxas_odoo, 0) taxas_dif,
       sisa.mjc_sisa,
       odoo.mjc_odoo,
       coalesce(sisa.mjc_sisa, 0) - coalesce(odoo.mjc_odoo, 0) mjc_dif,
       sisa.mav_sisa,
       odoo.mav_odoo,
       coalesce(sisa.mav_sisa, 0) - coalesce(odoo.mav_odoo, 0) mav_dif,
       sisa.mjmax_sisa,
       odoo.mjmax_odoo,
       coalesce(sisa.mjmax_sisa, 0) - coalesce(odoo.mjmax_odoo, 0) mjmax_dif,
       sisa.captacao_sisa,
       odoo.captacao_odoo,
       coalesce(sisa.captacao_sisa, 0) - coalesce(odoo.captacao_odoo, 0) captacao_dif,
       sisa.mjcaptacao_sisa,
       odoo.mjcaptacao_odoo,
       coalesce(sisa.mjcaptacao_sisa, 0) - coalesce(odoo.mjcaptacao_odoo, 0) mjcaptacao_dif,
       sisa.desconto_sisa,
       odoo.desconto_odoo,
       coalesce(sisa.desconto_sisa, 0) - coalesce(odoo.desconto_odoo, 0) desconto_dif,
       sisa.total_sisa,
       odoo.total_odoo,
       coalesce(sisa.total_sisa, 0) - coalesce(odoo.total_odoo, 0) total_dif,
       'XXXXXXX2' XXXXXXX2,
       sisa.dtpagamento_sisa,
       odoo.dtpagamento_odoo,
       case when sisa.dtpagamento_sisa is distinct from odoo.dtpagamento_odoo then 'Diferente' else '' end dtpagamento_dif,
       sisa.tipocob_sisa,
       odoo.tipocob_odoo,
       case when sisa.tipocob_sisa is distinct from odoo.tipocob_odoo then 'Diferente' else '' end tipocob_dif,
       sisa.referencia_sisa,
       odoo.referencia_odoo,
       case when sisa.referencia_sisa is distinct from odoo.referencia_odoo then 'Diferente' else '' end referencia_dif,
       sisa.datavencimento_sisa,
       odoo.datavencimento_odoo,
       case when sisa.datavencimento_sisa is distinct from odoo.datavencimento_odoo then 'Diferente' else '' end datavencimento_dif,
       'XXXXXXX3' XXXXXXX3,
       sisa.databaixa_sisa,
       sisa.valorbanco_sisa,
       sisa.ids_sisa,
       sisa.codigoboletos_sisa,
       odoo.invoices_odoo,
       pt.id product_id,
       pt.name product_name
  from (
       select string_agg(distinct cs.id::varchar, ',') ids_sisa,
              string_agg(distinct cs.codigoboleto::varchar, ',') codigoboletos_sisa,
              cs.land_id,
              cs.modulo,
              cs.quadra,
              cs.lote,
              cs.datavencimento::date datavencimento_sisa,
              cs.databaixa databaixa_sisa,
              cs.datapagamento::date dtpagamento_sisa,
              cs.tipo tipocob_sisa,
              cs.product_id,
              cs.referencia_anomes referencia_sisa,
              sum(cs.valoremitidoagua) agua_sisa,
              sum(cs.valoremitidocm) ctm_sisa,
              sum(cs.valortaxas) taxas_sisa,
              sum(cs.mjc) mjc_sisa,
              sum(cs.mav) mav_sisa,
              sum(cs.mjcmav) mjmax_sisa,
              sum(cs.tc) captacao_sisa,
              sum(cs.mjctc) mjcaptacao_sisa,
              sum(cs.valordesconto) desconto_sisa,
              sum(cs.total) total_sisa,
              sum(cs.valorbanco) valorbanco_sisa
         from task_439_contab.contab cs
--        where cs.codigo in (3008, -2266)
        group by
              cs.land_id,
               cs.modulo,
               cs.quadra,
               cs.lote,
               cs.datavencimento,
               cs.databaixa,
               cs.datapagamento,
               cs.tipo,
               cs.product_id,
               cs.referencia_anomes
      ) sisa full join
      (select string_agg(distinct co.invoice_id::varchar, ',') invoices_odoo,
              co.land_id,
              co.module_code::integer modulo,
              co.block_code quadra,
              co.lot_code lote,
              co.occurrence_date dtpagamento_odoo,
              co.tipocobranca tipocob_odoo,
              co.anomes_vencimento anomes_vencimento,
              case when co.product_id = 9 then 7 else co.product_id end product_id,
              co.anomes_vencimento referencia_odoo,
              co.due_date datavencimento_odoo,
              sum(co.total_agua) agua_odoo,
              sum(co.total_contribuicaomensal) ctm_odoo,
              sum(co.total_taxas) taxas_odoo,
              sum(co.jurosproporcional_valor) mjc_odoo,
              sum(co.total_areaverde) mav_odoo,
              sum(co.juros_areaverde) mjmax_odoo,
              sum(co.total_taxacaptacao) captacao_odoo,
              0 mjcaptacao_odoo,
              sum(co.descontos) desconto_odoo,
              round(sum(co.price_total_juros), 2) total_odoo
         from vw_report_contab_baixados co
        where co.occurrence_date between '2024-01-01' and '2024-01-31'
--          and co.land_id in (3008, -2266)
        group by
              co.land_id,
              co.module_code,
              co.block_code,
              co.lot_code,
              co.occurrence_date,
              co.tipocobranca,
              co.anomes_vencimento,
              case when co.product_id = 9 then 7 else co.product_id end,
              co.due_date
       ) odoo on sisa.land_id = odoo.land_id and sisa.product_id = odoo.product_id
       left join product_template pt on pt.id = coalesce(sisa.product_id, odoo.product_id)
       left join vw_property_land vpl on vpl.id = coalesce(sisa.land_id, odoo.land_id);

-- task_439_contab.vw_contab_odoo_vs_sisa_m source
-- momentaneamente comentada (está sendo utilizada para testes)
/*
CREATE MATERIALIZED VIEW task_439_contab.vw_contab_odoo_vs_sisa_m
TABLESPACE pg_default
AS SELECT vw_contab_odoo_vs_sisa.existe,
    vw_contab_odoo_vs_sisa.land_id,
    vw_contab_odoo_vs_sisa.modulo,
    vw_contab_odoo_vs_sisa.quadra,
    vw_contab_odoo_vs_sisa.lote,
    vw_contab_odoo_vs_sisa.xxxxxxx1,
    vw_contab_odoo_vs_sisa.agua_sisa,
    vw_contab_odoo_vs_sisa.agua_odoo,
    vw_contab_odoo_vs_sisa.agua_dif,
    vw_contab_odoo_vs_sisa.ctm_sisa,
    vw_contab_odoo_vs_sisa.ctm_odoo,
    vw_contab_odoo_vs_sisa.ctm_dif,
    vw_contab_odoo_vs_sisa.taxas_sisa,
    vw_contab_odoo_vs_sisa.taxas_odoo,
    vw_contab_odoo_vs_sisa.taxas_dif,
    vw_contab_odoo_vs_sisa.mjc_sisa,
    vw_contab_odoo_vs_sisa.mjc_odoo,
    vw_contab_odoo_vs_sisa.mjc_dif,
    vw_contab_odoo_vs_sisa.mav_sisa,
    vw_contab_odoo_vs_sisa.mav_odoo,
    vw_contab_odoo_vs_sisa.mav_dif,
    vw_contab_odoo_vs_sisa.mjmax_sisa,
    vw_contab_odoo_vs_sisa.mjmax_odoo,
    vw_contab_odoo_vs_sisa.mjmax_dif,
    vw_contab_odoo_vs_sisa.captacao_sisa,
    vw_contab_odoo_vs_sisa.captacao_odoo,
    vw_contab_odoo_vs_sisa.captacao_dif,
    vw_contab_odoo_vs_sisa.mjcaptacao_sisa,
    vw_contab_odoo_vs_sisa.mjcaptacao_odoo,
    vw_contab_odoo_vs_sisa.mjcaptacao_dif,
    vw_contab_odoo_vs_sisa.desconto_sisa,
    vw_contab_odoo_vs_sisa.desconto_odoo,
    vw_contab_odoo_vs_sisa.desconto_dif,
    vw_contab_odoo_vs_sisa.total_sisa,
    vw_contab_odoo_vs_sisa.total_odoo,
    vw_contab_odoo_vs_sisa.total_dif,
    vw_contab_odoo_vs_sisa.xxxxxxx2,
    vw_contab_odoo_vs_sisa.dtpagamento_sisa,
    vw_contab_odoo_vs_sisa.dtpagamento_odoo,
    vw_contab_odoo_vs_sisa.dtpagamento_dif,
    vw_contab_odoo_vs_sisa.tipocob_sisa,
    vw_contab_odoo_vs_sisa.tipocob_odoo,
    vw_contab_odoo_vs_sisa.tipocob_dif,
    vw_contab_odoo_vs_sisa.referencia_sisa,
    vw_contab_odoo_vs_sisa.referencia_odoo,
    vw_contab_odoo_vs_sisa.referencia_dif,
    vw_contab_odoo_vs_sisa.datavencimento_sisa,
    vw_contab_odoo_vs_sisa.datavencimento_odoo,
    vw_contab_odoo_vs_sisa.datavencimento_dif,
    vw_contab_odoo_vs_sisa.xxxxxxx3,
    vw_contab_odoo_vs_sisa.databaixa_sisa,
    vw_contab_odoo_vs_sisa.valorbanco_sisa,
    vw_contab_odoo_vs_sisa.ids_sisa,
    vw_contab_odoo_vs_sisa.codigoboletos_sisa,
    vw_contab_odoo_vs_sisa.invoices_odoo,
    vw_contab_odoo_vs_sisa.product_id,
    vw_contab_odoo_vs_sisa.product_name
   FROM task_439_contab.vw_contab_odoo_vs_sisa
WITH DATA;

commit;

*/

-- public.vw_report_contab_baixados_old_20231010 source

CREATE OR REPLACE VIEW public.vw_report_contab_baixados_old_20231010
AS SELECT t.invoice_id,
    vpl.id AS land_id,
    vpl.module_code,
    vpl.block_code,
    lpad(vpl.lot_code::text, 3, '0'::text) AS lot_code,
    ("substring"(t.anomes_vencimento::character varying::text, 5, 2) || '/'::text) || "substring"(t.anomes_vencimento::character varying::text, 1, 4) AS referencia,
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
    ''::text AS observacao,
    cre.real_payment_date,
    cre.due_date,
    t.anomes_vencimento,
    rp.id AS res_id,
    rp.name AS res_name,
    vpl.module_code__block_code__lot_code2 AS land,
    t.product_id,
    t.product_name,
    t.price_total_sum,
    t.total_juros,
    t.jurosproporcional_perc,
    t.price_total + t.jurosproporcional_valor AS price_total_juros
   FROM l10n_br_cnab_return_event cre
     JOIN account_invoice ai ON ai.id = cre.invoice_id
     JOIN vw_property_land vpl ON vpl.id = ai.land_id
     JOIN res_partner rp ON rp.id = ai.partner_id
     LEFT JOIN LATERAL func_report_contab_baixados(cre.invoice_id) t ON true
  WHERE true AND cre.invoice_id IS NOT NULL AND cre.occurrences::text = '06-Liquidação Normal *'::text AND (true OR ''::text = 'versão-2023-09-04'::text)
  ORDER BY t.invoice_id, t.anomes_vencimento;

commit;


-- public.vw_report_contab_baixados_old_20231116 source

CREATE OR REPLACE VIEW public.vw_report_contab_baixados_old_20231116
AS SELECT ims.invoice_id,
    vpl.id AS land_id,
    vpl.module_code,
    vpl.block_code,
    lpad(vpl.lot_code::text, 3, '0'::text) AS lot_code,
    ("substring"(t.anomes_vencimento::character varying::text, 5, 2) || '/'::text) || "substring"(t.anomes_vencimento::character varying::text, 1, 4) AS referencia,
    t.total_agua,
    t.total_contribuicaomensal,
    t.total_taxas,
    t.jurosproporcional_valor,
    t.total_areaverde,
    t.juros_areaverde,
    t.total_taxacaptacao,
    t.descontos,
    t.price_total,
    ims.datapagamento_ocorrencia_max AS occurrence_date,
    ims.datapagamento_real_max AS real_payment_date,
    ''::text AS observacao,
    ims.invoice_date_due AS due_date,
    t.anomes_vencimento,
    rp.id AS res_id,
    rp.name AS res_name,
    vpl.module_code__block_code__lot_code2 AS land,
    t.product_id,
    t.product_name,
    t.price_total_sum,
    t.total_juros,
    t.jurosproporcional_perc,
    t.price_total + t.jurosproporcional_valor AS price_total_juros,
    ims.tipocob__automatico_boleto_dinheiro
   FROM vw_account_invoice_move_sum ims
     JOIN account_invoice ai ON ai.id = ims.invoice_id
     JOIN vw_property_land vpl ON vpl.id = ai.land_id
     JOIN res_partner rp ON rp.id = ai.partner_id
     LEFT JOIN LATERAL func_report_contab_baixados(ims.invoice_id) t ON true
  WHERE true OR ''::text = 'versão-2023-10-09'::text;

-- public.vw_report_contab_baixados_old_20240317 source
 -- DROP FUNCTION public.func_report_contab_baixados_20240317(int4);
--Backup da função que estou mexendo neste script
CREATE OR REPLACE FUNCTION public.func_report_contab_baixados_20240317(_invoice_id integer)
 RETURNS TABLE(invoice_id integer, anomes_vencimento integer, product_id integer, product_name character varying, price_total_sum numeric, total_juros numeric, jurosproporcional_perc numeric, jurosproporcional_valor numeric, juros_areaverde numeric, price_total numeric, total_agua numeric, total_contribuicaomensal numeric, total_taxas numeric, total_areaverde numeric, total_taxacaptacao numeric, descontos numeric, tipocobranca character varying)
 LANGUAGE sql
AS $function$
--versao=2023-10-13
select ail.invoice_id,
       ail.anomes_vencimento,
       ail.product_id,
       ail.product_name,
       ail_total.price_total price_total_sum,
       ail_juros.price_total total_juros,
       coalesce(round(ail.price_total / (ail_total.price_total - ail_juros.price_total), 3), 0) jurosproporcional_perc,
       coalesce(round((ail.price_total / (ail_total.price_total - ail_juros.price_total)) * ail_juros.price_total, 3), 0) jurosproporcional_valor,
       0::numeric juros_areaverde,
       ail.price_total,
       ail.total_agua,
       ail.total_contribuicaomensal,
       ail.total_taxas,
       ail.total_areaverde,
       ail.total_taxacaptacao,
       0::numeric descontos,
       case when exists
       (select 1
          from res_partner_bank rpb
         where rpb.partner_id = ail.partner_id
           and rpb.acc_number is not null
       ) then 'A' else 'B' end tipocobranca --A-> Débito automático, B -> boleto
  from (select ail.invoice_id,
               ail.partner_id,
               ail.anomes_vencimento,
               ail.product_id,
               pt."name" product_name,
               sum(ail.price_total) price_total,
               sum(case when ail.product_id = 7 then ail.price_total else 0 end) total_agua,
               sum(case when ail.product_id = 1 then ail.price_total else 0 end) total_contribuicaomensal,
               sum(case when ail.product_id in (13, 11) then ail.price_total else 0 end) total_taxas,
               sum(case when ail.product_id = 10 then ail.price_total else 0 end) total_areaverde,
               sum(case when ail.product_id = 9 then ail.price_total else 0 end) total_taxacaptacao
          from account_invoice_line ail join product_template pt on pt.id = ail.product_id
         where ail.invoice_id = _invoice_id
           and ail.product_id <> 12
         group by
               ail.invoice_id,
               ail.partner_id,
               ail.anomes_vencimento,
               ail.product_id,
               pt."name"
       ) ail
       left join
       (select aims.valorpago price_total
          from vw_account_invoice_move_sum aims
         where aims.invoice_id = _invoice_id
       ) ail_total on true
       left join
       (select sum(t.price_total) price_total
          from (select ail.invoice_id,
                       ail.anomes_vencimento,
                       sum(ail.price_total) price_total
                  from account_invoice_line ail join product_template pt on pt.id = ail.product_id
                 where ail.product_id = 12
                   and ail.invoice_id = _invoice_id
                 group by ail.invoice_id, ail.anomes_vencimento
                 union all
                select aims.invoice_id,
                       anomes(aims.invoice_date_due) anomes_vencimento,
                       aims.valorjuros_cnab::numeric price_total
                  from vw_account_invoice_move_sum aims
                 where aims.invoice_id = _invoice_id
               ) t
       ) ail_juros on true
   where ail.invoice_id = _invoice_id;
$function$
;


CREATE OR REPLACE VIEW public.vw_report_contab_baixados_old_20240317
AS SELECT ims.invoice_id,
    vpl.id AS land_id,
    vpl.module_code,
    vpl.block_code,
    lpad(vpl.lot_code::text, 3, '0'::text) AS lot_code,
    ("substring"(t.anomes_vencimento::character varying::text, 5, 2) || '/'::text) || "substring"(t.anomes_vencimento::character varying::text, 1, 4) AS referencia,
    t.total_agua,
    t.total_contribuicaomensal,
    t.total_taxas,
    t.jurosproporcional_valor,
    t.total_areaverde,
    t.juros_areaverde,
    t.total_taxacaptacao,
    t.descontos,
    t.price_total,
    ims.datapagamento_ocorrencia_max AS occurrence_date,
    ims.datapagamento_real_max AS real_payment_date,
    ims.tipocob__automatico_boleto_dinheiro::character varying AS tipocobranca,
        CASE
            WHEN ims.cnab_semcnab = 'cnab-manual'::text THEN 'cnab-manual'::text
            ELSE ''::text
        END AS observacao,
    ims.invoice_date_due AS due_date,
    t.anomes_vencimento,
    rp.id AS res_id,
    rp.name AS res_name,
    vpl.module_code__block_code__lot_code2 AS land,
    t.product_id,
    t.product_name,
    t.price_total_sum,
    t.total_juros,
    t.jurosproporcional_perc,
    t.price_total + t.jurosproporcional_valor AS price_total_juros,
    ims.tipocob__automatico_boleto_dinheiro,
    ims.cnab_semcnab
   FROM vw_account_invoice_move_sum ims
     JOIN account_invoice ai ON ai.id = ims.invoice_id
     JOIN vw_property_land vpl ON vpl.id = ai.land_id
     JOIN res_partner rp ON rp.id = ai.partner_id
     LEFT JOIN LATERAL func_report_contab_baixados_20240317(ims.invoice_id) t ON true
  WHERE true OR ''::text = 'versão-2024-02-19-task-422'::text; 
 
--<<<<<<<<<<<<<<<<<<<<<<<
