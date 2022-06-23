# Copyright 2021 - TODAY, Marcel Savegnago <marcel.savegnago@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import re
from odoo import api, fields, models
from odoo.exceptions import UserError


class PropertyTax(models.Model):

    _name = 'property.tax'
    _description = 'Property Tax'

    name = fields.Char(compute='_compute_name', store=True)
    date = fields.Datetime(default=fields.Datetime.now)
    land_id = fields.Many2one('property.land', 'Land') # Land represent the client account. o2m in land
    amount_total = fields.Float()
    tax_line_ids = fields.One2many('property.tax.line', 'tax_id', 'Tax Details')
    state = fields.Selection([('draft', 'Draft'),
                              ('pending', 'Pending'),
                              ('processed', 'Processed'),
                              ('cancel', 'Cancelled')
                              ], default='draft')
    invoice_id = fields.Many2one('account.invoice', 'Invoice', help="Invoice where this tax was processed")
    formula = fields.Text(help="Formula used to compute the tax. For reference only")

    @api.depends('date', 'land_id')
    def _compute_name(self):
        for rec in self:
            rec.name = "{}/{}".format(
                rec.date.strftime('%m-%Y'),
                rec.land_id.name)

    def name_get_unifiedy(self):
        res = "{}/{}".format(self.date.strftime('%m-%Y'), self.land_id.land_id_invoice().name)
        return res

    def _get_formula(self):
        return self.env['ir.config_parameter'].sudo().get_param('property_tax.formula')

    def _get_tax_amount_and_lines(self, land_id, formula):

        get_param = self.env['ir.config_parameter'].sudo().get_param
        lines = []

        if land_id.is_not_taxpayer:
            lines.append((0, 0, {'name': 'alternative_contribution_tax_amount',
                                 'value': str(land_id.alternative_contribution_tax_amount),
                                 }))
            return land_id.alternative_contribution_tax_amount, lines, 'alternative_contribution_tax_amount'
        else:
            if land_id.formula:
                formula = land_id.formula #substituí a fórmula global pela fórmula específica desta rule (Possibilidade de criar fórmula para rule #21)

            # building_type = self.env.ref('property_base.type_building')
            building_type = self.env['property.land.type'].search([('code', '=', 'P')])
            coefficient = land_id.coefficient
            if (formula.find('exclusive_area') != -1):
                exclusive_area = land_id.exclusive_area

            if (formula.find('building_area') != -1):
                building_area = land_id.building_area

            fixed_value = float(get_param('property_tax.fixed_value'))
            monthly_index = float(get_param('property_tax.monthly_index'))
            pavement_qty = land_id.pavement_qty_calc
            occupation_rate = land_id.occupation_rate / 100
            discount = land_id.discount
            minimal_contribution = float(get_param('property_tax.minimal_contribution'))

            if not (fixed_value and minimal_contribution):
                raise UserError('You must configure settings values for Property Taxes')

            # Keep record of all variables and their values used in the formula
            # Look in property.tax.line
            variables_used = re.findall(r"[\w']+", formula)
            for var in variables_used:
                if var not in ('100'):
                    lines.append((0, 0, {'name': var,
                                         'value': eval(var),
                                         }))
            return eval(formula), lines, formula

    @api.multi
    def create_batch_land_taxes(self):
        land_ids = self.env['property.land'].search([
            ('active','=', True), ('state', '=', 'done')]
        )
        formula = self._get_formula()
        for land in self.web_progress_iter(land_ids, msg='Process Batch Tax'):
            self._process_tax_amount_and_lines(land, formula)

    def _process_tax_amount_and_lines(self, land, formula):
        amount, lines, formula = self._get_tax_amount_and_lines(land, formula)
        values = {
            'land_id': land.id,
            'amount_total': amount,
            'tax_line_ids': lines,
            'formula': formula,
        }
        self.create(values)