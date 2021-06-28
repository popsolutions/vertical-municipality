# Copyright 2021 - TODAY, Marcel Savegnago <marcel.savegnago@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _


class PropertyLandModule(models.Model):

    _name = 'property.land.module'
    _description = 'Property Land Module'

    code = fields.Char(required=True)
    name = fields.Char(required=True)
    info = fields.Text()
    zone_id = fields.Many2one('property.land.zone', 'Zone')
