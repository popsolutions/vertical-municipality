# Copyright 2021 - TODAY, Marcel Savegnago <marcel.savegnago@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models


class ResPartner(models.Model):

    _inherit = 'res.partner'

    property_count = fields.Integer(compute='_compute_property_count', string='Property Land Count')
    invoicesend_email = fields.Char(string='E-mail Invoice Send')

    def _compute_property_count(self):
        property_obj = self.env['property.land'].sudo()
        for rec in self:
            rec.property_count = property_obj.search_count([('owner_id', '=', rec.id)])
