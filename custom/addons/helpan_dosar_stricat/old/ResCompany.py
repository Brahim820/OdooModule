# -*- coding: utf-8 -*-

from openerp import models, api, fields

class ResCompany(models.Model):
    _inherit='res.company'

@api.multi
def updatePhoneNumber(self,new_number):
    self.ensure_one()
    company_as_superuser = self.sudo() # dsadas
    company_as_superuser.phone = new_number
    