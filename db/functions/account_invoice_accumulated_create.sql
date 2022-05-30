CREATE OR REPLACE FUNCTION public.account_invoice_accumulated_create(_anomes_destino integer, _anomes_ref integer, _fixed_invoice_id integer DEFAULT 0)
 RETURNS integer
 LANGUAGE plpgsql
AS $function$
  declare _invoice_id int;
  declare _reseted_count int = 0;
begin
/*versao:2022.05.30
 Parâmetros:
   _anomes_destino => Ano/Mês onde serão acumuladas as faturas anteriores que estão em aberto.

   _anomes_ref => Ano/Mês onde o sistema irá buscar se exite faturas em aberto(state=open). Se existir várias faturas abertas
                  neste ano/Mês o sistema irá utilizar a última fatura.

*/

 insert into account_invoice_line (id, create_uid, create_date, write_uid, write_date, "name", origin, "sequence", invoice_id, uom_id, product_id, account_id, price_unit, price_subtotal, price_total, price_subtotal_signed, quantity, discount, account_analytic_id, company_id, partner_id, currency_id, is_rounding_line, display_type, account_invoice_line_id_accumulated_ref, anomes_vencimento)
  select nextval('account_invoice_line_id_seq') id,
         1 create_uid,
         current_timestamp create_date,
         1 write_uid,
         current_timestamp write_date,
         ail_origem."name" "name",
         invoice_origem.id origin,
         ail_origem."sequence",
         invoice_destino.id invoice_id,
         null uom_id,
         ail_origem.product_id  product_id,
         167 account_id,
         ail_origem.price_unit,
         ail_origem.price_subtotal,
         ail_origem.price_total,
         ail_origem.price_subtotal_signed,
         1 quantity,
         0 discount,
         null account_analytic_id,
         1 company_id,
         ail_origem.partner_id partner_id,
         6 currency_id,
         false is_rounding_line,
         null display_type,
         ail_origem.id account_invoice_line_id_accumulated_ref,
         ail_origem.anomes_vencimento
    from (/*Este sql vai buscar a última account_invoice aberta para o Ano/Mês*/
          select (select aci_ultima_mes.id
                    from account_invoice aci_ultima_mes
                   where anomes(aci_ultima_mes.date_due) = anm.anomes_ref
                     and aci_ultima_mes.state = 'open'
                     and aci_ultima_mes.partner_id = aci.partner_id
                     and aci_ultima_mes.land_id = aci.land_id
                   order by aci_ultima_mes.date_due desc
                   limit 1
                 ) id_ultima_account_incoice_anomes,
                 anm.anomes_ref
            from account_invoice aci,
                 (select _anomes_ref /****:Informar Ano/Mês de REFERÊNCIA****/ anomes_ref,
                         anomes_inc(_anomes_destino, -3) anomes_3) anm
           where anomes(aci.date_due) = anm.anomes_ref
             and aci.state = 'open'
             and ((_fixed_invoice_id = 0) or (aci.land_id = (select land_id
                                                                from account_invoice aci_fix
                                                               where aci_fix.id = _fixed_invoice_id)
                                               )
                 )  /****Usar apenas para fixar invoice_id****/
             and (not exists
                 (select 1
                    from account_invoice aci_3
                   where aci_3.land_id = aci.land_id
                     and anomes(aci_3.date_due) = anm.anomes_3
                     and aci_3.state = 'open'
                   limit 1
                 )/*Este filtro irá eliminar o account_invoice caso tenha mais que 3 meses de boletos vencido para o cliente("Limpo com mensagem")*/)
           group by aci.partner_id, land_id, anm.anomes_ref
         ) accounts_acumular
         inner join account_invoice_line ail_origem
                 on ail_origem.invoice_id = accounts_acumular.id_ultima_account_incoice_anomes
                and ail_origem.anomes_vencimento = accounts_acumular.anomes_ref
         inner join product_product pdt on pdt.id = ail_origem.product_id
         inner join account_invoice invoice_origem on invoice_origem.id = accounts_acumular.id_ultima_account_incoice_anomes
         inner join account_invoice invoice_destino
                 on invoice_destino.partner_id = invoice_origem.partner_id
                and invoice_destino.land_id = invoice_origem.land_id
                and anomes(invoice_destino.date_due) = _anomes_destino /****:Informar Ano/Mês de processamento****/
   where pdt.default_code in ('PROPWC', 'PROPTAX')
     and ((_fixed_invoice_id = 0) or (invoice_destino.id::varchar = _fixed_invoice_id::varchar));  /****Usar apenas para fixar invoice_id****/

  --Inserir Juros
  insert into account_invoice_line (id, create_uid, create_date, write_uid, write_date, "name", origin, "sequence", invoice_id, uom_id, product_id, account_id, price_unit, price_subtotal, price_total, price_subtotal_signed, quantity, discount, account_analytic_id, company_id, partner_id, currency_id, is_rounding_line, display_type, account_invoice_line_id_accumulated_ref, anomes_vencimento)
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
         null account_invoice_line_id_accumulated_ref,
         mlt.anomes_vencimento
    from account_invoice aci,
         account_invoice_accumulated_calc_multa_lines(aci.id) mlt,
         (select id, name from product_template where default_code = 'PROPMJ') pdt
   where (exists
         (select 1
            from account_invoice_line acl
           where acl.invoice_id = aci.id
             and acl.account_invoice_line_id_accumulated_ref is not null
         ))
     and anomes(aci.date_due) = _anomes_destino
     and mlt.anomes_vencimento = _anomes_ref
     and aci.state in ('draft', 'open')
     and ((_fixed_invoice_id = 0) or (aci.id = _fixed_invoice_id));  /****Usar apenas para fixar invoice_id****/


  --Atualizar valores account_invoice para os account_invoice que tiveram registros inseridos
  for _invoice_id in
    select aci.id
      from account_invoice aci
     where (exists
           (select 1
              from account_invoice_line ail
             where ail.invoice_id = aci.id
               and ail.account_invoice_line_id_accumulated_ref is not null
           ))
       and anomes(aci.date_due) = _anomes_destino /****:Informar Ano/Mês de processamento****/
       and ((_fixed_invoice_id = 0) or (aci.id = _fixed_invoice_id))  /****Usar apenas para fixar invoice_id****/
  loop
    perform account_invoice_update_amounts(_invoice_id);
   _reseted_count = _reseted_count + 1;
  end loop;

  return _reseted_count;
END;
$function$
;
