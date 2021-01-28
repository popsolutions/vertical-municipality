import re
from odoo import api, fields, models
from odoo.exceptions import UserError


class PropertyTaxLines(models.Model):
    _name = 'property.tax.line'

    tax_id = fields.Many2one('property.tax', 'Tax')
    name = fields.Char()
    value = fields.Float()

class PropertyTax(models.Model):
    _name = 'property.tax'

    name = fields.Char(compute='_compute_name', store=True)
    date = fields.Datetime(default=fields.Datetime.now)
    land_id = fields.Many2one('property.land', 'Land') # Land represent the client account. o2m in land
    amount_total = fields.Float()
    tax_line_ids = fields.One2many('property.tax.line', 'tax_id', 'Tax Details')
    state = fields.Selection([('draft', 'Draft'),
                              ('pending', 'Pending'),
                              ('processed', 'Processed')], default='draft')
    invoice_id = fields.Many2one('account.invoice', 'Invoice', help="Invoice where this tax was processed")
    formula = fields.Text(help="Formula used to compute the tax. For reference only")

    @api.depends('date', 'land_id')
    def _compute_name(self):
        for rec in self:
            rec.name = "{}/{}".format(
                rec.date.strftime('%m-%Y'),
                rec.land_id.name)

    def _get_formula(self):
        return self.env['ir.config_parameter'].sudo().get_param('property_tax.formula')

    def _get_tax_amount_and_lines(self, land_id, formula):

        get_param = self.env['ir.config_parameter'].sudo().get_param

        area_exclusiva_do_lote = 1.1
        coeficiente_da_zona_de_localizacao = 2.2
        fixed_value = float(get_param('property_tax.fixed_value'))
        indexador_do_mes = 4.4
        no_de_pavimentos = 5.5
        taxa_de_ocupacao = 6.6
        minimal_contribution = float(get_param('property_tax.minimal_contribution'))

        if not (fixed_value and minimal_contribution):
            raise UserError('You must configure settings values for Property Taxes')

        # Keep record of all variables and their values used in the formula
        # Look in property.tax.line
        variables_used = re.findall(r"[\w']+", formula)
        lines = []
        for var in variables_used:
            lines.append((0, 0, {'name': var,
                                 'value': eval(var),
                                 }))
        return eval(formula), lines


    @api.multi
    def create_batch_land_taxes(self):
        land_ids = self.env['property.land'].search([], limit=10) # ToDo: Remove the limit
        formula = self._get_formula()
        for land in land_ids:
            amount, lines = self._get_tax_amount_and_lines(land, formula)
            values = {
                'land_id': land.id,
                'amount_total': amount,
                'tax_line_ids': lines,
                'formula': formula,
            }
            self.create(values)