CREATE OR REPLACE FUNCTION public.func_report_contab_baixados(_invoice_id integer)
 RETURNS TABLE(
invoice_id int4,
anomes_vencimento int4,
product_id int4,
product_name varchar,
price_total_sum numeric,
total_juros numeric,
jurosproporcional_perc numeric,
jurosproporcional_valor numeric,
juros_areaverde numeric,
price_total numeric,
total_agua numeric,
total_contribuicaomensal numeric,
total_taxas numeric,
total_areaverde numeric,
total_taxacaptacao numeric,
descontos numeric,
tipocobranca varchar(1)
 )
 LANGUAGE sql
AS $function$
--versao=2023-10-13
select ail.invoice_id,
       ail.anomes_vencimento,
       ail.product_id,
       ail.product_name,
       ail_total.price_total price_total_sum,
       ail_juros.price_total total_juros,
       coalesce(round(ail.price_total / (ail_total.price_total - ail_juros.price_total), 3), 0) jurosproporcional_perc,
       coalesce(round((ail.price_total / (ail_total.price_total - ail_juros.price_total)) * ail_juros.price_total, 3), 0) jurosproporcional_valor,
       0::numeric juros_areaverde,
       ail.price_total,
       ail.total_agua,
       ail.total_contribuicaomensal,
       ail.total_taxas,
       ail.total_areaverde,
       ail.total_taxacaptacao,
       0::numeric descontos,
       case when exists
       (select 1
          from res_partner_bank rpb
         where rpb.partner_id = ail.partner_id
           and rpb.acc_number is not null
       ) then 'A' else 'B' end tipocobranca --A-> Débito automático, B -> boleto
  from (select ail.invoice_id,
               ail.partner_id,
               ail.anomes_vencimento,
               ail.product_id,
               pt."name" product_name,
               sum(ail.price_total) price_total,
               sum(case when ail.product_id = 7 then ail.price_total else 0 end) total_agua,
               sum(case when ail.product_id = 1 then ail.price_total else 0 end) total_contribuicaomensal,
               sum(case when ail.product_id in (13, 11) then ail.price_total else 0 end) total_taxas,
               sum(case when ail.product_id = 10 then ail.price_total else 0 end) total_areaverde,
               sum(case when ail.product_id = 9 then ail.price_total else 0 end) total_taxacaptacao
          from account_invoice_line ail join product_template pt on pt.id = ail.product_id
         where ail.invoice_id = _invoice_id
           and ail.product_id <> 12
         group by
               ail.invoice_id,
               ail.partner_id,
               ail.anomes_vencimento,
               ail.product_id,
               pt."name"
       ) ail
       left join
       (select aims.valorpago price_total
          from vw_account_invoice_move_sum aims
         where aims.invoice_id = _invoice_id
       ) ail_total on true
       left join
       (select sum(t.price_total) price_total
          from (select ail.invoice_id,
                       ail.anomes_vencimento,
                       sum(ail.price_total) price_total
                  from account_invoice_line ail join product_template pt on pt.id = ail.product_id
                 where ail.product_id = 12
                   and ail.invoice_id = _invoice_id
                 group by ail.invoice_id, ail.anomes_vencimento
                 union all
                select aims.invoice_id,
                       anomes(aims.invoice_date_due) anomes_vencimento,
                       aims.valorjuros_cnab::numeric price_total
                  from vw_account_invoice_move_sum aims
                 where aims.invoice_id = _invoice_id
               ) t
       ) ail_juros on true
   where ail.invoice_id = _invoice_id;
$function$;