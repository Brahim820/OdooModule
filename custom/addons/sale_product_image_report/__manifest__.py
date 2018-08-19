# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Sale order HTML specification report',
    'version': '1.0',
    'author': 'gordan.cuic@gmail.com',
    'website': 'neembus.io',
    'category': 'Sales',
    'depends': ['sale'],
    'demo': [],
    'description': """

This module adds product specification ot sale order report
===========================================================

Specification is added to sale order report as additional page. It contains
Product name, product HTML description and product images.


Product Images
--------------

Each product can have as many images as needed. Add images to
"Additional images" tab in Product form. Make sure to use image sizes and
ratios that fit nicely to specification. Considering report page width, image
width will be resized to match 40% of page width.

If using Product Variants, note that images are related to Product itself
(product_template), not Product Variant (product_product).


Product HTML description
------------------------

Upon install, each product will have new "Template description HTML" tab, where
you can edit description using HTML.

When using Product Variants, there is additional HTML description field related
to Product Variant (product_product). Field is located in
"Variant description HTML" tab.


Printing Sale Order (Quotation) specification
---------------------------------------------
To print Quotation or Sale order with product specification, you need to click
"Print with spec" button. You will get standard Odoo Sale order report with
additional page that contains specification.


Organizing description
----------------------
Both Product and Product Variant have their own HTML description field. So when
printing Quotation or Sale order, this module first looks for HTML description
in Product Variant. If none is found, then will look for related Product HTML
description. If none is found, then will use product name.
""",
    'data': [
        'views/sale_order_view.xml',
        'views/sale_order_report.xml',
    ],
    'installable': True,
    'auto_install': False,
}
