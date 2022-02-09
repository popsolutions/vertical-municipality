# Copyright 2021 - TODAY, Marcel Savegnago <marcel.savegnago@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):

    _inherit = 'res.config.settings'

    property_ga_tax_index = fields.Float('Green Area Tax Index', config_parameter='property_ga_maintenance.property_ga_tax_index')
