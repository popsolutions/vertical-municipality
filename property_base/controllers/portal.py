# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import base64

from odoo import http, _
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
from odoo.addons.payment.controllers.portal import PaymentProcessing
from odoo.exceptions import AccessError, MissingError
from odoo.http import request


class PortalAccount(CustomerPortal):

    @http.route(['/my/invoices/<int:invoice_id>'], type='http', auth="public", website=True)
    def portal_my_invoice_detail(self, invoice_id, access_token=None, report_type=None, download=False, **kw):
        if '/bank_slip' in access_token:
            invoice_sudo = self._document_check_access('account.invoice', invoice_id, access_token)
            invoice_sudo.gera_boleto_pdf()
            pdf = invoice_sudo.file_pdf_id.datas
            pdf = base64.b64decode(pdf)
            pdfhttpheaders = [('Content-Type', 'application/pdf'), ('Content-Length', len(pdf))]
            return request.make_response(pdf, headers=pdfhttpheaders)
        else:
            return super().portal_my_invoice_detail(invoice_id, access_token, report_type, download, **kw)

