# -*- coding: utf-8 -*-

from openerp import models, fields, api

class helpan_teava(models.Model):
    _name = 'helpan_teava'
    _inherit = ['mail.thread']
    _description ="Evidenta Teava si Bara Helpan"
    #_order ='date_releasee desc,name'
    # _rec_name = 'short_name'
    # record representation oare ce inseamna asta? unde gasim informatia de name - COOL; aici nu folosim
    name= fields.Char('Denumire',required=True,help='Exemplu: Teava Rect Inox 40x40x2')
    dimensiuneX= fields.Float('Dimensiune X',help='masurata in mm. Exemplu: 6000',required="True") #cum pot sa pun la
    # sfarsit
    #  mm?
    dimensiuneY = fields.Float('Dimensiune Y',help='poate sa fie si 0')
    #denumirecompleta= fields.Char('Denumire completa',compute='_compute_denumire_completa',store='True') - nue e nevoie
    locatie = fields.Char()
    nrbuc = fields.Integer(string='Numar Bucati',required="True")
    state =fields.Selection([('stoc','Liber'),('comanda','Rezervat pt comanda'),('investigat','Nu este clar'),
                             ('mixt','Sunt cateva libere')],string='Stare',help='Daca se doreste rezervarea, '
                                                                              'se pune la comentariu')
    observatie = fields.Text('Observatii',help='Daca sunt aspecte de notificat (dosar unde se fac rezervarile)')

    active = fields.Boolean('Activ', default=True)
    #
    # @api.depends('name','dimensiuneX',)
    # def _compute_denumire_completa(self):
    #     self.denumirecompleta =  (self.name or '')+' '+(self.name or '')