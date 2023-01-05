# -*- coding: utf-8 -*-
{
    'name': "Property Water Catchment",
    'summary': """
        Module to charge the Water Consumption Catchment on land properties
        """,
    'description': """
        Module to charge the Water Consumption Catchment on land properties.
    """,
    'author': "PopSolutions",
    'website': "https://www.popsolutions.co",
    'category': 'Uncategorized',
    'version': '12.0.0.1.1',
    'depends': ['property_base', 'property_water_consumption'],
    'data': [
        'data/products.xml',
        'views/property_water_catchment_monthly_rate_view_form.xml',
        'views/property_water_catchment.xml',
        'views/wizard_views.xml',
        'views/property_land.xml',
        'views/menu.xml',
        'security/ir.model.access.csv'
    ],
}
