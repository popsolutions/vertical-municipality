# Copyright 2022 PopSolutions
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Property Ga Maintenance',
    'summary': """
        This modules creates features to charge a monthly invoice of Green Area Maintenance for the vertical municipality system.""",
    'version': '12.0.1.0.0',
    'license': 'AGPL-3',
    'author': 'PopSolutions,Odoo Community Association (OCA)',
    'website': 'popsolutions.co',
    'depends': [
        'property_base'
    ],
    'data': [
        'views/property_ga_tax.xml',
        'views/wizard_views.xml',
        'views/property_land.xml',
        'data/products.xml',
        'security/property_ga_tax.xml'
    ],
    'demo': [
    ],
}
