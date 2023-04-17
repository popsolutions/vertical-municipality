CREATE OR REPLACE FUNCTION public.account_invoice_accumulated_calc_multa(_invoice_id integer, _anomesDestino integer = null)
 RETURNS TABLE(pric_total numeric, index_coin_account_invoice_line numeric, index_coin_account_invoice numeric, valoratualizado numeric, correcaomonetaria numeric, multa numeric, juros numeric, multa_juros_correcao numeric, multa_juros_correcao_round2 numeric)
 LANGUAGE plpgsql
AS $function$
  declare _reseted_count int = 0;
begin
/*
 *versão:2023.04.13
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
