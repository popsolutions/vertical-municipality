CREATE OR REPLACE VIEW public.vw_vs_vw_l10n_br_cnab_return_event__vw_report_contab_baixados
AS SELECT
        CASE
            WHEN cnab.cnab = 1 AND contab.contab = 1 THEN 'ambos'::text
            WHEN cnab.cnab = 1 THEN 'cnab'::text
            WHEN contab.contab = 1 THEN 'contab'::text
            ELSE NULL::text
        END AS existe,
    cnab.cnab_id,
    COALESCE(cnab.invoice_id, contab.invoice_id) AS invoice_id,
    COALESCE(cnab.occurrence_date, contab.occurrence_date) AS occurrence_date,
    cnab.dt_importacao AS cnab_dt_importacao,
    cnab.payment_value AS cnab_valor,
    contab.price_total_juros AS contab_valor,
    COALESCE(cnab.payment_value, 0::numeric) - COALESCE(contab.price_total_juros, 0::numeric) AS dif_valor,
    abs(COALESCE(cnab.payment_value, 0::numeric) - COALESCE(contab.price_total_juros, 0::numeric)) AS dif_valorabs,
    contab.tipocob__automatico_boleto_dinheiro AS contab_tipocob__automatico_boleto_dinheiro,
    cnab.occurrence_date AS cnab_occurrence_date,
    contab.occurrence_date AS contab_occurrence_date,
    cnab.invoice_id AS cnab_invoice_id,
    contab.invoice_id AS contab_invoice_id
   FROM ( SELECT 1 AS cnab,
            e.id AS cnab_id,
            e.invoice_id,
            e.occurrence_date,
            e.dt_importacao,
            e.payment_value::numeric AS payment_value
           FROM vw_l10n_br_cnab_return_event e
          WHERE e.occurrences::text = '06-Liquidação Normal *'::text AND e.occurrence_date = '2024-02-14'::date) cnab
     FULL JOIN ( SELECT 1 AS contab,
            b.invoice_id,
            b.occurrence_date,
            b.tipocob__automatico_boleto_dinheiro,
            round(sum(b.price_total_juros), 2) AS price_total_juros
           FROM vw_report_contab_baixados b
          WHERE (b.tipocob__automatico_boleto_dinheiro = ANY (ARRAY['A'::text, 'B'::text])) AND b.occurrence_date = '2024-02-14'::date
          GROUP BY 1::integer, b.invoice_id, b.occurrence_date, b.tipocob__automatico_boleto_dinheiro) contab ON contab.invoice_id = cnab.invoice_id AND contab.occurrence_date = cnab.occurrence_date;

COMMENT ON VIEW public.vw_vs_vw_l10n_br_cnab_return_event__vw_report_contab_baixados IS '
task:418-Criar view vw_vs_vw_l10n_br_cnab_return_event__vw_report_contab_baixados para comparar relatório paid_invoice com os pagamento do banco via arquivo remessa/cnab

obs: por questão desempenho, ao invés de utilizar o campo occurrence_date no where, utilizar os campos cnab_occurrence_date em conjunto com contab_occurrence_date conforme exemplo abaixo:

Exemplo de uso:
select *
  from vw_vs_vw_l10n_br_cnab_return_event__vw_report_contab_baixados v
 where true
   and cnab_occurrence_date = ''2024-02-15''
   and contab_occurrence_date = ''2024-02-15''
   and dif_valorabs > 0
';