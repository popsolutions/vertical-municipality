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
    zone_id = fields.Many2one('property.land.zone', 'Zone')
    address = fields.Text()
    number = fields.Integer()
    zip = fields.Integer()
    # ToDo: attached_land_ids = m2m self
    stage_id = fields.Many2one('property.land.stage', 'Stage')

    @api.depends('module_id', 'block_id', 'lot_id')
    def _compute_name(self):
        for rec in self:
            rec.name = "{}{}{}".format(rec.module_id.code,
                                        rec.block_id.code,
                                        rec.lot_id.code)


class PropertyLandType(models.Model):
    _name = 'property.land.type'
    _description = 'Property Land Type'

    code = fields.Char()
    name = fields.Char()
    info = fields.Text()

    @api.multi
    def name_get(self):
        res = []
        for rec in self:
            custom_name = "{} - {}".format(rec.code, rec.name)
            res.append((rec.id, custom_name))
        return res

class PropertyLandUsage(models.Model):
    _name = 'property.land.usage'
    _description = 'Property Usage'

    code = fields.Char()
    name = fields.Char()
    info = fields.Text()

class PropertyLandLot(models.Model):
    _name = 'property.land.lot'
    _description = 'Property Land Lot'
    _rec_name = 'code'

    code = fields.Char()
    block_id = fields.Many2one('property.land.block', 'Block')
    info = fields.Text()

class PropertyLandBlock(models.Model):
    _name = 'property.land.block'
    _description = 'Property Land Block'
    _rec_name = 'code'

    code = fields.Char()
    module_id = fields.Many2one('property.land.module', 'Module')
    info = fields.Text()

class PropertyLandModule(models.Model):
    _name = 'property.land.module'
    _description = 'Property Land Module'

    code = fields.Char()
    name = fields.Char()
    zone_id = fields.Many2one('property.land.zone', 'Zone')
    info = fields.Text()

    @api.multi
    def name_get(self):
        res = []
        for rec in self:
            custom_name = "{} - {}".format(rec.code, rec.name)
            res.append((rec.id, custom_name))
        return res

class PropertyLandZone(models.Model):
    _name = 'property.land.zone'
    _description = 'Property Land Zone'

    code = fields.Char()
    name = fields.Char()
    info = fields.Text()

    @api.multi
    def name_get(self):
        res = []
        for rec in self:
            custom_name = "{} - {}".format(rec.code, rec.name)
            res.append((rec.id, custom_name))
        return res

class PropertyLandStage(models.Model):
    _name = 'property.land.stage'
    _description = 'Property Land Stage'

    code = fields.Char()
    name = fields.Char()
    info = fields.Text()
