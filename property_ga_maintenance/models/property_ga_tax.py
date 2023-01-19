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

    def name_get_unifiedy(self):
        res = "{}/{}".format(self.date.strftime('%m-%Y'), self.land_id.land_id_invoice().name)
        return res

    def process_batch_property_ga_maintenance(self):
        # This query inserts in the current month the green area calculation (property_ga_tax) based on the values of the previous month
        insert_property_ga_tax_From_Old_Month = """
insert into property_ga_tax(id,land_id,"date",tax_index,last_tax,current_tax,create_uid,create_date,write_uid,write_date,state)        
select nextval('property_ga_tax_id_seq') id,
       pl.id land_id,
       psml.invoice_date_due "date",
       psml.inpc tax_index,
       coalesce(pgt_old.current_tax, pl.tax_ga_initial_value) last_tax,
       round( perc_sum(coalesce(pgt_old.current_tax, pl.tax_ga_initial_value)::numeric, psml.inpc::numeric)::numeric, 2) current_tax,
       1 create_uid,
       current_timestamp  create_date,
       1 write_uid,
       current_timestamp write_date,
       'draft' state
  from property_land pl 
         left join property_ga_tax pgt_old join (select yearmonth_proc_ref() ref_yearmonth) ymp1 on 0 = 0
                on pgt_old.land_id = pl.id 
               and anomes(pgt_old.date) = ymp1.ref_yearmonth /*Anomes Referencia*/,
       vw_property_settings_monthly_last psml
 where not pl.is_not_tax_ga
   and not exists (select id 
                     from property_ga_tax pgt_cur 
                    where pgt_cur.land_id = pl.id 
                      and anomes(pgt_cur.date) = psml.year_month  /*AnoMes Vencimento*/
                  ) 
        """
        self.env.cr.execute(insert_property_ga_tax_From_Old_Month)
