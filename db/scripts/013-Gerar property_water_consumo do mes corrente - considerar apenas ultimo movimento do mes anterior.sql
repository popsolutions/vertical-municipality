create or replace view vw_property_water_consumption_last_month as
select * 
  from (
       select row_number() over(partition by pwc.land_id, anomes(pwc."date") order by land_id, pwc."date" desc) seq_land_anomes,
              anomes(pwc."date") anomes,
              pwc.*
         from property_water_consumption pwc
       ) t
 where seq_land_anomes = 1;
