--Atualizar modulo l10n_br_account_payment_brcobranca_batch

CREATE OR REPLACE FUNCTION public.func_lot_inc(lot_ text)
 RETURNS varchar(10)
 LANGUAGE plpgsql
AS $function$
declare char_part varchar(10);
declare number_part int;
begin
--versao:2022/0/24
  char_part = regexp_replace(lot_, '\d', '', 'g');
  number_part = regexp_replace(lot_, '\D','','g')::int;

  return char_part || (number_part + 1)::varchar;
--  return char_part;
END
$function$
;

CREATE OR REPLACE FUNCTION public.func_property_land_uni_summary(land_id_ integer)
 RETURNS TABLE(
   seq integer,
   amount integer,
   start_block varchar(10),
   start_module integer,
   start_lot varchar(3),
   start_lot3 varchar(3),
   end_block varchar(20),
   end_module integer,
   end_lot varchar(3),
   end_lot3 varchar(3),
   start_module_code__block_code__lot_code2 varchar(20),
   end_module_code__block_code__lot_code2 varchar(20),
   sumary_text1 varchar(200),
   sumary_text2 varchar(200)
 ) AS $func$
DECLARE
    rec RECORD;
    lot_code_next varchar(3);
begin
--versão:2022.06.24
--Ao efetuar manutenção na account_invoice_land_uni_summary, corrigir tambem a funcao func_property_land_uni_summary
  amount = 0;
  seq = 1;

  FOR rec IN
  select t.* from (
  select false lastrecord,
         v.id,
         vpl.block_code,
         vpl.module_code::integer,
         vpl.lot_code,
         vpl.module_code__block_code__lot_code2
    from vw_property_land_uni v left join vw_property_land vpl on vpl.id = v.id
   where v.id_unified =  land_id_
   union select true, 0, '', 0, '', '') t
  order by lastrecord, module_code::integer, block_code, lpad(lot_code, 3, '0')
  LOOP
--    RAISE NOTICE 'Computing %', rec.id;

    if (start_block is null) then
--      RAISE NOTICE 'if (start_block is null)';
      start_block = rec.block_code;
      start_module = rec.module_code;
      start_lot = rec.lot_code;
      start_module_code__block_code__lot_code2 = rec.module_code__block_code__lot_code2;
      lot_code_next = start_lot;
      amount = 0;
    end if;

--   raise notice 'rec.lot_code: %', rec.lot_code;

    if (   start_block <> rec.block_code
        or start_module <> rec.module_code
        or lot_code_next <> rec.lot_code
        or rec.lastrecord) then
--      RAISE NOTICE 'if (   start_block <> rec.block_code';
      start_lot3 = lpad(start_lot, 3, '0');
      end_lot3 = lpad(end_lot, 3, '0');

      sumary_text1 = start_module_code__block_code__lot_code2;
      sumary_text2 = 'Módulo: ' || start_module || ' Quadra: ' || start_block || ' Lote: ' || start_lot3;

      if (amount > 1) then
        sumary_text1 = sumary_text1 || ' ao ' || end_lot;
        sumary_text2 = sumary_text2 || ' ao ' || end_lot3;
      end if;

      RETURN NEXT;
      seq = seq + 1;

      start_block = rec.block_code;
      start_module = rec.module_code;
      start_lot = rec.lot_code;
      start_module_code__block_code__lot_code2 = rec.module_code__block_code__lot_code2;
      lot_code_next = start_lot;
      amount = 0;
    end if;

    end_block = rec.block_code;
    end_module = rec.module_code;
    end_lot = rec.lot_code;
    end_module_code__block_code__lot_code2 = rec.module_code__block_code__lot_code2;
    amount = amount + 1;

    if not (rec.lastrecord) then
      lot_code_next = func_lot_inc(lot_code_next);
    end if;

  END LOOP;
  RETURN;
END
$func$ LANGUAGE plpgsql;


CREATE OR REPLACE FUNCTION public.account_invoice_land_uni_summary(invoice_id_ integer)
 RETURNS TABLE(
   seq integer,
   amount integer,
   start_block varchar(10),
   start_module integer,
   start_lot varchar(3),
   start_lot3 varchar(3),
   end_block varchar(20),
   end_module integer,
   end_lot varchar(3),
   end_lot3 varchar(3),
   start_module_code__block_code__lot_code2 varchar(20),
   end_module_code__block_code__lot_code2 varchar(20),
   sumary_text1 varchar(200),
   sumary_text2 varchar(200)
 ) AS $func$
DECLARE
    rec RECORD;
    lot_code_next varchar(3);
begin
--versão:2022.06.24
--Ao efetuar manutenção na account_invoice_land_uni_summary, corrigir tambem a funcao func_property_land_uni_summary
  amount = 0;
  seq = 1;

  FOR rec IN
  select t.* from (
  select false lastrecord,
         v.id,
         vpl.block_code,
         vpl.module_code::integer,
         vpl.lot_code,
         vpl.module_code__block_code__lot_code2
    from (select distinct ail.land_id id
            from account_invoice_line ail
           where invoice_id = invoice_id_
         ) v left join vw_property_land vpl on vpl.id = v.id
   union select true, 0, '', 0, '', '') t
  order by lastrecord, module_code::integer, block_code, lpad(lot_code, 3, '0')
  LOOP
--    RAISE NOTICE 'Computing %', rec.id;

    if (start_block is null) then
--      RAISE NOTICE 'if (start_block is null)';
      start_block = rec.block_code;
      start_module = rec.module_code;
      start_lot = rec.lot_code;
      start_module_code__block_code__lot_code2 = rec.module_code__block_code__lot_code2;
      lot_code_next = start_lot;
      amount = 0;
    end if;

--   raise notice 'rec.lot_code: %', rec.lot_code;

    if (   start_block <> rec.block_code
        or start_module <> rec.module_code
        or lot_code_next <> rec.lot_code
        or rec.lastrecord) then
--      RAISE NOTICE 'if (   start_block <> rec.block_code';
      start_lot3 = lpad(start_lot, 3, '0');
      end_lot3 = lpad(end_lot, 3, '0');

      sumary_text1 = start_module_code__block_code__lot_code2;
      sumary_text2 = 'Módulo: ' || start_module || ' Quadra: ' || start_block || ' Lote: ' || start_lot3;

      if (amount > 1) then
        sumary_text1 = sumary_text1 || ' ao ' || end_lot;
        sumary_text2 = sumary_text2 || ' ao ' || end_lot3;
      end if;

      RETURN NEXT;
      seq = seq + 1;

      start_block = rec.block_code;
      start_module = rec.module_code;
      start_lot = rec.lot_code;
      start_module_code__block_code__lot_code2 = rec.module_code__block_code__lot_code2;
      lot_code_next = start_lot;
      amount = 0;
    end if;

    end_block = rec.block_code;
    end_module = rec.module_code;
    end_lot = rec.lot_code;
    end_module_code__block_code__lot_code2 = rec.module_code__block_code__lot_code2;
    amount = amount + 1;

    if not (rec.lastrecord) then
      lot_code_next = func_lot_inc(lot_code_next);
    end if;

  END LOOP;
  RETURN;
END
$func$ LANGUAGE plpgsql;


