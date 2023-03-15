CREATE OR REPLACE FUNCTION public.account_invoice_accumulated_calc_multa_lines(_invoice_id integer, _anomesDestino integer = null)
 RETURNS TABLE(anomes_vencimento integer, anomes_destino integer, pric_total numeric, index_coin_account_invoice_line numeric, index_coin_account_invoice numeric, valoratualizado numeric, correcaomonetaria numeric, anomesdif integer, multaPercentual numeric, multa numeric, juros numeric, multa_juros_correcao numeric, multa_juros_correcao_round2 numeric, pric_total_final numeric)
 LANGUAGE plpgsql
AS $function$
  declare _reseted_count int = 0;
begin
/*
  versao:2023.03.14
  Esta função retorna o valor a ser cobrado de juros de um boleto

  Quando o parâmetro <_anomesDestino>     é informado, estou querendo saber o juros de uma fatura do seu vencimento até <_anomesDestino> passado
  Quando o parâmetro <_anomesDestino> NÃO é informado, estou querendo saber o juros dos itens da fatura (account_invoice_line) que foram acumulados de meses anteriores
*/

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
         from (select ail.anomes_vencimento,
                      anomes(ai.date_due) anomes_destino,
                      sum(ail.price_total) pric_total,
                      (select psm.index_coin
                         from vw_property_settings_monthly psm
                        where year_month = ail.anomes_vencimento
                      ) index_coin_account_invoice_line,
                      psm2.index_coin index_coin_account_invoice
                 from account_invoice_line ail
                        inner join account_invoice ai on ai.id = ail.invoice_id
                        left join vw_property_settings_monthly psm2 on psm2.year_month = coalesce(_anomesDestino, anomes(ai.date_due))
                        inner join product_product pdt on pdt.id = ail.product_id
                where ail.invoice_id = _invoice_id
                  and (   (_anomesDestino is not null)
                       or (anomes(ai.date_due) <> ail.anomes_vencimento)
                      )
                  and pdt.default_code in ('PROPWC', 'PROPTAX', 'PROPGT')
                group by ail.anomes_vencimento, anomes(ai.date_due), psm2.index_coin
               ) t
      )
  loop
    if (_anomesDestino is not null) then
      anomes_destino = _anomesDestino;
    end if;

    if (index_coin_account_invoice is null) then
      raise exception '"property_settings_monthly.index_coin" não informado para o ano %"', anomes_destino;
    end if;

    if (index_coin_account_invoice_line is null) then
      raise exception '"property_settings_monthly.index_coin" não informado para o ano %"', anomes_vencimento;
    end if;


    correcaomonetaria = valoratualizado - pric_total;

    anomesdif = public.anomes_dif(anomes_vencimento, anomes_destino);
    correcaomonetaria = valoratualizado - pric_total;

    if (anomesdif <= 0) then
      multaPercentual = 0;
    elsif (anomes_vencimento <= 200212) then
      multaPercentual = 10;
    else
      multaPercentual = 2; --Apartir de janeiro de 20003 o percentual de multa passou a ser 2%
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