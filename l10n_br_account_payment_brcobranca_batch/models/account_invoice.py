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
import os
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
select anomes_text(anomes(pwc."date"), 3) mesReferencia,
       pwc."date" readDate,
       psm.nextread_date,
       pwc.last_read,
       pwc.current_read, --index 4
       (select sum(pwc2.consumption)
          from (select distinct land_id 
                  from account_invoice_line ail
                 where ail.invoice_id = aci.id 
                   and ail.product_id = 7 /*Consumo de agua*/
               ) ail,
               property_water_consumption pwc2 
         where pwc2.land_id = ail.land_id 
           and pwc2."date" between aci.pwc_primeirodia and aci.pwc_ultimodia
           and pwc2.state = 'processed'
       ) consumption2,--index 5
       anomes(aci.date_due) anomes_invoice,
       coalesce(
       (select 1
          from account_invoice ai_venc
         where ai_venc.land_id = aci.land_id
           and anomes(ai_venc.date_due) in (anomes_due, anomes_inc(anomes_due, -1), anomes_inc(anomes_due, -2), anomes_inc(anomes_due, -3))
           and state = 'open'
           and ai_venc.id <> aci.id
         limit 1 
       ), 0) accounts_open_exists,--index 7
       psm.rate_catchment,--index 8
       psm.ar_period,
       psm.ar_ph,
       psm.ar_ph_limit,
       psm.ar_uh_color,
       psm.ar_uh_color_limit,
       psm.ar_ut_turbidity,--index 14
       psm.ar_ut_turbidity_limit,
       psm.ar_chlorine_residual,
       psm.ar_chlorine_residual_limit,
       psm.ar_fluorides,
       psm.ar_fluorides_limit, --index 19
       psm.ar_ecoli,
       psm.ar_ecoli_limit,
       pl.water_consumption_economy_qty             
  from (select aci.id,
               aci.land_id,
               aci.date_due,
               anomes(aci.date_due) anomes_due,
               anomes_primeirodia(anomes_inc(anomes(aci.date_due), -1)) pwc_primeirodia,
               anomes_ultimodia(anomes_inc(anomes(aci.date_due), -1)) pwc_ultimodia
          from account_invoice aci
         where aci.id = ''' + str(invoice.id) + '''  
       ) aci
         inner join property_water_consumption pwc 
                 on pwc.land_id = aci.land_id 
                and pwc."date" between aci.pwc_primeirodia and aci.pwc_ultimodia
                and pwc.state = 'processed'
         inner join property_land pl
                 on pl.id = aci.land_id,
      vw_property_settings_monthly_last psm
'''

        self.env.cr.execute(sql)
        datas = self.env.cr.fetchall()

        if len(datas) == 1:
            data = datas[0]

            exibir_mensagem_aumento_agua = data[6] == 202206 # Esta mensagem será exibida apenas para vencimento em 2022/06

            readDate = data[1].strftime('%d/%m/%Y')
            readNext = data[2].strftime('%d/%m/%Y')

            consumptionJson.update({
                'mesReferencia': data[0],
                'nextread_date': readDate,
                'readNext': readNext,
                'last_read': data[3],
                'current_read': data[4],
                'consumption': data[5],
                'economias': data[22],
                'exibir_mensagem_aumento_agua': exibir_mensagem_aumento_agua,
                'accounts_open_exists': data[7],
                'rate_catchment': data[8],
                'ar_period': data[9],
                'ar_ph': data[10],
                'ar_ph_limit': data[11],
                'ar_uh_color': data[12],
                'ar_uh_color_limit': data[13],
                'ar_ut_turbidity': data[14],
                'ar_ut_turbidity_limit': data[15],
                'ar_chlorine_residual': data[16],
                'ar_chlorine_residual_limit': data[17],
                'ar_fluorides': data[18],
                'ar_fluorides_limit': data[19],
                'ar_ecoli': data[20],
                'ar_ecoli_limit': data[21]
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
                'exibir_mensagem_aumento_agua': False,
                'accounts_open_exists': ''
            })

        query = '''
select anomes_text(anomes(pwc."date"), 2) anomes,
       sum(pwc.consumption) consumption
  from (select distinct 
               anomes(aci.date_due) date_due_anomes,
               ail.land_id 
          from account_invoice aci
               inner join account_invoice_line ail on ail.invoice_id = aci.id and ail.product_id = 7 /*Consumo de agua*/
         where aci.id = ''' + str(invoice.id) + '''
       ) t
       inner join property_water_consumption pwc on pwc.land_id = t.land_id
 where anomes(pwc."date") between anomes_inc(t.date_due_anomes, -13) and anomes_inc(t.date_due_anomes, -2)
 group by 1, anomes(pwc."date")
 order by anomes(pwc."date") desc  
'''

        #Resolvendo Histórico de consumo(consumptionJson) [INICIO]

        self.env.cr.execute(query)
        consumptions = self.env.cr.fetchall()

        consumptionJson_Coluna1 = []
        consumptionJson_Coluna2 = []
        consumptionJsonHst = []
        somaM3 = 0
        qtdeItens = 0

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
        if not os.path.isdir(pdfDirName):
            raise Exception('Salvar pdf no servidor - Diretório "' + pdfDirName + '" inacesssivel ou não encontrado.')

        fileErros = pdfDirName + '/erros ao gerar PDFs.txt'
        text_file = open(fileErros, 'w')
        text_file.close()

        idsErro = []

        for invoice in self.web_progress_iter(self):
            try:
                process_boleto_frente_verso(str(invoice.id), True)
            except Exception as e:
                try:
                    msgErro = str(e.name)
                except:
                    msgErro = str(e)

                msgErro = str(invoice.id) + '-' + msgErro + '\n'

                #Salvar erro no arquivo de log
                text_file = open(fileErros, 'a')
                text_file.write("%s\n" % msgErro)
                text_file.close()

                idsErro.append(msgErro)
                logger.info('')
                logger.info('Falha ao gerar pdf de Boleto/Verso para id:"' + msgErro)
                logger.info('Continuando processamento...')

        if len(idsErro) > 0:
            idsErro.insert(0, 'Os seguintes ids não foram processados:\n\n')
            raise UserError(tuple(idsErro))

        return
