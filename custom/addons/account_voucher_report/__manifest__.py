# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2016 Serpent Consulting Services Pvt. Ltd.
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{
    "name": "Account Voucher Report",
    "version": "10.0.1.0.1",
    "license": 'AGPL-3',
    "author": "Serpent Consulting Services Pvt. Ltd.",
    'maintainer': 'Serpent Consulting Services Pvt. Ltd.',
    'summary': """
    Print payment receipt
    Payment receipt report
    Print voucher
    print sales receipt
    print purchase receipt
    print customer receipt
    print supplier payment report
    payment report
""",
    "website": "http://www.serpentcs.com",
    "description": """
    Print payment receipt
    Payment receipt report
    Print voucher
    print sales receipt
    print purchase receipt
    print customer receipt
    print supplier payment report
    payment report
""",
    'depends': ['account_accountant','helpan_dosar'],
    'data': ['views/account_payment_view.xml',
             'report/account_payment_report.xml',
            'views/account_invoice_view.xml',
             'views/report_configuration_view.xml'],
    'category': 'Accounting & Finance',
    'images': ['static/description/image.png'],
    'installable': True,
    'price': 12,
    'currency': 'EUR',
    'application': False,
    'auto_install': False,
}
