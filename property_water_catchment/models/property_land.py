from odoo import api, fields, models


class PropertyLand(models.Model):
    _inherit = 'property.land'

    property_water_catchment_ids = fields.One2many(
        'property.water.catchment',
        'land_id',
        'Water Catchment',
        help="Water Catchment Rate"
    )
