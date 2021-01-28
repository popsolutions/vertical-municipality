# -*- coding: utf-8 -*-
{
    'name': "Property Tax",

    'summary': """
        Module to charge the Tax on land properties
        """,

    'description': """
        With this module you can process the Taxes for land property.
        This module will add invoice lines for this concept when the
        cron job is executed.
    """,

    'author': "PopSolutions",
    'website': "https://www.popsolutions.co",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['property_base'],

    # always loaded
    'data': [
        'views/property_tax_views.xml',
        'security/ir.model.access.csv',
        'data/products.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        # 'demo/demo.xml',
    ],
}
