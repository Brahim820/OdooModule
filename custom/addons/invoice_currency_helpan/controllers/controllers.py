# -*- coding: utf-8 -*-
from odoo import http

# class InvoiceCurrencyHelpan(http.Controller):
#     @http.route('/invoice_currency_helpan/invoice_currency_helpan/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/invoice_currency_helpan/invoice_currency_helpan/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('invoice_currency_helpan.listing', {
#             'root': '/invoice_currency_helpan/invoice_currency_helpan',
#             'objects': http.request.env['invoice_currency_helpan.invoice_currency_helpan'].search([]),
#         })

#     @http.route('/invoice_currency_helpan/invoice_currency_helpan/objects/<model("invoice_currency_helpan.invoice_currency_helpan"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('invoice_currency_helpan.object', {
#             'object': obj
#         })