# -*- coding: utf-8 -*-
{
    'name': "Property Water Consumption",
    'summary': """
        Module to charge the Water Consumption on land properties
        """,
    'description': """
        With this module you can process the Water Consumption for land property.
        This module will add invoice lines for this concept when the
        cron job is executed.
    """,
    'author': "PopSolutions",
    'website': "https://www.popsolutions.co",
    'category': 'Uncategorized',
    'version': '12.0.0.1.7',
    'depends': ['property_base'],
    'data': [
        'data/products.xml',
        'views/property_land.xml',
        'views/property_water_consumption.xml',
        'views/property_water_consumption_issue.xml',
        'views/property_water_consumption_computation_parameter.xml',
        # 'views/property_land_type_water_consumption_rule.xml',
        'views/property_land_type.xml',
        'views/wizard_views.xml',
        'views/res_partner_views.xml',
        'views/menu.xml',
        'security/ir.model.access.csv',
        'security/property_land_type_water_consumption_rule.xml',
        'views/property_water_consumption_route_custom.xml',
        'views/property_water_consumption_route_lands.xml',
    ],
}
