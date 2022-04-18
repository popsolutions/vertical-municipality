from odoo import api, fields, models
from datetime import datetime
from dateutil.relativedelta import relativedelta

class PropertyWaterConsumption(models.Model):

    _name = 'property.water.consumption'
    _order = 'date desc'
    _description = 'Property Water Consumption'

    land_id = fields.Many2one('property.land')
    property_land_address = fields.Text('property.land', related='land_id.address', readonly=True)
    property_land_number = fields.Integer('property.land', related='land_id.number', readonly=True)
    date = fields.Date(default=fields.Date.context_today)
    last_read = fields.Integer()
    current_read = fields.Integer()
    consumption = fields.Integer(compute='_compute_consumption', store=True)
    issue_id = fields.Many2one('property.water.consumption.issue')
    reader_id = fields.Many2one('res.partner')
    total = fields.Float(compute='_compute_total', store=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('pending', 'Pending'),
        ('processed', 'Processed')
        ], default='draft')
    photo = fields.Binary('Photo')

    @api.multi
    def name_get(self):
        res = []
        for rec in self:
            custom_name = "{} ({})".format(rec.land_id.name, rec.date)
            res.append((rec.id, custom_name))
        return res

    @api.depends('last_read', 'current_read')
    def _compute_consumption(self):
        for rec in self:
            if not rec.current_read:
                rec.consumption = 0
            else:
                rec.consumption = rec.current_read - rec.last_read

    @api.depends('consumption', 'land_id')
    def _compute_total(self):
        for rec in self:
            if rec.consumption and rec.land_id and rec.state in ['draft']:
                consumption = rec.consumption
                water_consumption_economy_qty = rec.land_id.water_consumption_economy_qty or 1
                if consumption <= rec.land_id.type_id.minimum_water_consumption:
                    consumption = rec.land_id.type_id.minimum_water_consumption
                    water_consumption_economy_qty = 1
                else:
                    consumption = float(consumption / water_consumption_economy_qty)
                rec.total = (
                        rec.land_id.type_id.water_computation_parameter_id.get_total(
                            consumption)*water_consumption_economy_qty
                )
                rec.total += rec.total*0.8

    @api.multi
    def get_last_read(self, land_id):
        wc_id = self.search([('land_id', '=', land_id)], limit=1)
        return wc_id.current_read

    @api.multi
    def create_batch_water_consumptions(self):
        current_year_month = datetime.today().strftime("%Y%m")
        old_year_month = (datetime.today() - relativedelta(months=1)).strftime("%Y%m")

        #O Sql abaixo vai criar em property_water_consumption os registros existentes no mẽs anterior.
        insert_property_water_consumption = """
insert into property_water_consumption(id, land_id, last_read, current_read, consumption, total, state, "date", create_date, write_date, create_uid, write_uid)
select nextval('property_water_consumption_id_seq') id,
       pwc_old.land_id land_id,
       pwc_old.current_read last_read,
       null current_read,
       null consumption,
       null total,
       'draft' state,
       current_date "date",
       current_timestamp create_date,
       current_timestamp write_date,
       1 create_uid,
       1 write_uid
  from property_water_consumption pwc_old
         left join property_water_consumption pwc_current 
                on (     pwc_current.land_id = pwc_old.land_id 
                    and  TO_CHAR(pwc_current."date", 'yyyymm') = '""" + current_year_month + """'
                   ),
       property_land pl
 where TO_CHAR(pwc_old."date", 'yyyymm') = '""" + old_year_month + """'
   and pwc_current.id is null
   and pl.id = pwc_old.land_id 
   and pl.state = 'done'
        """

        self.env.cr.execute(insert_property_water_consumption)
