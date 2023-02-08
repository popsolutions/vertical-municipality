insert into property_water_consumption_issue(id, code, "name", create_uid, create_date, write_uid, write_date) VALUES
(2, 'SH', 'SUBSTITUIÇÃO HIDROMETRO', 17, '2023-01-11 14:34:40.414', 17, '2023-01-11 14:34:40.414')

update property_water_consumption_issue
   set code = 'LT',
       NAME = 'LEITURA'
  where id = 1;

update property_water_consumption pwc
   set issue_id = 2
where pwc.issue_id is not null;

update property_water_consumption pwc
   set issue_id = 1
where pwc.issue_id is null;

CREATE INDEX property_water_consumption_anomes_idx ON public.property_water_consumption (anomes(date));

create or replace view vw_property_water_consumption_read as
select *
  from property_water_consumption pwc
 where pwc.issue_id = 1; --leitura

ALTER TABLE public.property_water_consumption ALTER COLUMN issue_id SET NOT NULL;

drop view vw_property_water_consumption_unified_group_cym;

drop view vw_property_water_consumption_unified_cym;

create or replace view vw_property_water_consumption_unified_cym as
select v.*
  from vw_property_water_consumption_unified v,
       vw_property_settings_monthly_last psml
 where anomes(v.date) = psml.year_month_property_water_consumption;

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

drop view vw_property_water_consumption_unified_group;

create or replace view vw_property_water_consumption_unified_group as
select anomes(v."date") anomes,
       unified_property_id_orid,
       string_agg(case when unified_property_id_orid = land_id then v."date"::varchar else '' end, '')::date owner_readDate,
       sum(coalesce(last_read, 0)) last_read,
       sum(coalesce(current_read, 0)) current_read,
       sum(coalesce(consumption, 0)) consumption,
       sum(coalesce(water_consumption_economy_qty, 0)) water_consumption_economy_qty,
       sum(coalesce(total, 0)) total,
       count(0) qtde
  from vw_property_water_consumption_unified v
 group by 1, 2;