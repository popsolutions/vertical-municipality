import logging
from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class AccountInvoice(models.Model):

    _inherit = 'account.invoice'

    @api.multi
    def _get_process_methods_list(self):
        methods_list = super(AccountInvoice, self)._get_process_methods_list()
        methods_list.append('process_property_ga_tax')
        return methods_list

    @api.multi
    def process_property_ga_tax(self):
        """Main method that will be executed by the cron job
        and will create all of invoices from their pending Green Area Tax"""
        product_id = self.env.ref('property_ga_maintenance.property_ga_maintenance')
        account_id = product_id.product_tmpl_id.get_product_accounts()[
            'income']

        property_wc_ids = self.env['property.ga.tax'].search(
            [('state', 'not in', ['processed'])])
        inv_ids = self.search([('land_id', '!=', False),
                               ('state', 'not in', ['in_payment',
                                                    'paid',
                                                    'cancel'])])
        inv_land_ids = inv_ids.mapped('land_id').ids

        records_len = len(property_wc_ids)
        records_index = 0

        for p_wc in property_wc_ids:
            if p_wc.land_id.id not in inv_land_ids:
                self._create_property_ga_customer_invoice(
                    p_wc, product_id, account_id)
            else:
                inv_id = self.search([('land_id', '=', p_wc.land_id.id), ('state', 'not in', ['in_payment',
                                                    'paid',
                                                    'cancel'])], limit=1)
                inv_id.write({'invoice_line_ids': [(0, 0,  { 
                    'product_id': product_id.id,
                    'name': product_id.name,
                    'price_unit': p_wc.current_tax,
                    'account_id': account_id.id,
                    'invoice_line_tax_ids': [(6, 0, product_id.taxes_id.ids)],
                 })]})
            p_wc.state = 'processed'

            records_index += 1
            print('account.invoice - property.ga.tax - record ' + str(records_index) + '/' + str(records_len))

    @api.multi
    def _create_property_ga_customer_invoice(self, p_wc, product_id, account_id):

        inv_line_vals = {
            'product_id': product_id.id,
            'name': product_id.name,
            'price_unit': p_wc.current_tax,
            'account_id': account_id.id,
            'invoice_line_tax_ids': [(6, 0, product_id.taxes_id.ids)],
        }
        inv_data = {
            'type': 'out_invoice',
            'account_id': p_wc.land_id.owner_id.property_account_receivable_id.id,
            'partner_id': p_wc.land_id.owner_id.id,
            'origin': p_wc.display_name,
            'land_id': p_wc.land_id.id,
            'invoice_line_ids': [(0, 0, inv_line_vals)],
        }
        self.sudo().create(inv_data)
