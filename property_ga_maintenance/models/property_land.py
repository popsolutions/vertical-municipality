from odoo import api, fields, models


class PropertyLand(models.Model):
    _inherit = 'property.land'

    is_not_tax_ga = fields.Boolean(
        'Is Not Tax Green Area',
        default=True
    )

    tax_ga_initial_value = fields.Float(
        'Tax Green Area Initial Value',
        default=0
    )

    property_tax_ga_ids = fields.One2many(
        'property.ga.tax',
        'land_id',
        'Green Area Maintenance Taxes',
        help="Green Area Maintenance Taxes"
    )
