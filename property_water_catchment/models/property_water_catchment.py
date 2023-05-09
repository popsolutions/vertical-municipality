# Copyright 2022 popsolutions
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
from datetime import datetime
from dateutil.relativedelta import relativedelta

class PropertyGaTax(models.Model):

    _name = 'property.water.catchment'
    _description = 'Property Water Catchment'
    _order = 'date desc'

    name = fields.Char(compute='_compute_name', store=True)
    land_id = fields.Many2one('property.land')
    date = fields.Date(default=fields.Date.context_today)
    rate_catchment = fields.Float('Rate Catchment')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('pending', 'Pending'),
        ('processed', 'Processed')
        ], default='draft')

    @api.multi
    def name_get(self):
        res = []
        for rec in self:
            custom_name = "{} ({})".format(rec.land_id.name, rec.date)
            print(custom_name)
            res.append((rec.id, custom_name))
        return res

    def name_get_unifiedy(self):
        res = "{}/{}".format(self.date.strftime('%m-%Y'), self.land_id.land_id_invoice().name)
        return res

    @api.depends('date', 'land_id')
    def _compute_name(self):
        for rec in self:
            rec.name = "{}/{}".format(
                rec.date.strftime('%m-%Y'),
                rec.land_id.name)
    @api.multi
    def _compute_catchment_rate_current_month(self):
        #this sql calculate  set property_water_consumption.rate_catchment values
        sql = """
insert into property_water_catchment (id, land_id,"date",rate_catchment,state,create_uid,create_date,write_uid,write_date)
select nextval('property_water_catchment_id_seq') id,
       w.land_id,
       to_date(psml.year_month_property_water_catchment || '01', 'YYYYMMDD') "date",
       round((coalesce(w.consumption, 0) * t.factor_rate_catchment_monthy)::numeric, 2) rate_catchment,
       'draft' state,
       1 create_uid,
       current_timestamp  create_date,
       1 write_uid,
       current_timestamp write_date
       --w.total, t.factor_rate_catchment_monthy, rate_catchment_monthy, water_consumption_sum
  from property_water_consumption w,
       (select t.rate_catchment_monthy / coalesce(nullif(t.water_consumption_sum, 0), 1) factor_rate_catchment_monthy, rate_catchment_monthy, water_consumption_sum
          from (select coalesce(
                       (select p.rate_catchment  
                         from vw_property_settings_monthly_last p
                       ), 0) rate_catchment_monthy,
                       coalesce(
                       (
                       select sum(coalesce(w.consumption, 0))  
                         from property_water_consumption w
                         join property_land pl on pl.id = w.land_id
                        where anomes(w.date) = (select v.year_month_property_water_consumption from vw_property_settings_monthly_last v)
                          and not pl.is_not_waterpayer
                       ), 0) water_consumption_sum
               ) t       
       ) t,
       vw_property_settings_monthly_last psml
 where anomes(w.date) = psml.year_month_property_water_consumption
    and not vpl.is_not_waterpayer
    and not exists
       (select pwc.id
          from property_water_catchment pwc
         where pwc.land_id = w.land_id
           and anomes(pwc.date) = psml.year_month_property_water_catchment
         limit 1 
       )
"""
        self.env.cr.execute(sql)
