
from odoo import fields, models

class AccountInvoiceReport(models.Model):
#./odoo/addons/account/report/account_invoice_report.py
    _inherit = "account.invoice.report"

    land_id = fields.Many2one("property.land", string="Land")
    lote = fields.Char(string='Lote')
    module_id = fields.Integer(string='module_id')
    module_code = fields.Char(string='module_code')
    block_id = fields.Integer(string='block_id')
    block_code = fields.Char(string='block_code')
    lot_id = fields.Integer(string='lot_id')
    lot_code = fields.Char(string='lot_code')
    type_id = fields.Integer(string='type_id')
    type_code = fields.Char(string='type_code')
    type_name = fields.Char(string='type_name')
    usage_code = fields.Char(string='usage_code')
    usage_name = fields.Char(string='usage_name')
    stage_id = fields.Integer(string='stage_id')
    stage_code = fields.Char(string='stage_code')
    stage_name = fields.Char(string='stage_name')
    zone_id = fields.Integer(string='zone_id')
    zone_code = fields.Char(string='zone_code')
    zone_name = fields.Char(string='zone_name')

    occurrence_date = fields.Date(string='Ocurrence date')
    real_payment_date = fields.Date(string='Real Payment Date')


    state = fields.Selection([
        ('draft', 'Draft'),
        ('open', 'Open'),
        ('paid', 'Paid'),
        ('in_payment', 'In Paid'),
        ('cancel', 'Cancelled')
    ], string='Invoice Status', readonly=True)

    def _select(self):
        select_str = super()._select()
        select_str += """
            , sub.land_id
            , sub.lote
            , sub.module_id
            , sub.module_code
            , sub.block_id
            , sub.block_code
            , sub.lot_id
            , sub.lot_code
            , sub.type_id
            , sub.type_code
            , sub.type_name
            , sub.usage_code
            , sub.usage_name
            , sub.stage_id
            , sub.stage_code
            , sub.stage_name
            , sub.zone_id
            , sub.zone_code
            , sub.zone_name            
            , sub.occurrence_date
            , sub.real_payment_date
        """
        return select_str

    def _sub_select(self):
        select_str = super()._sub_select()

        select_str += """
            , ai.land_id
            , vpl.module_code__block_code__lot_code2 lote
            , vpl.module_id
            , vpl.module_code
            , vpl.block_id
            , vpl.block_code
            , vpl.lot_id
            , vpl.lot_code
            , vpl.type_id
            , vpl.type_code
            , vpl.type_name
            , vpl.usage_code
            , vpl.usage_name
            , vpl.stage_id
            , vpl.stage_code
            , vpl.stage_name
            , vpl.zone_id
            , vpl.zone_code
            , vpl.zone_name          
            , cre.occurrence_date
            , coalesce(cre.real_payment_date, ap.payment_date) real_payment_date
        """
        return select_str

    def _from(self):
        from_str = super()._from()
        from_str += """
            left join l10n_br_cnab_return_event cre on cre.invoice_id = ai.id AND cre.occurrences::text = '06-Liquidação Normal *'::text 
            left join vw_property_land vpl on vpl.id = ai.land_id
            left join account_invoice_payment_rel aipr on aipr.invoice_id = ai.id
            left join account_payment ap on ap.id = aipr.payment_id             
        """
        return from_str

    def _group_by(self):
        group_by_str = super()._group_by()
        group_by_str += """
            , ai.land_id
            , cre.occurrence_date
            , cre.real_payment_date
            , vpl.module_code__block_code__lot_code2
            , vpl.module_id
            , vpl.module_code
            , vpl.block_id
            , vpl.block_code
            , vpl.lot_id
            , vpl.lot_code
            , vpl.type_id
            , vpl.type_code
            , vpl.type_name
            , vpl.usage_code
            , vpl.usage_name
            , vpl.stage_id
            , vpl.stage_code
            , vpl.stage_name
            , vpl.zone_id
            , vpl.zone_code
            , vpl.zone_name
            , ap.payment_date
        """
        return group_by_str
