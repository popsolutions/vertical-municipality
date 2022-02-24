import logging
from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class AccountInvoice(models.Model):

    _inherit = 'account.invoice'

    @api.multi
    def _get_process_methods_list(self):
        methods_list = super(AccountInvoice, self)._get_process_methods_list()
        methods_list.append('process_property_water_consumption')
        return methods_list

    @api.multi
    def process_property_water_consumption(self):
        self.process_property_invoice('property_water_consumption.product_property_water_consumption', 'property.water.consumption',
                                      'Water Consumption', 'total')
        return