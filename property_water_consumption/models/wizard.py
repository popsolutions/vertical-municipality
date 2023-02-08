from odoo import fields, models, api


class PropertyWaterConsumptionWizard(models.TransientModel):

    _name = 'property.water.consumption.wizard'
    _description = 'Property Water Consumption Wizard'

    def process_batch_water_consumptions(self):
        self.env['property.water.consumption'].create_batch_water_consumptions()
        return self.env.ref('property_water_consumption.water_consumption_action').read()[0]

class PropertyWaterConsumptionWizardUnifiedy(models.TransientModel):
    _name = 'property.water.consumption.wizard.unifiedy'
    _description = 'Property Water Consumption Wizard Process Unifiedy'
    def process_batch_unifiedy_water_consumptions(self):
        self.env['property.water.consumption'].process_batch_unifiedy_water_consumptions()