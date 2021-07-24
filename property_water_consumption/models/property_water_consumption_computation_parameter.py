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

    # def get_total(self, consumption):
    #     total = 0
    #     line_ids = sorted(self.line_ids, key=lambda r: r.start, reverse=True)
    #     for line in line_ids:
    #         try:
    #             if consumption // line.start:
    #                 sub_consumption = consumption % line.start
    #                 total += sub_consumption * line.amount
    #                 consumption -= sub_consumption
    #         except ZeroDivisionError:
    #             total += consumption * line.amount
    #
    #     return total

    def get_total(self, consumption):
        total = 0
        line_ids = sorted(self.line_ids, key=lambda r: r.start, reverse=False)
        consumption_aux = 0
        consumption_aux2 = 0
        line_end_old = 0
        for line in line_ids:
            try:
                if consumption // (line.start or 1):
                    if not consumption_aux:
                        if consumption > line.end:
                            consumption_aux = line.end
                        else:
                            consumption_aux = consumption
                    elif (consumption_aux + line_end_old) > line.end:
                        consumption_aux = line.end - line_end_old
                    else:
                        consumption_aux = consumption - consumption_aux2
                    total += consumption_aux * line.amount
                    line_end_old = line.end
                    consumption_aux2 += consumption_aux
            except ZeroDivisionError:
                total += consumption * line.amount

        return total
