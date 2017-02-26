# -*- coding: utf-8 -*-

from odoo import models, fields, api

# class helpan_produs(models.Model):
#     _name = 'helpan_produs.helpan_produs'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         self.value2 = float(self.value) / 100

class account_journal(osv.osv):
    _name = "account.journal"
    _inherit = "account.journal"

    _columns = {
        "receipts_sequence_id": fields.many2one(
            'ir.sequence', 'Voucher Sequence',
            help="""This field contains the information related to the
            numbering of the vouchers (receipts) of this journal."""),
    }

class product_template(osv.osv):
    _name = "product.template"
    _inherit = "product.template"

    _columns = {
        "dosar_id": fields.int('Dosar ID',help="""Identificator de Dosar pentru reper."""),
    }
