CREATE OR REPLACE FUNCTION public.account_invoice_accumulated_create_full(anomes integer)
 RETURNS boolean
 LANGUAGE plpgsql
AS $function$
  declare anomes_1 int;
  declare anomes_2 int;
  declare state varchar;
begin
/*versao:2022.05.31
   Esta rotina vai (Para todos account_invoice com vencimento em <anomes>):
   1 - deletar(se exite) registros no account_invoice_line (Referente a <_invoice_id>) referente a boletos atrasados (account_invoice_accumulated_reset)
   2 - Criar em account_invoice_line registros referentes a boleto do mês PASSADO que não foi pago
   3 - Criar em account_invoice_line registros referentes a boleto do mês RETRASADO que não foi pago
*/

  --resetar(deletar) possívels registros acumulados já existentes em account_invoice_line...
  perform account_invoice_accumulated_reset(anomes);

  --Criar registros acumulados(Ou trazer registros atrasados) para account_invoice_line referente ao mes PASSADO e retrasado
  perform account_invoice_accumulated_create(anomes);

  return true;
END;
$function$
;
