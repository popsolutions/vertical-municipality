# Copyright 2022 popsolutions
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
from datetime import datetime
from dateutil.relativedelta import relativedelta

class PropertyGaTax(models.Model):

    _name = 'property.ga.tax'
    _description = 'Property Green Area Maintenance Tax'
    _order = 'date desc'

    name = fields.Char(compute='_compute_name', store=True)
    land_id = fields.Many2one('property.land')
    # property_land_address = fields.Text('property.land', related='land_id.address', readonly=True)
    # property_land_number = fields.Integer('property.land', related='land_id.number', readonly=True)
    date = fields.Date(default=fields.Date.context_today)
    tax_index = fields.Float('Tax index')
    last_tax = fields.Float('Last Tax')
    current_tax = fields.Float('Current Tax')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('pending', 'Pending'),
        ('processed', 'Processed')
        ], default='draft')

    @api.depends('date', 'land_id')
    def _compute_name(self):
        for rec in self:
            rec.name = "{}/{}".format(
                rec.date.strftime('%m-%Y'),
                rec.land_id.name)

    def process_batch_property_ga_maintenance(self):
        self.env.cr.execute("select to_char(t.maxdate, 'yyyy') old_year, to_char(t.maxdate, 'mm') old_month from (select max(date) maxdate from property_ga_tax) t")
        res = self.env.cr.fetchall()
        old_year = int(res[0][0])
        old_month = int(res[0][1])

        current_month = old_month + 1
        current_year = old_year

        if current_month > 12:
            current_year = current_year + 1
            current_month = 1

        old_year_month = str(old_year) + str(old_month).zfill(2)
        current_year_month = str(current_year) + str(current_month).zfill(2)

        date = str(current_year) + '-' + str(current_month).zfill(2) + '-01 23:00:00'

        # This query inserts in the current month the green area calculation (property_ga_tax) based on the values of the previous month
        insert_property_ga_tax_From_Old_Month = """
insert into property_ga_tax(id,land_id,"date",tax_index,last_tax,current_tax,create_uid,create_date,write_uid,write_date)
select nextval('property_ga_tax_id_seq') id,
       pl.id land_id,
       '""" + date + """' "date",
       rcs.property_ga_tax_index tax_index,
       coalesce(pgt_old.current_tax, pl.tax_ga_initial_value) last_tax,
       coalesce(pgt_old.current_tax, pl.tax_ga_initial_value) * rcs.property_ga_tax_index current_tax,
       1 create_uid,
       current_timestamp  create_date,
       1 write_uid,
       current_timestamp write_date
  from property_land pl 
         left join property_ga_tax pgt_old on pgt_old.land_id = pl.id and TO_CHAR(pgt_old.date, 'yyyymm') = '""" + old_year_month + """',         
       (select rcs.property_ga_tax_index  from res_config_settings rcs order by id desc limit 1) rcs
 where not pl.is_not_tax_ga
   and not exists (select id 
                     from property_ga_tax pgt_cur 
                    where pgt_cur.land_id = pl.id 
                      and TO_CHAR(pgt_cur.date, 'yyyymm') = '""" + current_year_month + """'
                  )   
        """
        self.env.cr.execute(insert_property_ga_tax_From_Old_Month)
