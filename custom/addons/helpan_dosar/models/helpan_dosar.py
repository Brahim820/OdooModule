# -*- coding: utf-8 -*-

from openerp import api, fields, models, _, osv
from odoo.exceptions import UserError      # pentru UserError
import odoo.addons.decimal_precision as dp
import logging
import fdb
import time
import datetime
## Conectare la MSSQL
import pyodbc
import requests
import sqlalchemy
import fdb
from datetime import datetime

from sqlalchemy import create_engine,inspect
from sqlalchemy import MetaData, Column, Table, ForeignKey
from sqlalchemy import Integer, String
from sqlalchemy import exc

import urllib

import sys
reload(sys)
sys.setdefaultencoding('UTF-8')
#ISO-8859-16
#utf-8
#latin-1
_logger = logging.getLogger(__name__)

class helpan_dosar(models.Model):
    _name = 'helpan.dosar'
    _rec_name = "internal_identify"
    _order = 'internal_identify desc'

    name = fields.Char('Name')
    internal_identify = fields.Integer(
        string="Dosar ID", help="Identificare Dosar"
    )
    date_created = fields.Date(string="Created")
    initiator = fields.Char('Initiator')

class purchase_order(models.Model):
    _inherit = 'purchase.order'
    dosar_id = fields.Many2one('helpan.dosar', 'Dosar')
    team_id= fields.Many2one('crm.team','Echipa')

class purchase_order_line(models.Model):
    _inherit = 'purchase.order.line'
    dosar_id = fields.Many2one('helpan.dosar', 'Dosar')

    '''
    # didn't find any fields named "value" or "value2" in purchase.order.line

    value2 = fields.Float(compute="_value_pc", store=True)
    description = fields.Text()

    @api.depends('value')
    def _value_pc(self):
        self.value2 = float(self.value) / 100
    '''
