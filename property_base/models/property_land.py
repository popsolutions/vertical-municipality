# Copyright 2021 - TODAY, Marcel Savegnago <marcel.savegnago@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, tools


class PropertyLand(models.Model):
    _name = 'property.land'
    _description = 'Property Land'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    active = fields.Boolean(
        default=True
    )
    name = fields.Char(
        compute="_compute_name",
        store=True
    )
    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('done', 'In Progress')
        ],
        string='Status',
        readonly=True,
        copy=False,
        index=True,
        track_visibility='onchange',
        default='done'
    )
    type_id = fields.Many2one(
        'property.land.type',
        'Type',
        track_visibility='onchange',
        # required=True,
    )
    usage_id = fields.Many2one(
        'property.land.usage',
        'Usage',
        track_visibility='onchange',
        # required=True,
    )
    owner_id = fields.Many2one(
        'res.partner',
        'Owner',
        track_visibility='onchange'
    )
    owner_invoice_id = fields.Many2one(
        'res.partner',
        'Owner Invoice',
        track_visibility='onchange'
    )
    unified_property_id = fields.Many2one(
        'property.land',
        'Unified property',
        track_visibility='onchange'
    )
    module_id = fields.Many2one(
        'property.land.module',
        'Module',
        track_visibility='onchange',
        # required=True,
    )
    block_id = fields.Many2one(
        'property.land.block',
        'Block',
        track_visibility = 'onchange',
        required=True,
    )
    lot_id = fields.Many2one(
        'property.land.lot',
        'Lot',
        track_visibility='onchange',
        required=True,
    )
    zone_id = fields.Many2one(
        'property.land.zone',
        'Zone',
        related='module_id.zone_id',
        required=True,
    )
    stage_id = fields.Many2one(
        'property.land.stage',
        'Stage',
        track_visibility='onchange',
        # required=True,
    )
    pavement_qty = fields.Float(
        'Pavement Qty',
        track_visibility='onchange'
    )
    exclusive_area = fields.Float(
        'Exclusive Area',
        track_visibility='onchange'
    )
    building_area = fields.Float(
        'Building Area',
        track_visibility='onchange'
    )
    address = fields.Text(
        'Address',
        track_visibility='onchange'
    )
    number = fields.Integer(
        'Number',
        track_visibility='onchange'
    )
    zip = fields.Integer(
        'Zip',
        track_visibility='onchange'
    )
    discount = fields.Float(
        related='stage_id.discount',
        track_visibility='onchange'
    )
    is_not_waterpayer = fields.Boolean(
        'Is Not Water Payer',
        default=False,
        track_visibility='onchange'
    )
    alternative_contribution_water_amount = fields.Float(
        track_visibility='onchange'
    )

    # image: all image fields are base64 encoded and PIL-supported
    image = fields.Binary("Image", attachment=True,
        help="This field holds the image used for this property land, limited to 1024x1024px",)
    image_medium = fields.Binary("Medium-sized image", attachment=True,
        help="Medium-sized image of this property land. It is automatically "\
             "resized as a 128x128px image, with aspect ratio preserved. "\
             "Use this field in form views or some kanban views.")
    image_small = fields.Binary("Small-sized image", attachment=True,
        help="Small-sized image of this property land. It is automatically "\
             "resized as a 64x64px image, with aspect ratio preserved. "\
             "Use this field anywhere a small image is required.")

    @api.depends('module_id', 'block_id', 'lot_id')
    def _compute_name(self):
        for rec in self:
            rec.name = "{}{} {}".format(rec.module_id.code or '-',
                                       rec.block_id.code or '-',
                                       rec.lot_id.code or '-')

    @api.onchange('module_id')
    def _onchange_module_id(self):
        self.block_id = self.lot_id = None

    @api.onchange('block_id')
    def _onchange_block_id(self):
        self.lot_id = None

    @api.multi
    def action_done(self):
        return self.write({'state': 'done'})

    @api.multi
    def action_draft(self):
        return self.write({'state': 'draft'})

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('image'):
               tools.image_resize_images(vals, sizes={'image': (1024, None)})
        result = super(PropertyLand, self).create(vals_list)
        return result

    @api.multi
    def write(self, vals):
        tools.image_resize_images(vals, sizes={'image': (1024, None)})
        result = super(PropertyLand, self).write(vals)
        return result

    def getInvoiceOwner_id(self):
        return self.owner_invoice_id or self.owner_id

    def land_id_invoice(self):
        if self.unified_property_id:
            return self.unified_property_id
        else:
            return self

    @api.model
    def invoice_process(self):
        #esta rotina vai reprocessar as invoices de property_land
        def process(productIdName, modelName, modelLabel, price_unitFieldName, domain_id):
            if domain_id:
                self.env['account.invoice'].process_property_invoice(productIdName, modelName, modelLabel, price_unitFieldName, [('id', '=', domain_id)])

        for land in self:

            query = '''            
                select property_tax_id, property_ga_tax_id, property_water_consumption_id, property_water_catchment_id
                  from vw_property_land_lasts_ids
                 where land_id = ''' + str(land.id)

            self.env.cr.execute(query)
            last_ids = self.env.cr.fetchall()[0]

            product_property_tax_id = last_ids[0]

            if product_property_tax_id:
                #Se existe um product_property vou cancelar o que ja existe e gerar um novo
                product_property_tax = self.env['property.tax'].search([('id', '=', product_property_tax_id)])
                product_property_tax.write({'state': 'cancel'})

            #criar um novo product.property.tax
            self.action_create_batch_taxes()

            # Atualizar o id do novo product.property.tax
            self.env.cr.execute(query)
            last_ids = self.env.cr.fetchall()[0]

            product_property_tax_id = last_ids[0]

            process('property_tax.product_property_tax', 'property.tax', 'Property taxes', 'amount_total', product_property_tax_id)

            process('property_ga_maintenance.property_ga_maintenance', 'property.ga.tax', 'Green Area Tax', 'current_tax', last_ids[1])
            process('property_water_consumption.product_property_water_consumption',
                                          'property.water.consumption',
                                          'Water Consumption', 'total', last_ids[2])

            process('property_water_catchment.product_property_water_catchment',
                                          'property.water.catchment',
                                          ' Water Catchment', 'rate_catchment', last_ids[3])
