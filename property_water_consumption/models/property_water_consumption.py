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
    hydrometer_number = fields.Char(
        'hydrometer Number'
    )

    @api.model
    def create(self, vals):
        if 'hydrometer_number' in vals:
            if not vals['hydrometer_number']:
                land_id = self.env['property.land'].search([('id', '=', vals['land_id'])])
                if land_id:
                    vals.update({'hydrometer_number': land_id.hydrometer_number})

        res = super(PropertyWaterConsumption, self).create(vals)

        return res


    @api.multi
    def name_get(self):
        res = []
        for rec in self:
            custom_name = "{} ({})".format(rec.land_id.name, rec.date)
            res.append((rec.id, custom_name))
        return res

    def name_get_unifiedy(self):
        res = "{}/{}".format(self.date.strftime('%m-%Y'), self.land_id.land_id_invoice().name)
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
            if rec.land_id and rec.state in ['draft']:
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
                rec.total += rec.total*0.8 # 0.8 é o cálculo do Esgoto

    @api.multi
    def get_last_read(self, land_id):
        wc_id = self.search([('land_id', '=', land_id)], limit=1)
        return wc_id.current_read

    @api.multi
    def create_batch_water_consumptions(self):
        # Menu "Imóveis/Ajudante/Criar Consumo de água em lote"
        #O Sql abaixo vai criar em property_water_consumption os registros existentes no mẽs anterior.
        insert_property_water_consumption = """
insert into property_water_consumption(id, land_id, last_read, current_read, consumption, total, state, hydrometer_number, "date", create_date, write_date, create_uid, write_uid)        
select nextval('property_water_consumption_id_seq') id,
       t.land_id land_id,
       t.last_read,
       null::int current_read,
       null::int consumption,
       null::double precision total,
       'draft' state,
       t.hydrometer_number,
       current_date "date",
       current_timestamp create_date,
       current_timestamp write_date,
       1 create_uid,
       1 write_uid
  from (select pwc_old.land_id land_id,
               pwc_old.current_read last_read,
               pl.hydrometer_number
          from property_water_consumption pwc_old
                 join vw_property_settings_monthly_last sml on (0 = 0)
                 left join property_water_consumption pwc_current 
                        on (     pwc_current.land_id = pwc_old.land_id 
                            and  anomes(pwc_current."date") = sml.year_month_property_water_consumption
                           ),
               property_land pl
         where anomes(pwc_old."date") = anomes_inc(sml.year_month_property_water_consumption, -1)
           and pwc_current.id is null
           and pl.id = pwc_old.land_id 
           and pl.state = 'done'
         union all   
        --Propriedades que não existem property_water_consumption porém estão marcadas como "not is_not_waterpayer"    
        --São as propriedades que foram ativadas o consumo de água recentemente e ainda não houve nenhuma movimentação (Não existem nenhum registro property_water_consumption no período anterior)
        select pl.id land_id,
               0 last_read,
               pl.hydrometer_number
          from property_land pl,
               vw_property_settings_monthly_last sml
         where not pl.is_not_waterpayer
           and not exists --Não existe registro em property_water_consumption no período anterior
               (select 1
                  from property_water_consumption pwc
                 where pwc.land_id = pl.id  
                   and anomes(pwc."date") = anomes_inc(sml.year_month_property_water_consumption, -1)
                 limit 1
               )
           and not exists --Não existe registro em property_water_consumption no período atual
               (select 1
                  from property_water_consumption pwc
                 where pwc.land_id = pl.id  
                   and anomes(pwc."date") = sml.year_month_property_water_consumption --período atual
                 limit 1
               )               
       ) t"""

        self.env.cr.execute(insert_property_water_consumption)
