from odoo import api, models

class MailTemplate(models.Model):
    _inherit = 'mail.template'

    @api.multi
    def generate_email(self, res_ids, fields=None):
        res = super(MailTemplate, self).generate_email(res_ids, fields)
        if self.env.context.get('active_model') != 'account.invoice':
            return res

        # Anexar pdf do boleto ao e-mail
        for res_id, template in self.web_progress_iter(self.get_email_template(res_ids).items(), 'Gerando boletos'):
            invoice = self.env['account.invoice'].browse(res_id)
            invoice.gera_boleto_pdf()
            attachments = [('Boleto', invoice.file_pdf_id.datas)]
            res[res_id]['attachments'] += attachments

        return res