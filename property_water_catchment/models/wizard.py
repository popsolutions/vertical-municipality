from odoo import fields, models, api


class PropertyWaterConsumptionWizard(models.TransientModel):

    _inherit = 'property.water.consumption.wizard'

    @api.model
    def process_batch_water_consumptions(self, fields):
        # res = super(PropertyWaterConsumptionWizard, self).process_batch_water_consumptions() todo.remover este comentário
        self.env['property.water.catchment.monthly.rate']._compute_catchment_rate_current_month()
        return
        # return res
