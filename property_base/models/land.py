from odoo import api, fields, models


class PropertyLand(models.Model):
    _name = 'property.land'
    _description = 'Property Land'

    name = fields.Char(compute="_compute_name", store=True)
    type_id = fields.Many2one('property.land.type', 'Type')
    usage_id = fields.Many2one('property.land.usage', 'Usage')
    owner_id = fields.Many2one('res.partner', 'Owner')
    module_id = fields.Many2one('property.land.module', 'Module')
    block_id = fields.Many2one('property.land.block', 'Block')
    lot_id = fields.Many2one('property.land.lot', 'Lot')
    zone_id = fields.Many2one('property.land.zone', 'Zone', related='module_id.zone_id')
    pavement_qty = fields.Float()
    exclusive_area = fields.Float()
    address = fields.Text()
    number = fields.Integer()
    zip = fields.Integer()
    # ToDo: attached_land_ids = m2m self
    stage_id = fields.Many2one('property.land.stage', 'Stage')

    coefficient = fields.Float(compute='_compute_rate')
    occupation_rate = fields.Float(compute='_compute_rate')
    discount = fields.Float(related="stage_id.discount")

    # TODO: implementar se o registro é ativo ou inativo

    # TODO: Implementar o filtro da regra de contribuição
    def _compute_rate(self):
        for record in self:
            contribution_rule_id = self.env['property.land.contribution.rule'].search(
                [
                    ('state', '=', 'approved'),
                    ('module_ids', 'in', record.module_id.id),
                    ('type_ids', 'in', record.type_id.id),
                    ('stage_ids', 'in', record.stage_id.id),
                ],
                limit=1,
            )
            occupation_rate_id = self.env['property.land.contribution.rule.occupation.rate'].search(
                [
                    ('contribution_rule_id', '=', contribution_rule_id.id),
                    ('pavement_qty', '>=', record.pavement_qty )

                ],
                order='pavement_qty ASC',
                limit=1,
            )

            if contribution_rule_id.coefficient:
                record.coefficient = contribution_rule_id.coefficient

            if not occupation_rate_id.occupation_rate:
                record.occupation_rate = 100
            else:
                record.occupation_rate = occupation_rate_id.occupation_rate

    @api.depends('module_id', 'block_id', 'lot_id')
    def _compute_name(self):
        for rec in self:
            rec.name = "{}{}{}".format(rec.module_id.code or '-',
                                        rec.block_id.code or '-',
                                        rec.lot_id.code or '-')

    @api.onchange('module_id')
    def _onchange_module_id(self):
        self.block_id = self.lot_id = None

    @api.onchange('block_id')
    def _onchange_block_id(self):
        self.lot_id = None

class PropertyLandLot(models.Model):
    _name = 'property.land.lot'
    _description = 'Property Land Lot'

    code = fields.Char()
    block_id = fields.Many2one('property.land.block', 'Block')
    info = fields.Text()

    @api.multi
    def name_get(self):
        res = []
        for rec in self:
            custom_name = "{} (Block {})".format(rec.code, rec.block_id.code)
            res.append((rec.id, custom_name))
        return res

class PropertyLandBlock(models.Model):
    _name = 'property.land.block'
    _description = 'Property Land Block'

    code = fields.Char()
    module_id = fields.Many2one('property.land.module', 'Module')
    info = fields.Text()

    @api.multi
    def name_get(self):
        res = []
        for rec in self:
            custom_name = "{} (Module {})".format(rec.code, rec.module_id.code)
            res.append((rec.id, custom_name))
        return res

class PropertyLandModule(models.Model):
    _name = 'property.land.module'
    _description = 'Property Land Module'

    code = fields.Char()
    name = fields.Char()
    zone_id = fields.Many2one('property.land.zone', 'Zone')
    # coefficient = fields.Float()
    # pavement_qty = fields.Float()
    # occupation_rate = fields.Integer()
    info = fields.Text()

    # @api.multi
    # def name_get(self):
    #     res = []
    #     for rec in self:
    #         custom_name = "{} ({})".format(rec.code, rec.name)
    #         res.append((rec.id, custom_name))
    #     return res

class PropertyLandZone(models.Model):
    _name = 'property.land.zone'
    _description = 'Property Land Zone'

    code = fields.Char()
    name = fields.Char()
    info = fields.Text()

class PropertyLandType(models.Model):
    _name = 'property.land.type'
    _description = 'Property Land Type'

    code = fields.Char()
    name = fields.Char()
    info = fields.Text()

class PropertyLandUsage(models.Model):
    _name = 'property.land.usage'
    _description = 'Property Usage'

    code = fields.Char()
    name = fields.Char()
    info = fields.Text()

class PropertyLandStage(models.Model):
    _name = 'property.land.stage'
    _description = 'Property Land Stage'

    code = fields.Char()
    name = fields.Char()
    discount = fields.Float(string="Discount (%)")
    info = fields.Text()
