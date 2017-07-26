# -*- coding: utf-8 -*-
#from odoo import http

# class HelpanProdus(http.Controller):
#     @http.route('/helpan_produs/helpan_produs/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/helpan_produs/helpan_produs/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('helpan_produs.listing', {
#             'root': '/helpan_produs/helpan_produs',
#             'objects': http.request.env['helpan_produs.helpan_produs'].search([]),
#         })

#     @http.route('/helpan_produs/helpan_produs/objects/<model("helpan_produs.helpan_produs"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('helpan_produs.object', {
#             'object': obj
#         })