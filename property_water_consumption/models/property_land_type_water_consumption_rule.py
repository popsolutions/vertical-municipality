# Copyright 2021 - TODAY, Marcel Savegnago <marcel.savegnago@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _


class PropertyLandTypeWaterConsumptionRule(models.Model):

    _name = 'property.land.type.water.consumption.rule'
    _description = 'Property Land Type Water Consumption Rule'

    minimum_consumption = fields.Float()
    maximum_consumption = fields.Float()
    unit_price = fields.Float()

    land_type_id = fields.Many2one(
        'property.land.type',
        'Land Type',
        required=True
    )
