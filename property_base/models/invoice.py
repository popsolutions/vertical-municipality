# Copyright 2021 - TODAY, Marcel Savegnago <marcel.savegnago@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class AccountInvoice(models.Model):

    _inherit = 'account.invoice'

    land_id = fields.Many2one('property.land', string='Land')
    block_id = fields.Many2one('property.land.block', 'Block', related='land_id.block_id')
    module_id = fields.Many2one('property.land.module', 'Module', related='land_id.module_id')
    zone_id = fields.Many2one('property.land.zone', 'Zone', related='land_id.module_id.zone_id')

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