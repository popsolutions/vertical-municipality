from odoo import fields, models, api


class PropertyWaterConsumptionWizard(models.TransientModel):

    _name = 'property.water.catchment.wizard'
    _description = 'Property Water Catchment Wizard'

    @api.model
    def process_batch_water_catchment(self, fields):
        self.env['property.water.catchment']._compute_catchment_rate_current_month()


