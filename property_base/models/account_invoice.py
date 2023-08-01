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

    # Usado para deixar invisivel o botão
    # Imprimir Boleto, quando não for o caso
    payment_method_code = fields.Char(related="payment_mode_id.payment_method_id.code")

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

            if date_due > datetime.strptime('09/08/2023', '%d/%m/%Y').date():
                raise UserError('Data de vencimento maior que o permitido')

            if invoice.state in ("draft", "open"):
                invoice.write({'state': 'cancel'})
                invoice.write({'state': 'draft'})
                invoice.write({'payment_mode_id': False})
                invoice.write({'state': 'open', 'date_due': date_due})
                invoice.write({'state': 'paid'})

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

            if self.state == 'in_payment':
                payment_date = self.cnab_payment_occurrence_date()

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
     where cre.invoice_id = """ + str(self.id)

        self.env.cr.execute(sql)
        res = self.env.cr.fetchone()

        return res[0]

