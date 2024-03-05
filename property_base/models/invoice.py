# Copyright 2021 - TODAY, Marcel Savegnago <marcel.savegnago@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import logging

from odoo import api, fields, models
import logging
import datetime
from odoo import tools
_logger = logging.getLogger(__name__)

class AccountInvoice(models.Model):

    _inherit = 'account.invoice'

    land_id = fields.Many2one('property.land', string='Land', required=True)
    block_id = fields.Many2one('property.land.block', 'Block', related='land_id.block_id')
    module_id = fields.Many2one('property.land.module', 'Module', related='land_id.module_id')
    zone_id = fields.Many2one('property.land.zone', 'Zone', related='land_id.module_id.zone_id')
    cnab_days_due_limit = fields.Integer(default=10, string='Dias de limite para cnab')

    @api.multi
    def _get_process_methods_list(self):
        """Return the list of methods to invoke in order to
        run the particular processes that will add invoice.lines
        for that specific service/product.
        Override this method if you add a new service to invoice for the
        vertical municipality.
        i.e return ['process_land_tax', process_water_consumption]"""
        methods_list = []
        return methods_list

    def _cron_process_municipality_services(self):
        methods_list = self._get_process_methods_list()
        for method in methods_list:
            if hasattr(self, method):
                getattr(self, method)()
            else:
                _logger.info("The {} method wasn't found".format(method))

    @api.multi
    def process_property_invoice(self, productIdName, modelName, modelLabel, price_unitFieldName, domain=None):
        """Main method that will be executed by the cron job
        and will create all of invoices from their pending <modelName> param"""
        product_id = self.env.ref(productIdName)
        account_id = product_id.product_tmpl_id.get_product_accounts()[
            'income']

        if domain:
            property_wc_ids_domain = domain
        else:
            property_wc_ids_domain = [('state', 'not in', ['processed'])]

        property_wc_ids = self.env[modelName].search(property_wc_ids_domain)

        inv_ids = self.invoices_get_monthly_last_draft()

        inv_land_ids = inv_ids.mapped('land_id').ids

        records_len = len(property_wc_ids)
        records_index = 0

        for p_wc in self.web_progress_iter(property_wc_ids, msg="Process " + modelLabel):
            if p_wc[price_unitFieldName] == 0:
                p_wc.state = 'processed'
                continue

            if p_wc.land_id.land_id_invoice().id not in inv_land_ids:
                # Se não existe uma fatura no status DRAFT, vou criar uma
                self._create_property_customer_invoice(
                    p_wc, product_id, account_id, price_unitFieldName)

                inv_land_ids.append(p_wc.land_id.land_id_invoice().id)
            else:
                # Se já existe uma fatura no status DRAFT, vou adcionar o item atual a ela
                inv_id = self.search([('land_id', '=', p_wc.land_id.land_id_invoice().id), ('state', 'in', ['draft'])], limit=1)
                
                inv_id.write({'invoice_line_ids': [(0, 0, {
                    'product_id': product_id.id,
                    'name': product_id.name,
                    'price_unit': p_wc[price_unitFieldName],
                    'account_id': account_id.id,
                    'land_id': p_wc.land_id.id,
                    'invoice_line_tax_ids': [(6, 0, product_id.taxes_id.ids)],
                })]})
            p_wc.state = 'processed'

            records_index += 1
            _logger.info('account.invoice - ' + modelName + ' - record ' + str(records_index) + '/' + str(records_len))

    @api.multi
    def _create_property_customer_invoice(self, p_wc, product_id, account_id, price_unitFieldName):
        invoice_owner_id = p_wc.land_id.getInvoiceOwner_id()

        self.env.cr.execute('select invoice_date_due from vw_property_settings_monthly_last')
        dts = self.env.cr.fetchall()[0]
        date_due = dts[0]

        inv_line_vals = {
            'product_id': product_id.id,
            'name': product_id.name,
            'price_unit': p_wc[price_unitFieldName],
            'account_id': account_id.id,
            'land_id': p_wc.land_id.id,
            'invoice_line_tax_ids': [(6, 0, product_id.taxes_id.ids)],
        }
        inv_data = {
            'type': 'out_invoice',
            'account_id': invoice_owner_id.property_account_receivable_id.id,
            'partner_id': invoice_owner_id.id,
            'origin': p_wc.name_get_unifiedy(),
            'date_due': date_due,
            'initial_date_due': date_due,
            'date_invoice': datetime.date.today(),
            'land_id': p_wc.land_id.land_id_invoice().id,
            'invoice_line_ids': [(0, 0, inv_line_vals)],
            'payment_term_id': None,
            'payment_mode_id': invoice_owner_id.customer_payment_mode_id.id or 1
        }
        self.sudo().create(inv_data)

    def process_old_invoices_fees(self):
        self.env.cr.execute('select account_invoice_create_fees_traffic_curcorrection_defproc()')

    def get_partner_id_email(self, invoice):
        #Retorna qual email deverá ser enviado o boleto
        #O email é enviado para o primeiro campo preenchido de acordo com a seguinte ordem:
        #  property_land.invoicesend_email, res_partner.invoicesend_email, res_partner.email (res_partner considerando "faturar ao proprietário"(owner_invoice_id))
        query = 'select func_land_emailboleto_byinvoice(' + str(self[0].id) + ')'
        self.env.cr.execute(query)
        cur = self.env.cr.fetchall()[0]
        emails = tools.email_split(cur[0])
        Partner = self.env['res.partner']
        partner_ids = ''

        for email in emails:
            partner_id = Partner.find_or_create(email)
            partner_ids += str(partner_id) + ','

        return partner_ids
