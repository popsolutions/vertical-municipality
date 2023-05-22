from odoo import api, fields, models


class PropertyWaterConsumptionComputationParameterLine(models.Model):

    _name = 'property.water.consumption.computation.parameter.line'
    _description = 'Property Water Consumption Computation Parameter Line'
    _order = 'start asc'

    start = fields.Integer()
    end = fields.Integer()
    amount = fields.Float(digits=(12, 4))
    param_id = fields.Many2one('property.water.consumption.computation.parameter')