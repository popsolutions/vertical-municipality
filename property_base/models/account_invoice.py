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

    date_due_initial = fields.Date(string='Due Date Initial')
    date_payment = fields.Date(string='Data de pagamento(Sisa)')

    # Usado para deixar invisivel o botão
    # Imprimir Boleto, quando não for o caso
    payment_method_code = fields.Char(related="payment_mode_id.payment_method_id.code")
    # transmit_method_simnao = fields.Char(string='Transmite Sim/Não', compute='_compute_transmit_method_simnao')

    # def _compute_transmit_method_simnao(self):
    #     for rec in self:
    #         if rec.transmit_method_id.id == 4:
    #             rec.transmit_method_simnao = 'Não'
    #         else:
    #             rec.transmit_method_simnao = 'Sim'

    @api.model
    def create(self, vals):
        if not vals['origin']:
            land_id = self.env['property.land'].search([('id', '=', vals['land_id'])])[0]
            vals['origin'] = "{}/{}".format(datetime.strptime(vals['date_due'], '%Y-%m-%d').strftime('%m-%Y'), land_id.name)

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
        brcobranca_api_url = get_brcobranca_api_url()
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
        for invoice in self.web_progress_iter(self):
            if invoice.state in ("draft", "open"):
                self.env.cr.execute('select account_invoice_accumulated_create_invoice_id(' + str(invoice.id) + ')')
                logger.info("Efetuado processo de acúmulo das 2 últimas faturas para a fatura Fatura %s", str(invoice.id))

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
                if 'date_due_initial' in values:
                    invoice_date_due_initial = datetime.strptime(values['date_due_initial'], '%Y-%m-%d').date()
                else:
                    invoice_date_due_initial = invoice.date_due_initial

                if 'date_due' in values:
                    if type(values['date_due']) is str:
                        invoice_date_due = datetime.strptime(values['date_due'], '%Y-%m-%d').date()
                    else:
                        invoice_date_due = values['date_due']
                else:
                    invoice_date_due = invoice.date_due

                if invoice_date_due_initial and invoice_date_due_initial < invoice_date_due:
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
                        if (valTxPermanencia != invoice_line_TxPermanencia.price_unit):
                            invoice_line_TxPermanencia.write(jsonTxPermanencia)
                    else:
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
                raise UserError(_(
                    'No Payment Line created for invoice %s because '
                    'it already exists or because this invoice is '
                    'already paid.') % inv.number)
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
