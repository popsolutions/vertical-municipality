CREATE OR REPLACE VIEW public.vw_property_water_consumption_unified_group
AS SELECT anomes(v.date::timestamp without time zone) AS anomes,
    v.unified_property_id_orid,
    min(v.date) filter (where v.unified_property_id_orid = v.land_id) owner_readdate,
    sum(COALESCE(v.last_read, 0)) AS last_read,
    sum(COALESCE(v.current_read, 0)) AS current_read,
    sum(COALESCE(v.consumption, 0)) AS consumption,
    sum(COALESCE(v.water_consumption_economy_qty, 0)) AS water_consumption_economy_qty,
    sum(COALESCE(v.total, 0::double precision)) AS total,
    count(0) AS qtde
   FROM vw_property_water_consumption_unified v
  GROUP BY (anomes(v.date::timestamp without time zone)), v.unified_property_id_orid;