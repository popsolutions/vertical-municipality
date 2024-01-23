# Mateus ONunes - mateus.2006@gmail.com
from odoo import _, fields, models, api
from odoo.exceptions import Warning as UserError

logger = logging.getLogger(__name__)

class AccountPayment(models.Model):
    #/odoo/addons/account/models/account_payment.py
    _inherit = "account.payment"

    accumulated_invoice_id = fields.Many2one(
        comodel_name='account.invoice', string="Acumulado na fatura",
        ondelete='restrict')
