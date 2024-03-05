from odoo import api, fields, models

class PropertyWaterConsumptionRouteLands(models.Model):

    _name = 'property.water.consumption.route.lands'
    _description = 'Rotas personalizadas'

    routecustom_id = fields.Many2one('property.water.consumption.route.custom', string='Rota', required=True)
    land_id = fields.Many2one('property.land', string='Propriedade', required=True)

    land_id_address = fields.Text(related = 'land_id.address', string='Endereço', readonly=True)
    land_id_property_name = fields.Char(related = 'land_id.owner_id.name', string='Proprietário', readonly=True)
    land_id_module_id_code = fields.Char(related = 'land_id.module_id.code', string='Módulo', readonly=True, store = True)
    land_id_block_id_code = fields.Char(related = 'land_id.block_id.code', string='Bloco', readonly=True, store = True)
    land_id_lot_id_code = fields.Char(related = 'land_id.lot_id.code', string='Lote', readonly=True, store = True)
    land_id_type_id_name = fields.Char(related = 'land_id.type_id.name', string='Tipo', readonly=True)
    land_id_usage_id_name = fields.Char(related = 'land_id.usage_id.name', string='Uso', readonly=True)
    land_id_stage_id_name = fields.Char(related = 'land_id.stage_id.name', string='Estágio', readonly=True)

    # property_land_address = fields.Text('property.land', related='land_id.address', readonly=True)

    sequence = fields.Integer()

    _sql_constraints = [
        ('pwcrl_unique1', 'unique(routecustom_id, land_id)', 'Endreço já existe para esta rota'),
    ]
