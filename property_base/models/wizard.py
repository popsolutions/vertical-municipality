# Copyright 2021 - TODAY, Marcel Savegnago <marcel.savegnago@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models, api


class PropertyInvoiceWizard(models.TransientModel):

    _name = 'property.invoice.wizard'
    _description = 'Property Invoice Wizard'

    def process_batch_invoices(self):
        self.env['account.invoice']._cron_process_municipality_services()

        return self.env.ref('account.action_invoice_tree1').read()[0]
