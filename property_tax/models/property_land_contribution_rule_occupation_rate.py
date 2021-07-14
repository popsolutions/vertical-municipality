# Copyright 2021 - TODAY, Marcel Savegnago <marcel.savegnago@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _


class PropertyLandContributionRuleOccupationRate(models.Model):

    _name = 'property.land.contribution.rule.occupation.rate'
    _description = 'Property Land Contribution Rule Occupation Rate'

    contribution_rule_id = fields.Many2one(
        'property.land.contribution.rule',
        string='Contribution Rule')
    pavement_qty = fields.Float(string="Pavement Quantity")
    occupation_rate = fields.Float(string="Occupation Rate (%)")