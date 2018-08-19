# -*- coding: utf-8 -*-
from openerp import http

# class InvoiceHelpan(http.Controller):
#     @http.route('/invoice_helpan/invoice_helpan/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/invoice_helpan/invoice_helpan/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('invoice_helpan.listing', {
#             'root': '/invoice_helpan/invoice_helpan',
#             'objects': http.request.env['invoice_helpan.invoice_helpan'].search([]),
#         })

#     @http.route('/invoice_helpan/invoice_helpan/objects/<model("invoice_helpan.invoice_helpan"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('invoice_helpan.object', {
#             'object': obj
#         })