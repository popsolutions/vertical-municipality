
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
        if date_from:
            domain += [('date_due', '>=', date_from)]
        date_to = self.date_to
        if date_to:
            domain += [('date_due', '<=', date_to)]
        # print("\n\nTest................\n", domain)

        # appointments = self.env['account.invoice'].search_read(domain, limit=10)

        appointments = []
        appointments_lines = []

        appointments_lines.append({'id':1, 'total': 10})
        appointments_lines.append({'id':2, 'total': 10})
        appointments_lines.append({'id':3, 'total': 10})

        appointments.append({'code':'A', 'lines': appointments_lines})
        appointments_lines = []
        appointments_lines.append({'id':4, 'total': 10})
        appointments_lines.append({'id':5, 'total': 20})
        appointments_lines.append({'id':6, 'total': 30})
        appointments.append({'code':'B', 'lines': appointments_lines})

        appointments_lines = []
        appointments_lines.append({'id':8, 'total': 10})
        appointments_lines.append({'id':9, 'total': 20})
        appointments.append({'code':'C', 'lines': appointments_lines})

        sql = """
select row_to_json(t)::varchar invoices_sum
  from ( 
        select sum(total_proprietario) total_proprietario_sum,
               sum(total_agua) total_agua_sum,
               sum(t.total_contribuicaomensal) total_contribuicaomensal_sum,
               sum(t.total_taxas) total_taxas_sum,
               sum(t.jurosproporcional_valor) jurosproporcional_valor_sum,
               sum(t.total_areaverde) total_areaverde_sum,
               sum(t.juros_areaverde) juros_areaverde_sum,
               sum(t.total_taxacaptacao) total_taxacaptacao_sum,
               sum(t.descontos) descontos_sum,
               sum(t.price_total) price_total_sum,
               json_agg(t) invoices
         from (
               select v.res_id,
                      v.res_name,
                      count(0) qtde,
                      sum(v.price_total) total_proprietario,
                      sum(v.total_agua) total_agua,
                      sum(v.total_contribuicaomensal) total_contribuicaomensal,
                      sum(v.total_taxas) total_taxas,
                      sum(v.jurosproporcional_valor) jurosproporcional_valor,
                      sum(v.total_areaverde) total_areaverde,
                      sum(v.juros_areaverde) juros_areaverde,
                      sum(v.total_taxacaptacao) total_taxacaptacao,
                      sum(v.descontos) descontos,
                      sum(v.price_total) price_total,
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
                      v.price_total) t)) res_lines
                 from vw_report_contab_baixados v
                where v.real_payment_date between'""" + date_from.strftime('%Y/%m/%d') + """' and '""" + date_to.strftime('%Y/%m/%d') + """'
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
