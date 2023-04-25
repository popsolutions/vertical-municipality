CREATE INDEX property_land_unified_property_id_idx ON public.property_land (unified_property_id);

CREATE OR REPLACE FUNCTION public.func_land_name(_land_id integer)
 RETURNS varchar
 LANGUAGE plpgsql
AS $function$
declare res varchar;
begin
  select module_code__block_code__lot_code2
    from vw_property_land
   where id = _land_id
    into res;

 return res;
END
$function$
;

drop view if exists vw_property_water_consumption_unified_group_cym;
drop view if exists vw_property_water_consumption_unified_cym;
drop view if exists vw_property_water_consumption_unified_group;
drop view if exists vw_property_water_consumption_unified;

create or replace view vw_property_water_consumption_unified as
select pwc.id,
       coalesce(pl.unified_property_id, pl.id) unified_property_id_orid,
       unified_property_id,
       pwc.land_id,
       pwc.last_read,
       pwc.current_read,
       pwc.consumption,
       pwc.date,
       pwc.total,
       pl.water_consumption_economy_qty
  from property_water_consumption pwc
       join property_land pl on pl.id = pwc.land_id;

create or replace view vw_property_water_consumption_unified as
select pwc.id,
       coalesce(pl.unified_property_id, pl.id) unified_property_id_orid,
       unified_property_id,
       pwc.land_id,
       pwc.last_read,
       pwc.current_read,
       pwc.consumption,
       pwc.date,
       pwc.total,
       pl.water_consumption_economy_qty
  from vw_property_water_consumption_read pwc
       join property_land pl on pl.id = pwc.land_id;

create or replace view vw_property_water_consumption_unified_group as
select anomes(v."date") anomes,
       unified_property_id_orid,
       sum(coalesce(last_read, 0)) last_read,
       sum(coalesce(current_read, 0)) current_read,
       sum(coalesce(consumption, 0)) consumption,
       sum(coalesce(water_consumption_economy_qty, 0)) water_consumption_economy_qty,
       sum(coalesce(total, 0)) total,
       count(0) qtde
  from vw_property_water_consumption_unified v
 group by 1, 2;

create or replace view vw_property_water_consumption_unified_cym as
select *
  from vw_property_water_consumption_unified v,
       (select anomes_primeirodia(v.year_month_property_water_consumption) primeirodia,
               anomes_ultimodia(v.year_month_property_water_consumption) ultimodia
          from vw_property_settings_monthly_last v
       ) anomes_proc
 where v.date between anomes_proc.primeirodia and anomes_proc.ultimodia;

create or replace view vw_property_water_consumption_unified_group_cym as
select unified_property_id_orid,
       sum(coalesce(last_read, 0)) last_read,
       sum(coalesce(current_read, 0)) current_read,
       sum(coalesce(consumption, 0)) consumption,
       sum(coalesce(water_consumption_economy_qty, 0)) water_consumption_economy_qty,
       sum(coalesce(total, 0)) total,
       count(0) qtde
  from vw_property_water_consumption_unified_cym v
 group by unified_property_id_orid;