class account_invoice(models.Model):
    _inherit = 'account.invoice'
    swanFacturaID = fields.Integer(string="ID Factura din EDA")
    esteSincronizatEDA = fields.Boolean(string="Este sincronizat deja?")
    dosar_id = fields.Many2one('helpan.dosar', 'Dosar')
    # curs=round(1/model('').browse(1).rate,4)

    def setCurrency(self):
        currencies = self.env["res.currency"]
        id_needed = currencies.search([('name', '=', 'EUR')]).rate
        #round(1/model('res.currency').browse(1).rate,4)
        CursBNR=round(1/id_needed,4)
        CursBNR=CursBNR
        _logger.info (CursBNR)
        return CursBNR
        

    ExchangeRateEurRON = fields.Float('Curs Euro', digits=dp.get_precision('Account'),default=setCurrency)

    @api.one
    def adaugaComentariu(self,server, database):
        connection_string = "DRIVER={ODBC Driver 13 for SQL Server};TimeOut=2;Database=" + database + ";SERVER=" + \
                            server + ";UID=bogdan;PWD=HELPAN123$;TIMEOUT=2"
        connection_string = urllib.quote_plus (connection_string)
        connection_string = "mssql+pyodbc:///?odbc_connect=%s" % connection_string
        _logger.info(connection_string)



        try:
            engine = sqlalchemy.create_engine(connection_string)
            _logger.info ('\nRunning: ' + connection_string)
            from sqlalchemy.engine.reflection import Inspector
            sql = 'UPDATE DOSARE set Valoare = {0} WHERE DosarID= {1}'.format (str (self.amount_untaxed), str (
                self.dosar_id.internal_identify))
            _logger.info('\nRunning: '+sql)
            result = engine.execute (sql)
            cur =1

            now = datetime.now()  # timezone-aware datetime.utcnow()
            FORMAT = '%Y-%m-%dT'
            engine = sqlalchemy.create_engine (connection_string)
            sql = "INSERT INTO Comentarii (Continut,Utilizator,DosarID,Data) VALUES (\'factura {0} cu  valoarea {1} lei " \
                  "fara TVA" \
                  "\'," \
                  "\'{2}\',{3},\'{4}\')".format (
                str (self.number), str (self.amount_untaxed), str(self.user_id.name),str (
                    self.dosar_id.internal_identify),now)
            _logger.info ('\nRunning: ' + sql)
            result = engine.execute (sql)

        except IndexError:
            cur = -2
        #except exc.SQLAlchemyError as ex:
        #    _logger.info(ex.__class__)
        #    cur = -3
        _logger.info('\nReturnare comanda: '+str(cur))
        return cur

    @api.one
    def sincronizeazaEDA(self, context=None):
        if (self.dosar_id.internal_identify>0):
            self.adaugaComentariu("192.168.2.49","Metal")
        else:
            UserWarning('Nu avem Dosar alocat')
        # teoretic face asa   12.07.2018
        # 0. verifica daca e sincronizat documentul (daca exista) - Partial
        # 1. verifica daca clientul e sincronizat (OK)
        # 2. adauga liniile de produs
        # 3. adauga totalul la factura
        # 4. adauga valorile la swanFacturaID si bifeaza este SincronizatEDA
        res = {}
        update = False

        #Pasul 0
        if (self.esteSincronizatEDA == True):
            _logger.info('Baza de date este sincronizata')
            res = {'warning': {'title': _('Warning'), 'message': _('Este deja sincronizat' + str(self.name))}}
            return {
                'warning': {'title': _('Error'), 'message': _('Error message'), },
            }
        if res:
            return res
        con = fdb.connect(
            host='192.168.2.163', database='D:\Contabilitate\DataBase\helpan.FDB',
            user='sysdba', password='masterkey'
        )
        cur = con.cursor()
        _logger.info("Verificam daca avem inregistrari\n");
        #PASUL 0.A - De verificat dupa documentul din Odoo in SWAN
        #PASUL 1
        if(not ((self.state=="open")or(self.state=="paid"))):
            raise UserError(
                _('Nu putem sincroniza facturi decat deschise sau platite'))
            return
        serieFactura,numarFactura=self.number.split("-")
        if (not(self.partner_id.esteSincronizatEDA)):
            raise UserError(
                _('Userul nu e sincronizat'+str(serieFactura)+" "+str(numarFactura)))
            return

        #verifica daca numarulFacturii exista
        if(self.AvemNumarulFacturiiDeja(cur, numarFactura)):
            return  #iese din functie si asta e

        cur.execute("select lastid from tblcount where name='BXIESIRE'")
        result = cur.fetchone()
        BXID = result[0] + 1
         #BXCONT_ID - 246 - DRAGOS;  221 - HP
        BXCONT_ID = self.team_id.ContFacturi.swanContID  # 221 - HP sau 246 - Dragos
        BXREC_TYPE = 2  # nu stiu ce inseamna
        BXIESIRETIPDOC_ID = 4  # 4 HP ; 5 HEV
        BXCUSTOMER_ID = self.partner_id.swan_ID  # de afisat daca e partner_id sau partner_id.id
        BXDOC_NO = numarFactura
        BXDOC_DATE = datetime.strptime(self.date_invoice, '%Y-%m-%d').strftime('%d.%m.%Y %H:%M:%S')
        #2018-08-10
        #'2018-07-11' does not match format '%Y-%m-%d'
        #'20.10.2011 10:10:10'
        BXVALUTA_ID = None  # 2 daca e EUR
        BXVALUTA_CURS = None  # efectiv daca e in eur
        BXGAMOUNT = self.amount_total  # test
        BXVALFTVA = self.amount_untaxed  # test
        BXVALTVA = self.amount_tax  # test
        BXLAMOUNT = self.amount_total  # test
        BXSETTLED_VALUE = self.amount_total
        #timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        #BXDATASCADENTA = time.mktime(datetime.datetime.strptime(self.date_due, '%Y-%m-%d').timetuple())
        #BXDATASCADENTA = datetime.datetime.strptime(self.date_due, '%d.%m.%Y')
        BXDATASCADENTA = datetime.strptime(self.date_due, '%Y-%m-%d').strftime('%d.%m.%Y %H:%M:%S')
        BXVATCONT_ID = 72  # asa e in BD
        BXUNITATE_ID = 0  # asa era in BD
        BXSURSA_ID = 1  # asa era in BD
        BXVALCASA = 0  # asa era
        BXSOLD = self.amount_total
        BXSOLDINT = 1  # ce draci o fi
        BXUNITATE_ID = 0
        BXSURSA_ID = 1  # ce inseamna?
        BXVALUTA_ID = 2  # la factura 4808 cu un curs
        BXVATCONT_ID = 72  # la toate
        BXSOLD= self.amount_total
        BXSOLDINT = 1
        BXSERIA = serieFactura
        interogare="INSERT INTO BXIESIRE (BXID,BXCONT_ID,BXREC_TYPE,BXIESIRETIPDOC_ID,BXCUSTOMER_ID,BXDOC_NO," \
                   "BXDOC_DATE,BXVALUTA_ID,BXVALUTA_CURS,BXGAMOUNT,BXVALFTVA,BXVALTVA,BXLAMOUNT,BXSETTLED_VALUE," \
                   "BXDATASCADENTA,BXVATCONT_ID,BXUNITATE_ID,BXSURSA_ID,BXVALCASA,BXSOLD,BXSOLDINT,BXSERIA) VALUES(" \
                   + str(BXID) + "," + str(BXCONT_ID) + "," + str(BXREC_TYPE) + "," + str(BXIESIRETIPDOC_ID) + "," + str(BXCUSTOMER_ID) + "," + str(BXDOC_NO) + ",'" + str(BXDOC_DATE) + "'," + str(BXVALUTA_ID) + "," + str(BXVALUTA_CURS) + "," + str(BXGAMOUNT) + "," + str(BXVALFTVA) + "," + str(BXVALFTVA) + "," + str(BXLAMOUNT) + "," + str(BXSETTLED_VALUE) + ",'" + str(BXDATASCADENTA) + "'," + str(BXVATCONT_ID) + "," + str(BXUNITATE_ID) + "," + str(BXSURSA_ID)+ "," + str(BXVALCASA)+ "," + str(BXSOLD)+ "," + str(BXSOLDINT) + "," +  str(BXSERIA) + "')"
        _logger.info(interogare)
        interogare= "update tblcount set lastid=" + str(BXID) + "  WHERE name='BXIESIRE'"
        _logger.info(interogare)

        raise UserError("nu avem implementare - TODO\n"+str(BXCUSTOMER_ID)+" "+str(self.partner_id.id)+ " "
                                                                                                      ""+self.date_due+" " +str(BXDATASCADENTA))
        return
        #BXIESIRE. BXDOC_NO +BXDOC_DATE+ BXGAMOUNT    - afli noul id si apoi
        #BXIESIRELNS - introducem aici datele
        TermenCautat = self.display_name.upper().replace("SC ", "").replace(" SRL", "")

        _logger.info("SELECT bxid FROM BXCUSTOMER WHERE UPPER(BXDENUMIRE) LIKE '%" + TermenCautat + "%'")
        cur.execute("SELECT bxid FROM BXCUSTOMER WHERE UPPER(BXDENUMIRE) LIKE '%" + TermenCautat + "%'")
        result = cur.fetchall()


        if (len(result) == 1):
            newId = result[0][0]
            update = True
        else:
            if (len(result) > 1):
                raise UserError(
                    _('Prea multe rezultate pentru acest client \n Sunt ' + str(len(result)) + ' rezultate'))
                return
            else:
                cur.execute("select lastid from tblcount where name='BXCUSTOMER'")
                result = cur.fetchone()
                newId = result[0] + 1

        # TODO1 : verifica daca nu este deja
        self.swan_ID = newId
        self.esteSincronizatEDA = True
        _logger.info(str(self.display_name).encode('utf-8'))
        if (update == True):
            _logger.info('Actualizam date!')
            _logger.info("UPDATE BXCUSTOMER SET BXDENUMIRE=" + str(self.display_name) + ", BXCODFISCAL=" + str(
                self.vat) + ", BXREGCOM=" + str(self.nrc) + ",BXADRESA='" + str(self.street) + "', BXORAS='" + str(
                self.city) + "', BXEMAIL='" + str(self.email) + "' WHERE BXID=newId")
          #  con.commit()
        else:
            _logger.info(
                "INSERT INTO BXCUSTOMER(BXID, BXDENUMIRE, BXCODFISCAL, BXREGCOM,BXADRESA, BXORAS, BXEMAIL,BXSERIA, "
                "BXINOUT_BOOL,BXSALARIAT_BOOL,BXGRUPACLIENTI_ID) VALUES(" + str(
                    newId) + ",'" + str(self.display_name) + "','" + str(self.vat) + "','" + str(
                    self.nrc) + "','" + str(self.street) + "','" + str(self.city) + "','" + str(
                    self.email) + "','RO',1,0,1)")
            cur.execute(
                "INSERT INTO BXCUSTOMER(BXID, BXDENUMIRE, BXCODFISCAL, BXREGCOM,BXADRESA, BXORAS, BXEMAIL,BXSERIA, "
                "BXINOUT_BOOL,BXSALARIAT_BOOL,BXGRUPACLIENTI_ID) VALUES(" + str(
                    newId) + ",'" + str(self.display_name) + "','" + str(self.vat) + "','" + str(
                    self.nrc) + "','" + str(self.street) + "','" + str(self.city) + "','" + str(
                    self.email) + "','RO',1,0,1)")
            _logger.info('\n\nID alocat: ' + str(newId) + ' - Incercam sa inseram in BXCUSTOMER\n\n')
            cur.execute("update tblcount set lastid=" + str(newId) + "  WHERE name='BXCUSTOMER'")
           # con.commit()




    def AvemNumarulFacturiiDeja(self, cur, numarFactura):
        interogare = "SELECT BXID FROM BXIESIRE WHERE BXDOC_NO LIKE \'%" + str (numarFactura)+"%\'"
        _logger.info(interogare)
        cur.execute (interogare)
        result = cur.fetchall ()
        if (len (result) > 0):
            raise UserError ("Exista mai multe inregistrari cu numarul de factura. Sincronizati manual ")
            return True
        return False


