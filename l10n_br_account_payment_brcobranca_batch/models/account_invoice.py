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

        pdf_string = self._get_brcobranca_boleto(boletos)
        pdf_string = base64.b64encode(pdf_string)
        return pdf_string

        file_name = "boleto_nf.pdf"
        file_pdf_id = self.env["ir.attachment"].create(
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

        return file_pdf_id

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