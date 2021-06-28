from odoo import api, fields, models


class PropertyWaterConsumptionLineReader(models.Model):

    _name = 'property.water.consumption.issue'
    _description = 'Property Water Consumption Issue'

    code = fields.Char()
    name = fields.Char()
    info = fields.Text()