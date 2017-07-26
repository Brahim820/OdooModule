# -*- coding: utf-8 -*-

from openerp import models, fields, api

class purchase_order_line(osv.osv):
    _name='purchase.order.line'
    _inherit='purchase.order.line'
    _columns={
            'dosarId': fields.Many2one('helpan_dosar', 'Dosar',readonly=False),
             }

class account_invoice_line(osv.osv):
    _name='account.invoice.line'
    _inherit='account.invoice.line'
    _columns={
            'dosarId': fields.Many2one('helpan_dosar', 'Dosar', readonly=False),
                }

class helpan_dosar(models.Model):
    _name = 'helpan_dosar.helpan_dosar'

    _rec_name = "dosarID"
    _order = 'dosarID DESC'
    name = fields.Char()
    dosarID=fields.Integer(string="Dosar ID",help="Identificare Dosar")
    DataCrearii=fields.Date()
    initiator=fields.Char()

#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         self.value2 = float(self.value) / 100