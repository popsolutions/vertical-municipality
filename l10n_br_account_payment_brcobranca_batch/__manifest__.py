# Copyright 2022 PopSolutions, mateusonunesc@gmail.com
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'L10n Br Account Payment Brcobranca Batch',
    'summary': """
        l10n_br_account_payment_brcobranca_batch""",
    'version': '12.0.1.0.1',
    'license': 'AGPL-3',
    'author': 'PopSolutions, mateusonunesc@gmail.com,Odoo Community Association (OCA)',
    'website': 'https://www.popsolutions.co',
    'depends': ['account', 'l10n_br_account_payment_order', 'web'
    ],
    'data': [
        'reports/boleto_verso.xml',
        'reports/boleto_frente.xml',
    ],
    'demo': [
    ],
}
