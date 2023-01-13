drop view if exists dev.vw_account_invoice_line_res;

drop view if exists dbo0424.vw_account_invoice_line_odoo_sisa;

ALTER TABLE public.account_invoice_line ALTER COLUMN anomes_vencimento TYPE varchar USING anomes_vencimento::varchar;

-- dev.vw_account_invoice_line_res source

CREATE OR REPLACE VIEW dev.vw_account_invoice_line_res
AS SELECT aci.id AS invoice_id,
    ail.id AS account_invoice_line_id,
    anomes(aci.date_due::timestamp without time zone) AS invoice_date_due_anomes,
    ail.price_total,
    ail.product_id,
    ail.name,
    ail.anomes_vencimento,
    ail.account_invoice_line_id_accumulated_ref,
    ail.anomes_vencimento_original,
    ail.name_original,
    vpl.module_code__block_code__lot_code2,
    aci.name AS invoice_name,
    rp.name AS res_partner_name,
    aci.origin
   FROM account_invoice aci
     JOIN account_invoice_line ail ON ail.invoice_id = aci.id
     JOIN vw_property_land vpl ON vpl.id = aci.land_id
     JOIN res_partner rp ON rp.id = aci.partner_id;


-- dbo0424.vw_account_invoice_line_odoo_sisa source

CREATE OR REPLACE VIEW dbo0424.vw_account_invoice_line_odoo_sisa
AS SELECT t.invoice_anomes,
    t.land_id,
    t.anomes_vencimento,
    t.product_id,
    t.name,
    t.account_invoice_line_id,
    t.account_invoice_line_id_sisa,
    t.valodoo,
    t.valor_sisa,
    t.valodoo - t.valor_sisa AS dif
   FROM ( SELECT t_1.invoice_anomes,
            t_1.land_id,
            t_1.anomes_vencimento,
            t_1.product_id,
            pt.name,
            sum(t_1.account_invoice_line_id) AS account_invoice_line_id,
            sum(t_1.account_invoice_line_id_sisa) AS account_invoice_line_id_sisa,
            sum(t_1.valodoo) AS valodoo,
            sum(t_1.valor_sisa) AS valor_sisa
           FROM ( SELECT anomes(ai.date_due::timestamp without time zone) AS invoice_anomes,
                    ai.land_id,
                    ail.id AS account_invoice_line_id,
                    0 AS account_invoice_line_id_sisa,
                    ail.anomes_vencimento,
                    ail.product_id,
                    ail.price_total AS valodoo,
                    0 AS valor_sisa
                   FROM account_invoice_line ail
                     JOIN account_invoice ai ON ai.id = ail.invoice_id
                UNION ALL
                 SELECT anomes(ai.date_due::timestamp without time zone) AS invoice_anomes,
                    ai.land_id,
                    0 AS account_invoice_line_id,
                    ail.id AS account_invoice_line_id_sisa,
                    ail.anomes_vencimento::varchar,
                    ail.product_id,
                    0 AS valodoo,
                    ail.price_total AS valor_siza
                   FROM dbo0424.account_invoice_line ail
                     JOIN dbo0424.account_invoice ai ON ai.id = ail.invoice_id) t_1
             LEFT JOIN product_template pt ON pt.id = t_1.product_id
          GROUP BY t_1.invoice_anomes, t_1.land_id, t_1.anomes_vencimento, t_1.product_id, pt.name) t;