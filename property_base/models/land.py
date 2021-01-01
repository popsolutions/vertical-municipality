from odoo import fields, models


class PropertyLand(models.Model):
    _name = 'property.land'
    _description = 'Property Land'

    lot_id = fields.Many2one('property.land.lot', 'Lot')
    type_id = fields.Many2one('PropertyLandType', 'Type')
    use_id = fields.Many2one('PropertyLandUse', 'Use')
    owner_id = fields.Many2one('res.partner', 'Owner')
    block_id = fields.Many2one('property.land.block', 'Block')
    zone_id = fields.Many2one('property.land.zone', 'Zone')
    address = fields.Text()
    number = fields.Integer()
    zip = fields.Integer()
    # ToDo: attached_land_ids = m2m self
    status = fields.Selection([
        ('empty', 'Empty'),
        ('construction', 'Under Construction'),
        ('occupied', 'Occupied')])

    # def name_get(self):
    #     pass
    # concat lot + block + zone

class PropertyLandType(models.Model):
    _name = 'property.land.type'
    _descriptio = 'Property Land Type'

    code = fields.Char()
    info = fields.Text()

class PropertyLandUse(models.Model):
    _name = 'property.land.use'
    _description = 'Property Usage'

    code = fields.Char()
    info = fields.Text()

class PropertyLandLot(models.Model):
    _name = 'property.land.lot'
    _description = 'Property Land Lot'

    code = fields.Char()
    info = fields.Text()


class PropertyLandBlock(models.Model):
    _name = 'property.land.block'
    _description = 'Property Land Block'

    code = fields.Char()
    info = fields.Text()


class PropertyLandZone(models.Model):
    _name = 'property.land.zone'
    _description = 'Property Land Zone'

    code = fields.Char()
    info = fields.Text()
