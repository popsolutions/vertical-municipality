# Copyright 2021 - TODAY, Marcel Savegnago <marcel.savegnago@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _


class PropertyLandZone(models.Model):

    _name = 'property.land.zone'
    _description = 'Property Land Zone'

    code = fields.Char(required=True)
    name = fields.Char(required=True)
    info = fields.Text()
