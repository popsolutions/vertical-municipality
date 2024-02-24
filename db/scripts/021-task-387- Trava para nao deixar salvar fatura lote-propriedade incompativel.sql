
CREATE OR REPLACE VIEW public.vw_property_land
AS SELECT pl.id,
    (((plm.code::text || '-'::text) || plb.code::text) || '-'::text) || pll.code::text AS module_code__block_code__lot_code,
    pl.type_id,
    pl.module_id,
    pl.block_id,
    pl.lot_id,
    pl.owner_id,
    coalesce(pl.owner_invoice_id, pl.owner_id) owner_invoice_id,
    plb.code AS block_code,
    plb.module_id AS block_module_id,
    plb.info AS block_info,
    pll.code AS lot_code,
    pll.block_id AS lot_block_id,
    pll.info AS lot_info,
    plm.code AS module_code,
    plm.name AS module_name,
    plm.zone_id AS module_zone_id,
    plm.info AS module_info,
    pl.address,
    pl.exclusive_area,
    pl.pavement_qty,
    pl.building_area,
    pl.is_not_waterpayer,
    pl.alternative_contribution_water_amount,
    pl.is_not_taxpayer,
    pl.alternative_contribution_tax_amount,
    plt.code AS type_code,
    plt.name AS type_name,
    plt.info AS type_info,
    plu.code AS usage_code,
    plu.name AS usage_name,
    plu.info AS usage_info,
    pls.id AS stage_id,
    pls.code AS stage_code,
    pls.name AS stage_name,
    pls.info AS stage_info,
    plz.id AS zone_id,
    plz.code AS zone_code,
    plz.name AS zone_name,
    plz.info AS zone_info,
    res_owner.name AS owner_name,
    owner_invoice.name AS owner_invoice_name,
    ((plm.code::text || plb.code::text) || ' '::text) || pll.code::text AS module_code__block_code__lot_code2,
    pl.unified_property_id,
    pl.water_consumption_economy_qty,
    pl.sisa_id,
    pl.invoicesend_email,
    func_land_emailboleto(pl.id) AS email_boleto_calc
   FROM property_land pl
     LEFT JOIN property_land_block plb ON plb.id = pl.block_id
     LEFT JOIN property_land_lot pll ON pll.id = pl.lot_id
     LEFT JOIN property_land_module plm ON plm.id = pl.module_id
     LEFT JOIN property_land_type plt ON plt.id = pl.type_id
     LEFT JOIN property_land_usage plu ON plu.id = pl.usage_id
     LEFT JOIN property_land_stage pls ON pls.id = pl.stage_id
     LEFT JOIN property_land_zone plz ON plz.id = plm.zone_id
     LEFT JOIN res_partner res_owner ON res_owner.id = pl.owner_id
     LEFT JOIN res_partner owner_invoice ON owner_invoice.id = coalesce(pl.owner_invoice_id, pl.owner_id)
  WHERE pl.active;

