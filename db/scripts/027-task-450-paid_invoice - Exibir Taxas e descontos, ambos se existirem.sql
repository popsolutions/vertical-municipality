CREATE OR REPLACE FUNCTION public.func_report_contab_baixados(_invoice_id integer)
 RETURNS TABLE(invoice_id integer,
               func_sequence integer,
               anomes_vencimento integer,
               product_id integer,
               product_name character varying,
               price_total_sum numeric, --Valor total pago
               juros numeric, -- Juros total da fatura
               taxaPermanencia numeric, -- Taxa de permanencia total da fatura
               total_juros numeric,  -- Juros total + taxa de permanência da fatura
               juros_anomes numeric,
               txpermanencia_anomes numeric,
               jurostotal_anomes numeric,
               jurosproporcional_perc numeric,
               jurosproporcional_valor numeric,
               juros_areaverde numeric,
               jurosproporcional_total numeric,
               price_total numeric,
               price_total_anomes numeric,
               total_agua numeric,
               total_contribuicaomensal numeric,
               total_taxas numeric,
               total_areaverde numeric,
               total_taxacaptacao numeric,
               descontos numeric)
 LANGUAGE plpgsql
AS $function$
  declare _ai_anomesVencimentoInicial integer;
  declare _pt_juros bool;
  declare _anomes_vencimento_count integer;
  declare _anomes_vencimento_current integer;
  declare _anomes_vencimento_index integer;
  declare _jurosProporcionalJaDiluido_Anomes numeric = 0; --esta variável vai acumular o total de juros que já foi diluído para ano/mês
begin
/*
  versão 2024-03-24
    task=450-paid_invoice - Exibir Taxas e descontos, ambos se existirem
  versão=2024-03-23
    task-445-paid_invoice - reconstrução de func_report_contab_baixados
  versao=2023-10-13
*/
  invoice_id = _invoice_id;
  txpermanencia_anomes = 0;

  select sum(aims.valorjuros_cnab::numeric) taxa_permanencia,
         sum(aims.valorpago) price_total_sum
    from vw_account_invoice_move_sum aims
   where aims.invoice_id = _invoice_id
    into taxaPermanencia,
         price_total_sum;

  select anomes(ai.date_due_initial) ai_anomesVencimentoInicial
    from account_invoice ai
   where ai.id = _invoice_id
    into _ai_anomesVencimentoInicial;

