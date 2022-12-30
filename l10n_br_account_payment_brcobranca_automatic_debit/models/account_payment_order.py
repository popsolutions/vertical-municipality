# Copyright 2022 popsolutions
# @author Mateus ONunes <mateus.2006@gmail.com>
# Copyright 2022 popsolutions
# @author Marcos Mendez <mendez.foto@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging

from odoo import _, fields, models

logger = logging.getLogger(__name__)

class PaymentOrder(models.Model):
    _inherit = "account.payment.order"

    def _get_brcobranca_remessa(self, bank_brcobranca, remessa_values, cnab_type):
        #Esta rotina basicamente insere na linha do arquivo de remessa as informações de débito automático para o banco bradesco
        #Manual em https://banco.bradesco/assets/pessoajuridica/pdf/4008-524-0121-layout-cobranca-versao-portugues.pdf

        remessa = super(PaymentOrder, self)._get_brcobranca_remessa(bank_brcobranca, remessa_values, cnab_type)
        index = 1
        fileStr = ''
        remessaLines = remessa.decode("utf-8").split('\n')
        remessaLen = len(remessaLines)

        for line in remessaLines:

            def lineSubst(strSubst: str, startCol: int, endCol: int):
                nonlocal line
                line = line[0:startCol - 1] + strSubst + line[endCol:]

            if index == 1:
                fileStr = line + '\n'
            elif index + 1 == remessaLen:
                fileStr += line + '\n'
            elif index + 1 > remessaLen:
                break #última linha em branco
            else:
                nossoNumero = line[71:81]

                query = """
                SELECT b.bra_number agencia_numero,
                       b.bra_number_dig agencia_digito,
                       b.acc_number conta_numero,
                       b.acc_number_dig conta_digito,
                       b.bank_account_type       
                  FROM res_partner_bank b
                 WHERE partner_id = (select apl.partner_id  
                                       from account_payment_line apl
                                      where apl.own_number = '""" + str(int(nossoNumero)) + """'
                                        and apl.order_id = """ + str(self.id) + """)
                 order by id desc
                 limit 1"""

                self.env.cr.execute(query)
                bankAccountData = self.env.cr.fetchall()

                if len(bankAccountData) == 1:
                    #Inserir na linha as informações da conta corrente do cliente
                    bankAccountDataLine = bankAccountData[0]

                    razaoContaCorrente = ''

                    if bankAccountDataLine[4] in ('01', '02'): #01 -> Conta corrente individual, 02 -> Conta poupança individual
                        razaoContaCorrente = '00705'
                    elif bankAccountDataLine[4] in ('11', '12'): #11 -> Conta corrente conjunta, 12 -> Conta poupança conjunta
                        razaoContaCorrente = '00105'
                    else:
                        raise Exception('Tipo de Conta desconhecida')

                    def getValue(index: int, size:int):
                        return bankAccountDataLine[index].rjust(size, '0')

                    checkingAccount = getValue(0, 5)  # posição 02 a 06 - Agência
                    checkingAccount += getValue(1, 1) # posição 07 a 07 - Dígito da Agência
                    checkingAccount += razaoContaCorrente # posição 08 a 12 - Razão da Conta corrente
                    checkingAccount += getValue(2, 7) # posição 13 a 19 - Conta corrente
                    checkingAccount += getValue(3, 1) # posição 20 a 20 - Dígito da Conta corrente

                    lineSubst(checkingAccount, 2, 20)
                    lineSubst(' ', 94, 94)   # 094 a 094 - Condições de Registro para Débito Automático
                                             # - Quando igual a “N” e os dados do débito estiverem incorretos, rejeita o registro na cobrança e não
                                             # emite boleto de cobrança.
                                             # - Quando diferente de “N” e os dados do débito estiverem incorretos, registra na cobrança e emite boleto de cobrança. Nessa condição, não ocorrerá o agendamento do débito
                    lineSubst('237', 63, 65)  # #63, 65 - Código do Banco a ser debitado na Câmara de Compensação
                fileStr += line + '\n'

            index += 1

        remessaFileStr = bytes(fileStr, "UTF-8")
        return remessaFileStr
