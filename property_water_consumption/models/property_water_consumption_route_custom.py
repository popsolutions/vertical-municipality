from odoo import api, fields, models


class PropertyWaterConsumptionRouteCustom(models.Model):

    _name = 'property.water.consumption.route.custom'
    _description = 'Rotas personalizadas'

    name = fields.Char(string= "Nome")
    route_id = fields.Many2one('property.water.consumption.route', string='Rota', required=True)
    land_ids = fields.One2many('property.water.consumption.route.lands', 'routecustom_id', copy=True)
    active = fields.Boolean(string='Ativo', default=True)
