# Copyright 2021 - TODAY, Marcel Savegnago <marcel.savegnago@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class AccountInvoice(models.Model):

    _inherit = 'account.invoice'

    @api.multi
    def _get_process_methods_list(self):
        methods_list = super(AccountInvoice, self)._get_process_methods_list()
        methods_list.append('process_property_tax')
        return methods_list

    @api.multi
    def process_property_tax(self):
        """Main method that will be executed by the cron job
        and will create all of invoices from their pending property taxes"""
        product_id = self.env.ref('property_tax.product_property_tax')
        account_id = product_id.product_tmpl_id.get_product_accounts()[
            'income']

        property_tax_ids = self.env['property.tax'].search(
            [('state', 'not in', ['processed'])])
        inv_ids = self.search([('land_id', '!=', False),
                               ('state', 'not in', ['in_payment',
                                                    'paid',
                                                    'cancel'])])
        inv_land_ids = inv_ids.mapped('land_id').ids

        for p_tax in property_tax_ids:
            if p_tax.land_id.id not in inv_land_ids:
                self._create_property_tax_customer_invoice(
                    p_tax, product_id, account_id)
            # else:
                #TODO: Add new lines to invoice
            p_tax.state = 'processed'

    @api.multi
    def _create_property_tax_customer_invoice(self, p_tax, product_id, account_id):

        inv_line_vals = {
            'product_id': product_id.id,
            'name': product_id.description,
            'price_unit': p_tax.amount_total,
            'account_id': account_id.id,
            'invoice_line_tax_ids': [(6, 0, product_id.taxes_id.ids)],
        }
        inv_data = {
            'type': 'out_invoice',
            'account_id': p_tax.land_id.owner_id.property_account_receivable_id.id,
            'partner_id': p_tax.land_id.owner_id.id,
            'origin': p_tax.name,
            'land_id': p_tax.land_id.id,
            'invoice_line_ids': [(0, 0, inv_line_vals)],
        }
        self.sudo().create(inv_data)
