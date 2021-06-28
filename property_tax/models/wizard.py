# Copyright 2021 - TODAY, Marcel Savegnago <marcel.savegnago@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models, api


class PropertyTaxWizard(models.TransientModel):

    _name = 'property.tax.wizard'
    _description = 'Property Tax Wizard'

    def process_batch_taxes(self):
        self.env['property.tax'].create_batch_land_taxes()

        return self.env.ref('property_tax.property_tax_action').read()[0]
