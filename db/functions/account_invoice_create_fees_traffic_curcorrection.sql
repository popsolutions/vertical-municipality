CREATE OR REPLACE FUNCTION public.account_invoice_create_fees_traffic_curcorrection(_invoice_id integer)
 RETURNS bool
 LANGUAGE plpgsql
AS $function$
  declare _reseted_count int = 0;
begin
/*versao:2023.03.14
 * Esta função delete/insere os valores de  Mutlas(fees), juros(Traffic) e correção monetária(currencycorrection) para uma fatura
 * O valor final de data para considerar os cálculos é vw_property_settings_monthly_last.year_month
 Parâmetros:
   _invoice_id => usado para processar um invoice individualmente
*/

  delete
    from account_invoice_line ail
   where ail.invoice_id = _invoice_id
     and ail.account_invoice_line_id_accumulated_ref = ail.invoice_id
     and ail.product_id = (select id from product_template where default_code = 'PROPMJ');

  insert into account_invoice_line (id, create_uid, create_date, write_uid, write_date, "name", origin, "sequence", invoice_id, uom_id, product_id, account_id, price_unit, price_subtotal, price_total, price_subtotal_signed, quantity, discount, account_analytic_id, company_id, partner_id, currency_id, is_rounding_line, display_type, account_invoice_line_id_accumulated_ref, anomes_vencimento, land_id)
   select nextval('account_invoice_line_id_seq') id,
          1 create_uid,
          current_timestamp create_date,
          1 write_uid,
          current_timestamp write_date,
          pdt."name" || ' ' || anomes_text(mlt.anomes_vencimento) "name",
          null origin,
          null "sequence",
          aci.id invoice_id,
          null uom_id,
          pdt.id product_id,
          167 account_id,
          mlt.multa_juros_correcao_round2 price_unit,
          mlt.multa_juros_correcao_round2 price_subtotal,
          mlt.multa_juros_correcao_round2 price_total,
          mlt.multa_juros_correcao_round2 price_subtotal_signed,
          1 quantity,
          0 discount,
          null account_analytic_id,
          1 company_id,
          aci.partner_id partner_id,
          6 currency_id,
          false is_rounding_line,
          null display_type,
          aci.id account_invoice_line_id_accumulated_ref,
          mlt.anomes_destino anomes_vencimento,
          aci.land_id /*obs: O ideal e que o land_id venha do account_invoice_line*/
     from account_invoice aci,
          account_invoice_accumulated_calc_multa_lines(aci.id, (select v.year_month from vw_property_settings_monthly_last v)) mlt,
          (select id, name from product_template where default_code = 'PROPMJ') pdt
    where aci.state in ('draft', 'open')
      and aci.id = _invoice_id;

  perform account_invoice_update_amounts(_invoice_id);

  return True;
END;
$function$
;