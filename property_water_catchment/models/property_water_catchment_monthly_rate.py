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

    _sql_constraints = [
        ('property_water_catchment_monthly_rate_year_month_uniq', 'unique (year_month)', 'Ano/Mês duplicado !')
    ]

    @api.multi
    def _compute_catchment_rate_current_month(self):
        current_year_month = datetime.now().strftime("%Y%m")

        #this sql calculate  set property_water_consumption.rate_catchment values
        sql = """
with t as ( 
select w.id,
       round((w.total * t.factor_rate_catchment_monthy)::numeric, 2) rate_catchment_calc
       --w.total, t.factor_rate_catchment_monthy, rate_catchment_monthy, water_consumption_sum
  from property_water_consumption w,
       (select t.rate_catchment_monthy / coalesce(nullif(t.water_consumption_sum, 0), 1) factor_rate_catchment_monthy, rate_catchment_monthy, water_consumption_sum
          from (select coalesce(
                       (select p.rate_catchment  
                         from property_water_catchment_monthly_rate p
                        where year_month = """ + current_year_month + """
                       ), 0) rate_catchment_monthy,
                       coalesce(
                       (
                       select sum(coalesce(w.total, 0))  
                         from property_water_consumption w
                        where TO_CHAR(w.date, 'yyyymm') = '""" + current_year_month + """'
                       ), 0) water_consumption_sum
               ) t       
       ) t
 where TO_CHAR(w.date, 'yyyymm') = '""" + current_year_month + """'
) update property_water_consumption pwc set rate_catchment = t.rate_catchment_calc from t where pwc.id = t.id  
"""
        self.env.cr.execute(sql)