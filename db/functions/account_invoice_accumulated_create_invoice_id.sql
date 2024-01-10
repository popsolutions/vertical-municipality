-- DROP FUNCTION public.account_invoice_accumulated_create_invoice_id(int4);

CREATE OR REPLACE FUNCTION public.account_invoice_accumulated_create_invoice_id(_invoice_id integer DEFAULT 0)
 RETURNS boolean
 LANGUAGE plpgsql
AS $function$
  declare anomes int;
  declare state varchar;
begin
/*
 versao:2024.01.08
   Task:371-Juros para fatura acumulada paga no mês seguinte - 28A 8
 versao:2022.05.31
 *  Esta rotina vai:
   1 - deletar(se exite) registros no account_invoice_line (Referente a <_invoice_id>) referente a boletos atrasados (account_invoice_accumulated_reset)
   2 - Criar em account_invoice_line registros referentes a boleto do mês PASSADO que não foi pago
   3 - Criar em account_invoice_line registros referentes a boleto do mês RETRASADO que não foi pago
*/

  select anomes(coalesce(aci.date_due_initial, aci.date_due)) anomes,
         aci.state
    from account_invoice aci
   where aci.id = _invoice_id
    into anomes, state;

  if (state in ('draft', 'open'))  then
    --resetar(deletar) possívels registros acumulados já existentes em account_invoice_line...
    perform account_invoice_accumulated_reset(anomes, _invoice_id);

    --Criar registros acumulados(Ou trazer registros atrasados) para account_invoice_line referente ao mes PASSADO (1 mes antes)
    perform account_invoice_accumulated_create(anomes, _invoice_id);

  end if;

  return true;
END;
$function$
;
