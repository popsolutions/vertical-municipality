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
--versao=2023-07-20
select ail.invoice_id,
       ail.anomes_vencimento,
       ail.product_id,
       ail.product_name,
       ail_total.price_total price_total_sum,
       ail_juros.price_total total_juros,
       coalesce(round(ail.price_total / (ail_total.price_total - ail_juros.price_total), 2), 0) jurosproporcional_perc,
       coalesce(round((ail.price_total / (ail_total.price_total - ail_juros.price_total)) * ail_juros.price_total, 2), 0) jurosproporcional_valor,
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
               ail.price_total,
               sum(case when ail.product_id = 7 then ail.price_total else 0 end) total_agua,
               sum(case when ail.product_id = 1 then ail.price_total else 0 end) total_contribuicaomensal,
               sum(case when ail.product_id in (13, 11) then ail.price_total else 0 end) total_taxas,
               sum(case when ail.product_id = 10 then ail.price_total else 0 end) total_areaverde,
               sum(case when ail.product_id = 9 then ail.price_total else 0 end) total_taxacaptacao
          from account_invoice_line ail join product_template pt on pt.id = ail.product_id
         where true
           and ail.product_id <> 12
         group by
               ail.invoice_id,
               ail.partner_id,
               ail.anomes_vencimento,
               ail.product_id,
               pt."name",
               ail.price_total
       ) ail
       left join
       (select ail.invoice_id,
               ail.anomes_vencimento,
               sum(ail.price_total) price_total
          from account_invoice_line ail join product_template pt on pt.id = ail.product_id
         group by ail.invoice_id, ail.anomes_vencimento
       ) ail_total on ail_total.invoice_id = ail.invoice_id and ail_total.anomes_vencimento = ail.anomes_vencimento
       left join
       (select ail.invoice_id,
               ail.anomes_vencimento,
               sum(ail.price_total) price_total
          from account_invoice_line ail join product_template pt on pt.id = ail.product_id
         where ail.product_id = 12
         group by ail.invoice_id, ail.anomes_vencimento
       ) ail_juros on ail_juros.invoice_id = ail.invoice_id and ail_juros.anomes_vencimento = ail.anomes_vencimento
   where ail.invoice_id = _invoice_id;
$function$