# Copyright 2021 - TODAY, Marcel Savegnago <marcel.savegnago@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _


class PropertyLandType(models.Model):

    _inherit = 'property.land.type'

    minimum_water_consumption = fields.Float()

    water_computation_parameter_id = fields.Many2one(
        'property.water.consumption.computation.parameter',
        string="Consumption Parameters"
    )

    # water_consumption_rule_ids = fields.One2many(
    #     'property.land.type.water.consumption.rule',
    #     'land_type_id',
    #     'Water Consumption Rules',
    #     help="Water Consumption Rules"
    # )
