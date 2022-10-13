from odoo import api, models
from ...l10n_br_account_payment_brcobranca_batch.controllers.portal import *

class MailTemplate(models.Model):
    _inherit = 'mail.template'

    @api.multi
    def generate_email(self, res_ids, fields=None):
        res = super(MailTemplate, self).generate_email(res_ids, fields)
        if self.env.context.get('active_model') != 'account.invoice':
            return res

        # Anexar pdf do boleto ao e-mail
        for res_id, template in self.web_progress_iter(self.get_email_template(res_ids).items(), 'Gerando boletos'):
            ir_attachment = process_boleto_frente_verso(str(res_id), False, True)
            attachments = [('Boleto.pdf', ir_attachment.datas)]
            res[res_id]['attachments'] += attachments

        return res