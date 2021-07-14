# Copyright 2021 - TODAY, Marcel Savegnago <marcel.savegnago@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _


class PropertyLandContributionRule(models.Model):

    _name = 'property.land.contribution.rule'
    _description = 'Property Land Contribution Rule'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char()
    active = fields.Boolean(
        default=True
    )
    module_ids = fields.Many2many(
        "property.land.module",
        "property_land_module_rel",
        "contribution_rule_id",
        "module_id",
        "Modules",
    )
    type_ids = fields.Many2many(
        "property.land.type",
        "property_land_type_rel",
        "contribution_rule_id",
        "type_id",
        "Types",
    )
    stage_ids = fields.Many2many(
        "property.land.stage",
        "property_land_stage_rel",
        "contribution_rule_id",
        "stage_id",
        "Stages",
    )
    occupation_rate_ids = fields.One2many(
        comodel_name='property.land.contribution.rule.occupation.rate',
        inverse_name='contribution_rule_id',
        string='Occupation Rates',
    )
    coefficient = fields.Float()
    state = fields.Selection(
        string="State",
        selection=[
            ('draft', 'Draft'),
            ('approved', 'Approved'),
        ],
        readonly=True,
        copy=False,
        track_visibility='onchange',
        default='draft'
    )

    @api.multi
    def action_approve(self):
        return self.write({'state': 'approved'})

    @api.multi
    def action_draft(self):
        return self.write({'state': 'draft'})