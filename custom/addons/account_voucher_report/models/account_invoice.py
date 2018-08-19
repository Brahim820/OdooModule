# -*- coding: utf-8 -*-


from openerp import fields, models, api
from openerp import api, fields, models, _, osv
from odoo.exceptions import UserError      # pentru UserError
import logging
_logger = logging.getLogger(__name__)


class account_invoice(models.Model):
    _inherit = 'account.invoice'
    @api.one
    def afiseazaChitante(self, context=None):
        raise UserError ("nu avem implementare - TODO\n")
