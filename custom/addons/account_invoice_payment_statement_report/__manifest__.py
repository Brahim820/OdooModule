# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Invoice report with payments specification statement',
    'version': '1.0',
    'author': 'gordan.cuic@gmail.com',
    'website': 'odoosee.com',
    'category': 'Invoicing & Payments',
    'depends': ['account'],
    'demo': [],
    'description': """

Payments specification statement
================================
This module adds payments specification to invoice report, on a separate page.

    Wouldn't it be cool to send your customer debt specification with invoice
    to remind him on unpaid invoices?

Each customer's invoice can be printed (.pdf) with additional page that will
hold information on unpaid invoices (if any). All unreconciled receivable
entries will be specified with number, reference, date, due, date, amounts
invoiced, paid and currently open.

If customer has paid all his or hers invoices, statement will not be printed.

Information in payments specification coresponds with "Due payments" report
which can be accessed from "Customers - Print - Due payments" in tree view.
""",
    'data': [
        'views/invoice_view.xml',
        'views/report_invoice.xml',
    ],
    'installable': True,
    'auto_install': False,
}
