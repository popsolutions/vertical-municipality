# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import base64

from odoo import http, _
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
from odoo.addons.payment.controllers.portal import PaymentProcessing
from odoo.exceptions import AccessError, MissingError
from odoo.http import request
from ...l10n_br_account_payment_brcobranca_batch.controllers.portal import *



class PortalAccount(CustomerPortal):

    @http.route(['/my/invoices/<int:invoice_id>'], type='http', auth="public", website=True)
    def portal_my_invoice_detail(self, invoice_id, access_token=None, report_type=None, download=False, **kw):
        if '/bank_slip' in access_token:
            res = process_boleto_frente_verso(str(invoice_id))
            return res
        elif report_type in ('html', 'pdf', 'text'):
            try:
                invoice_sudo = self._document_check_access('account.invoice', invoice_id, access_token)
            except (AccessError, MissingError):
                return request.redirect('/my')

            return self._show_report(model=invoice_sudo, report_type='html',
                                     report_ref='l10n_br_account_payment_brcobranca_batch.report_invoice_boleto_verso_report_id',
                                     download=download)
        else:
            return super().portal_my_invoice_detail(invoice_id, access_token, report_type, download, **kw)
