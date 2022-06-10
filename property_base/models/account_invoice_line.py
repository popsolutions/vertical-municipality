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
       anomes_text(anomes(ai.date_due)) anomes_text,
       anomes_text(anomes_inc(anomes(ai.date_due), -1)) anomes_anterior_text,
       (select pt."name"  from product_template pt where pt.id = ''' + str(vals['product_id']) + ''') product_template_name
  from account_invoice ai
 where id = ''' + str(vals['invoice_id'])

        self.env.cr.execute(query)
        res = self.env.cr.fetchall()[0]

        # if vals['account_invoice_line_id_accumulated_ref'] == 0:
        #     vals['account_invoice_line_id_accumulated_ref'] = None

        if 'anomes_vencimento_original' in vals and vals['anomes_vencimento_original'] == 0:
            vals['anomes_vencimento_original'] = None

        if 'anomes_vencimento' in vals:
            if vals['anomes_vencimento'] == 0 and res[0] != None:
                # se o anomes_vencimento não esta em vals, certamente ele não e uma copia (duplicação de invoice)

                if vals['product_id'] in (1, 10, 12): ### 1-Contribuição mensal, 10-Manutenção de Area verde, 12-Multas
                    # Na fatura o texto fica como Ano/mês ATUAL
                    anomes_text = res[1] # anomes_text
                else: ### 7-Agua/esgoto, 9-Taxa de captação
                    #Na fatura o texto fica como Ano/mês ANTERIOR
                    anomes_text = res[2] # anomes_anterior_text

                vals['name'] = res[3] + ' ' + anomes_text
                vals.update({'anomes_vencimento': res[0]})

            if vals['anomes_vencimento'] == 0:
                vals['anomes_vencimento'] = None

        res = super().create(vals)
        return res