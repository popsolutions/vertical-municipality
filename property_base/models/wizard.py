from odoo import fields, models, api


class PropertyInvoiceWizard(models.TransientModel):
    _name = 'property.invoice.wizard'

    def process_batch_invoices(self):
        self.env['account.invoice']._cron_process_municipality_services()

        return self.env.ref('account.action_invoice_tree1').read()[0]
