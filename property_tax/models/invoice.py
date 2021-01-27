import logging
from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def _get_process_methods_list(self):
        methods_list = super(AccountInvoice, self)._get_process_methods_list()
        methods_list.append('process_land_tax')
        return methods_list

    def process_land_tax(self):
        pass
        #get all non-processed taxes
            #  self.env[property.land.tax].search([('state', 'not in', ['processed'])])
        #create_invoices_lines
        #mark them as processed
        _logger.info("\n\n TEST Land Tax \n")