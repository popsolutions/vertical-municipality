from odoo import api, fields, models
from datetime import datetime

class PropertyWaterConsumption(models.Model):

    _name = 'property.water.catchment.monthly.rate'
    _description = 'Property Water Monthly Rate'

    date = fields.Date(default=fields.Date.context_today)
    year_month = fields.Integer('Ano/Mês')

    # date = datetime.strptime(date_field, DEFAULT_SERVER_DATE_FORMAT)
    # month = date.month
    # year = date.year

    state = fields.Selection([
        ('draft', 'Draft'),
        ('pending', 'Pending'),
        ('processed', 'Processed')
        ], default='draft')
    rate_catchment = fields.Float('Rate Catchment')

    #ra - Analytic Result Fields - Campos exibidos no quadro de Resultado analítico da fatura do cliente
    ar_period = fields.Char('Period')
    ar_ph = fields.Char('PH')
    ar_ph_limit = fields.Char('PH Limit')
    ar_uh_color = fields.Char('Color U.H.')
    ar_uh_color_limit = fields.Char('Color U.H. Limit')
    ar_ut_turbidity = fields.Char('Turbity')
    ar_ut_turbidity_limit = fields.Char('Turbity Limit')
    ar_chlorine_residual = fields.Char('Chlorine Residual')
    ar_chlorine_residual_limit = fields.Char('Chlorine Residual Limit')
    ar_fluorides = fields.Char('Fluorides')
    ar_fluorides_limit = fields.Char('Fluorides Limit')
    ar_ecoli = fields.Char('E Coli')
    ar_ecoli_limit = fields.Char('E Coli Limit')

    index_coin = fields.Float('Index Coin', digits=(12, 5))
    nextread_date = fields.Date('Next Read Date')

    property_tax_fixed_value = fields.Float('Fixed Value', digits=(12,4))
    property_tax_minimal_contribution = fields.Float('Minimal Contribution')
    property_tax_monthly_index = fields.Float('Monthly Index', digits=(12,5))
    inpc = fields.Float('INPC', digits=(12, 4))
