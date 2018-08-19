# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Migration from version 9 to version 10',
    'version': '1.0',
    'author': 'gordan.cuic@gmail.com',
    'website': 'neembus.io',
    'category': 'Administration',
    'depends': ['base'],
    'demo': [],
    'description': """

This module migrates data from database in version 9 to 10
==========================================================

Install this module to empty database version 10. Then use data migrate model
to initialize data transfer from database ver 9 to database you are currently
logged in (version 10).


Data migrate
------------
Create record. You will need to enter postgres server IP, port, username,
password and database name in order to connect to v9 database.


Models that can be migrated
---------------------------
- Company data
- Products
- Partners
- Users

Changes
-------
2017-08-25: Initial deploy. Installable module. Customized migrate process for
HELPAN CO, Romaina. Migrates Currencies, Countries, States, Companies, Users,
Partner titles, Partners, Unit of measure categories, Units of measure (distinct
on name) and Products.

""",
    'data': [
        'security/data_migrate_security.xml',
        'security/ir.model.access.csv',
        'views/data_migrate_view.xml',
        'data/data_migrate_data.xml',
    ],
    'installable': True,
    'auto_install': False,
}
