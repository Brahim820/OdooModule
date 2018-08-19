# -*- coding: utf-8 -*-
{
    'name': "invoice_helpan",

    'summary': """
        Cum Adaug Chitanta!""",

    'description': """
        test
    """,

    'author': "IDEYAs",
    'website': "http://www.ideya.ro",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/master/openerp/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base_setup', 'report'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
        'report/invoice_view.xml',
        'report/invoice_report.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}