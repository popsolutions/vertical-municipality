CREATE OR REPLACE FUNCTION public.account_invoice_create_fees_traffic_curcorrection(_invoice_id integer)
 RETURNS boolean
 LANGUAGE plpgsql
AS $function$
  declare _reseted_count int = 0;
begin
/**versao:2024.02.05
 * task:414-Rotina account_invoice_create_fees_traffic_curcorrection está dando erro quando fatura não possui juros - Fatura 1161229
 **versao:2023.04.13
 * Esta função delete/insere os valores de  Mutlas(fees), juros(Traffic) e correção monetária(currencycorrection) para uma fatura
 * O valor final de data para considerar os cálculos é vw_property_settings_monthly_last.year_month
 Parâmetros:
   _invoice_id => usado para processar um invoice individualmente
*/

  delete
    from account_invoice_line ail
   where ail.invoice_id = _invoice_id
     and ail.product_id in (select id from product_template where default_code in ('PROPJU', 'PROPMU', 'PROPCM'));

  insert into account_invoice_line (id, create_uid, create_date, write_uid, write_date, "name", origin, "sequence", invoice_id, uom_id, product_id, account_id, price_unit, price_subtotal, price_total, price_subtotal_signed, quantity, discount, account_analytic_id, company_id, partner_id, currency_id, is_rounding_line, display_type, account_invoice_line_id_accumulated_ref, anomes_vencimento, land_id)
  select nextval('account_invoice_line_id_seq') id,
         1 create_uid,
         current_timestamp create_date,
         1 write_uid,
         current_timestamp write_date,
         pdt."name" || ' ' || anomes_text(ym.year_month) "name",
         null origin,
         null "sequence",
         aci.id invoice_id,
         null uom_id,
         pdt.id product_id,
         167 account_id,
         round(case pdt.default_code when 'PROPJU' then mlt.juros when 'PROPMU' then mlt.multa when 'PROPCM' then mlt.correcaomonetaria end, 2) price_unit,
         round(case pdt.default_code when 'PROPJU' then mlt.juros when 'PROPMU' then mlt.multa when 'PROPCM' then mlt.correcaomonetaria end, 2) price_subtotal,
         round(case pdt.default_code when 'PROPJU' then mlt.juros when 'PROPMU' then mlt.multa when 'PROPCM' then mlt.correcaomonetaria end, 2) price_total,
         round(case pdt.default_code when 'PROPJU' then mlt.juros when 'PROPMU' then mlt.multa when 'PROPCM' then mlt.correcaomonetaria end, 2) price_subtotal_signed,
         1 quantity,
         0 discount,
         null account_analytic_id,
         1 company_id,
         aci.partner_id partner_id,
         6 currency_id,
         false is_rounding_line,
         null display_type,
         null account_invoice_line_id_accumulated_ref,
         ym.year_month anomes_vencimento,
         aci.land_id /*obs: O ideal e que o land_id venha do account_invoice_line*/
    from account_invoice aci,
         (select v.year_month from vw_property_settings_monthly_last v) ym
         join account_invoice_accumulated_calc_multa(aci.id, ym.year_month) mlt on 0 = 0,
         (select id, name, default_code from product_template where default_code in ('PROPJU', 'PROPMU', 'PROPCM')) pdt
   where aci.state in ('draft', 'open')
     and aci.id = _invoice_id
     and mlt.pric_total is not null;

  perform account_invoice_update_amounts(_invoice_id);

  return True;
END;
$function$
;
