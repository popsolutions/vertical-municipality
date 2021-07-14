# Copyright 2021 - TODAY, Marcel Savegnago <marcel.savegnago@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _


class PropertyLand(models.Model):

    _inherit = 'property.land'

    state = fields.Selection(
        selection_add=[("block_tax", "Navigate")]
    )
    coefficient = fields.Float(
        compute='_compute_rate',
        track_visibility='onchange',
    )
    occupation_rate = fields.Float(
        compute='_compute_rate',
        track_visibility='onchange'
    )
    is_not_taxpayer = fields.Boolean(
        'Is Not Taxpayer',
        default=False,
        track_visibility='onchange'
    )
    alternative_contribution_tax_amount = fields.Float(
        track_visibility='onchange'
    )
    property_tax_ids = fields.One2many(
        'property.tax',
        'land_id',
        'Property Taxes',
        help="Property Taxes"
    )

    # TODO: Implementar o filtro da regra de contribuição
    def _compute_rate(self):
        for record in self:
            contribution_rule_id = self.env['property.land.contribution.rule'].search(
                [
                    ('active', '=', True),
                    ('state', '=', 'approved'),
                    ('module_ids', 'in', record.module_id.id),
                    ('type_ids', 'in', record.type_id.id),
                    ('stage_ids', 'in', record.stage_id.id),
                ],
                limit=1,
            )
            occupation_rate_id = self.env['property.land.contribution.rule.occupation.rate'].search(
                [
                    ('contribution_rule_id', '=', contribution_rule_id.id),
                    ('pavement_qty', '>=', record.pavement_qty)

                ],
                order='pavement_qty ASC',
                limit=1,
            )

            if contribution_rule_id.coefficient:
                record.coefficient = contribution_rule_id.coefficient

            if not occupation_rate_id.occupation_rate:
                record.occupation_rate = 100
            else:
                record.occupation_rate = occupation_rate_id.occupation_rate

    @api.multi
    def action_block(self):
        return self.write({'state': 'block'})