CREATE OR REPLACE FUNCTION public.account_invoice_update_amounts(_invoice_id integer)
 RETURNS void
 LANGUAGE plpgsql
AS $function$
declare sum_price_total numeric;
declare _residual numeric;
declare _state varchar(30);
begin
  --versão:2022.10.13

  select aci.state,
         coalesce(account_invoice_calc_amount_total(aci.id), 0)
    from account_invoice aci
   where aci.id = _invoice_id
    into _state, sum_price_total;

  if (_state = 'paid') then
    _residual = 0;
  else
    _residual = sum_price_total;
  end if;

  update account_invoice ai
     set amount_untaxed = sum_price_total,
         amount_untaxed_signed = sum_price_total,
         amount_total = sum_price_total,
         amount_total_signed = sum_price_total,
         amount_total_company_signed = sum_price_total,
         residual_signed = _residual,
         residual_company_signed = _residual,
         residual = _residual
    where ai.id = _invoice_id;

  update account_move_line
     set amount_residual = _residual,
         debit = sum_price_total,
         balance = sum_price_total
   where invoice_id = _invoice_id
     and product_id is null;

END;
$function$
;
