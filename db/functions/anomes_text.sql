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
  --versão 2024.02.22
  --  Retornar nulo se length de anomes <> 6
  --versao:2024.02.05
  --versao:2022.05.23

  if (length(anomes::text) <> 6) then
    return null;
  end if;

  ano = substring(anomes::varchar, 1, 4);
  mes = substring(anomes::varchar, 5, 2);

  if (anomesMode = 1) then
    AnoMesStr = ('{Jan,Fev,Mar,Abr,Mai,Jun,Jul,Ago,Set,Out,Nov,Dez}'::VARCHAR[])[mes];
  elseif (anomesMode in (2, 3)) then
    AnoMesStr = ('{Janeiro,Fevereiro,Março,Abril,Maio,Junho,Julho,Agosto,Setembro,Outubro,Novembro,Dezembro}'::VARCHAR[])[mes];
  elseif (anomesMode = 4) then
    AnoMesStr = lpad(mes::varchar, 2, '0');
  elseif (anomesMode = 5) then
    AnoMesStr = ano::varchar || '/' || lpad(mes::varchar, 2, '0');
  end if;

  if (anomesMode not in (3, 5)) then
    AnoMesStr = AnoMesStr || '/' || ano;
  end if;

  return AnoMesStr;
END
$function$
;
