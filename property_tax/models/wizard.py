from odoo import fields, models, api


class PropertyTaxWizard(models.TransientModel):
    _name = 'property.tax.wizard'

    def process_batch_taxes(self):
        self.env['property.tax'].create_batch_land_taxes()

        return self.env.ref('property_tax.property_tax_action').read()[0]
