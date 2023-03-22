create or replace view vw_property_land_unified as
select coalesce(pl.unified_property_id, pl.id) unified_property_id_orid,
       pl.unified_property_id is null unified_father,--indica que esta propriedade é pai de outras
       pl.*
  from property_land pl;

create or replace view vw_property_land_unified_group as
select t.unified_property_id_orid,
       module_code__block_code__lot_code2,
       unified_count,
       pl.*
  from (select t.unified_property_id_orid,
               string_agg(t.module_code__block_code__lot_code2, ',') module_code__block_code__lot_code2,
               count(0) unified_count
          from (select coalesce(pl.unified_property_id, pl.id) unified_property_id_orid,
                       pl.*,
                       vpl.module_code__block_code__lot_code2
                  from property_land pl
                  join vw_property_land vpl on vpl.id = pl.id
                 order by pl.unified_property_id, vpl.module_code__block_code__lot_code2 nulls first
               ) t
         group by t.unified_property_id_orid
        ) t
        join property_land pl on pl.id = t.unified_property_id_orid;
