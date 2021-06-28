from odoo import api, fields, models


class PropertyLand(models.Model):
    _inherit = 'property.land'

    water_connection_date = fields.Date(
        string="Water Conection Date"
    )
    water_charging_date = fields.Date(
        string="Water Charging Date"
    )
    sewage_connection_date = fields.Date(
        string="Sewage Connection Date"
    )
    sewage_charging_date = fields.Date(
        string="Sewage Charging Date"
    )
    water_consumption_route_id = fields.Many2one(
        'property.water.consumption.route',
        string="Consumption Route"
    )
    water_computation_parameter_id = fields.Many2one(
        'property.water.consumption.computation.parameter',
        string="Consumption Parameters"
    )
    water_consumption_meter_code = fields.Char(
        string="Consumption Meter Code"
    )
    water_consumption_economy_qty = fields.Integer(
        string="Consumption Economy Qty"
    )
    water_consumption_unit_qty = fields.Integer(
        string="Consumption Unit Qty"
    )
    water_consumption_count = fields.Integer(
        compute='_compute_water_consumption_count',
        string='Consumption Count'
    )

    def _compute_water_consumption_count(self):
        wc_obj = self.env['property.water.consumption'].sudo()
        for rec in self:
            rec.water_consumption_count = wc_obj.search_count([('land_id', '=', rec.id)])
