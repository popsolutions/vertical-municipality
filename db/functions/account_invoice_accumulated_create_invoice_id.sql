CREATE OR REPLACE FUNCTION public.account_invoice_accumulated_create_invoice_id(_invoice_id integer DEFAULT 0)
 RETURNS boolean
 LANGUAGE plpgsql
AS $function$
  declare anomes int;
  declare anomes_1 int;
  declare anomes_2 int;
  declare state varchar;
begin
/* versao:2022.05.30
 *  Esta rotina vai:
   1 - deletar(se exite) registros no account_invoice_line (Referente a <_invoice_id>) referente a boletos atrasados (account_invoice_accumulated_reset)
   2 - Criar em account_invoice_line registros referentes a boleto do mês PASSADO que não foi pago
   3 - Criar em account_invoice_line registros referentes a boleto do mês RETRASADO que não foi pago
*/

  select anomes(aci.date_due) anomes,
         anomes_inc(anomes(aci.date_due), -1) anomes_1,
         anomes_inc(anomes(aci.date_due), -2) anomes_2,
         aci.state
    from account_invoice aci
   where aci.id = _invoice_id
    into anomes, anomes_1, anomes_2, state;

  if (state in ('draft', 'open'))  then
    --resetar(deletar) possívels registros acumulados já existentes em account_invoice_line...
    perform account_invoice_accumulated_reset(anomes, _invoice_id);

    --Criar registros acumulados(Ou trazer registros atrasados) para account_invoice_line referente ao mes PASSADO (1 mes antes)
    perform account_invoice_accumulated_create(anomes, anomes_1, _invoice_id);

    --Criar registros acumulados(Ou trazer registros atrasados) para account_invoice_line referente ao mes RETRASADO (2 meses antes)
    perform account_invoice_accumulated_create(anomes, anomes_2, _invoice_id);
  end if;

  return true;
END;
$function$
;
