from odoo import fields, models, api


class PropertyWaterConsumptionWizard(models.TransientModel):

    _name = 'property.water.consumption.wizard'
    _description = 'Property Water Consumption Wizard'

    def process_batch_water_consumptions(self):
        self.env['property.water.consumption'].create_batch_water_consumptions()

        return self.env.ref('property_water_consumption.water_consumption_action').read()[0]
