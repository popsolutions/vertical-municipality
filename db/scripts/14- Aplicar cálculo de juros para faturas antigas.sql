--task:156 - Aplicar cálculo de juros para faturas antigas

drop function account_invoice_accumulated_calc_multa_lines;

CREATE OR REPLACE FUNCTION public.account_invoice_accumulated_calc_multa_lines(_invoice_id integer, _anomesdestino integer DEFAULT NULL::integer)
 RETURNS TABLE(anomes_vencimento integer, anomes_destino integer, pric_total numeric, index_coin_account_invoice_line numeric, index_coin_account_invoice numeric, valoratualizado numeric, correcaomonetaria numeric, anomesdif integer, multapercentual numeric, multa numeric, juros numeric, multa_juros_correcao numeric, multa_juros_correcao_round2 numeric, pric_total_final numeric)
 LANGUAGE plpgsql
AS $function$
  declare _reseted_count int = 0;
  declare isFaturaAntiga bool;
  declare isFaturaNova bool;
begin
/*
  versao:2023.04.17
  Esta função retorna o valor a ser cobrado de juros de um boleto

  Quando o parâmetro <_anomesDestino>     é informado(Faturas antigas               ), estou querendo saber o juros de uma fatura do seu vencimento até <_anomesDestino> passado
  Quando o parâmetro <_anomesDestino> NÃO é informado(Faturas novas, 2 últimos mesea), estou querendo saber o juros dos itens da fatura (account_invoice_line) que foram acumulados de meses anteriores
*/
  isFaturaAntiga = _anomesDestino is not null;
  isFaturaNova = not isFaturaAntiga; --_anomesDestino is null

  for anomes_vencimento,
      anomes_destino,
      pric_total,
      index_coin_account_invoice_line,
      index_coin_account_invoice,
      valoratualizado
   in (select t.anomes_vencimento,
              t.anomes_destino,
              t.pric_total,
              t.index_coin_account_invoice_line,
              t.index_coin_account_invoice,
              t.pric_total / t.index_coin_account_invoice_line * t.index_coin_account_invoice valoratualizado
         from (select case when isFaturaNova then ail.anomes_vencimento else anomes(ai.date_due) end anomes_vencimento,
                      anomes(ai.date_due) anomes_destino,
                      sum(ail.price_total) pric_total,
                      (select psm.index_coin
                         from vw_property_settings_monthly psm
                        where year_month = case when isFaturaNova then ail.anomes_vencimento else anomes(ai.date_due) end
--                        where year_month = ail.anomes_vencimento
                      ) index_coin_account_invoice_line,
                      psm2.index_coin index_coin_account_invoice
                 from account_invoice_line ail
                        inner join account_invoice ai on ai.id = ail.invoice_id
                        left join vw_property_settings_monthly psm2 on psm2.year_month = coalesce(_anomesDestino, anomes(ai.date_due))
                        inner join product_product pdt on pdt.id = ail.product_id
                where ail.invoice_id = _invoice_id
                  and (   (isFaturaAntiga)
                       or (anomes(ai.date_due) <> ail.anomes_vencimento)
                      )
                  and pdt.default_code in ('PROPWC', 'PROPTAX', 'PROPGT')
                group by ail.anomes_vencimento, ai.date_due, psm2.index_coin
               ) t
      )
  loop
    if (isFaturaAntiga) then --_anomesDestino is not null
      anomes_destino = _anomesDestino;
    end if;

    if (index_coin_account_invoice is null) then
      raise exception 'index_coin_account_invoice - "property_settings_monthly.index_coin" não informado para o Ano/Mês %, _invoice_id %"', anomes_destino, _invoice_id;
    end if;

    if (index_coin_account_invoice_line is null) then
      raise exception 'index_coin_account_invoice_line - "property_settings_monthly.index_coin" não informado para o Ano/Mês %, _invoice_id %"', anomes_vencimento, _invoice_id;
    end if;


    correcaomonetaria = valoratualizado - pric_total;

    anomesdif = public.anomes_dif(anomes_vencimento, anomes_destino);
    correcaomonetaria = valoratualizado - pric_total;

    if (anomesdif <= 0) then
      multaPercentual = 0;
    elsif (anomes_vencimento <= 200212) then
      multaPercentual = 10;
    else
      multaPercentual = 2;
    end if;

    multa = multaPercentual / 100 * valoratualizado;

    juros = 0.01 * anomesdif * valoratualizado;
    multa_juros_correcao = correcaomonetaria + multa + juros;
    multa_juros_correcao_round2 = round(multa_juros_correcao, 2);

    pric_total_final = pric_total + multa_juros_correcao_round2;

    return next;
  end loop;

END;
$function$
;


drop function public.account_invoice_accumulated_calc_multa;

CREATE OR REPLACE FUNCTION public.account_invoice_accumulated_calc_multa(_invoice_id integer, _anomesDestino integer = null)
 RETURNS TABLE(pric_total numeric, index_coin_account_invoice_line numeric, index_coin_account_invoice numeric, valoratualizado numeric, correcaomonetaria numeric, multa numeric, juros numeric, multa_juros_correcao numeric, multa_juros_correcao_round2 numeric)
 LANGUAGE plpgsql
AS $function$
  declare _reseted_count int = 0;
begin
/*
 *versão:2023.04.13
 *
  Esta função retorna o valor a ser cobrado de juros de um boleto
*/
  return query
  select sum(v.pric_total) pric_total,
         sum(v.index_coin_account_invoice_line) index_coin_account_invoice_line,
         sum(v.index_coin_account_invoice) index_coin_account_invoice,
         sum(v.valoratualizado) valoratualizado,
         sum(v.correcaomonetaria) correcaomonetaria,
         sum(v.multa) multa,
         sum(v.juros) juros,
         sum(v.multa_juros_correcao) multa_juros_correcao,
         sum(v.multa_juros_correcao_round2) multa_juros_correcao_round2
    from account_invoice_accumulated_calc_multa_lines(_invoice_id, _anomesDestino) v;
END;
$function$
;

CREATE OR REPLACE FUNCTION public.account_invoice_create_fees_traffic_curcorrection(_invoice_id integer)
 RETURNS bool
 LANGUAGE plpgsql
AS $function$
  declare _reseted_count int = 0;
begin
/*versao:2023.04.13
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
     and aci.id = _invoice_id;

  perform account_invoice_update_amounts(_invoice_id);

  return True;
END;
$function$
;

CREATE OR REPLACE FUNCTION public.account_invoice_create_fees_traffic_curcorrection_defproc()
 RETURNS boolean
 LANGUAGE plpgsql
AS $function$
  declare invoice_id int = 0;
begin
/*versao:2023.03.14
 * defproc => Processamento padrão
 * Esta função faz o processamento de account_invoice_create_fees_traffic_curcorrection para todas a faturas em aberto e com vencimento antes dos 3 últimos meses
 * A função account_invoice_create_fees_traffic_curcorrection => Esta função delete/insere os valores de  Multas(fees), juros(Traffic) e correção monetária(currencycorrection) para uma fatura
 *
*/
  for invoice_id in (
  select ai.id
    from account_invoice ai
   where anomes(ai.date_due) < (select anomes_inc(v.year_month, -2) from vw_property_settings_monthly_last v)
     and ai.state = 'open')
  loop
    perform account_invoice_create_fees_traffic_curcorrection(invoice_id);
  end loop;

  return True;
END;
$function$
;

