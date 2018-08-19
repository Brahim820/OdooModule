# -*- coding: utf-8 -*-
{
    'name': "helpan_teava",

    'summary': """
        Care e situatia la teava din firma ? Denumire ( teava inox 40x40x2 )  DimensiuniX (5000mm), DimensiuniY (0mm), DenumireCompleta, Locatie, NrBuc(5) ,Observatie """,

    'description': """
        Este un pas intermediar pentru gestiunea tevilor si barilor din gestiune
    """,

    'author': "Bogdan Hurezeanu",
    'website': "http://www.helpan.ro",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Inventar',
    'version': '0.3',

    # any module necessary for this one to work correctly
    'depends': ['base','mail'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}