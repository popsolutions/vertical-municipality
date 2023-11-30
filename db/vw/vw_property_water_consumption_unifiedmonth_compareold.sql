create or replace view vw_property_water_consumption_unifiedmonth_compareold as
select ym.yearmonth_vencimento,
       ym.yearmonth_ref,
       ym.yearmonth_ref_old,
       plug.id land_id,
       rp."name" nomeproprietario,
       plug.module_code__block_code__lot_code2 land,
       plug.module_code__block_code__lot_code2_childs land_childs,
       plug.unified_count,
       pwc_group.consumption unifiedmonth_consumption,
       pwc_group.total unifiedmonth_total,
       pwc_group.qtdelotes unifiedmonth_qtdelotes,
       pwc_group_oldmonth.consumption unifiedmonth_old_consumption,
       pwc_group_oldmonth.total unifiedmonth_old_total,
       pwc_group_oldmonth.qtdelotes unifiedmonth_old_qtdelotes,
       case when coalesce(pwc_group_oldmonth.consumption, 0) = 0 then 0 else round(((pwc_group.consumption::numeric  / pwc_group_oldmonth.consumption) - 1) * 100, 2) end  unified_difperc_consumption,
       case when coalesce(pwc_group_oldmonth.total, 0) = 0 then 0 else round(((pwc_group.total / pwc_group_oldmonth.total)::numeric - 1) * 100, 2) end unified_difperc_total,
       pwc_group.consumption - pwc_group_oldmonth.consumption unified_difval_consumption,
       pwc_group.total - pwc_group_oldmonth.total unified_difval_total
  from (select anomes_inc(yearmonth_ref, 1) yearmonth_vencimento,
               yearmonth_ref,
               anomes_inc(yearmonth_ref, -1) yearmonth_ref_old
          from (select distinct anomes(date) yearmonth_ref
                  from property_water_consumption
               ) y
       ) ym,
       vw_property_land_unified_group plug
       left join lateral (
       select sum(pwc_old_month.consumption) consumption,
              round(sum(pwc_old_month.total::numeric), 2) total,
              count(0) qtdelotes
         from vw_property_land_unified plu,
              property_water_consumption pwc_old_month
        where plu.unified_property_id_orid = plug.id
          and pwc_old_month.land_id = plu.id
          and pwc_old_month.issue_id = 1 /*Leitura*/
          and pwc_old_month.state = 'processed'
          and anomes(pwc_old_month."date") = ym.yearmonth_ref_old
       ) pwc_group_oldmonth on true
       left join lateral (
       select sum(pwc_cur_month.consumption) consumption,
              round(sum(pwc_cur_month.total::numeric), 2) total,
              count(0) qtdelotes
         from vw_property_land_unified plu,
              property_water_consumption pwc_cur_month
        where plu.unified_property_id_orid = plug.id
          and pwc_cur_month.land_id = plu.id
          and pwc_cur_month.issue_id = 1 /*Leitura*/
          and pwc_cur_month.state = 'processed'
          and anomes(pwc_cur_month."date") = ym.yearmonth_ref
       ) pwc_group on true
       join property_land pl on pl.id = plug.id
       join res_partner rp on rp.id = pl.owner_id
 where true
 order by plug.unified_count desc;

COMMENT ON VIEW public.vw_property_water_consumption_unifiedmonth_compareold IS '
Esta view exibe o valor de consumo mensal de cada lote juntando seus respectivos filhos (unifieds) e compara com os valores do mês anterior

Esta view foi criada inicialmente para atender a task task 321(1. Alerta de consumo acima de 50% com relação Ao consumo anterior) porém não foi utilizada pois já existia no fonte uma maneira de fazer a análise de percentagem de aumento de consumo
'