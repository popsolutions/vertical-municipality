# Copyright 2021 - TODAY, Marcel Savegnago <marcel.savegnago@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _


class PropertyLandType(models.Model):

    _inherit = 'property.land.type'

    used_area_to_tax = fields.Selection(
        selection=[
            ('exclusive','Exclusive Area'),
            ('building', 'Building Area'),
        ],
        default='exclusive',
        required=True
    )
