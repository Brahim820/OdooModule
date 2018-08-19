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
from openerp import models
from openerp.report.report_sxw import rml_parse


class payment_parser(rml_parse):

    def __init__(self, cr, uid, ids, context=None):

        super(payment_parser, self).__init__(cr, uid, ids, context=context)

        self.localcontext.update({
            'get_username': self.get_username
        })

    def get_username(self, data):
        return data.env.user.name


class voucher_abstract(models.AbstractModel):

    _name = 'report.account_voucher_report.report_account_payment_details'
    _inherit = 'report.abstract_report'
    _template = 'account_voucher_report.report_account_payment_details'
    _wrapped_report_class = payment_parser
