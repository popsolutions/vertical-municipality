
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta

from odoo import models, fields, api
import json
from odoo import sql_db
from psycopg2.extras import RealDictCursor

class AppointmentReportWizard(models.TransientModel):
    _name = "property_base.paidinvoicereport.wizard"
    _description = "Print Paid invoices"

    date_from = fields.Date(string='Date from', required=False)
    date_to = fields.Date(string='Date to', required=False)

    def button_action_menu_rel_cont_invoices_paid(self):
        domain = []

        date_from = self.date_from
        date_to = self.date_to

        sql = """
select row_to_json(t)::varchar invoices_sum
  from ( 
        select coalesce(sum(t.total_proprietario), 0) total_proprietario_sum,
               coalesce(sum(t.total_agua), 0) total_agua_sum,
               coalesce(sum(t.total_contribuicaomensal), 0) total_contribuicaomensal_sum,
               coalesce(sum(t.total_taxas), 0) total_taxas_sum,
               coalesce(sum(t.jurosproporcional_valor), 0) jurosproporcional_valor_sum,
               coalesce(sum(t.total_areaverde), 0) total_areaverde_sum,
               coalesce(sum(t.juros_areaverde), 0) juros_areaverde_sum,
               coalesce(sum(t.total_taxacaptacao), 0) total_taxacaptacao_sum,
               coalesce(sum(t.descontos), 0) descontos_sum,
               coalesce(sum(t.price_total), 0) price_total_sum,
               coalesce(sum(t.price_total_juros), 0) price_total_juros_sum,
               json_agg(t) invoices
         from (
               select v.res_id,
                      v.res_name,
                      count(0) qtde,
                      sum(v.price_total_juros) total_proprietario,
                      sum(v.total_agua) total_agua,
                      sum(v.total_contribuicaomensal) total_contribuicaomensal,
                      sum(v.total_taxas) total_taxas,
                      sum(v.jurosproporcional_valor) jurosproporcional_valor,
                      sum(v.total_areaverde) total_areaverde,
                      sum(v.juros_areaverde) juros_areaverde,
                      sum(v.total_taxacaptacao) total_taxacaptacao,
                      sum(v.descontos) descontos,
                      sum(v.price_total) price_total,
                      sum(v.price_total_juros) price_total_juros,
                      json_agg((
                      select t from (select
                      v.invoice_id,
                      v.land_id,
                      v.module_code,
                      v.block_code,
                      v.lot_code,
                      v.referencia,
                      v.total_agua,
                      v.total_contribuicaomensal,
                      v.total_taxas,
                      v.jurosproporcional_valor,
                      v.total_areaverde,
                      v.juros_areaverde,
                      v.total_taxacaptacao,
                      v.descontos,
                      v.price_total,
                      v.occurrence_date,
                      v.tipocobranca,
                      v.observacao,
                      v.real_payment_date,
                      v.due_date,
                      v.res_name,
                      v.product_id,
                      v.land,
                      v.product_name,
                      v.price_total,
                      v.price_total_juros) t)) res_lines
                 from vw_report_contab_baixados v
                where v.occurrence_date between'""" + date_from.strftime('%Y/%m/%d') + """' and '""" + date_to.strftime('%Y/%m/%d') + """'
                group by
                      v.res_id,
                      v.res_name
             ) t
        ) t
"""
        # where v.real_payment_date between'""" + date_from.strftime('%Y/%m/%d') + """' and '""" + date_to.strftime('%Y/%m/%d') + """'

        self.env.cr.execute(sql)
        invoices_cr = self.env.cr.fetchall()

        appointments = json.loads(invoices_cr[0][0])

        data = {
            'doc_model': 'action_paidinvoice_report',
            'date_from':date_from,
            'date_to':date_to,
            'form_data': self.read()[0],
            'appointments': appointments
        }
        return self.env.ref('property_base.action_paidinvoice_report').report_action(self, data=data)


    @api.constrains('date_from', 'date_to')
    def _check_date_validation(self):
        for record in self:
            if record.date_from > record.date_to:
                raise ValidationError("Date from must be previous than date to.")

class AppointmentReportWizard_Report(models.AbstractModel):
    """
        Abstract Model specially for report template.
        _name = Use prefix `report.` along with `module_name.report_name`
    """
    _name = 'report.property_base.paidinvoicereport.wizard'

    @api.model
    def _get_report_values(self, docids, data=None):
        print('x')
        return {
            'data': data,
        }
