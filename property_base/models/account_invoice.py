# Copyright 2020 Akretion
# @author Magno Costa <magno.costa@akretion.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import base64
import json
import logging
import tempfile

import requests

from odoo import _, fields, models, api
from odoo.exceptions import Warning as UserError

from ..constants.br_cobranca import get_brcobranca_api_url
from datetime import datetime

from odoo.tools import float_is_zero


logger = logging.getLogger(__name__)


class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    file_boleto_pdf_id = fields.Many2one(
        comodel_name="ir.attachment",
        string="Boleto PDF",
        ondelete="restrict",
        copy=False,
    )

    date_due_initial = fields.Date(string='Data inicial Vencimento')
    date_payment = fields.Date(string='Data de pagamento(Sisa)')

    # Usado para deixar invisivel o botão
    # Imprimir Boleto, quando não for o caso
    payment_method_code = fields.Char(related="payment_mode_id.payment_method_id.code")
    # transmit_method_simnao = fields.Char(string='Transmite Sim/Não', compute='_compute_transmit_method_simnao')
    payment_mode_id = fields.Many2one(
        comodel_name='account.payment.mode', string="Payment Mode",
        ondelete='restrict',
        required=True,
        readonly=True, states={'draft': [('readonly', False)]})

    accumulated = fields.Boolean(string="Fatura acumulada")

    # def _compute_transmit_method_simnao(self):
    #     for rec in self:
    #         if rec.transmit_method_id.id == 4:
    #             rec.transmit_method_simnao = 'Não'
    #         else:
    #             rec.transmit_method_simnao = 'Sim'

    @api.model
    def create(self, vals):
        if not vals['date_due']:
            raise UserError(
                _(
                    'Informe a data de vencimento da fatura.'
                )
            )

        if not vals['origin']:
            land_id = self.env['property.land'].search([('id', '=', vals['land_id'])])[0]
            vals['origin'] = "{}/{}".format(datetime.strptime(vals['date_due'], '%Y-%m-%d').strftime('%m-%Y'), land_id.name)

        if not vals['date_due_initial']:
            vals.update({'date_due_initial':vals['date_due']})

        sql = """
select vpl.owner_invoice_id
  from vw_property_land vpl
 where vpl.id = """ + str(vals['land_id'])
        self.env.cr.execute(sql)
        owner_invoice_id = self.env.cr.fetchall()[0][0]

        if vals['partner_id'] != owner_invoice_id:
            raise UserError(
                _(
                    'Propriedade/Proprietário incompatível.'
                )
            )

        res = super().create(vals)
        return res

    def gera_boleto_pdf(self):
        file_pdf = self.file_boleto_pdf_id
        self.file_boleto_pdf_id = False
        file_pdf.unlink()

        receivable_ids = self.mapped("financial_move_line_ids")

        boletos = receivable_ids.send_payment()
        if not boletos:
            raise UserError(
                _(
                    "It is not possible generated boletos\n"
                    "Make sure the Invoice are in Confirm state and "
                    "Payment Mode method are CNAB."
                )
            )

        pdf_string = self._get_brcobranca_boleto(boletos)

        inv_number = self.get_invoice_fiscal_number().split("/")[-1].zfill(8)
        file_name = "boleto_nf-" + inv_number + ".pdf"

        self.file_pdf_id = self.env["ir.attachment"].create(
            {
                "name": file_name,
                "datas_fname": file_name,
                "res_model": self._name,
                "res_id": self.id,
                "datas": base64.b64encode(pdf_string),
                "mimetype": "application/pdf",
                "type": "binary",
            }
        )

    def _get_brcobranca_boleto(self, boletos):

        content = json.dumps(boletos)
        f = open(tempfile.mktemp(), "w")
        f.write(content)
        f.close()
        files = {"data": open(f.name, "rb")}

        # brcobranca_api_url = self.env['ir.config_parameter'].get_param('BRCOBRANCA_API_URL')
        brcobranca_api_url = get_brcobranca_api_url(self)
        brcobranca_service_url = brcobranca_api_url + "/api/boleto/multi"
        logger.info(
            "Connecting to %s to get Boleto of invoice %s",
            brcobranca_service_url,
            self.name,
        )
        res = requests.post(brcobranca_service_url, data={"type": "pdf"}, files=files)

        if str(res.status_code)[0] == "2":
            pdf_string = res.content
        else:
            raise UserError(res.text.encode("utf-8"))

        return pdf_string

    def _target_new_tab(self, attachment_id):
        if attachment_id:
            return {
                "type": "ir.actions.act_url",
                "url": "/web/content/{id}/{nome}".format(
                    id=attachment_id.id, nome=attachment_id.name
                ),
                "target": "new",
            }

    def view_boleto_pdf(self):
        if not self.file_boleto_pdf_id:
            self.gera_boleto_pdf()
        return self._target_new_tab(self.file_pdf_id)

    def get_boleto_pdf(self):
        if not self.file_boleto_pdf_id:
            self.gera_boleto_pdf()
        return self.file_pdf_id.local_url

    @api.model
    def action_account_invoice_accumulated(self):
        self.invoice_accumulated()

    def invoices_get_monthly_last_draft(self):
        #Retorna lista contendo as faturas DRAFT que estão no mês de processamento (vw_property_settings_monthly_last)
        sql = """
        select anomes_primeirodia(anomes(invoice_date_due))::date primeirodia,
               anomes_ultimodia(anomes(invoice_date_due))::date ultimodia
          from vw_property_settings_monthly_last            
                """
        self.env.cr.execute(sql)
        dts = self.env.cr.fetchall()[0]
        primeirodia = dts[0]
        ultimodia = dts[1]

        invoices = self.search([('land_id', '!=', False),
                                ('state', 'in', ['draft']),
                                ('date_due', '>=', primeirodia),
                                ('date_due', '<=', ultimodia),
                                ])
        return invoices

    def invoice_accumulated__all_monthly_last(self):
        #Processa todas as faturas DRAFT referente ao mês de processamento (vw_property_settings_monthly_last)
        invoices = self.invoices_get_monthly_last_draft()
        for invoice in self.web_progress_iter(invoices, msg="Processando faturas acumuladas"):
            invoice.invoice_accumulated()

    def invoice_accumulated(self):
        #Esta rotina:
        #  1. Processa a rotina que acumula faturas anteriores na fatura atual (self)
        #  2. Chama a rotina de processamento de baixas nas faturas de origem (action_account_invoice_acumular_emoutra_fatura)

        for invoice in self.web_progress_iter(self):
            if invoice.state not in ('draft', 'open'):
                self.raiseUserError("Não pode ser processado pois não está no estado RASCUNHO ou ABERTO")

        for invoice in self.web_progress_iter(self):
            invoice.invoice_message_post_valorfatura('** Processado rotina "Processar Boleto atrasado (Acumular)"[INÍCIO]')
            old_state = invoice.state

            if invoice.state == 'open':
                invoice.cancel_and_draft()

            logger.info("##ACUMULAR Efetuado processo de acúmulo das 2 últimas faturas para a fatura Fatura %s", str(invoice.id))
            invoice.cancelaracumulados()  # Cancela qualquer pagamento que esteja apontando para a fatura atual (fatura de destino) de acumulo
            self.env.cr.execute('select account_invoice_accumulated_create_invoice_id(' + str(invoice.id) + ')')
            invoice.invoice_baixa_nas_origens()

            if old_state == 'open':
                #Se a fatura estava open inicialmente, volto o status dela
                invoice.action_invoice_open()

            invoice.invoice_message_post_valorfaturaFromDatabase('** Processado rotina "Processar Boleto atrasado (Acumular)"[FIM]')

            logger.info("Efetuado processo de acúmulo das 2 últimas faturas para a fatura Fatura %s", str(invoice.id))

    @api.model
    def action_account_invoice_remover_boletos_acumulados(self):
        #Esta rotina:
        #  1. Remove da fatura atual itens (invoice_account_lines) que sejam acumulados
        #  2. Remove a baixa AOF na fatura de origem (Fatura que foi acumulada em Self)
        for invoice in self.web_progress_iter(self):
            if invoice.state not in ('draft', 'open'):
                self.raiseUserError("Não pode ser processado pois não está no estado RASCUNHO ou ABERTO")

        for invoice in self.web_progress_iter(self):
            if invoice.state in ("draft", "open"):
                invoice.invoice_message_post_valorfatura('** Processado rotina "Remover boletos acumulados"[INÍCIO]')

                old_state = invoice.state

                if invoice.state == 'open':
                    invoice.cancel_and_draft()

                invoice.cancelaracumulados()  # Cancela qualquer pagamento que esteja apontando para a fatura atual (fatura de destino) de acumulo
                self.env.cr.execute('select account_invoice_accumulated_reset(null, ' + str(invoice.id) + ')')

                if old_state == 'open':
                    # Se a fatura estava open inicialmente, volto o status dela
                    invoice.action_invoice_open()

                invoice.invoice_message_post_valorfaturaFromDatabase('** Processado rotina "Remover boletos acumulados" [FIM]')
                logger.info("Removido boletos acumulados para a fatura Fatura %s", str(invoice.id))


    def invoice_baixa_nas_origens(self):
        #Verifica se em self(DESTINO) existem faturas acumuladas(ORIGEM) e aplicar as baixas(AOF- Acumulado outra fatura) nelas (Baixa nas origens)

        for invoice in self:
            #O Sql abaixo retorna a fatura de origem de acúmulo e seu respectivo valor de acúmulo + juros
            sql= """
    select ail_ref.invoice_id invoice_id_ref, 
           sum(ail_ref.price_total) +
           coalesce(
           (select sum(ail.price_total) multa_juros_correcao
             from account_invoice_line ail
            where ail.invoice_id = ail_ref.invoice_id
              and ail.product_id = 12 /*Multas, Juros, Correção Monetária*/
           ), 0) value_ref           
      from account_invoice ai 
           join account_invoice_line ail on ail.invoice_id = ai.id
           join account_invoice_line ail_ref on ail_ref.id = ail.account_invoice_line_id_accumulated_ref
     where true 
       and ai.id = """ + str(invoice.id) + """
       and ail.account_invoice_line_id_accumulated_ref is not null
     group by ail_ref.invoice_id
            """
            self.env.cr.execute(sql)
            cur_invoices = self.env.cr.fetchall()

            for cur_invoice in cur_invoices:
                invoice_id_ref = cur_invoice[0]
                value_ref = cur_invoice[1]

                invoice_origem = self.env['account.invoice'].search([('id', '=', invoice_id_ref)], limit=1)[0]
                invoice_origem.acumularemoutrafatura(invoice.id, value_ref)


    def acumularemoutrafatura(self, faturadestino_id, pay_amount):
        #Nomenclaturas:
        #  Fatura de ORIGEM => Fatura de vencimento anterior que teve seus itens transferidos(acumulados)em outra fatura(nata fatura de destino)
        #  Fatura de DESTINO => Fatura que recebeu os itens acumulados da fatura de ORIGEM
        #  * O Self é a Fatura de ORIGEM
        #Esta rotina:
        #   1. Recebe a fatura de ORIGEM (Self) e efetua nela o pagamento "Acumulado em outra fatura"
        #   2. Muda o campo account_invoice.accumulated para TRUE
        #
        #Parâmetros:
        #  faturadestino_id => Id da fatura de destino que recebeu a fatura acumulada
        #  pay_amount => Valor a ser dado baixa na fatura de ORIGEM

        for invoice in self.web_progress_iter(self):
            if invoice.state == 'open':
                journal = self.env['account.journal'].search([('code', '=', 'AOF')], limit=1)
                new_invoice_state = ''

                if not journal:
                    raise UserError(
                        _(
                            "Diário AOF(Acumulado em outra Fatura) não encontrado"
                        )
                    )

                payment_vals = self._prepare_payment_vals(journal, pay_amount=pay_amount)
                payment_vals.update({'accumulated_invoice_id': faturadestino_id})

                if (self._context.get('active_ids')):
                    self._context.update({'active_id': invoice.id})
                    self._context.update({'active_ids': [invoice.id]})

                try:
                    # A mudança das variaveis de contexto active_id e active_ids é para que não dê problema
                    #   em /odoo/addons/account/models/account_payment.py.default_get
                    #   pois apesar de eu estar trabalhando com invoice, a rotina internamente entende que estou trabalhando com faturadestino_id(que é de fato a fatura que está ativa em tela)
                    payment = self.env['account.payment'].create(payment_vals)
                    payment.post()
                finally:
                    if (self._context.get('active_ids')):
                        self._context.update({'active_id': faturadestino_id})
                        self._context.update({'active_ids': [faturadestino_id]})

                invoice.write({'accumulated': True})

    def cancelaracumulados(self):
        #  Cancela todos os pagamentos com code=AOF(Acumulado em outra fatura) que tem como referência a fatura self
        for invoice in self.web_progress_iter(self):
            account_payments = self.env['account.payment'].search(['&', ('accumulated_invoice_id', '=', invoice.id), ('state', '=', 'posted')])

            for account_payment in account_payments:
                account_payment.cancel()

    def account_invoice_create_fees_traffic_curcorrection(self):
        for invoice in self.web_progress_iter(self):
            if invoice.state in ("draft", "open"):
                self.env.cr.execute('select account_invoice_create_fees_traffic_curcorrection(' + str(invoice.id) + ')')
                logger.info("Efetuado cálculo de juros da Fatura %s", str(invoice.id))

    def remover_cnab(self):
        # Esta rotina é temporária, e serve apenas para corrigir dados da importação.
        # Esta rotina remove o cnab e marca o boleto como pago.
        for invoice in self.web_progress_iter(self):
            date_due = invoice.date_due

            if date_due > datetime.strptime('09/10/2023', '%d/%m/%Y').date():
                raise UserError('Data de vencimento maior que o permitido')

            if invoice.state in ("draft", "open"):
                self.env.cr.execute("update account_invoice set state = 'paid' where id = " + str(invoice.id))

    @api.multi
    def write(self, values):
        #processar Taxa de permanência
        for invoice in self:
            invoice_state = values.get('state') or invoice.state

            if invoice_state == 'draft':
                if 'date_due_initial' in values and values['date_due_initial']:
                    invoice_date_due_initial = datetime.strptime(values['date_due_initial'], '%Y-%m-%d').date()
                else:
                    invoice_date_due_initial = invoice.date_due_initial

                if 'date_due' in values:
                    if type(values['date_due']) is str:
                        invoice_date_due = datetime.strptime(values['date_due'], '%Y-%m-%d').date()
                    else:
                        invoice_date_due = values['date_due']
                elif invoice.date_due:
                    invoice_date_due = invoice.date_due
                else:
                    invoice_date_due = False

                if invoice_date_due and invoice_date_due_initial and invoice_date_due_initial < invoice_date_due:
                    invoice_date_due_yearmonth = int(str(invoice_date_due.year) + str(invoice_date_due.month).zfill(2))
                    invoice_id = values.get('id') or int(invoice.id)

                    invoice_line_TxPermanencia = self.env['account.invoice.line']
                    product_product = self.env['product.product'].search([('default_code', '=', 'PROPTP')])[0] #PROPTP-Taxa de pemanência
                    valorBaseJuros = 0

                    for invoice_line in self.invoice_line_ids:
                        if invoice_line.anomes_vencimento == invoice_date_due_yearmonth:
                            if invoice_line.product_id.code == 'PROPTP':
                                invoice_line_TxPermanencia = invoice_line

                            if invoice_line.product_id.default_code in ('PROPTAX', 'PROPGT', 'PROPWC'):
                                valorBaseJuros += invoice_line.price_total

                    multaDiaria = round(valorBaseJuros * 0.001, 2)
                    diasTaxaPermanencia = abs((invoice_date_due - invoice_date_due_initial).days)
                    valTxPermanencia = multaDiaria * diasTaxaPermanencia

                    jsonTxPermanencia = {
                        'invoice_id': invoice_id,
                        'product_id': product_product.id,
                        'name': product_product.name,
                        'price_unit': valTxPermanencia,
                        'account_id': product_product.product_tmpl_id.get_product_accounts()['income'].id,
                        'anomes_vencimento': invoice_date_due_yearmonth,
                        'land_id': invoice.land_id.id}

                    if len(product_product.taxes_id) > 0:
                        jsonTxPermanencia.append({'invoice_line_tax_ids': [(6, 0, product_product.taxes_id.ids)]})

                    if invoice_line_TxPermanencia.id:
                        if valTxPermanencia == 0:
                            invoice_line_TxPermanencia.unlink() # Já existe uma taxa de permanência porém o valor calculado foi 0. Então vou deletar o que já existe
                        elif (valTxPermanencia != invoice_line_TxPermanencia.price_unit):
                            invoice_line_TxPermanencia.write(jsonTxPermanencia)
                    elif valTxPermanencia > 0:
                        invoice_line_TxPermanencia.create(jsonTxPermanencia)

            return super(AccountInvoice, self).write(values)
    @api.model
    def _get_payments_vals(self):
        """
            Método Sobrescrevido para trazer a data de pagamento para arquivos de cnab como sendo a data que foi pago no banco, e não a data que foi importado o arquivo.
        """
        if not self.payment_move_line_ids:
            return []
        payment_vals = []
        currency_id = self.currency_id
        for payment in self.payment_move_line_ids:
            payment_currency_id = False
            if self.type in ('out_invoice', 'in_refund'):
                amount = sum([p.amount for p in payment.matched_debit_ids if p.debit_move_id in self.move_id.line_ids])
                amount_currency = sum(
                    [p.amount_currency for p in payment.matched_debit_ids if p.debit_move_id in self.move_id.line_ids])
                if payment.matched_debit_ids:
                    payment_currency_id = all([p.currency_id == payment.matched_debit_ids[0].currency_id for p in
                                               payment.matched_debit_ids]) and payment.matched_debit_ids[
                                              0].currency_id or False
            elif self.type in ('in_invoice', 'out_refund'):
                amount = sum(
                    [p.amount for p in payment.matched_credit_ids if p.credit_move_id in self.move_id.line_ids])
                amount_currency = sum([p.amount_currency for p in payment.matched_credit_ids if
                                       p.credit_move_id in self.move_id.line_ids])
                if payment.matched_credit_ids:
                    payment_currency_id = all([p.currency_id == payment.matched_credit_ids[0].currency_id for p in
                                               payment.matched_credit_ids]) and payment.matched_credit_ids[
                                              0].currency_id or False
            # get the payment value in invoice currency
            if payment_currency_id and payment_currency_id == self.currency_id:
                amount_to_show = amount_currency
            else:
                currency = payment.company_id.currency_id
                amount_to_show = currency._convert(amount, self.currency_id, payment.company_id, payment.date or fields.Date.today())
            if float_is_zero(amount_to_show, precision_rounding=self.currency_id.rounding):
                continue
            payment_ref = payment.move_id.name
            invoice_view_id = None
            if payment.move_id.ref:
                payment_ref += ' (' + payment.move_id.ref + ')'
            if payment.invoice_id:
                invoice_view_id = payment.invoice_id.get_formview_id()

            payment_date = payment.date

            # if self.state == 'in_payment':
            if (self.payment_mode_id.id == 1): #cnab
                payment_date_temp = self.cnab_payment_occurrence_date()
                if payment_date_temp:
                    payment_date = payment_date_temp


            payment_vals.append({
                'name': payment.name,
                'journal_name': payment.journal_id.name,
                'amount': amount_to_show,
                'currency': currency_id.symbol,
                'digits': [69, currency_id.decimal_places],
                'position': currency_id.position,
                'date': payment_date,
                'payment_id': payment.id,
                'account_payment_id': payment.payment_id.id,
                'invoice_id': payment.invoice_id.id,
                'invoice_view_id': invoice_view_id,
                'move_id': payment.move_id.id,
                'ref': payment_ref,
            })
        return payment_vals

    def cnab_payment_occurrence_date(self):
        # Retorna a data que o cliente pagou o título (boleto) ou o dia que foi efetuado o débito automático

        sql = """
    select cre.occurrence_date
      from l10n_br_cnab_return_event cre 
             join l10n_br_cnab_return_log crl on crl.id = cre.cnab_return_log_id
     where cre.invoice_id = """ + str(self.id) + """
       and cre.occurrences = '06-Liquidação Normal *'"""

        self.env.cr.execute(sql)
        res = self.env.cr.fetchone()

        if res == None:
            return None
        else:
            return res[0]

    @api.multi
    def create_account_payment_line(self):
        # override de /home/mateus/OdooDev/odoo/custom-addons/riviera/bank-payment/account_payment_order/models/account_invoice.py
        # Override para adcionar um progress (web_progress_iter) e para commitar de 20 em 20(indexCommit)
        apoo = self.env['account.payment.order']
        result_payorder_ids = []
        action_payment_type = 'debit'
        indexCommit = 0

        for inv in self.web_progress_iter(self):
            if inv.state != 'open':
                raise UserError(_(
                    "The invoice %s is not in Open state") % inv.number)
            if not inv.move_id:
                raise UserError(_(
                    "No Journal Entry on invoice %s") % inv.number)
            applicable_lines = inv.move_id.line_ids.filtered(
                lambda x: (
                    not x.reconciled and x.payment_mode_id.payment_order_ok and
                    x.account_id.internal_type in ('receivable', 'payable') and
                    not any(p_state in ('draft', 'open', 'generated')
                            for p_state in x.payment_line_ids.mapped('state'))
                )
            )
            if not applicable_lines:
                logger.info('### Falha ao gerar cnab para fatura id: ' + str(inv.id))
                continue
                # raise UserError(_(
                #     'No Payment Line created for invoice %s because '
                #     'it already exists or because this invoice is '
                #     'already paid.') % inv.number)
            payment_modes = applicable_lines.mapped('payment_mode_id')
            if not payment_modes:
                raise UserError(_(
                    "No Payment Mode on invoice %s") % inv.number)
            for payment_mode in payment_modes:
                payorder = apoo.search([
                    ('payment_mode_id', '=', payment_mode.id),
                    ('state', '=', 'draft')
                ], limit=1)
                new_payorder = False
                if not payorder:
                    payorder = apoo.create(inv._prepare_new_payment_order(
                        payment_mode
                    ))
                    new_payorder = True
                result_payorder_ids.append(payorder.id)
                action_payment_type = payorder.payment_type
                count = 0
                for line in applicable_lines.filtered(
                    lambda x: x.payment_mode_id == payment_mode
                ):
                    line.create_payment_line_from_move_line(payorder)
                    count += 1
                if new_payorder:
                    inv.message_post(body=_(
                        '%d payment lines added to the new draft payment '
                        'order %s which has been automatically created.')
                        % (count, payorder.name))
                else:
                    inv.message_post(body=_(
                        '%d payment lines added to the existing draft '
                        'payment order %s.')
                        % (count, payorder.name))

            indexCommit += 1

            if indexCommit >= 20:
                self.env.cr.commit()
                indexCommit = 0

        action = self.env['ir.actions.act_window'].for_xml_id(
            'account_payment_order',
            'account_payment_order_%s_action' % action_payment_type)
        if len(result_payorder_ids) == 1:
            action.update({
                'view_mode': 'form,tree,pivot,graph',
                'res_id': payorder.id,
                'views': False,
                })
        else:
            action.update({
                'view_mode': 'tree,form,pivot,graph',
                'domain': "[('id', 'in', %s)]" % result_payorder_ids,
                'views': False,
                })
        return action

    @api.multi
    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        res = super(AccountInvoice, self).copy(default=default)

        res.date_invoice = self.date_invoice
        res.date_due = self.date_due

        i = 0

        while i < len(self.invoice_line_ids):
            j = 0
            while j < len(res.invoice_line_ids):
                if ((res.invoice_line_ids[j].product_id.id == self.invoice_line_ids[i].product_id.id)
                  and (res.invoice_line_ids[j].name == self.invoice_line_ids[i].name)
                  and (res.invoice_line_ids[j].land_id.id == self.invoice_line_ids[i].land_id.id)
                  and (res.invoice_line_ids[j].price_total == self.invoice_line_ids[i].price_total)
                  and (res.invoice_line_ids[j].anomes_vencimento == 0)):
                    res.invoice_line_ids[j].anomes_vencimento = self.invoice_line_ids[i].anomes_vencimento
                    break
                j += 1

            i += 1

        return res

    def action_account_invoice_limpar_nosso_numerro(self):
        def showError(msg: str):
            raise UserError(
                _(
                    'Erro na Fatura ' + rec['origin'] + ' ao efetuar Operação Limpar Nosso Número:\n\n' + msg + '\n\nRotina: account_invoice.action_account_invoice_limpar_nosso_numerro'
                )
            )

        for rec in self.web_progress_iter(self):
            if rec['state'] not in ('draft', 'open'):
                showError('Fatura precisa estar no Status PROVISÓRIO ou ABERTO')

            for payment in rec.payment_ids:
                if payment.state != 'cancelled':
                    showError('Fatura não pode ter movimentações de Baixa')

        for rec in self.web_progress_iter(self):
            current_state = rec['state']

            if rec['state'] == 'open':
                rec.cancel_and_draft()

            if rec['state'] != 'draft':
                showError('Não foi possível retornar fatura ao Status PROVISORIO')

            old_move_name = rec.move_name

            rec.write({'number': None,
                       'move_name': None,
                       'reference': None})

            rec.message_post(body=_('Nosso Número "' + str(old_move_name or '') + '" excluído'))

            if current_state == 'open':
                rec.action_invoice_open()
                rec.invoice_message_post_valorfatura('Nosso Número alterado de "' + str(old_move_name or '') + '" para "' + str(rec.move_name or '') + '"')

    def cancel_and_draft(self):
        for rec in self:
            rec.action_invoice_cancel()
            rec.write({'state': 'draft'}) # O Ideal seria rec.action_invoice_draft porém por algum motivo desconhecido em alguns testes a fatura não ficava no status DRAFT

    def invoice_message_post_valorfatura(self, msg):
        self.invoice_message_post(msg + ' - Valor da Fatura: ' + str(self.amount_total))

    def invoice_message_post_valorfaturaFromDatabase(self, msg):
        self.invoice_message_post(msg + ' - Valor da Fatura: ' + str(self.invoiceGetAmountValueFromDatabase()))

    def invoice_message_post(self, msg):
        self.message_post(body=_(msg))

    def raiseUserError(self, msg):
        raise UserError(
            _(
                "Boleto id: " + str(self.id) + ", " + self.origin + ": \n\n" + msg
            )
        )

    def invoiceGetAmountValueFromDatabase(self):
        self.env.cr.execute('select ai.amount_total from account_invoice ai where id = ' + str(self.id))
        cur_invoices = self.env.cr.fetchone()
        return cur_invoices[0]
