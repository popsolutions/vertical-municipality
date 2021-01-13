from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    property_count = fields.Integer(compute='_compute_property_count', string='Property Land Count')

    def _compute_property_count(self):
        property_obj = self.env['property.land'].sudo()
        for rec in self:
            rec.property_count = property_obj.search_count([('owner_id', '=', rec.id)])
