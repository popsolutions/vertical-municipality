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

    def get_total(self, consumption, display_name):
        total = 0
        line_ids = sorted(self.line_ids, key=lambda r: r.start, reverse=False)
        consumption_balance = consumption
        aux_1 = 0
        index = 1

        if (len(line_ids) == 0) and (consumption > 0):
            raise Exception('Não foi possível calcular a água para o lote "' + str(display_name) + '" pois não foi encontrado os parâmetros de cálculo para este lote.')

        for line in line_ids:
            line_consumption = line.end - line.start + aux_1
            if (consumption_balance > line_consumption) and (index < len(line_ids)):
                consumption_calc = line_consumption
            else:
                consumption_calc = consumption_balance

            total += consumption_calc * line.amount
            consumption_balance = consumption_balance - consumption_calc
            aux_1 = 1
            index += 1

            if consumption_balance == 0:
                break

        if (consumption_balance != 0):
            raise Exception('Falha no cálculo da água para o lote "' + str(display_name) + '". Variável consumption_balance tem que finalizar com valor ZERO.')

        return total

    # Cálculo anterior - estava se pertendo apartir da terceira entrada no loop
    # def get_total(self, consumption):
    #     total = 0
    #     line_ids = sorted(self.line_ids, key=lambda r: r.start, reverse=False)
    #     consumption_aux = 0
    #     consumption_aux2 = 0
    #     line_end_old = 0
    #     for line in line_ids:
    #         try:
    #             if consumption // (line.start or 1):
    #                 if not consumption_aux:
    #                     if consumption > line.end:
    #                         consumption_aux = line.end
    #                     else:
    #                         consumption_aux = consumption
    #                 elif (consumption_aux2 + line_end_old) > line.end:
    #                     consumption_aux = line.end - line_end_old
    #                 else:
    #                     consumption_aux = consumption - consumption_aux2
    #                 total += consumption_aux * line.amount
    #                 line_end_old = line.end
    #                 consumption_aux2 += consumption_aux
    #         except ZeroDivisionError:
    #             total += consumption * line.amount
    #
    #     return total
