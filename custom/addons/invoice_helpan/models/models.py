# -*- coding: utf-8 -*-

from openerp import models, fields, api
from amount_to_text_ro import *
# class invoice_helpan(models.Model):
#     _name = 'invoice_helpan.invoice_helpan'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         self.value2 = float(self.value) / 100