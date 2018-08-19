# -*- coding: utf-8 -*-
from openerp import http

# class HelpanTeava(http.Controller):
#     @http.route('/helpan_teava/helpan_teava/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/helpan_teava/helpan_teava/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('helpan_teava.listing', {
#             'root': '/helpan_teava/helpan_teava',
#             'objects': http.request.env['helpan_teava.helpan_teava'].search([]),
#         })

#     @http.route('/helpan_teava/helpan_teava/objects/<model("helpan_teava.helpan_teava"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('helpan_teava.object', {
#             'object': obj
#         })