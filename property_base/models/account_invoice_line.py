import logging
from odoo import models, api, fields

_logger = logging.getLogger(__name__)

class AccountMoveLine(models.Model):
    _inherit = "account.invoice.line"

    anomes_vencimento = fields.Integer('Ano/Mês Venc.', defaul=None)
    # account_invoice_line_id_accumulated_ref = fields.Integer()
    anomes_vencimento_original = fields.Integer('Ano/Mês Vencimento')
    name_original = fields.Text
    land_id = fields.Many2one(
        'property.land',
        'Property',
        track_visibility='onchange'
    )

    @api.model
    def create(self, vals):
        # if vals['product_id'] in [1, 10, 7, 9, 12]
        query = '''
select anomes(ai.date_due) anomes,
       anomes_text(anomes_inc(anomes(ai.date_due), pt.yearmonth_dec_from_invoice)) anomes_text,
       pt."name" product_template_name        
  from account_invoice ai,
       (select * from product_template pt where pt.id = ''' + str(vals['product_id']) + ''') pt
 where ai.id = ''' + str(vals['invoice_id'])

        self.env.cr.execute(query)
        res = self.env.cr.fetchall()[0]

        # if vals['account_invoice_line_id_accumulated_ref'] == 0:
        #     vals['account_invoice_line_id_accumulated_ref'] = None

        if 'anomes_vencimento_original' in vals and vals['anomes_vencimento_original'] == 0:
            vals['anomes_vencimento_original'] = None

        if 'anomes_vencimento' not in 'vals':
            vals.update({'anomes_vencimento': 0})

        if not vals['anomes_vencimento']:
            vals.update({'anomes_vencimento': 0})

        if vals['anomes_vencimento'] == 0 and res[0] != None:
            anomes_text = res[1] # anomes_text
            vals['name'] = res[2] + ' ' + anomes_text
            vals.update({'anomes_vencimento': res[0]})

        if vals['anomes_vencimento'] == 0:
            vals['anomes_vencimento'] = None

        res = super().create(vals)
        return res