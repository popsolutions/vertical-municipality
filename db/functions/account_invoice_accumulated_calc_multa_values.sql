CREATE OR REPLACE FUNCTION public.account_invoice_accumulated_calc_multa_values(anomes_vencimentoinicial integer, anomes_vencimentofinal integer, valorbase numeric)
 RETURNS TABLE(index_coin_inicial numeric, index_coin_final numeric, valoratualizado numeric, correcaomonetaria numeric, anomesdif integer, multapercentual numeric, multa numeric, juros numeric, multa_juros_correcao numeric, multa_juros_correcao_round2 numeric, valorbasefinal numeric)
 LANGUAGE plpgsql
AS $function$
  declare _reseted_count int = 0;
  declare isFaturaAntiga bool;
  declare isFaturaNova bool;
begin
/*
 * Retorna multa, juros e correção monetária a ser aplicado
*/

  select psm.index_coin
    from vw_property_settings_monthly psm
   where year_month = anomes_VencimentoInicial
    into index_coin_Inicial;

  select psm.index_coin
    from vw_property_settings_monthly psm
   where year_month = anomes_VencimentoFinal
    into index_coin_Final;


  if (index_coin_Inicial is null) then
    raise exception 'index_coin_account_invoice - "property_settings_monthly.index_coin" não informado para o Ano/Mês %"', index_coin_Inicial;
  end if;

  if (index_coin_Final is null) then
    raise exception 'index_coin_account_invoice_line - "property_settings_monthly.index_coin" não informado para o Ano/Mês %"', anomes_VencimentoFinal;
  end if;


  valoratualizado = valorBase / index_coin_Inicial * index_coin_Final;

  correcaomonetaria = valoratualizado - valorBase;

  anomesdif = public.anomes_dif(anomes_VencimentoInicial, anomes_VencimentoFinal);


  if (anomesdif <= 0) then
    multaPercentual = 0;
  elsif (anomes_VencimentoInicial <= 200212) then
    multaPercentual = 10;
  else
    multaPercentual = 2;
  end if;

  multa = multaPercentual / 100 * valoratualizado;

  juros = 0.01 * anomesdif * valoratualizado;
  multa_juros_correcao = correcaomonetaria + multa + juros;
  multa_juros_correcao_round2 = round(multa_juros_correcao, 2);

  valorBaseFinal = valorBase + multa_juros_correcao_round2;

  return next;
END;
$function$
;
