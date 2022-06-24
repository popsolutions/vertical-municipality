# Copyright 2022 PopSolutions, mateusonunesc@gmail.com
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models, _
import base64
import logging
from odoo.exceptions import Warning as UserError
import json
import tempfile
import requests
from ..constants.br_cobranca import get_brcobranca_api_url
from ..controllers.portal import *
import datetime
logger = logging.getLogger(__name__)

class AccountInvoice(models.Model):

    _inherit = 'account.invoice'

    def gera_boleto_pdf_multi(self):
        boletos = None

        for account_invoice in self:
            file_pdf = account_invoice.file_boleto_pdf_id
            account_invoice.file_boleto_pdf_id = False
            file_pdf.unlink()

            receivable_ids = account_invoice.mapped("financial_move_line_ids")

            boleto = receivable_ids.send_payment()
            if not boleto:
                raise UserError(
                    _(
                        "It is not possible generated boletos\n"
                        "Make sure the Invoice are in Confirm state and "
                        "Payment Mode method are CNAB."
                    )
                )

            if (boletos == None):
                boletos = boleto
            else:
                boletos.extend(boleto)

        pdf_string = self.get_brcobranca_boleto(boletos)
        pdf_string = base64.b64encode(pdf_string)
        return pdf_string


    def get_brcobranca_boleto(self, boletos):

        content = json.dumps(boletos)
        f = open(tempfile.mktemp(), "w")
        f.write(content)
        f.close()
        files = {"data": open(f.name, "rb")}

        # brcobranca_api_url = self.env['ir.config_parameter'].get_param('BRCOBRANCA_API_URL')
        brcobranca_api_url = get_brcobranca_api_url()
        brcobranca_service_url = brcobranca_api_url + "/api/boleto/multi"
        logger.info(
            "Connecting to %s to get Boletos",
            brcobranca_service_url,
        )
        res = requests.post(brcobranca_service_url, data={"type": "pdf"}, files=files)

        if str(res.status_code)[0] == "2":
            pdf_string = res.content
        else:
            raise UserError(res.text.encode("utf-8"))

        return pdf_string

    def boletoData(self):
        def formatValue(value, decimais=0):
            formatMask = '{:,.' + str(decimais) + 'f}'
            res = formatMask.format(value).replace(',', '.')
            return res

        invoice = self[0]

        consumptionJson = {}

        sql = '''
               select anomes_text(anomes(ail.create_date), 3) mesReferencia,
                      pwc."date" readDate,
                      pwc."date" + 30 readNext,
                      pwc.last_read,
                      pwc.current_read,
                      pwc.consumption,
                      anomes(ail.date_due) anomes_invoice
                 from account_invoice ail 
                        inner join property_water_consumption pwc 
                                on pwc.land_id = ail.land_id 
                               and pwc."date" <= ail.date_due
                               and pwc.state = 'processed'
                where ail.id = ''' + str(invoice.id) + ''' 
                order by pwc."date" desc
                limit 1'''

        self.env.cr.execute(sql)
        datas = self.env.cr.fetchall()

        if len(datas) == 1:
            data = datas[0]

            exibir_mensagem_aumento_agua = data[6] == 202206 # Esta mensagem será exibida apenas para vencimento em 2022/06

            readDate = data[1].strftime('%d/%m/%Y')
            readNext = data[2].strftime('%d/%m/%Y')

            consumptionJson.update({
                'mesReferencia': data[0],
                'readDate': readDate,
                'readNext': readNext,
                'last_read': data[3],
                'current_read': data[4],
                'consumption': data[5],
                'economias': 'X',
                'exibir_mensagem_aumento_agua': exibir_mensagem_aumento_agua
            })
        else:
            consumptionJson.update({
                'mesReferencia': '',
                'readDate': '',
                'readNext': '',
                'last_read': '',
                'current_read': '',
                'consumption': '',
                'economias': 'X',
                'exibir_mensagem_aumento_agua': False
            })

        query = '''
select anomes_text(anomes(pwc."date"), 2) anomes,
       pwc.consumption
  from account_invoice ail inner join property_water_consumption pwc on pwc.land_id = ail.land_id
 where ail.id = ''' + str(invoice.id) + '''
   and anomes(pwc."date") between anomes_inc(anomes(ail.date_due), -13) and anomes_inc(anomes(ail.date_due), -2)
 order by pwc."date" desc        
        '''

        #Resolvendo Histórico de consumo(consumptionJson) [INICIO]

        self.env.cr.execute(query)
        consumptions = self.env.cr.fetchall()

        consumptionJson_Coluna1 = []
        consumptionJson_Coluna2 = []
        consumptionJsonHst = []
        somaM3 = 0
        qtdeItens = 0;

        for index, consumption in enumerate(consumptions):
            item = {
                    'anomes': consumption[0],
                    'consumption': consumption[1]
                }

            if consumption[1]:
                somaM3 += consumption[1]

            qtdeItens += 1

            if index <= 5:
                consumptionJson_Coluna1.append(item)
            else:
                consumptionJson_Coluna2.append(item)

        for index, consumptionJson_Coluna1_Item in enumerate(consumptionJson_Coluna1):
            anomes_coluna2 = ''
            consumption_coluna2 = ''

            if len(consumptionJson_Coluna2) > index:
                anomes_coluna2 = consumptionJson_Coluna2[index]['anomes']
                consumption_coluna2 = consumptionJson_Coluna2[index]['consumption']

            consumptionJsonHst.append({
                    'anomes_coluna1': consumptionJson_Coluna1_Item['anomes'],
                    'consumption_coluna1': consumptionJson_Coluna1_Item['consumption'],
                    'anomes_coluna2': anomes_coluna2,
                    'consumption_coluna2': consumption_coluna2
            })

        mediam3 = 0

        if (qtdeItens > 0):
            mediam3 = somaM3 / qtdeItens

        mesiam3Str = formatValue(mediam3)
        somaM3Str = formatValue(somaM3)

        consumptionJson.update({'consumptionJsonHst': consumptionJsonHst,
                           'somam3': str(somaM3Str) + ' m3',
                           'mediam3formatated': str(mesiam3Str) + ' m³/mês',
                           'mediam3': str(mesiam3Str)
        })

        # Resolvendo Histórico de consumo(consumptionJson) [FIM]


        #Resolvendo account_invoice_line (Agrupado) [INICIO]
        query = '''
select ail.name,
       sum(ail.price_total) price_total,
       ail.anomes_vencimento,
       ail.product_id
  from account_invoice_line ail  
 where ail.invoice_id = ''' + str(invoice.id) + '''
 group by ail.name, ail.product_id, ail.anomes_vencimento
 order by ail.anomes_vencimento desc 
'''

        self.env.cr.execute(query)
        account_invoice_lines = self.env.cr.fetchall()
        current_anomes = account_invoice_lines[0][2]
        account_invoice_lineJson = []

        for account_invoice_line in account_invoice_lines:
            if account_invoice_line[2] != current_anomes:
                account_invoice_lineJson.append({'name': '', 'price_total': ''}) # Criar linha em branco para fazer quebra de linha pois mudou ano/mês

            account_invoice_lineJson.append(
                {'name': account_invoice_line[0], 'price_total': formatValue(account_invoice_line[1], 2)})

            current_anomes = account_invoice_line[2]

        consumptionJson.update({'account_invoice_line': account_invoice_lineJson})
        #Resolvendo account_invoice_line (Agrupado) [FIM]


        # Resolvendo lotes que compoeem a fatura [INICIO]
        query = '''
select string_agg(sumary_text1, ', ') unified_lots, sum(amount) amount
  from account_invoice_land_uni_summary(''' + str(invoice.id) + ''')  
        '''

        self.env.cr.execute(query)
        unified_lotsRows = self.env.cr.fetchall()
        unified_lots = unified_lotsRows[0][0]
        unified_amount = unified_lotsRows[0][1]

        unified_lotsRows = []
        unified_lotsRows.append(
            {'unified_lots': unified_lots, 'unified_amount': unified_amount})

        consumptionJson.update({'unified_lots': unified_lotsRows})
        # Resolvendo lotes que compoeem a fatura [INICIO]

        res = consumptionJson
        return res

    @api.model
    def action_account_invoice_gerar_boleto_servidor(self):
        idsErro = []
        for invoice in self.web_progress_iter(self):
            try:
                process_boleto_frente_verso(str(invoice.id), True)
            except Exception as e:
                msgErro = str(invoice.id) + '-' + str(e.name) + '\n'
                idsErro.append(msgErro)
                logger.info('')
                logger.info('Falha ao gerar pdf de Boleto/Verso para id:"' + msgErro)
                logger.info('Continuando processamento...')

        if idsErro != '':
            idsErro.insert(0, 'Os seguintes ids não foram processados:\n\n')
            # print id erros em arquivo texto
            raise UserError(tuple(idsErro))

        return
