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

    formula = fields.Char(
        compute='_compute_rate',
        track_visibility='onchange',
    )

    pavement_qty = fields.Float(
        'Pavement Qty',
        track_visibility='onchange',
        readonly=True
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

    @api.multi
    def write(self, vals):
        for item in self:
            if 'module_id' in vals:
                module_id = vals['module_id']
            else:
                module_id = item.module_id.id

            if 'type_id' in vals:
                type_id = vals['type_id']
            else:
                type_id = item.type_id.id

            if 'stage_id' in vals:
                stage_id = vals['stage_id']
            else:
                stage_id = item.stage_id.id

            contribution_rule_calcs = item.get_contribution_rule_calcs(module_id, type_id, stage_id)

            if 'pavement_qty' in contribution_rule_calcs:
                vals['pavement_qty'] = contribution_rule_calcs['pavement_qty']

            super(PropertyLand, item).write(vals)


    # TODO: Implementar o filtro da regra de contribuição
    def _compute_rate(self):
        for record in self:
            contribution_rule_calcs = self.get_contribution_rule_calcs(record.module_id.id, record.type_id.id, record.stage_id.id)

            if 'coefficient' in contribution_rule_calcs:
                record.coefficient = contribution_rule_calcs['coefficient']

            record.occupation_rate = contribution_rule_calcs['occupation_rate']

            record.formula = contribution_rule_calcs['formula']

    def get_contribution_rule_calcs(self, module_id, type_id, stage_id):
        contribution_rule_id = self.env['property.land.contribution.rule'].search(
            [
                ('active', '=', True),
                ('state', '=', 'approved'),
                ('module_ids', 'in', module_id),
                ('type_ids', 'in', type_id),
                ('stage_ids', 'in', stage_id),
            ],
            limit=1,
        )
        occupation_rate_id = self.env['property.land.contribution.rule.occupation.rate'].search(
            [
                ('contribution_rule_id', '=', contribution_rule_id.id)
            ],
            limit=1,
        )

        res = {}

        res.update({'formula': contribution_rule_id.formula})

        if contribution_rule_id.coefficient:
            res.update({'coefficient': contribution_rule_id.coefficient})

        if occupation_rate_id.pavement_qty:
            res.update({'pavement_qty': occupation_rate_id.pavement_qty})
        else:
            res.update({'pavement_qty': 0})

        if not occupation_rate_id.occupation_rate:
            res.update({'occupation_rate': 0})
        else:
            res.update({'occupation_rate': occupation_rate_id.occupation_rate})

        return res

    @api.multi
    def action_block(self):
        return self.write({'state': 'block_tax'})

    @api.multi
    def action_create_batch_taxes(self):
        formula = self.env['property.tax']._get_formula()
        for property_land in self:
            self.env['property.tax']._process_tax_amount_and_lines(property_land, formula)
