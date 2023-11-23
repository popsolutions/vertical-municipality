-- public.vw_property_water_consumption_last_month source

CREATE OR REPLACE VIEW public.vw_property_water_consumption_last_month
AS SELECT t.seq_land_anomes,
    t.anomes,
    t.id,
    t.land_id,
    t.date,
    t.last_read,
    t.current_read,
    t.consumption,
    t.issue_id,
    t.reader_id,
    t.total,
    t.state,
    t.create_uid,
    t.create_date,
    t.write_uid,
    t.write_date,
    t.photo,
    t.hydrometer_number
   FROM ( SELECT row_number() OVER (PARTITION BY pwc.land_id, (anomes(pwc.date::timestamp without time zone)) order by date desc) AS seq_land_anomes,
            anomes(pwc.date::timestamp without time zone) AS anomes,
            pwc.id,
            pwc.land_id,
            pwc.date,
            pwc.last_read,
            pwc.current_read,
            pwc.consumption,
            pwc.issue_id,
            pwc.reader_id,
            pwc.total,
            pwc.state,
            pwc.create_uid,
            pwc.create_date,
            pwc.write_uid,
            pwc.write_date,
            pwc.photo,
            pwc.hydrometer_number
           FROM property_water_consumption pwc
          WHERE 0 = 0) t
  WHERE t.seq_land_anomes = 1;