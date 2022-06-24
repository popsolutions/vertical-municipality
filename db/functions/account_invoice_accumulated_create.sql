CREATE OR REPLACE FUNCTION public.account_invoice_accumulated_create(_anomes_destino integer, _fixed_invoice_id integer DEFAULT 0)
 RETURNS integer
 LANGUAGE plpgsql
AS $function$
  declare _invoice_id int;
  declare _reseted_count int = 0;
begin
/*versao:2022.05.31
 Parâmetros:
   _anomes_destino => Ano/Mês onde serão acumuladas as faturas anteriores que estão em aberto.
   _fixed_invoice_id => usado para processar um invoice individualmente
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
        t.invoice_destino_id invoice_id,
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
   from (select invoice_line_origem_id,
                invoice_destino_id
           from (select t1.invoice_destino_id,
                        t1.invoice_line_origem_id,
                        t1.invoice_origem_id,
                        t1.invoice_line_origem_anomes_vencimento,
                        row_number() over (partition by t1.land_id, t1.invoice_line_origem_product_id, t1.invoice_line_origem_anomes_vencimento) rownumber
                   from (select invoice_destino.id invoice_destino_id,
                                invoice_destino.land_id,
                                invoice_origem.id invoice_origem_id,
                                invoice_origem.date_due date_due,
                                invoice_line_origem.id invoice_line_origem_id,
                                invoice_line_origem.product_id invoice_line_origem_product_id,
                                invoice_line_origem.anomes_vencimento invoice_line_origem_anomes_vencimento
                           from (select anomes_inc(_anomes_destino, -1) anomes_1, /*mes passado (com relacao ao _anomes_destino) */
                                        anomes_inc(_anomes_destino, -2) anomes_2, /*mes retrasado (com relacao ao _anomes_destino) */
                                        anomes_inc(_anomes_destino, -3) anomes_3  /*3 meses antes passado (com relacao ao _anomes_destino) */
                                ) anm,
                                (select invoice_destino1.id,
                                        invoice_destino1.land_id
                                   from account_invoice invoice_destino1
                                  where invoice_destino1.state = 'open'
                                    and anomes(invoice_destino1.date_due) = _anomes_destino
                                    and (   (_fixed_invoice_id = 0)
                                         or (invoice_destino1.id = _fixed_invoice_id)
                                        )  /****Usar apenas para fixar invoice_id****/
                                 ) invoice_destino,
                                 account_invoice invoice_origem,
                                 account_invoice_line invoice_line_origem
                                   join product_product pdt on pdt.id = invoice_line_origem.product_id and pdt.default_code in ('PROPWC', 'PROPTAX', 'PROPGT')
                           where invoice_origem.land_id = invoice_destino.land_id
                             and invoice_origem.state = 'open'
                             and anomes(invoice_origem.date_due) in (anm.anomes_1, anm.anomes_2)
                             and (not exists
                                 (select 1
                                    from account_invoice aci_3
                                   where aci_3.land_id = invoice_destino.land_id
                                     and anomes(aci_3.date_due) = anm.anomes_3
                                     and aci_3.state = 'open'
                                   limit 1
                                 )/*Este filtro irá eliminar o account_invoice caso tenha mais que 3 meses de boletos vencido para o cliente("Limpo com mensagem")*/)
                             and invoice_line_origem.invoice_id = invoice_origem.id
                             and invoice_line_origem.anomes_vencimento in (anm.anomes_1, anm.anomes_2)
                           order by invoice_destino.land_id, invoice_line_origem.product_id, invoice_line_origem.anomes_vencimento, invoice_origem.id desc
                        ) t1
                 ) t
          where 0 = 0 
            and t.rownumber = 1 /*eliminar repetidos*/
          order by t.invoice_line_origem_anomes_vencimento, t.invoice_origem_id  
        ) t 
        join account_invoice_line ail_origem on ail_origem.id = t.invoice_line_origem_id
        join account_invoice invoice_origem on invoice_origem.id = ail_origem.invoice_id;
             
     
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
