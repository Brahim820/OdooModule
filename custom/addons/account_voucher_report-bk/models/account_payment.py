# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2016 Serpent Consulting Services Pvt. Ltd.
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from openerp import fields, models, api
from openerp.tools import amount_to_text_en
from amount_to_text_ro import *

class account_payment(models.Model):
    _inherit = "account.payment"

    journal_id_type = fields.Char(related='journal_id.name', string="Type")
    check_no = fields.Char('Check No.')
    reference = fields.Char('Payment Ref')

    def get_amount(self, amount, currency):
      #  amt_en = amount_to_text_en.amount_to_text(amount, 'ro', currency)
        amt_ro = amount_to_text_ro(amount)
        return amt_ro
