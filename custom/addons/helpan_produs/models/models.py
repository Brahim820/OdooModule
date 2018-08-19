# -*- coding: utf-8 -*-

from openerp import api, fields, models, _, osv
from odoo.exceptions import UserError
import psycopg2
import logging
_logger = logging.getLogger(__name__)


class helpan_produs(models.Model):
    _name = 'helpan_produs.helpan_produs'
    _rec_name = "dosarID"
    _order = 'dosarID DESC'
    name = fields.Char()
    dosarID=fields.Integer(string="Dosar ID",help="Identificare Dosar")
    DataCrearii=fields.Date()
    initiator=fields.Char()


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
#
# class account_journal(osv.osv):
#     _name = "account.journal"
#     _inherit = "account.journal"
#
#     _columns = {
#         "receipts_sequence_id": fields.many2one(
#             'ir.sequence', 'Voucher Sequence',
#             help="""This field contains the information related to the
#             numbering of the vouchers (receipts) of this journal."""),
#     }

# class product_product(models.Model):
#     _name = "product.product"
#     _inherit = "product.product"
#
#     _columns = {
#
#         "dosar_id": fields.Integer('Dosar ID',help="""Identificator de Dosar pentru reper."""),
#     }