class res_partner(models.Model):
    _inherit = 'res.partner'
    swan_ID = fields.Integer(string="ID din EDA")
    esteSincronizatEDA = fields.Boolean(string="Este sincronizat deja?")

    @api.one
    def sincronizeazaEDA(self,context=None):
        res = {}
        update=False
        if(self.esteSincronizatEDA==True):
            _logger.info('Baza de date este sincronizata')
            res = {'warning': {'title': _('Warning'),'message': _('Este deja sincronizat'+str(self.name))}}
            return {
                'warning': {'title': _('Error'), 'message': _('Error message'), },
            }
        if res:
            return res
        con = fdb.connect(
            host='192.168.2.163', database='D:\Contabilitate\DataBase\helpan.FDB',
            user='sysdba', password='masterkey'
        )
        cur = con.cursor()
        _logger.info("Verificam daca avem inregistrari\n");
        #TermenCautat=self.display_name.upper().replace("SC ","").replace(" SRL","").replace(" SA","")
        # csa caute si dupa CUI BXCODFISCAL=
        codCUI=self.vat.replace("CUI ","").replace("RO ","").replace("RO","").strip()
        if(codCUI==""):
            raise UserError(_('Nu avem CUIul setat la acest client \n '))
            return
        interogare="SELECT bxid FROM BXCUSTOMER WHERE BXCODFISCAL='"+str(codCUI)+"'"
        _logger.info(interogare)
        cur.execute(interogare)
        
        #cur.execute("SELECT bxid FROM BXCUSTOMER WHERE UPPER(BXDENUMIRE) LIKE '%"+TermenCautat+"%'")
        result = cur.fetchall()
        if (len(result)==1):
            newId=result[0][0]
            update=True
        else:
            if(len(result)>1):
                raise UserError(_('Prea multe rezultate pentru acest client \n Sunt '+str(len(result))+' rezultate'))
                return
            else:
                cur.execute("select lastid from tblcount where name='BXCUSTOMER'")
                result = cur.fetchone()
                newId = result[0] + 1

        # TODO1 : verifica daca nu este deja
        self.swan_ID = newId
        self.esteSincronizatEDA=True
        _logger.info(str(self.display_name).encode('utf-8'))
        if(update==True):
            _logger.info('Actualizam date!')
            _logger.info("UPDATE BXCUSTOMER SET BXDENUMIRE="+str(self.display_name)+", BXCODFISCAL="+str(self.vat)+", BXREGCOM="+str(self.nrc)+",BXADRESA='"+str(self.street)+"', BXORAS='"+str(self.city)+"', BXEMAIL='"+str(self.email)+"' WHERE BXID=newId")
            con.commit()
        else:
            _logger.info("INSERT INTO BXCUSTOMER(BXID, BXDENUMIRE, BXCODFISCAL, BXREGCOM,BXADRESA, BXORAS, BXEMAIL,BXSERIA, BXINOUT_BOOL,BXSALARIAT_BOOL,BXGRUPACLIENTI_ID) VALUES(" + str(newId) + ",'"+str(self.display_name)+"','"+str(self.vat)+"','"+str(self.nrc)+"','"+str(self.street)+"','"+str(self.city)+"','"+str(self.email)+"','RO',1,0,1)")
            cur.execute("INSERT INTO BXCUSTOMER(BXID, BXDENUMIRE, BXCODFISCAL, BXREGCOM,BXADRESA, BXORAS, BXEMAIL,BXSERIA, BXINOUT_BOOL,BXSALARIAT_BOOL,BXGRUPACLIENTI_ID) VALUES(" + str(newId) + ",'"+str(self.display_name)+"','"+str(self.vat)+"','"+str(self.nrc)+"','"+str(self.street)+"','"+str(self.city)+"','"+str(self.email)+"','RO',1,0,1)")
            _logger.info('\n\nID alocat: '+str(newId)+' - Incercam sa inseram in BXCUSTOMER\n\n')
            cur.execute("update tblcount set lastid=" + str(newId) + "  WHERE name='BXCUSTOMER'")
            con.commit()

    @api.one
    def sincronizeaza_eda(self,cr,uid,ids,context=None):
        return {
            'name': 'My Window',
            'domain': [],
            'res_model': 'res.partner',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'view_type': 'form',
            'context': {},
            'target': 'new',
        }



class account_invoice_line(models.Model):
    _inherit = 'account.invoice.line'
    dosar_id = fields.Many2one('helpan.dosar', 'Dosar')

class account_tax(models.Model):
    _inherit = 'account.tax'
    swanTVAID = fields.Integer(string="Inregistrare TVA in EDA")


class account_account(models.Model):
    _inherit = 'account.account'
    swanContID = fields.Integer(string="Identificator Cont in EDA",help="Se deschide in SWAN in Setup->Conturi->Browse si se gaseste in coloana ID")

class crm_team(models.Model):
    _inherit = 'crm.team'
    ContFacturi = fields.Many2one ('account.account', string='Cont alocat facturilor acestei echipe',help="Pentru Sincronizare cu EDA")