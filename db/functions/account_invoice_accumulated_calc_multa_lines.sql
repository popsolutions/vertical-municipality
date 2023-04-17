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
