# Copyright 2021 - TODAY, Marcel Savegnago <marcel.savegnago@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ResConfigSettings(models.TransientModel):

    _inherit = 'res.config.settings'

    # property_tax_fixed_value = fields.Float('Fixed Value', digits=(12,4), config_parameter='property_tax.fixed_value') # Transferido para vw_property_settings_monthly_last.property_tax_fixed_value
    # property_tax_minimal_contribution = fields.Float('Minimal Contribution', config_parameter='property_tax.minimal_contribution') # Transferido para vw_property_settings_monthly_last.property_tax_minimal_contribution
    # property_tax_monthly_index = fields.Float('Monthly Index', digits=(12,5), config_parameter='property_tax.monthly_index') # Transferido para vw_property_settings_monthly_last.property_tax_monthly_index
    property_tax_formula = fields.Char('Formula', config_parameter='property_tax.formula')
