-- DROP FUNCTION public.anomes_text(int4, int4);

CREATE OR REPLACE FUNCTION public.anomes_text(anomes integer, anomesmode integer DEFAULT 1)
 RETURNS character varying
 LANGUAGE plpgsql
 IMMUTABLE STRICT
AS $function$
declare ano int;
declare mes int;
declare AnoMesStr varchar(20);
begin
  --versao:2022.05.23
  ano = substring(anomes::varchar, 1, 4);
  mes = substring(anomes::varchar, 5, 2);

  if (anomesMode = 1) then
    AnoMesStr = ('{Jan,Fev,Mar,Abr,Mai,Jun,Jul,Ago,Set,Out,Nov,Dez}'::VARCHAR[])[mes];
  elseif (anomesMode in (2, 3)) then
    AnoMesStr = ('{Janeiro,Fevereiro,Março,Abril,Maio,Junho,Julho,Agosto,Setembro,Outubro,Novembro,Dezembro}'::VARCHAR[])[mes];
  end if;

  if (anomesMode <> 3) then
    AnoMesStr = AnoMesStr || '/' || ano;
  end if;

  return AnoMesStr;
END
$function$
;
