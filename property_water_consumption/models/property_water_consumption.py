from odoo import api, fields, models


class PropertyWaterConsumption(models.Model):

    _name = 'property.water.consumption'
    _order = 'date desc'
    _description = 'Property Water Consumption'

    land_id = fields.Many2one('property.land')
    date = fields.Date(default=fields.Date.context_today)
    last_read = fields.Integer()
    current_read = fields.Integer()
    consumption = fields.Integer(compute='_compute_consumption', store=True)
    issue_id = fields.Many2one('property.water.consumption.issue')
    reader_id = fields.Many2one('res.partner')
    total = fields.Float(compute='_compute_total', store=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('pending', 'Pending'),
        ('processed', 'Processed')
        ], default='draft')
    photo = fields.Binary('Photo')

    @api.multi
    def name_get(self):
        res = []
        for rec in self:
            custom_name = "{} ({})".format(rec.land_id.name, rec.date)
            res.append((rec.id, custom_name))
        return res

    @api.depends('last_read', 'current_read')
    def _compute_consumption(self):
        for rec in self:
            if not rec.current_read:
                rec.consumption = 0
            else:
                rec.consumption = rec.current_read - rec.last_read

    @api.depends('consumption', 'land_id')
    def _compute_total(self):
        for rec in self:
            if rec.consumption and rec.land_id and rec.state in ['draft']:
                consumption = rec.consumption
                water_consumption_economy_qty = rec.land_id.water_consumption_economy_qty or 1
                if consumption <= rec.land_id.type_id.minimum_water_consumption:
                    consumption = rec.land_id.type_id.minimum_water_consumption
                    water_consumption_economy_qty = 1
                else:
                    consumption = float(consumption / water_consumption_economy_qty)
                rec.total = (
                        rec.land_id.type_id.water_computation_parameter_id.get_total(
                            consumption)*water_consumption_economy_qty
                )
                rec.total += rec.total*0.8

    @api.multi
    def get_last_read(self, land_id):
        wc_id = self.search([('land_id', '=', land_id)], limit=1)
        return wc_id.current_read

    @api.multi
    def create_batch_water_consumptions(self):
        land_ids = self.env['property.land'].search([], limit=10) #TODO: Remove this limit
        # formula = self._get_formula()
        for land in land_ids:
            # wc_id = self.search([('land_id', '=', land.id)])
            # amount, lines = self._get_tax_amount_and_lines(land, formula)
            values = {
                'land_id': land.id,
                'last_read': self.get_last_read(land.id)
            }

            self.create(values)
