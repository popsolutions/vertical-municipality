# -*- coding: utf-8 -*-
{
    'name': "Property Base",

    'summary': """
        Base Module to manage land and properties definitions
        """,

    'description': """
        Set of Odoo12 module to manage land property taxes and other charges
        like Water consumption, urban waste management, etc.
    """,

    'author': "PopSolutions",
    'website': "https://www.popsolutions.co",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['account'],

    # always loaded
    'data': [
        'views/land_views.xml',
        'views/res_partner_views.xml',
        'views/invoice_views.xml',
        'views/wizard_views.xml',
        'security/ir.model.access.csv',
        'data/ir_cron.xml',
        # 'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        # 'demo/demo.xml',
    ],
}
