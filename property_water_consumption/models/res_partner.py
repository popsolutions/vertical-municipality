from odoo import api, fields, models


class ResPartner(models.Model):

    _inherit = 'res.partner'

    water_consumption_reader = fields.Boolean('Is a Water Consumption Reader')
