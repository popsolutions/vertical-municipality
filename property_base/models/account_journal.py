# @ 2020 Akretion - https://popsolutions.co/ -
#   <Mateus ONunes> <mateus.2006@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html)

import os
import sys
import traceback

from odoo import _, fields, models
from odoo.exceptions import UserError, ValidationError

from odoo.addons.account_move_base_import.parser.parser import new_move_parser
import logging

logger = logging.getLogger(__name__)

class AccountJournal(models.Model):
    _inherit = "account.journal"

    def _get_moves(self, parser, result_row_list):

        #Override de /home/mateus/OdooDev/odoo/custom-addons/riviera/l10n-brazil/l10n_br_account_payment_brcobranca/models/account_journal.py.
        # Override criado apenas para fazer a validação antes através da rotina validarMovimentacoesBaixas, e depois segue o processamento normalmente
        def validarMovimentacoesBaixas():
            move_obj = self.env["account.move"]
            move_line_obj = self.env["account.move.line"]
            moves = self.env["account.move"]
            lista_erros = ''
            index = 0
            data_count = len(result_row_list)

            # Cada retorno precisa ser feito um único account.move para que o campo
            # Date tanto da account.move quanto o account.move.line tenha o mesmo
            # valor e sejam referentes a Data de Credito daquele lançamento
            # especifico.
            for result_row in self.web_progress_iter(result_row_list):
                index += 1
                logger.info("## Validando Conciliações - " + str(index) + '/' + str(data_count))

                parsed_cols = list(parser.get_move_line_vals(result_row[0]).keys())
                for col in parsed_cols:
                    if col not in move_line_obj._fields:
                        raise UserError(
                            _(
                                "Missing column! Column %s you try to import is not "
                                "present in the move line!"
                            )
                            % col
                        )

                move_vals = self.prepare_move_vals(result_row, parser)

                # O campo referente a Data de Credito no account.move é o date que
                # no account.move.line existe um related desse campo a forma de
                # obter e preencher ele por enquanto e feito da forma abaixo,
                # verificar se possível melhorar isso.
                data_credito = ""
                for row in result_row:
                    if row.get("type") == "liquidado":
                        data_credito = row.get("date")
                        break
                move_vals["date"] = data_credito

                move = move_obj.create(move_vals)
                # moves |= move

                move_store = []
                for line in result_row:
                    parser_vals = parser.get_move_line_vals(line)
                    values = self.prepare_move_line_vals(parser_vals, move)
                    move_store.append(values)
                move_line_obj.with_context(check_move_validity=False).create(move_store)

                for line in move.line_ids:
                    if line.invoice_id:
                        line_to_reconcile = move_line_obj.search(
                            [
                                ("own_number", "=", line.ref),
                                ("invoice_id", "=", line.invoice_id.id),
                            ]
                        )

                        # Conciliação Automatica entre a Linha da Fatura e a Linha criada
                        if self.return_auto_reconcile:
                            try:
                                if line_to_reconcile:
                                    (line + line_to_reconcile)._check_reconcile_validity()
                            except Exception as e:
                                try:
                                    lista_erros += '\n' + e.name
                                except:
                                    lista_erros += '\n' + str(e)

            if (lista_erros != ''):
                raise UserError(_('Foram encontrados os seguintes erros na validação de reconciliação:\n' + lista_erros))

        validarMovimentacoesBaixas()
        res = super()._get_moves(parser, result_row_list)
        return res
