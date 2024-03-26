from datetime import datetime

from odoo.exceptions import UserError

from odoo import models, fields, api
import json

class AppointmentReportWizard(models.TransientModel):
    _name = "property_base.paidinvoicereport.wizard"
    _description = "Print Paid invoices"

    datapagamento_real_inicio = fields.Date(string='Início', required=False)
    datapagamento_real_fim = fields.Date(string='Fim', required=False)
    datapagamento_ocorrencia_inicio = fields.Date(string='Início', required=False)
    datapagamento_ocorrencia_fim = fields.Date(string='Fim', required=False)
    datapagamento_vencimento_inicio = fields.Date(string='Início', required=False)
    datapagamento_vencimento_fim = fields.Date(string='Fim', required=False)
    anomesreferenciavenc_inicio = fields.Char(string='Início', required=False)
    anomesreferenciavenc_fim = fields.Char(string='Fim', required=False)
    fatura_id = fields.Integer(string='Fatura_id', required=False)

    tipocobranca_dinheiro = fields.Boolean(string='Dinheiro', default=True)
    tipocobranca_boleto = fields.Boolean(string='Boleto', default=True)
    tipocobranca_debitoautomatico = fields.Boolean(string='Débito Automático', default=True)
    tipocobranca_acumulado = fields.Boolean(string='Acumulados', default=False)

    tipoagrupamento = fields.Selection([
        ('proprietario', 'Proprietário'),
        ('modulo_bloco', 'Módulo/Bloco'),
    ], default = 'modulo_bloco', string = 'Tipo Agrupamento')

    def button_action_menu_rel_cont_invoices_paid(self):
        domain = []
        tipoagrupamento_proprietario = self.tipoagrupamento == 'proprietario'
        tipoagrupamento_modulobloco = not tipoagrupamento_proprietario
        sql = ''

        if tipoagrupamento_proprietario:
            sql = """
select row_to_json(t)::varchar invoices_sum
  from ( 
        select coalesce(sum(t.total_proprietario), 0) total_proprietario_sum,
               coalesce(sum(t.total_agua), 0) total_agua_sum,
               coalesce(sum(t.total_contribuicaomensal), 0) total_contribuicaomensal_sum,
               coalesce(sum(t.total_taxas), 0) total_taxas_sum,
               coalesce(sum(t.jurosproporcional_valor), 0) jurosproporcional_valor_sum,
               coalesce(sum(t.total_areaverde), 0) total_areaverde_sum,
               coalesce(sum(t.juros_areaverde), 0) juros_areaverde_sum,
               coalesce(sum(t.total_taxacaptacao), 0) total_taxacaptacao_sum,
               coalesce(sum(t.descontos), 0) descontos_sum,
               coalesce(sum(t.price_total), 0) price_total_sum,
               coalesce(sum(t.price_total_juros), 0) price_total_juros_sum,
               json_agg(t) invoices
         from (
               select v.res_id,
                      v.res_name,
                      count(0) qtde,
                      sum(v.price_total_juros) total_proprietario,
                      sum(v.total_agua) total_agua,
                      sum(v.total_contribuicaomensal) total_contribuicaomensal,
                      sum(v.total_taxas) total_taxas,
                      sum(v.jurosproporcional_valor) jurosproporcional_valor,
                      sum(v.total_areaverde) total_areaverde,
                      sum(v.juros_areaverde) juros_areaverde,
                      sum(v.total_taxacaptacao) total_taxacaptacao,
                      sum(v.descontos) descontos,
                      sum(v.price_total) price_total,
                      sum(v.price_total_juros) price_total_juros,
                      json_agg((
                      select t from (select
                      v.invoice_id,
                      v.land_id,
                      v.module_code,
                      v.block_code,
                      v.lot_code,
                      v.referencia,
                      v.total_agua,
                      v.total_contribuicaomensal,
                      v.total_taxas,
                      v.jurosproporcional_valor,
                      v.total_areaverde,
                      v.juros_areaverde,
                      v.total_taxacaptacao,
                      v.descontos,
                      v.price_total,
                      v.occurrence_date,
                      v.tipocobranca,
                      v.observacao,
                      v.real_payment_date,
                      v.due_date,
                      v.res_name,
                      v.product_id,
                      v.land,
                      v.product_name,
                      v.price_total,
                      v.price_total_juros) t order by v.real_payment_date, v.land)) res_lines
                 from vw_report_contab_baixados v
                where true"""

        if tipoagrupamento_modulobloco:
            sql = """
select row_to_json(t)::varchar invoices_sum
  from ( 
        select coalesce(sum(modulesum.total_proprietario_modulesum), 0) total_proprietario_sum,
               coalesce(sum(modulesum.total_agua_modulesum), 0) total_agua_sum,
               coalesce(sum(modulesum.total_contribuicaomensal_modulesum), 0) total_contribuicaomensal_sum,
               coalesce(sum(modulesum.total_taxas_modulesum), 0) total_taxas_sum,
               coalesce(sum(modulesum.jurosproporcional_valor_modulesum), 0) jurosproporcional_valor_sum,
               coalesce(sum(modulesum.total_areaverde_modulesum), 0) total_areaverde_sum,
               coalesce(sum(modulesum.juros_areaverde_modulesum), 0) juros_areaverde_sum,
               coalesce(sum(modulesum.total_taxacaptacao_modulesum), 0) total_taxacaptacao_sum,
               coalesce(sum(modulesum.descontos_modulesum), 0) descontos_sum,
               coalesce(sum(modulesum.price_total_modulesum), 0) price_total_sum,
               coalesce(sum(modulesum.price_total_juros_modulesum), 0) price_total_juros_sum,
               json_agg(modulesum) modules
         from (select module_code,
                      coalesce(sum(blocksum.total_proprietario_blocksum), 0) total_proprietario_modulesum,
                      coalesce(sum(blocksum.total_agua_blocksum), 0) total_agua_modulesum,
                      coalesce(sum(blocksum.total_contribuicaomensal_blocksum), 0) total_contribuicaomensal_modulesum,
                      coalesce(sum(blocksum.total_taxas_blocksum), 0) total_taxas_modulesum,
                      coalesce(sum(blocksum.jurosproporcional_valor_blocksum), 0) jurosproporcional_valor_modulesum,
                      coalesce(sum(blocksum.total_areaverde_blocksum), 0) total_areaverde_modulesum,
                      coalesce(sum(blocksum.juros_areaverde_blocksum), 0) juros_areaverde_modulesum,
                      coalesce(sum(blocksum.total_taxacaptacao_blocksum), 0) total_taxacaptacao_modulesum,
                      coalesce(sum(blocksum.descontos_blocksum), 0) descontos_modulesum,
                      coalesce(sum(blocksum.price_total_blocksum), 0) price_total_modulesum,
                      coalesce(sum(blocksum.price_total_juros_blocksum), 0) price_total_juros_modulesum,
                      json_agg(blocksum) blocks
                 from (select v.module_code::integer module_code,
                              v.block_code,
                              count(0) qtde,
                              sum(v.price_total_juros) total_proprietario_blocksum,
                              sum(v.total_agua) total_agua_blocksum,
                              sum(v.total_contribuicaomensal) total_contribuicaomensal_blocksum,
                              sum(v.total_taxas) total_taxas_blocksum,
                              sum(v.jurosproporcional_valor) jurosproporcional_valor_blocksum,
                              sum(v.total_areaverde) total_areaverde_blocksum,
                              sum(v.juros_areaverde) juros_areaverde_blocksum,
                              sum(v.total_taxacaptacao) total_taxacaptacao_blocksum,
                              sum(v.descontos) descontos_blocksum,
                              sum(v.price_total) price_total_blocksum,
                              sum(v.price_total_juros) price_total_juros_blocksum,
                              json_agg((
                              select t from (select
                              v.invoice_id,
                              v.land_id,
                              v.module_code,
                              v.block_code,
                              v.lot_code,
                              v.referencia,
                              v.total_agua,
                              v.total_contribuicaomensal,
                              v.total_taxas,
                              v.jurosproporcional_valor,
                              v.total_areaverde,
                              v.juros_areaverde,
                              v.total_taxacaptacao,
                              v.descontos,
                              v.price_total,
                              v.occurrence_date,
                              v.tipocobranca,
                              v.observacao,
                              v.real_payment_date,
                              v.due_date,
                              v.res_name,
                              v.product_id,
                              v.land,
                              v.product_name,
                              v.price_total,
                              v.price_total_juros) t order by v.module_code::integer, v.block_code, v.lot_code)) res_lines
                         from vw_report_contab_baixados v
                        where true             
            """

        labelRelatorio = ''

        def labelRelatorioAdd(val: str):
            nonlocal labelRelatorio
            if labelRelatorio != '':
                labelRelatorio += ', '

            labelRelatorio += val

        def addSql(nomeCampo: str, data:datetime, label: str ):
            nonlocal sql

            if data:
                sql = sql + " and " + nomeCampo + "'" + data.strftime('%Y-%m-%d') + "'"
                labelRelatorioAdd(label + data.strftime('%d/%m/%Y'))

        addSql('v.occurrence_date >= ', self.datapagamento_ocorrencia_inicio, ' Data de OCORRÊNCIA do PAGAMENTO Apartir de ')
        addSql('v.occurrence_date <= ', self.datapagamento_ocorrencia_fim, ' Data OCORRÊNCIA do PAGAMENTO Até ')

        addSql('v.real_payment_date >= ', self.datapagamento_real_inicio, ' Data REAL do PAGAMENTO Apartir de ')
        addSql('v.real_payment_date <= ', self.datapagamento_real_fim, ' Data REAL do PAGAMENTO  Até ')

        addSql('v.due_date >= ', self.datapagamento_vencimento_inicio, ' Data de VENCIMENTO Apartir de ')
        addSql('v.due_date <= ', self.datapagamento_vencimento_fim, ' Data de VENCIMENTO Até ')

        def addAnoMesReferencia(nomeCampo: str, anoMesReferencia: str, label: str):
            if anoMesReferencia:
                if ((len(anoMesReferencia) != 7) or
                    (not anoMesReferencia.__contains__('/'))
                   ):
                    raise UserError('Ano/Mês de referência precisa estar no formato AAAA/MM, exemplo: 2023/10')

                anoMesRefereenciaInt = anoMesReferencia.replace('/', '')

                nonlocal sql

                sql = sql + " and " + nomeCampo + anoMesRefereenciaInt
                labelRelatorioAdd(label + anoMesReferencia)

        addAnoMesReferencia('v.anomes_vencimento >= ', self.anomesreferenciavenc_inicio, ' Ano/Mês REFERÊNCIA VENCTO Apartir dê ')
        addAnoMesReferencia('v.anomes_vencimento <= ', self.anomesreferenciavenc_fim, ' Ano/Mês REFERÊNCIA VENCTO Até ')

        if self.fatura_id != 0:
            sql = sql + " and v.invoice_id = " + str(self.fatura_id)
            labelRelatorioAdd(' ID FATURA = ' + str(self.fatura_id))

        if (labelRelatorio == ''):
            raise UserError('É preciso preencher ao menos 1 parâmetro de data ou id Fatura')

        tipocob__automatico_boleto_dinheiro_in = ''
        tipocob__automatico_boleto_dinheiro_Label = ''

        if self.tipocobranca_dinheiro:
            tipocob__automatico_boleto_dinheiro_in += "'D'"
            tipocob__automatico_boleto_dinheiro_Label = 'Dinheiro'

        if self.tipocobranca_boleto:
            if tipocob__automatico_boleto_dinheiro_in != '':
                tipocob__automatico_boleto_dinheiro_in += ", "

            tipocob__automatico_boleto_dinheiro_in += "'B'"

            if tipocob__automatico_boleto_dinheiro_Label != '':
                tipocob__automatico_boleto_dinheiro_Label += ', '

            tipocob__automatico_boleto_dinheiro_Label += 'Boleto'

        if self.tipocobranca_debitoautomatico:
            if tipocob__automatico_boleto_dinheiro_in != '':
                tipocob__automatico_boleto_dinheiro_in += ", "

            tipocob__automatico_boleto_dinheiro_in += "'A'"
            if tipocob__automatico_boleto_dinheiro_Label != '':
                tipocob__automatico_boleto_dinheiro_Label += ', '
            tipocob__automatico_boleto_dinheiro_Label += 'Débito Automático'

        if self.tipocobranca_acumulado:
            if tipocob__automatico_boleto_dinheiro_in != '':
                tipocob__automatico_boleto_dinheiro_in += ", "

            tipocob__automatico_boleto_dinheiro_in += "'C'"
            if tipocob__automatico_boleto_dinheiro_Label != '':
                tipocob__automatico_boleto_dinheiro_Label += ', '
            tipocob__automatico_boleto_dinheiro_Label += 'Acumulados'


        labelRelatorioAdd(', Tipo de Cobrança: ' + tipocob__automatico_boleto_dinheiro_Label)

        sql = sql + " and v.tipocob__automatico_boleto_dinheiro in (" + tipocob__automatico_boleto_dinheiro_in + ")"

        if tipoagrupamento_proprietario:
            sql = sql + """
                group by
                      v.res_id,
                      v.res_name
                order by
                      v.res_name                      
             ) t
        ) t
"""
        if tipoagrupamento_modulobloco:
            sql = sql + """
                        group by
                              v.module_code::integer, 
                              v.block_code
                        order by
                              v.module_code::integer, 
                              v.block_code
                     ) blocksum
                group by module_code
                order by module_code
            ) modulesum
     ) t
"""

        self.env.cr.execute(sql)
        invoices_cr = self.env.cr.fetchall()

        appointments = json.loads(invoices_cr[0][0])

        action_name = ''

        if tipoagrupamento_proprietario:
            action_name = 'action_paidinvoice_report'

        if tipoagrupamento_modulobloco:
            action_name = 'action_paidinvoice_report_blockmodule'

        data = {
            'doc_model': action_name,
            'date_from': self.datapagamento_real_inicio,
            'date_to': self.datapagamento_real_fim,
            'label_relatorio': labelRelatorio,
            'form_data': self.read()[0],
            'appointments': appointments
        }
        return self.env.ref('property_base.' + action_name).report_action(self, data=data)


    @api.constrains('date_from', 'date_to')
    def _check_date_validation(self):
        for record in self:
            if record.date_from > record.date_to:
                raise ValidationError("Date from must be previous than date to.")

class AppointmentReportWizard_Report(models.AbstractModel):
    """
        Abstract Model specially for report template.
        _name = Use prefix `report.` along with `module_name.report_name`
    """
    _name = 'report.property_base.paidinvoicereport.wizard'

    @api.model
    def _get_report_values(self, docids, data=None):
        print('x')
        return {
            'data': data,
        }