--  raise notice 'taxaPermanencia %, _ai_anomesVencimentoInicial %', taxaPermanencia, _ai_anomesVencimentoInicial;

  func_sequence = 1;

  for anomes_vencimento,
      product_id,
      product_name,
      _pt_juros,
      price_total,
      price_total_anomes,
      juros,
      _anomes_vencimento_count,
      total_agua,
      total_contribuicaomensal,
      total_areaverde,
      total_taxacaptacao,
      total_taxas,
      descontos
   in select t.anomes_vencimento,
             t.product_id,
             t.product_name,
             t.pt_juros,
             t.price_total,
             sum(t.price_total) filter(where not t.pt_juros) over(partition by t.anomes_vencimento) price_total_anomes,
             sum(t.price_total) filter(where     t.pt_juros) over() juros,
             t.anomes_vencimento_count,
             t.total_agua,
             t.total_contribuicaomensal,
             t.total_areaverde,
             t.total_taxacaptacao,
             t.total_taxas,
             t.descontos
        from (select ail.anomes_vencimento,
                     ail.product_id_tranformado product_id,
                     pt."name" product_name,
                     coalesce(pt.juros, false) pt_juros,
                     sum(ail.price_total) price_total,
                     sum(case when ail.product_id = 7 then ail.price_total else 0 end) total_agua,
                     sum(case when ail.product_id = 1 then ail.price_total else 0 end) total_contribuicaomensal,
                     sum(case when ail.product_id = 10 then ail.price_total else 0 end) total_areaverde,
                     sum(case when ail.product_id = 9 then ail.price_total else 0 end) total_taxacaptacao,
                     sum(ail.total_taxas) total_taxas,
                     sum(ail.descontos) descontos,
                     count(0) over(partition by ail.anomes_vencimento) anomes_vencimento_count
                from (select ail2.anomes_vencimento,
                             case when ail2.product_id = 9/*Taxa Captação*/ then 7/*água*/
                                  when coalesce(pt.juros, false) then 12 /*Multa, Juros e correção monetária*/
                                  when ((ail2.product_id not in (1, 7, 10, 9)) and (not coalesce(pt.juros, false))) then 33 /*Taxas*/
                                  else ail2.product_id
                             end product_id_tranformado,
                             case when ((ail2.product_id not in (1, 7, 10, 9)) and (not coalesce(pt.juros, false)) and ail2.price_total > 0) then ail2.price_total else 0 end total_taxas,
                             case when ((ail2.product_id not in (1, 7, 10, 9)) and (not coalesce(pt.juros, false)) and ail2.price_total < 0) then ail2.price_total else 0 end descontos,
                             ail2.product_id,
                             ail2.price_total
                        from account_invoice_line ail2 join product_template pt on pt.id = ail2.product_id
                       where ail2.invoice_id = _invoice_id
                     ) ail join product_template pt on pt.id = ail.product_id_tranformado
               group by
                     ail.anomes_vencimento,
                     ail.product_id_tranformado,
                     pt."name",
                     coalesce(pt.juros, false)
               order by
                     ail.anomes_vencimento,
                     case when coalesce(pt.juros, false) then 0 else 1 end,
                     price_total
              ) t
  loop
     if (func_sequence = 1) then
       total_juros = juros + taxaPermanencia;
     end if;

     if (_anomes_vencimento_current is distinct from anomes_vencimento) then
       --Mudou ano/mês
--       raise notice 'Novo ano/mês de % para % ', _anomes_vencimento_current, anomes_vencimento;
       _anomes_vencimento_current = anomes_vencimento;
       juros_anomes = 0;
       txpermanencia_anomes = 0;

--       raise notice 'anomes_vencimento %, _ai_anomesVencimentoInicial %', anomes_vencimento, _ai_anomesVencimentoInicial;

       if (anomes_vencimento = _ai_anomesVencimentoInicial) then
         txpermanencia_anomes = coalesce(taxaPermanencia, 0);
--         raise notice 'txpermanencia_anomes %, taxaPermanencia %', txpermanencia_anomes, taxaPermanencia;
       end if;

       if (_pt_juros) then
         juros_anomes = price_total;
       end if;

       jurostotal_anomes = juros_anomes + txpermanencia_anomes;
       _anomes_vencimento_index = 0;
      _jurosProporcionalJaDiluido_Anomes = 0;

       if (_pt_juros) then
         _anomes_vencimento_index = _anomes_vencimento_index + 1;
         continue;
       end if;
     end if;

--     raise notice 'func_sequence %, product_name %, anomes_vencimento %, juros_anomes %, total_taxas %', func_sequence, product_name, anomes_vencimento, juros_anomes, total_taxas;

     _anomes_vencimento_index = _anomes_vencimento_index + 1;

     jurosproporcional_perc = price_total / price_total_anomes;

     if (_anomes_vencimento_index = _anomes_vencimento_count) then
       --É o último registro do ano/mês. Vou jogar diretamente a diferença de juros que falta
       jurosproporcional_total = jurostotal_anomes - _jurosProporcionalJaDiluido_Anomes;
     else
       jurosproporcional_total = round(jurosproporcional_perc * jurostotal_anomes, 2);
     end if;

     _jurosProporcionalJaDiluido_Anomes = _jurosProporcionalJaDiluido_Anomes + jurosproporcional_total;

     if (product_id = 10) then
       juros_areaverde = jurosproporcional_total;
       jurosproporcional_valor = 0;
     else
       juros_areaverde = 0;
       jurosproporcional_valor = jurosproporcional_total;
     end if;


     return next;
--     raise notice '-------------------';
     func_sequence = func_sequence + 1;
  end loop;
end
$function$
;
