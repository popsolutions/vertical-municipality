# Copyright 2021 - TODAY, Marcel Savegnago <marcel.savegnago@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _


class PropertyLandBlock(models.Model):

    _name = 'property.land.block'
    _description = 'Property Land Block'

    code = fields.Char(required=True)
    info = fields.Text()
    module_id = fields.Many2one(
        'property.land.module',
        'Module',required=True
    )

    @api.multi
    def name_get(self):
        res = []
        for rec in self:
            custom_name = "{} (Module {})".format(rec.code, rec.module_id.code)
            res.append((rec.id, custom_name))
        return res
