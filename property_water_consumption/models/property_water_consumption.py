from odoo import api, fields, models
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.exceptions import Warning as UserError

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
    issue_id = fields.Many2one('property.water.consumption.issue', default=1) #1-Leitura
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
                if rec.current_read >= rec.last_read:
                    rec.consumption = rec.current_read - rec.last_read
                else:
                    #O Hidrômetro zerou
                    hydrometer_maxvalue = 9999

                    if rec.last_read > hydrometer_maxvalue:
                        hydrometer_maxvalue = 99999

                    rec.consumption = (hydrometer_maxvalue - rec.last_read) + rec.current_read


    @api.depends('consumption', 'land_id')
    def _compute_total(self, economy_qty_child_and_owner=None):
        for rec in self:
            if rec.land_id and rec.state in ['draft', 'pending']:
                rec._compute_total_pwd(economy_qty_child_and_owner)

    def _compute_total_pwd(self, economy_qty_child_and_owner=None, consumption_child_and_owner=None):
        rec = self
        land_id = rec.land_id

        if (not land_id.water_consumption_economy_qty) or (land_id.water_consumption_economy_qty == 0):
            rec.total = 0
        else:
            if economy_qty_child_and_owner:
                water_consumption_economy_qty = economy_qty_child_and_owner
                consumption = consumption_child_and_owner
            else:
                water_consumption_economy_qty = land_id.water_consumption_economy_qty
                consumption = rec.consumption

            consumption = float(consumption / water_consumption_economy_qty)

            if consumption <= land_id.type_id.minimum_water_consumption:
                consumption = land_id.type_id.minimum_water_consumption

            rec.total = (
              land_id.type_id.water_computation_parameter_id.get_total(
                  consumption, land_id.display_name) * water_consumption_economy_qty
            )

            if not land_id.is_not_sewagepayer:
                rec.total += rec.total * 0.8  # 0.8 é o cálculo do Esgoto

            if economy_qty_child_and_owner:
                # Neste caso trata-se de cálculo de Propriedades unificadas.
                rec.total = round(rec.total / economy_qty_child_and_owner * land_id.water_consumption_economy_qty, 2)

    @api.multi
    def get_last_read(self, land_id):
        wc_id = self.search([('land_id', '=', land_id)], limit=1)
        return wc_id.current_read

    def process_batch_unifiedy_water_consumptions(self):
        #A variável abaixo sql_pwc_currentyearmonth_owners contém sql que vai retornar todas águas do mês atual que possuem filhos

        sql_pwc_currentyearmonth_owners = """
select pwc.id
  from vw_property_water_consumption_unified_group_cym pwcg
       join vw_property_water_consumption_unified_cym pwc on pwc.land_id = pwcg.unified_property_id_orid
 where pwcg.qtde > 1         
        """

        self.env.cr.execute(sql_pwc_currentyearmonth_owners)
        pwc_currentyearmonth_owners = self.env.cr.fetchall()

        for pwc_currentyearmonth_owner in self.web_progress_iter(pwc_currentyearmonth_owners):
            pwc = self.env['property.water.consumption'].search([('id', '=', pwc_currentyearmonth_owner)])
            pwc.unified_watter_consumption_process()
    def unified_watter_consumption_process(self):
        #todo.do validar anomes
        date_yearmonth = self.date.strftime("%Y%m")

        sql = "select v.year_month_property_water_consumption from vw_property_settings_monthly_last v"
        self.env.cr.execute(sql)
        res = self.env.cr.fetchone()

        if date_yearmonth != str(res[0]):
            raise UserError('Para ser processado o consumo de água precisa estar no Ano/Mês "' + str(res[0]) + '"')

        for pwc in self:
            sql = """
select l.unified_property_id,
       (select count(0) 
          from property_land pl
         where pl.unified_property_id = l.id
       ) qtde_filhos
  from (select pl1.id,
               pl1.unified_property_id
          from property_land pl1
         where id = """ + str(pwc.land_id.id) + """ 
       ) l        
        """
            self.env.cr.execute(sql)
            res = self.env.cr.fetchone()

            if res[0] != None:
                # unified_property_id preenchido indicando que este lote é "um filho"
                # Neste caso vou solicitar o processamento do Lote pai.

                sql = "select id from vw_property_water_consumption_unified_cym w where land_id = " + str(res[0])
                self.env.cr.execute(sql)
                pwc_owner_id = self.env.cr.fetchone()
                pwc = self.env['property.water.consumption'].search([('id', '=', pwc_owner_id[0])])
                pwc.unified_watter_consumption_process()
            elif res[1] > 0:
                # qtde_filhos preenchido indicando que este lote é "um pai".
                # Vou pegar os filhos (incluindo o pai e processar 1 a 1)
                sql = """
select w.id
  from vw_property_water_consumption_unified_cym w
 where unified_property_id_orid = """ + str(pwc.land_id.id)

                self.env.cr.execute(sql)
                pwcs_childs_and_owner = self.env.cr.fetchall()

                sql = """
select w.water_consumption_economy_qty economy_qty_child_and_owner,
       w.consumption consumption_child_and_owner
  from vw_property_water_consumption_unified_group_cym w
 where unified_property_id_orid = """ + str(pwc.land_id.id)

                self.env.cr.execute(sql)
                res = self.env.cr.fetchone()

                economy_qty_child_and_owner = res[0] #Somatória total da economia dos filhos e do pai
                consumption_child_and_owner = res[1]

                for pwc_childs_and_owner in pwcs_childs_and_owner:
                    pwc = self.env['property.water.consumption'].search([('id', '=', pwc_childs_and_owner[0])])

                    print('process:' + pwc.land_id.name)
                    pwc._compute_total_pwd(economy_qty_child_and_owner, consumption_child_and_owner)
            else:
                # O Lote nem é filho e nem pai, é uma situação normal, farei o processamento normal
                self._compute_total()

            print('x')

    @api.multi
    def create_batch_water_consumptions(self):
        # Menu "Imóveis/Ajudante/Criar Consumo de água em lote"
        #O Sql abaixo vai criar em property_water_consumption os registros existentes no mẽs anterior.
        insert_property_water_consumption = """
insert into property_water_consumption(id, land_id, last_read, current_read, consumption, total, state, hydrometer_number, "date", create_date, write_date, create_uid, write_uid, issue_id)        
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
       1 write_uid,
       1 issue_id
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
