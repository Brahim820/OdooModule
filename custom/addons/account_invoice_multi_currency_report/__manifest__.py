# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Account invoice multi-currency report',
    'version': '1.0',
    'author': 'gordan.cuic@gmail.com',
    'website': 'odoosee.com',
    'category': 'Invoicing & Payments',
    'depends': ['account'],
    'demo': [],
    'description': """

Multi-currrency in invoice report
=================================
When invoice currency is different than the one defined in company settings,
this module will:

* show product's unit price in company's default currency
* create currency conversion rate specification below invoice lines

Setup
-----
For this module to work correctly, make sure you have properly defined
conversion rates. To view and edit rates:

* Go to Accounting - Configuration - Multi-Currencies - Currencies
* Find currency (other than company default)
* In form, click "View Rates" button and modify existing or create new rate

When entering rate, note that it must be amount that represents this currency
expressed as default company's currency. I.e. if EUR is default company
currency, USD rate would be 1.18
""",
    'data': [
        'views/report_invoice.xml',
    ],
    'installable': True,
    'auto_install': False,
}
