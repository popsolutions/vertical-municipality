import logging
from odoo import models, fields

class ProductTemplate(models.Model):
    _inherit = "product.template"

    yearmonth_dec_from_invoice = fields.Integer('Ano/Mês Decremento Fatura.', defaul=0)

