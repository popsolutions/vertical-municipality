from odoo import fields, models


class PropertyTaxLand(models.Model):
    _name = 'property_tax.land'
    _description = 'Property Land'

    lot_id = fields.Many2one('property_tax.land.lot', 'Lot')
    owner_id = fields.Many2one('res.partner', 'Owner')
    block_id = fields.Many2one('property_tax.land.block', 'Block')
    zone_id = fields.Many2one('property_tax.land.zone', 'Zone')
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

class PropertyTaxLandType(models.Model):
    _name = 'property_tax.land.type'
    _descriptio = 'Property Land Type'

    code = fields.Chart()
    info = fields.Text()

class PropertyTaxLandUse(models.Model):
    _name = 'property_tax.land.use'
    _description = 'Property Usage'

    code = fields.Chart()
    info = fields.Text()

class PropertyTaxLandLot(models.Model):
    _name = 'property_tax.land.lot'
    _description = 'Property Land Lot'

    code = fields.Char()
    info = fields.Text()


class PropertyTaxLandBlock(models.Model):
    _name = 'property_tax.land.block'
    _description = 'Property Land Block'

    code = fields.Char()
    info = fields.Text()


class PropertyTaxLandZone(models.Model):
    _name = 'property_tax.land.zone'
    _description = 'Property Land Zone'

    code = fields.Char()
    info = fields.Text()
