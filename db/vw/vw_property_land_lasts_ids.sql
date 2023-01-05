CREATE OR REPLACE VIEW public.vw_property_land_lasts_ids
AS SELECT t.land_id,
    t.year_month,
    t.property_tax_id,
    ptx.date AS property_tax_date,
    t.property_ga_tax_id,
    pga.date AS property_ga_tax_date,
    t.property_water_consumption_id,
    pwc.date AS property_water_consumption_date,
    t.property_water_catchment_id,
    pcc.date AS property_water_catchment_date
   FROM ( SELECT l.id AS land_id,
            ( SELECT p.id
                   FROM property_tax p
                  WHERE p.land_id = l.id AND anomes(p.date) = sml.year_month_property_tax
                  ORDER BY p.date DESC
                 LIMIT 1) AS property_tax_id,
            ( SELECT p.id
                   FROM property_ga_tax p
                  WHERE p.land_id = l.id AND anomes(p.date::timestamp without time zone) = sml.year_month_property_ga_tax
                  ORDER BY p.date DESC
                 LIMIT 1) AS property_ga_tax_id,
            ( SELECT p.id
                   FROM property_water_consumption p
                  WHERE p.land_id = l.id AND anomes(p.date::timestamp without time zone) = sml.year_month_property_water_consumption
                  ORDER BY p.date DESC
                 LIMIT 1) AS property_water_consumption_id,
            ( SELECT p.id
                   FROM property_water_catchment p
                  WHERE p.land_id = l.id AND anomes(p.date::timestamp without time zone) = sml.year_month_property_water_catchment
                  ORDER BY p.date DESC
                 LIMIT 1) AS property_water_catchment_id,
            sml.year_month
           FROM property_land l,
            vw_property_settings_monthly_last sml) t
     LEFT JOIN property_tax ptx ON ptx.id = t.property_tax_id
     LEFT JOIN property_ga_tax pga ON pga.id = t.property_ga_tax_id
     LEFT JOIN property_water_consumption pwc ON pwc.id = t.property_water_consumption_id
     LEFT JOIN property_water_catchment pcc ON pcc.id = t.property_water_catchment_id;