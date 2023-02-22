# Copyright 2021 - TODAY, Marcel Savegnago <marcel.savegnago@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import re
from odoo import api, fields, models
from odoo.exceptions import UserError
import logging

logger = logging.getLogger(__name__)

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

            sql = """select v.property_tax_fixed_value, v.property_tax_monthly_index, property_tax_minimal_contribution from vw_property_settings_monthly_last v"""
            self.env.cr.execute(sql)
            property_settings_monthly_last = self.env.cr.fetchone()

            fixed_value = property_settings_monthly_last[0]
            monthly_index = property_settings_monthly_last[1]
            pavement_qty = land_id.pavement_qty_calc
            occupation_rate = land_id.occupation_rate / 100
            discount = land_id.discount
            minimal_contribution = property_settings_monthly_last[2]

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

        property_tax_date = self.get_next_date_insert()

        for land in self.web_progress_iter(land_ids, msg='Process Batch Tax'):
            self._process_tax_amount_and_lines(land, formula, property_tax_date)

    def get_next_date_insert(self):
        sql = """select to_timestamp(year_month_property_tax || '10 23', 'yyyymmdd h24') from vw_property_settings_monthly_last sml"""
        self.env.cr.execute(sql)
        lines = self.env.cr.fetchone()
        return lines[0]


    @api.multi
    def create_generic_process(self):
        #processar todas as águas
        waters = self.env['property.water.consumption'].search([
            ('date', '>', '2023-02-01'), ('state', '=', 'pending')]
        )

        length = len(waters)
        i = 0

        for water in waters:
            i += 1
            water.state = 'draft'
            water._compute_consumption()
            water._compute_total()
            water.state = 'pending'
            water.write({'total': water.total})
            logger.info(
                str(i) + '/' + str(length) + ' - Corrigido "' + water.land_id.name + '" para total: "' + str(
                    water.total) + '"')

        print('x')

    def _process_tax_amount_and_lines(self, land, formula, property_tax_date=None):
        if property_tax_date == None:
            property_tax_date = self.get_next_date_insert()

        amount, lines, formula = self._get_tax_amount_and_lines(land, formula)
        values = {
            'land_id': land.id,
            'amount_total': amount,
            'tax_line_ids': lines,
            'formula': formula,
            'date': property_tax_date
        }
        self.create(values)