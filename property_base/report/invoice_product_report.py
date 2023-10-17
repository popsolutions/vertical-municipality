# -*- coding: utf-8 -*-

from odoo import tools
from odoo import models, fields, api


class InvoicesProductReport(models.Model):
    # _name = "invoice.product.report"
    _name = "invoice.product.report"
    _description = "Faturas Riviera"
    _auto = False
    # _rec_name = 'date'

    invoice_id = fields.Integer('Invoice #', readonly=True)
    land_id = fields.Many2one('property.land', string='Propriedade', readonly=True)
    land = fields.Char('Lote', readonly=True)
    res_id = fields.Many2one('res.partner', string='Proprietário', readonly=True)
    res_name = fields.Char('Nome Cliente', readonly=True)
    product_id = fields.Many2one('product.product', string='Produto', readonly=True)
    product_name = fields.Char('Nome Produto', readonly=True)
    module_code = fields.Char('Código do Módulo', readonly=True)
    block_code = fields.Char('Código do Bloco', readonly=True)
    lot_code = fields.Char('Código do Lote', readonly=True)
    referencia = fields.Char('Referência', readonly=True)
    total_agua = fields.Float('Água', readonly=True)
    total_contribuicaomensal = fields.Float('CTM', readonly=True)
    total_taxas = fields.Float('', readonly=True)
    jurosproporcional_valor = fields.Float('Juros', readonly=True)
    total_areaverde = fields.Float('Área Verde', readonly=True)
    juros_areaverde = fields.Float('Juros Área Verde', readonly=True)
    total_taxacaptacao = fields.Float('Taxa Captação', readonly=True)
    descontos = fields.Float('Descontos', readonly=True)
    price_total = fields.Float('Preço Total', readonly=True)
    occurrence_date = fields.Date('Data Ocorrência', readonly=True)
    tipocobranca = fields.Char('Tipo Cobrança', readonly=True)
    observacao = fields.Char('', readonly=True)
    real_payment_date = fields.Date('Data Real Pgto', readonly=True)
    due_date = fields.Date('Data Vencimento', readonly=True)
    anomes_vencimento = fields.Integer('Ano/Mês Venc Prod.', readonly=True)
    price_total_sum = fields.Float('Preço Total(Soma)', readonly=True)
    total_juros = fields.Float('Total Juros(Soma)', readonly=True)
    jurosproporcional_perc = fields.Float('Juros Proporc. %', readonly=True)
    price_total_juros = fields.Float('Preço Total Juros', readonly=True)


    # _order = 'due_date desc'

    _depends = {
        'account.invoice': [
            'account_id', 'amount_total_company_signed', 'commercial_partner_id', 'company_id',
            'currency_id', 'date_due', 'date_invoice', 'fiscal_position_id',
            'journal_id', 'number', 'partner_bank_id', 'partner_id', 'payment_term_id',
            'residual', 'state', 'type', 'user_id',
        ],
        'account.invoice.line': [
            'account_id', 'invoice_id', 'price_subtotal', 'product_id',
            'quantity', 'uom_id', 'account_analytic_id',
        ],
        'product.product': ['product_tmpl_id'],
        'product.template': ['categ_id'],
        'uom.uom': ['category_id', 'factor', 'name', 'uom_type'],
        'res.currency.rate': ['currency_id', 'name'],
        'res.partner': ['country_id'],
    }

    def _select(self):
        select_str = """
            SELECT  invoice_id as id
                   ,invoice_id
                   ,land_id
                   ,module_code
                   ,block_code
                   ,lot_code
                   ,referencia
                   ,total_agua
                   ,total_contribuicaomensal
                   ,total_taxas
                   ,jurosproporcional_valor
                   ,total_areaverde
                   ,juros_areaverde
                   ,total_taxacaptacao
                   ,descontos
                   ,price_total
                   ,occurrence_date
                   ,tipocobranca
                   ,observacao
                   ,real_payment_date
                   ,due_date
                   ,anomes_vencimento
                   ,res_id
                   ,res_name
                   ,land
                   ,product_id
                   ,product_name
                   ,price_total_sum
                   ,total_juros
                   ,jurosproporcional_perc
                   ,price_total_juros            
        """
        return select_str

    def _sub_select(self):
        select_str = """
        """
        return select_str

    def _from(self):
        from_str = """
                vw_report_contab_baixados ail
        """
        return from_str

    def _group_by(self):
        group_by_str = """
        """
        return group_by_str

    @api.model_cr
    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        sql = """CREATE or REPLACE VIEW %s as 
            %s
            FROM  %s 
            %s
            """ % (self._table, self._select(), self._from(), self._group_by())
        self.env.cr.execute(sql)