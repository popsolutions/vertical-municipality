--Atualizar modulos:
--property_tax
--property_base

update account_invoice_line ail
   set land_id = (select aci.land_id from account_invoice aci where aci.id = ail.invoice_id)
 where land_id is null;

UPDATE public.product_template SET yearmonth_dec_from_invoice=0 WHERE id=12;
UPDATE public.product_template SET yearmonth_dec_from_invoice=0 WHERE id=13;
UPDATE public.product_template SET yearmonth_dec_from_invoice=0 WHERE id=11;
UPDATE public.product_template SET yearmonth_dec_from_invoice=0 WHERE id=14;
UPDATE public.product_template SET yearmonth_dec_from_invoice=0 WHERE id=1;
UPDATE public.product_template SET yearmonth_dec_from_invoice=0 WHERE id=10;
UPDATE public.product_template SET yearmonth_dec_from_invoice=-1 WHERE id=7;
UPDATE public.product_template SET yearmonth_dec_from_invoice=-1 WHERE id=9;

create or replace view vw_product_template_ids as
--Ids relativos a product_template.id
select 12 multa,
       1  property_tax,
       10 property_ga_tax,
       7  property_water_consumption,
       9  property_water_catchment;

create or replace view vw_product_template_yearmonth_dec_from_invoice as
select (select pdt.yearmonth_dec_from_invoice from product_template pdt where pdt.id = pti.multa) multa,
       (select pdt.yearmonth_dec_from_invoice from product_template pdt where pdt.id = pti.property_tax) property_tax,
       (select pdt.yearmonth_dec_from_invoice from product_template pdt where pdt.id = pti.property_ga_tax) property_ga_tax,
       (select pdt.yearmonth_dec_from_invoice from product_template pdt where pdt.id = pti.property_water_consumption) property_water_consumption,
       (select pdt.yearmonth_dec_from_invoice from product_template pdt where pdt.id = pti.property_water_catchment) property_water_catchment
  from vw_product_template_ids pti;

drop view vw_property_settings_monthly_last;

CREATE OR REPLACE VIEW public.vw_property_settings_monthly
AS SELECT psm.year_month,
    (((("substring"(psm.year_month::character varying::text, 1, 4) || '-'::text) || "substring"(psm.year_month::character varying::text, 5, 4)) || '-'::text) || '10'::text)::date AS invoice_date_due,
    psm.index_coin,
    anomes_inc(psm.year_month, yfi.multa) year_month_multa,
    anomes_inc(psm.year_month, yfi.property_tax) year_month_property_tax,
    anomes_inc(psm.year_month, yfi.property_ga_tax) year_month_property_ga_tax,
    anomes_inc(psm.year_month, yfi.property_water_consumption) year_month_property_water_consumption,
    anomes_inc(psm.year_month, yfi.property_water_catchment) year_month_property_water_catchment
   FROM property_settings_monthly psm,
        vw_product_template_yearmonth_dec_from_invoice yfi
  ORDER BY psm.year_month DESC;

CREATE OR REPLACE VIEW public.vw_property_settings_monthly_last AS
SELECT year_month,
    invoice_date_due,
    index_coin,
    year_month_multa,
    year_month_property_tax,
    year_month_property_ga_tax,
    year_month_property_water_consumption,
    year_month_property_water_catchment
    FROM vw_property_settings_monthly psm
  ORDER BY psm.year_month DESC
 LIMIT 1;

drop view vw_property_land_lasts_ids;

CREATE OR REPLACE VIEW public.vw_property_land_lasts_ids as
SELECT t.land_id,
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
                  WHERE p.land_id = l.id
                    and anomes(p.date) = sml.year_month_property_tax
                  ORDER BY p.date DESC
                 LIMIT 1) AS property_tax_id,
            ( SELECT p.id
                   FROM property_ga_tax p
                  WHERE p.land_id = l.id
                    and anomes(p.date) = sml.year_month_property_ga_tax
                  ORDER BY p.date DESC
                 LIMIT 1) AS property_ga_tax_id,
            ( SELECT p.id
                   FROM property_water_consumption p
                  WHERE p.land_id = l.id
                    and anomes(p.date) = sml.year_month_property_water_consumption
                  ORDER BY p.date DESC
                 LIMIT 1) AS property_water_consumption_id,
            ( SELECT p.id
                   FROM property_water_catchment p
                  WHERE p.land_id = l.id
                    and anomes(p.date) = sml.year_month_property_water_catchment
                  ORDER BY p.date DESC
                 LIMIT 1) AS property_water_catchment_id,
                 sml.year_month
           FROM property_land l,
                vw_property_settings_monthly_last sml
           ) t
     LEFT JOIN property_tax ptx ON ptx.id = t.property_tax_id
     LEFT JOIN property_ga_tax pga ON pga.id = t.property_ga_tax_id
     LEFT JOIN property_water_consumption pwc ON pwc.id = t.property_water_consumption_id
     LEFT JOIN property_water_catchment pcc ON pcc.id = t.property_water_catchment_id;

