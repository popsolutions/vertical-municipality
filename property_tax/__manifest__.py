# Copyright 2021 - TODAY, PopSolutions
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

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
    'category': 'Uncategorized',
    'version': '12.0.0.1.0',
    'depends': [
        'property_base'
    ],
    'data': [
        'views/property_land_type.xml',
        'views/property_land.xml',
        'views/property_tax_views.xml',
        'views/property_land_contribution_rule.xml',
        'views/res_config_settings_views.xml',
        'views/wizard_views.xml',
        'security/ir.model.access.csv',
        'security/property_land_contribution_rule_occupation_rate.xml',
        'security/property_land_contribution_rule.xml',
        'data/products.xml',
        'data/ir_cron.xml',
    ],
}
