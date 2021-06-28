# Copyright 2021 - TODAY, Marcel Savegnago <marcel.savegnago@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _


class PropertyLandStage(models.Model):

    _name = 'property.land.stage'
    _description = 'Property Land Stage'

    code = fields.Char(required=True)
    name = fields.Char(required=True)
    info = fields.Text()
    discount = fields.Float(string="Discount (%)")
