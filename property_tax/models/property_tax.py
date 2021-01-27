import re
from odoo import api, fields, models


class PropertyTaxLines(models.Model):
    _name = 'property.tax.line'

    tax_id = fields.Many2one('property.tax', 'Tax')
    name = fields.Char()
    value = fields.Float()

class PropertyTax(models.Model):
    _name = 'property.tax'

    date = fields.Datetime()
    land_id = fields.Many2one('property.land', 'Land') # Land represent the client account. o2m in land
    amount_total = fields.Float()
    tax_line_ids = fields.One2many('property.tax.line', 'tax_id', 'Tax Details')
    state = fields.Selection([('draft', 'Draft'),
                              ('pending', 'Pending'),
                              ('processed', 'Processed')], default='draft')
    invoice_id = fields.Many2one('account.invoice', 'Invoice', help="Invoice where this tax was processed")
    formula = fields.Text(help="Formula used to compute the tax. For reference only")

    """
    ÁREA EXCLUSIVA DO LOTE x COEFICIENTE  DA ZONA DE LOCALIZAÇÃO x VALOR FIXO 
        x INDEXADOR DO MÊS x No. DE  PAVIMENTOS x TAXA DE OCUPAÇÃO = VALOR
        +  CONTRIBUIÇÃO MÍNIMA.
    """

    def _get_formula(self):
        # get it from ir.parameters
        # return "(area_exclusiva_do_lote * coeficiente_da_zona_de_localizacao " \
        #        "* valor_fixo * indexador_do_mes * no_de_pavimentos " \
        #        "* taxa_de_ocupacao) + contribuicao_minima"

        return "(area_exclusiva_do_lote * coeficiente_da_zona_de_localizacao " \
               "* taxa_de_ocupacao) + contribuicao_minima"

    def _get_tax_amount_and_lines(self, land_id, formula):
        """
        ÁREA EXCLUSIVA DO LOTE x COEFICIENTE  DA ZONA DE LOCALIZAÇÃO x VALOR FIXO
            x INDEXADOR DO MÊS x No. DE  PAVIMENTOS x TAXA DE OCUPAÇÃO = VALOR
            +  CONTRIBUIÇÃO MÍNIMA.
        """

        area_exclusiva_do_lote = 1.1
        coeficiente_da_zona_de_localizacao = 2.2
        valor_fixo = 3.3
        indexador_do_mes = 4.4
        no_de_pavimentos = 5.5
        taxa_de_ocupacao = 6.6
        contribuicao_minima = 7.7

        variables_used = re.findall(r"[\w']+", formula)
        lines = []
        for var in variables_used:
            lines.append((0, 0, {'name': var,
                                 'value': eval(var),
                                 }))
        return eval(formula), lines



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