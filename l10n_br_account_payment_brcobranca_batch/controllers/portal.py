import base64
import io
from typing import List
from odoo import http, _
import json
from odoo.http import request
from odoo.addons.web.controllers.main import ReportController
# from PyPDF2 import PdfFileReader, PdfFileWriter
import PyPDF2.generic as pdf_generic
from pikepdf import Pdf, Page, Rectangle
import pikepdf

import logging

logger = logging.getLogger(__name__)

# pdfDirName = '/tmp/odoo_pdfs_boleto_verso/'
pdfDirName = '/var/lib/odoo/.local/share/Odoo/boleto_verso/'

class ReportControllerInherited(ReportController):
    _name = 'ReportControllerInherited'

    @http.route([
        '/report/<converter>/<reportname>',
        '/report/<converter>/<reportname>/<docids>',
    ], type='http', auth='user', website=True)
    def report_routes(self, reportname, docids=None, converter=None, **data):
        # account_invoice = request.env['account.invoice'].sudo().search([('id', '=', docids)])
        # return super().report_routes(reportname, docids, converter, **data)

        if (reportname != 'l10n_br_account_payment_brcobranca_batch.report_invoice_boleto_verso'):
            return super().report_routes(reportname, docids, converter, **data)
        else:
            res = process_boleto_frente_verso(docids)
            return res


def process_boleto_frente_verso(docids, saveToLocalServer = False, return_ir_attachment = False):
    report = request.env['ir.actions.report']._get_report_from_name('l10n_br_account_payment_brcobranca_batch.report_invoice_boleto_verso')
    context = dict(request.env.context)

    if docids and (not isinstance(docids, list)):
        docids = [int(i) for i in docids.split(',')]

    pdfVersoBoleto = report.with_context(context).sudo().render_qweb_pdf(docids)

    # pdfhttpheaders = [('Content-Type', 'application/pdf'), ('Content-Length', len(pdfVersoBoleto))]
    # jpdfres = request.make_response(pdfVersoBoleto, headers=pdfhttpheaders)
    # return jpdfres

    ###################################
    account_invoice = request.env['account.invoice'].sudo().search([('id', 'in', docids)])

    pdfBoleto = account_invoice.gera_boleto_pdf_multi()

    # Join PDFs
    jpdf = join_two_pdf([pdfBoleto, base64.b64encode(pdfVersoBoleto[0])], docids, saveToLocalServer)

    if saveToLocalServer:
        return

    if return_ir_attachment:
        ir_attachment = request.env["ir.attachment"].create(
            {
                "name": 'teste.pdf',
                "datas_fname": 'teste.pdf',
                "res_model": account_invoice._name,
                "res_id": account_invoice.id,
                "datas": base64.b64encode(jpdf),
                "mimetype": "application/pdf",
                "type": "binary",
            }
        )
        return ir_attachment

    pdfhttpheaders = [('Content-Type', 'application/pdf'), ('Content-Length', len(jpdf))]
    jpdfres = request.make_response(jpdf, headers=pdfhttpheaders)

    return jpdfres

def join_two_pdf(pdf_chunks: List[bytes], docids, saveToLocalServer) -> bytes:
    result_pdf = Pdf.new()

    stream_boleto = io.BytesIO(initial_bytes=base64.b64decode(pdf_chunks[0]))
    pdfBoleto = Pdf.open(stream_boleto)

    stream_verso = io.BytesIO(initial_bytes=base64.b64decode(pdf_chunks[1]))
    pdfVerso = Pdf.open(stream_verso)

    if len(pdfBoleto.pages) * 2 != len(pdfVerso.pages):
        raise Exception('PDFs(Boleto e verso do boleto) o número de páginas está incompatível.')

    pageNum = 0
    while pageNum < len(pdfBoleto.pages):
        pageFatura = pageNum * 2
        page_Boleto = Page(pdfBoleto.pages[pageNum])
        page_Fatura = Page(pdfVerso.pages[pageFatura])
        page_Verso = Page(pdfVerso.pages[pageFatura + 1])

        # page_Boleto.cropbox = Rectangle(0, 395, page_Boleto.width, page_Boleto.height)
        page_Boleto.cropbox = [0, 0, 595, 395]
        page_Fatura.add_overlay(page_Boleto, Rectangle(0, 0, 595, 395)) # Do boleto na fatura

        if saveToLocalServer:
            account_invoice = request.env['account.invoice'].sudo().search([('id', '=', docids[pageNum])])
            pdfFileName = str(account_invoice.id) + '-' + account_invoice.land_id.display_name + '-' + account_invoice.partner_id.name

            pdfFileName = pdfDirName + pdfFileName.replace('/', '') + '.pdf'

            pdfToSave = Pdf.new()
            pdfToSave.pages.append(page_Fatura)
            pdfToSave.pages.append(page_Verso)

            no_extracting = pikepdf.Permissions(extract=False)
            pdfToSave.save(pdfFileName, encryption=pikepdf.Encryption(user=account_invoice.partner_id.cnpj_cpf[0:4], owner="user", allow=no_extracting))

            logger.info('Arquivo pdf (' + str(pageNum) + '/' + str(len(pdfBoleto.pages)) + ') Criado em "' + pdfFileName + '"')

        else:
            result_pdf.pages.append(page_Fatura)
            result_pdf.pages.append(page_Verso)

        pageNum += 1

    if saveToLocalServer:
        return True
    else:
        # Writes all bytes to bytes-stream
        response_bytes_stream = io.BytesIO()

        if len(docids) == 1:
            #Se o pdf de retorno contém apenas 1 fatura, vou colocar a senha, caso contrário (Contém várias faturas), deixarei sem senha
            account_invoice = request.env['account.invoice'].sudo().search([('id', '=', docids[0])])
            no_extracting = pikepdf.Permissions(extract=False)
            response_bytes_stream = io.BytesIO()
            result_pdf.save(response_bytes_stream,
                            encryption=pikepdf.Encryption(user=account_invoice.partner_id.cnpj_cpf[0:4], owner="user",
                                                          allow=no_extracting))
        else:
            result_pdf.save(response_bytes_stream)

        return response_bytes_stream.getvalue()

#pdfBoleto.resolvedObjects


