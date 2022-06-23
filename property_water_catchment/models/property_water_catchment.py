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
        self.env.cr.execute("select to_char(t.maxdate, 'yyyy') old_year, to_char(t.maxdate, 'mm') old_month from (select max(date) maxdate from property_water_catchment pwc) t")
        res = self.env.cr.fetchall()
        current_year = int(res[0][0])
        current_month = int(res[0][1]) + 1

        if current_month > 12:
            current_year = current_year + 1
            current_month = 1

        current_year_month = str(current_year) + str(current_month).zfill(2)
        date = str(current_year) + '-' + str(current_month).zfill(2) + '-01'

        #this sql calculate  set property_water_consumption.rate_catchment values
        sql = """
insert into property_water_catchment (id, land_id,"date",rate_catchment,state,create_uid,create_date,write_uid,write_date)
select nextval('property_water_catchment_id_seq') id,
       w.land_id,
       '""" + date + """' "date",
       round((w.consumption * t.factor_rate_catchment_monthy)::numeric, 2) rate_catchment,
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
                         from property_water_catchment_monthly_rate p
                        where year_month = '""" + current_year_month + """'
                       ), 0) rate_catchment_monthy,
                       coalesce(
                       (
                       select sum(coalesce(w.consumption, 0))  
                         from property_water_consumption w
                        where TO_CHAR(w.date, 'yyyymm') = '""" + current_year_month + """'
                       ), 0) water_consumption_sum
               ) t       
       ) t
 where TO_CHAR(w.date, 'yyyymm') = '""" + current_year_month + """'
    and not exists
       (select pwc.id
          from property_water_catchment pwc
         where pwc.land_id = w.land_id
           and TO_CHAR(pwc.date, 'yyyymm') = '""" + current_year_month + """'
         limit 1 
       ) 
"""
        self.env.cr.execute(sql)
