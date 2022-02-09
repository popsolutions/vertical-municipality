from odoo import fields, models, api


class PropertyWaterConsumptionWizard(models.TransientModel):

    _name = 'property.ga.tax.wizard'
    _description = 'Property Green Area Maintenance Tax Wizard'

    def process_batch_property_ga_maintenance(self):
        self.env['property.ga.tax'].process_batch_property_ga_maintenance()
        # return self.env.ref('property_ga_tax.property_ga_tax_act_window').read()[0]
