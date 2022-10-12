# Copyright 2021 - TODAY, PopSolutions
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': "Property Base",
    'summary': """
        Base Module to manage land and properties definitions
        """,
    'description': """
        Set of module to manage land property taxes and other charges
        like Water consumption, urban waste management, etc.
    """,
    'author': "PopSolutions",
    'website': "https://www.popsolutions.co",
    'category': 'Uncategorized',
    'version': '12.0.0.1.1',
    'depends': [
        'account', 'l10n_br_account_payment_order', 'mail'
    ],
    'data': [
        'views/property_land.xml',
        'views/property_land_block.xml',
        'views/property_land_lot.xml',
        'views/property_land_module.xml',
        'views/property_land_stage.xml',
        'views/property_land_type.xml',
        'views/property_land_usage.xml',
        'views/property_land_zone.xml',
        'views/account_portal_templates.xml',
        'views/menu.xml',
        'views/res_partner_views.xml',
        'views/invoice_views.xml',
        'views/wizard_views.xml',
        'security/ir.model.access.csv',
        'data/ir_cron.xml',
        'demo/demo.xml',
    ],
}
