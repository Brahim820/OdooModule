# -*- coding: utf-8 -*-
{
    'name': "helpan_dosar",

    'summary': """
        Afisare dosare ale lui helpan XXX - sincronizare cu serverul de web""",

    'description': """
       Afurisit el de manifest
    """,

    'author': "Helpan",
    'website': "http://www.helpan.ro",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Invatare',
    'version': '0.43',

    # any module necessary for this one to work correctly
    'depends': ['base'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml', 
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}