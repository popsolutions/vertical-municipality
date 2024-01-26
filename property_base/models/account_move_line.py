# Copyright 2017 Akretion
# @author Raphaël Valyi <raphael.valyi@akretion.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from odoo import models, api, _

from ..constants.br_cobranca import DICT_BRCOBRANCA_CURRENCY, get_brcobranca_bank
from odoo.exceptions import Warning as UserError

_logger = logging.getLogger(__name__)


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"
    # _name = "account.move.line"
    # _name = "account.move.line.inherited.property.base"

    # see the list of brcobranca boleto fields:
    # https://github.com/kivanio/brcobranca/blob/master/lib/
    # brcobranca/boleto/base.rb
    # and test a here:
    # https://github.com/kivanio/brcobranca/blob/master/spec/
    # brcobranca/boleto/itau_spec.rb

    @api.multi
    def send_payment(self):

        # super(AccountMoveLine, self).send_payment()
        wrapped_boleto_list = []

        for move_line in self:

            sql = 'select multa_diaria from func_account_invoice_JurosDiario(' + str(move_line.invoice_id.id) + ')'
            self.env.cr.execute(sql)
            curr_move_line = self.env.cr.fetchall()[0]

            bank_account_id = move_line.payment_mode_id.fixed_journal_id.bank_account_id

            if not bank_account_id:
                raise UserError('Informe um mode de pagamento cnab válido.')

            bank_name_brcobranca = get_brcobranca_bank(
                bank_account_id, move_line.payment_mode_id.payment_method_code
            )
            precision = self.env["decimal.precision"]
            precision_account = precision.precision_get("Account")

            if move_line.invoice_id.land_id.owner_invoice_id:
                sacado = move_line.invoice_id.land_id.owner_id.legal_name + ' A/C ' + move_line.invoice_id.land_id.owner_invoice_id.legal_name
            else:
                sacado = move_line.partner_id.legal_name

            boleto_cnab_api_data = {
                "bank": bank_name_brcobranca[0],
                # "valor": str("%.2f" % move_line.debit), # Mateus - esta linha foi comentada pois não estou inserindo ainda registros em account_move_line quando eu efetuo o processo de ACUMULU DE BOLETOS ou (TRAZER MOVIMENTOS DE BOLETOS ATRASADOS) inerente ao processo de Riviera. # rever futuramente esta alteração. Podem surgir impactos em contabilidade/fiscal
                "valor": str("%.2f" % move_line.invoice_id.amount_total),
                "cedente": move_line.company_id.partner_id.legal_name + ' CNPJ: ' + move_line.company_id.cnpj_cpf,
                "cedente_endereco": (move_line.company_id.partner_id.street_name or "")
                + ", "
                + (move_line.company_id.partner_id.street_number or "")
                + " - "
                + (move_line.company_id.partner_id.district or "")
                + " - "
                + (move_line.company_id.partner_id.city_id.name or "")
                + " - "
                + ("CEP:" + move_line.company_id.partner_id.zip or "")
                + " - "
                + (move_line.company_id.partner_id.state_id.code or ""),
                "documento_cedente": move_line.company_id.cnpj_cpf,
                "sacado": sacado,
                "sacado_documento": move_line.partner_id.cnpj_cpf,
                "agencia": bank_account_id.bra_number,
                "conta_corrente": bank_account_id.acc_number,
                "convenio": move_line.payment_mode_id.code_convetion,
                "carteira": str(move_line.payment_mode_id.boleto_wallet),
                "nosso_numero": int(
                    "".join(i for i in move_line.own_number if i.isdigit())
                ),
                "documento_numero": move_line.document_number,
                "data_vencimento": move_line.date_maturity.strftime("%Y/%m/%d"),
                "data_documento": move_line.invoice_id.date_invoice.strftime(
                    "%Y/%m/%d"
                ),
                "especie": move_line.payment_mode_id.boleto_species,
                "moeda": DICT_BRCOBRANCA_CURRENCY["R$"],
                "aceite": move_line.payment_mode_id.boleto_accept,
                "sacado_endereco": (move_line.partner_id.street_name or "")
                + ", "
                + (move_line.partner_id.street_number or "")
                + ", "
                + (move_line.partner_id.district or "")
                + ", "
                + (move_line.partner_id.city_id.name or "")
                + " - "
                + (move_line.partner_id.state_id.code or ""),
                "data_processamento": move_line.invoice_id.date_invoice.strftime(
                    "%Y/%m/%d"
                ),
                "instrucao1": move_line.payment_mode_id.instructions or "",
            }

            # Instrução de Juros
            if move_line.payment_mode_id.boleto_interest_perc > 0.0:
                # Cálculo Original
                # valor_juros = round(
                #     move_line.debit
                #     * ((move_line.payment_mode_id.boleto_interest_perc / 100) / 30),
                #     precision_account,
                # )

                valor_juros = curr_move_line[0] or 0

                if (valor_juros > 0):
                    instrucao_juros = (
                        "APÓS VENCIMENTO COBRAR R$ %s AO DIA "
                        % (
                            ("%.2f" % valor_juros).replace(".", ","),
                        )
                    )

                    boleto_cnab_api_data.update(
                        {
                            "instrucao3": instrucao_juros,
                        }
                    )

            # Instrução Multa
            if move_line.payment_mode_id.boleto_fee_perc > 0.0:
                valor_multa = round(
                    move_line.debit * (move_line.payment_mode_id.boleto_fee_perc / 100),
                    precision_account,
                )
                instrucao_multa = (
                    "APÓS VENCIMENTO COBRAR MULTA"
                    + " DE %s %% ( R$ %s )"
                    % (
                        ("%.2f" % move_line.payment_mode_id.boleto_fee_perc).replace(
                            ".", ","
                        ),
                        ("%.2f" % valor_multa).replace(".", ","),
                    )
                )
                boleto_cnab_api_data.update(
                    {
                        "instrucao4": instrucao_multa,
                    }
                )

            # Instrução Desconto
            if move_line.payment_mode_id.boleto_discount_perc > 0.0:
                valor_desconto = round(
                    move_line.debit
                    * (move_line.payment_mode_id.boleto_discount_perc / 100),
                    precision_account,
                )
                instrucao_desconto_vencimento = (
                    "CONCEDER ABATIMENTO PERCENTUAL DE" + " %s %% "
                    "ATÉ O VENCIMENTO EM %s ( R$ %s )"
                    % (
                        (
                            "%.2f" % move_line.payment_mode_id.boleto_discount_perc
                        ).replace(".", ","),
                        move_line.date_maturity.strftime("%d/%m/%Y"),
                        ("%.2f" % valor_desconto).replace(".", ","),
                    )
                )
                boleto_cnab_api_data.update(
                    {
                        "instrucao5": instrucao_desconto_vencimento,
                    }
                )

            if bank_account_id.bank_id.code_bc in ("021", "004"):
                digito_conta_corrente = move_line.payment_mode_id.bank_id.acc_number_dig
                boleto_cnab_api_data.update(
                    {
                        "digito_conta_corrente": digito_conta_corrente,
                    }
                )

            # Fields used in Sicredi and Sicoob Banks
            if bank_account_id.bank_id.code_bc in ("748", "756"):
                boleto_cnab_api_data.update(
                    {
                        "byte_idt": move_line.payment_mode_id.boleto_byte_idt,
                        "posto": move_line.payment_mode_id.boleto_post,
                    }
                )

            wrapped_boleto_list.append(boleto_cnab_api_data)

        return wrapped_boleto_list

    def _check_reconcile_validity(self):
        #Override de /home/mateus/OdooDev/odoo/addons/account/models/account_move.py
        #Perform all checks on lines
        company_ids = set()
        all_accounts = []
        for line in self:
            company_ids.add(line.company_id.id)
            all_accounts.append(line.account_id)
            if (line.matched_debit_ids or line.matched_credit_ids) and line.reconciled:
                raise UserError(_('fatura id/seu número: ' + str(line.invoice_id.id) + '-' + line.invoice_id.move_name + ', Propriedade: "' + line.invoice_id.land_id.name + '", nosso número: "' + line.own_number + '"' + ' - Movimentação já reconciliada'))
        if len(company_ids) > 1:
            raise UserError(_('To reconcile the entries company should be the same for all entries.'))
        if len(set(all_accounts)) > 1:
            raise UserError(_('Entries are not from the same account.'))
        if not (all_accounts[0].reconcile or all_accounts[0].internal_type == 'liquidity'):
            raise UserError(_('Account %s (%s) does not allow reconciliation. First change the configuration of this account to allow it.') % (all_accounts[0].name, all_accounts[0].code))



