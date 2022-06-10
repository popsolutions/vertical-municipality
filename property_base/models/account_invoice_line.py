import logging
from odoo import models, api, fields

_logger = logging.getLogger(__name__)

class AccountMoveLine(models.Model):
    _inherit = "account.invoice.line"

    anomes_vencimento = fields.Integer('Ano/Mês Venc.', defaul=None)
    # account_invoice_line_id_accumulated_ref = fields.Integer()
    anomes_vencimento_original = fields.Integer('Ano/Mês Vencimento')
    name_original = fields.Text

    @api.model
    def create(self, vals):
        # if vals['product_id'] in [1, 10, 7, 9, 12]
        query = '''
select anomes(ai.date_due) anomes,
       anomes_inc(anomes(ai.date_due), -1) anomes_anterior,
       anomes_text(anomes(ai.date_due)) anomes_text,
       anomes_text(anomes_inc(anomes(ai.date_due), -1)) anomes_anterior_text,
       (select pt."name"  from product_template pt where pt.id = ''' + str(vals['product_id']) + ''') product_template_name
  from account_invoice ai
 where id = ''' + str(vals['invoice_id'])

        self.env.cr.execute(query)
        res = self.env.cr.fetchall()[0]

        # if vals['account_invoice_line_id_accumulated_ref'] == 0:
        #     vals['account_invoice_line_id_accumulated_ref'] = None

        if vals['anomes_vencimento_original'] == 0:
            vals['anomes_vencimento_original'] = None

        if vals['anomes_vencimento'] == 0 and res[0] != None:
            # se o anomes_vencimento não esta em vals, certamente ele não e uma copia (duplicação de invoice)
            if vals['product_id'] in (1, 10):
                anomes = res[0] # anomes
                anomes_text = res[2] # anomes_anterior
            else:
                anomes = res[1] # anomes_anterior
                anomes_text = res[3] # anomes_anterior_text

            vals['name'] = res[4] + ' ' + anomes_text
            vals.update({'anomes_vencimento': anomes})

        if vals['anomes_vencimento'] == 0:
            vals['anomes_vencimento'] = None

        res = super().create(vals)
        return res