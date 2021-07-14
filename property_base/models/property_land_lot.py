# Copyright 2021 - TODAY, Marcel Savegnago <marcel.savegnago@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _


class PropertyLandLot(models.Model):

    _name = 'property.land.lot'
    _description = 'Property Land Lot'

    code = fields.Char(required=True)
    block_id = fields.Many2one('property.land.block', 'Block')
    info = fields.Text()

    @api.multi
    def name_get(self):
        res = []
        for rec in self:
            custom_name = "{} (Block {})".format(rec.code, rec.block_id.code)
            res.append((rec.id, custom_name))
        return res
