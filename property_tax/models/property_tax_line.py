# Copyright 2021 - TODAY, Marcel Savegnago <marcel.savegnago@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class PropertyTaxLines(models.Model):

    _name = 'property.tax.line'
    _description = 'Property Tax Line'

    tax_id = fields.Many2one('property.tax', 'Tax')
    name = fields.Char()
    value = fields.Float()
