CREATE OR REPLACE FUNCTION public.yearmonth_proc(proconlyyear boolean DEFAULT false)
 RETURNS TABLE(due_yearmonth integer, due_datedue date, due_dateproc date, ref_yearmonth integer, ref_datedue date, ref_dateproc date)
 LANGUAGE plpgsql
AS $function$
begin
  raise notice '%', 'yearmonth_proc';
  select year_month
    from vw_property_settings_monthly_last psm
    into due_yearmonth;

  ref_yearmonth = anomes_inc(due_yearmonth, -1);

  if not procOnlyYear then
    due_datedue = to_date(due_yearmonth || '10', 'yyyymmdd');
    due_dateproc = to_date(due_yearmonth || '24', 'yyyymmdd');

    ref_datedue = to_date(ref_yearmonth || '10', 'yyyymmdd');
    ref_dateproc = to_date(ref_yearmonth || '24', 'yyyymmdd');
  end if;

  return next;
end
$function$
;