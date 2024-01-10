-- DROP FUNCTION public.account_invoice_accumulated_reset(int4, int4);

CREATE OR REPLACE FUNCTION public.account_invoice_accumulated_reset(_anomes integer, _fixed_invoice_id integer DEFAULT 0)
 RETURNS integer
 LANGUAGE plpgsql
AS $function$
  declare _invoice_id int;
  declare _reseted_count int = 0;
BEGIN
  FOR _invoice_id in
    select aci.id invoice_id
      from account_invoice aci
     where (exists
           (select 1
              from account_invoice_line acl
             where acl.invoice_id = aci.id
               and acl.account_invoice_line_id_accumulated_ref is not null
           ))
       and anomes(aci.date_due) = _anomes
       and aci.state in ('draft', 'open')
       and ((_fixed_invoice_id = 0) or (aci.id = _fixed_invoice_id))  /****Usar apenas para fixar invoice_id****/
  loop
--    raise notice 'deletar invoice_id:%', _invoice_id;

    delete from account_invoice_line ail
     where ail.invoice_id = _invoice_id
       and (   ail.account_invoice_line_id_accumulated_ref is not null
            or (select default_code from product_template where id = ail.product_id ) = 'PROPMJ'
           ) ;

--    raise notice 'Atualizar valores de  invoice_id:%', _invoice_id;

    perform account_invoice_update_amounts(_invoice_id);
    _reseted_count = _reseted_count + 1;
--    raise notice 'registro processado:%', _reseted_count;

  end loop;

  return _reseted_count;
END;
$function$
;
