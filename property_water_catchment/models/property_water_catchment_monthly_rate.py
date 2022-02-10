from odoo import api, fields, models
from datetime import datetime

class PropertyWaterConsumption(models.Model):

    _name = 'property.water.catchment.monthly.rate'
    _description = 'Property Water Monthly Rate'

    date = fields.Date(default=fields.Date.context_today)
    year_month = fields.Integer('Ano/Mês')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('pending', 'Pending'),
        ('processed', 'Processed')
        ], default='draft')
    rate_catchment = fields.Float('Rate Catchment')

