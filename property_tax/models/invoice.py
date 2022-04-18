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
        self.process_property_invoice('property_tax.product_property_tax', 'property.tax',
                                      'Property taxes', 'amount_total')
