from odoo import api, fields, models


class PropertyLand(models.Model):
    _inherit = 'property.water.consumption'

    rate_catchment = fields.Float("Taxa de Captação")
