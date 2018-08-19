# -*- coding: utf-8 -*-
{
    "name": "Invoice Pricelist",
    "version": "10.0.0.1.1",
    'license': 'OPL-1',
    'author': 'Josef Kaser, pragmasoft',
    'website': 'https://www.pragmasoft.de',
    'support': 'info@pragmasoft.de',
    'price': '19',
    'currency': 'EUR',
    "summary": """
    Set pricelist on customer invoice.
    """,
    "description": """
Invoice Pricelist
=================
Set a pricelist on the customer invoice. Recalculates the line item prices and sets the invoice currency when the pricelist is changed.
    """,
    "images": [
        "images/main_screenshot.png",
    ],
    "category": "Invoicing",
    "depends": [
        "base",
        "account_accountant",
    ],
    "data": [
        "views/invoice.xml",
    ],
    "installable": True,
    "auto_install": False,
}
