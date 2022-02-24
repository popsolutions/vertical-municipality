# Copyright 2021 - TODAY, Marcel Savegnago <marcel.savegnago@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, tools


class PropertyLand(models.Model):
    _inherit = 'property.land'

    owner_invoice_id = fields.Many2one(
        'res.partner',
        'Owner',
        track_visibility='onchange'
    )

