from odoo import api, fields, models


class PropertyWaterConsumptionComputationParameter(models.Model):

    _name = 'property.water.consumption.computation.parameter'
    _description = 'Property Water Consumption Computation Parameter'
    _rec_name = 'code'

    code = fields.Char()
    info = fields.Text()
    line_ids = fields.One2many('property.water.consumption.computation.parameter.line', 'param_id')

    @api.multi
    def name_get(self):
        res = []
        for rec in self:
            custom_name = "{} ({})".format(rec.code, rec.info)
            res.append((rec.id, custom_name))
        return res

    def get_total(self, consumption):
        total = 0
        line_ids = sorted(self.line_ids, key=lambda r: r.start, reverse=True)
        for line in line_ids:
            try:
                if consumption // line.start:
                    sub_consumption = consumption % line.start
                    total += sub_consumption * line.amount
                    consumption -= sub_consumption
            except ZeroDivisionError:
                total += consumption * line.amount

        return total
