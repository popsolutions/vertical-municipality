from odoo import api, fields, models


class PropertyWaterConsumptionRoute(models.Model):

    _name = 'property.water.consumption.route'
    _description = 'Property Water Consumption Route'

    name = fields.Char()
    info = fields.Text()
