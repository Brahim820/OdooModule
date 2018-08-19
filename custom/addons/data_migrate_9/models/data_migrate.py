# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# This file is created by gordan.cuic@gmail.com

from openerp import api, fields, models, _, osv
from odoo.exceptions import UserError
import psycopg2
import logging

_logger = logging.getLogger(__name__)

class DataMigrateOrder(models.Model):
    _name = "data.migrate.order"
    _rec_name = 'other_db_name'

    # fields ------------------------------------------------------------------
    other_db_server = fields.Char(string='Server name or IP', required=True,
        readonly=True, states={'draft': [('readonly', False)]}
    )
    other_db_name = fields.Char(string='Database name',
        help='Other database name, not this one', required=True,
        readonly=True, states={'draft': [('readonly', False)]}
    )
    other_db_port = fields.Char(string='Port', required=True,
        readonly=True, states={'draft': [('readonly', False)]}
    )
    other_db_user = fields.Char(string='User name', required=True,
        readonly=True, states={'draft': [('readonly', False)]}
    )
    other_db_pwd = fields.Char(string='Password', required=True,
        readonly=True, states={'draft': [('readonly', False)]}
    )
    notes = fields.Text(
        string='Notes', readonly=True, states={'draft': [('readonly', False)]}
    )
    state = fields.Selection([('draft', 'Draft'), ('ready', 'Ready'),
        ('done', 'Done'), ('cancel', 'Cancelled')], string='Status',
        required=True, default='draft'
    )
    line_ids = fields.One2many(
        'data.migrate.line', 'migrate_id', string='Migration jobs'
    )

    def _get_other_cr(self):
        """ Reads other server connection info and tries to establish
        connection. Returns cursor
        """
        conn_info = "dbname='%s' " % self.other_db_name
        conn_info += "user='%s' " % self.other_db_user
        conn_info += "host='%s' " % self.other_db_server
        conn_info += "password='%s'" % self.other_db_pwd
        conn = psycopg2.connect(conn_info)

        return conn.cursor()

    @api.multi
    def return_draft(self):
        self.ensure_one()
        self.write({'state': 'draft'})

        return True

    @api.multi
    def do_ready(self):
        self.ensure_one()
        self._get_other_cr()
        self.write({
            'notes': 'Connected to %s' % self.other_db_name, 'state': 'ready',
        })

        return True

    @api.multi
    def do_done(self):
        self.ensure_one()
        if not self.line_ids:
            msg = _('''You haven't selected any jobs"''')
            raise UserError(msg)
        cr2 = self._get_other_cr()
        for step in self.line_ids:
            if step.state != 'pending':
                continue

            if step.job_id.code == 'cur01':
                self.Currencies(cr2)
            if step.job_id.code == 'count01':
                self.Countries(cr2)
            elif step.job_id.code == 'states01':
                self.CountryStates(cr2)
            elif step.job_id.code == 'comp01':
                self.Company(cr2)
            elif step.job_id.code == 'usr01':
                self.Users(cr2)
            elif step.job_id.code == 'part01_pre':
                self.PartnersPre(cr2)
            elif step.job_id.code == 'part01':
                self.Partners(cr2)
            elif step.job_id.code == 'part01_post':
                self.PartnersPost(cr2)
            elif step.job_id.code == 'uom01':
                self.Uom(cr2)
            elif step.job_id.code == 'prod01':
                self.Product(cr2)
            elif step.job_id.code == 'so01_pre':
                self.SaleOrderPre(cr2)
            elif step.job_id.code == 'so01':
                self.SaleOrder(cr2)
            elif step.job_id.code == 'po01_pre':
                self.PurchaseOrderPre(cr2)
            elif step.job_id.code == 'po01':
                self.PurchaseOrder(cr2)
            elif step.job_id.code == 'po01_post':
                self.PurchaseOrderPost(cr2)
            elif step.job_id.code == 'inv01_pre':
                self.InvoicePre(cr2)
            elif step.job_id.code == 'inv01':
                self.Invoice(cr2)
            elif step.job_id.code == 'inv01_post':
                self.InvoicePost(cr2)
            elif step.job_id.code == 'usr01_post':
                self.UserPost(cr2)
                # res_users.sale_team_id --------------------------------------
            elif step.job_id.code == 'comp01_post':
                # res_company.currency_exchange_journal_id
                pass
            elif step.job_id.code == 'seq_upd':
                """ Not ready yet """
                #self.SequencesUpdate(cr2)
                raise UserError("Sequences update is not ready yet")
            elif step.job_id.code == 'emp01_pre':
                self.EmployeesPre(cr2)
            elif step.job_id.code == 'emp01':
                self.Employees(cr2)
            elif step.job_id.code == 'emp01_post':
                self.EmployeesPost(cr2)
            elif step.job_id.code == 'dosar01':
                self.HelpanDosar(cr2)

        return self.write({'state': 'done'})

    @staticmethod
    def RecordKey(cr2, table_name, where=False):
        assert cr2, 'Need cr2 here'
        assert table_name, 'Need table name here'
        assert isinstance(table_name, str), 'Table name must be string'
        allowed = ['account_invoice']
        assert table_name in allowed, 'Not ready yet to calculate key for this table'

        if not where:
            where = ''
        sql = "select count(*) from %s %s" % (table_name, where)
        cr2.execute(sql)
        res = cr2.fetchone()
        total_records = res and res[0] or 0
        if total_records:
            kkey = 'name, number, company_id, journal_id, type, partner_id'
            kkey += ', date, amount_total'
            sql = """
            with this as (
                select %s from %s %s group by %s
            )
            select count(*) from this
            """ % (kkey, table_name, where, kkey)
            cr2.execute(sql)
            res = cr2.fetchone()
            grouped_results = res and res[0] or 0
            if str(grouped_results) != str(total_records):
                msg = 'Unable to calculate unique key for %s' % table_name
                raise UserError(msg)
        else:
            kkey = 'name'


        return kkey

    @staticmethod
    def translated_value(cr2, lang, model, src, res_id=False, field_name='name'):
        """
        Returns translated field value string from version 9 database
        :param cr2: other database cursor
        :param lang: str, language code
        :param model: str, model name
        :param src: str, original field value written in database
        :param res_id: int, src record ID
        :param field_name: str, model's field name who's value needs to be
        checked for translation
        :return: str
        """
        assert cr2, 'Missing param cr2'
        assert lang, 'Missing param lang'
        assert model, 'Missing param model'
        assert src, 'Missing param src'

        if res_id:
            assert isinstance(res_id, (int, long)), 'Record ID must be int'
            sql = """
            select value from ir_translation where name = '%s,%s'
            and lang = '%s' and res_id = %s
            """ % (model, field_name, lang, res_id)
        else:
            sql = """
            select value from ir_translation where name = '%s,%s'
            and lang = '%s'
            """ % (model, field_name, lang)
        sql += """
        and src = %s order by id desc limit 1
        """
        cr2.execute(sql, (src,))
        res = cr2.fetchone()

        return res and res[0] or src

    @api.model
    def IdVersion10Product(self, cr2, vernine_id, what='product'):
        assert what in ('product', 'template'), 'Can return product or template ID only'
        verten_id = False
        if what == 'product':
            alias = 'p'
            model = 'product.product'
        else:
            alias = 't'
            model = 'product.template'

        sql = """select t.name, p.default_code, p.active, t.active, t.id
        from product_product p
        left join product_template t on p.product_tmpl_id = t.id
        where %s.id = %s order by %s.id desc
        """ % (alias, vernine_id, alias)
        cr2.execute(sql)
        res = cr2.fetchall()

        name, code = False, False
        for r in res:
            name, code = r[0], r[1]
            template_id = r[4]
            name = self.translated_value(
                cr2, 'ro_RO', 'product.template', name, res_id=template_id,
                field_name='name'
            )
            break

        obj = self.env[model]
        args = [('name', '=', name), ('default_code', '=', code)]
        if obj.search_count(args):
            verten = obj.search(args)
            verten.ensure_one()
            verten_id = verten.id
        if not verten_id:
            err_args = ''
            for i in args:
                err_args += '%s = %s\n' % (i[0], i[2])
            raise UserError(_("""No records found in new database
            for %s, for:\n%s""") % (model, err_args))

        return verten_id


    @api.model
    def IdVersion10(self, cr2, model, table_key, vernine_id, table=None):
        verten_id = False
        assert table_key, 'Need key set here'
        assert isinstance(table_key, tuple), 'Key set must be tuple'

        # it table is specified use it - otherwise replace dot in model
        if not table:
            table = model.replace('.', '_')

        # what table.field can be translated
        transaltable = ['account_payment_term.name', 'utm_campaign.name']

        # turn key to select fields string
        db_fields = ', '.join(map(str, table_key))
        if table == 'helpan_dosar_helpan_dosar':
            db_fields = '"dosarID"'
            table_key = ('internal_identify',)
            model = 'helpan.dosar'

        sql = """select %s from %s where id = %s
        """ % (db_fields, table, vernine_id)
        cr2.execute(sql)
        res = cr2.fetchone()
        args = []

        if table == 'helpan_dosar_helpan_dosar' and not res:
            return False

        for i, r in enumerate(res):
            if table_key[i] == 'name':
                if table == 'product_uom':
                    # this is tweak in order to unify multiple uoms
                    r = self.mapped_uom_name(r)
                    assert r, 'Need mapped uom name here'
                elif table == 'product_uom_categ':
                    # this is tweak in order to unify multiple uoms
                    r = self.mapped_uom_category(r)
                    assert r, 'Need mapped uom category name here'
            if '_id' in table_key[i]:
                if 'company' in table_key[i]:
                    company_id2 = r
                    company_id = self.IdVersion10(
                        cr2, 'res.company', ('name',), company_id2
                    )
                    r = company_id
                if 'country' in table_key[i]:
                    country_id2 = r
                    country_id = self.IdVersion10(
                        cr2, 'res.country', ('code', 'name',), country_id2
                    )
                    r = country_id
            if table + '.' + table_key[i] in transaltable:
                r = self.translated_value(
                    cr2, 'ro_RO', model, r, res_id=vernine_id
                )
            args.append((table_key[i], '=', r))  # build args
        obj = self.env[model]
        if obj.search_count(args):
            verten = obj.search(args)
            verten.ensure_one()
            verten_id = verten.id

        if not verten_id:
            err_args = ''
            for i in args:
                err_args += '%s = %s\n' % (i[0], i[2])
            raise UserError(_("""No records found in new database
            for %s, for:\n%s""") % (model, err_args))

        return verten_id

    @api.model
    def UpdateName(self, table_name, verten_id, vernine_name, unique_field='name'):
        """
        Updates unique human identification field on document.
        :param table_name: str, table name in version 10 database
        :param verten_id: int, record ID in version 10 database
        :param vernine_name: str, human identification string from version 9
        database
        :param unique_field: str, field name that needs to be updates (default
         is 'name' because it's most common document identification field
         visible to user
        :return: boolean, True
        """
        assert table_name, 'Missing table_name param'
        assert verten_id, 'Missing verten_id param'
        assert vernine_name, 'Missing vernine_name param'

        assert isinstance(
            table_name, (str, unicode)
        ), 'table_name param must be string'
        assert isinstance(verten_id, (int, long)), 'verten_id must be int'
        assert isinstance(
            vernine_name, (str, unicode)
        ), 'vernine_name param must be string'
        assert isinstance(
            unique_field, (str, unicode)
        ), 'unique_field param must be string'

        # go ------------------------------------------------------------------
        self._cr.execute("""
            update %s set %s = '%s' where id = %s""" % (
                table_name, unique_field, vernine_name, verten_id
            )
        )

        return True


class DataMigrateLine(models.Model):
    _name = "data.migrate.line"
    migrate_id = fields.Many2one(
        'data.migrate.order', string='Data migrate order', required=True
    )
    job_id = fields.Many2one(
        'data.migrate.jobs', string='Job', required=True
    )
    state = fields.Selection([('pending', 'Pending'),
        ('progress', 'In progress'), ('done', 'Done'), ('cancel', 'Cancelled')],
        string='Status', required=True, default='pending'
    )
    sequence = fields.Integer(
        related="job_id.sequence", string='Job sequence', required=True
    )


class DataMigrateJobs(models.Model):
    _name = "data.migrate.jobs"

    # fields ------------------------------------------------------------------
    code = fields.Char(string='Job name', size=16, required=True)
    name = fields.Char(string='Job name', required=True)
    description = fields.Text(string='Description', readonly=True)
    sequence = fields.Integer(string='Sequence', required=True)

    _sql_constraints = [
        ('code_uniq', 'unique(code)', 'Job  code must be unique!'),
    ]

    @api.multi
    @api.depends('name', 'sequence')
    def name_get(self):
        result = []
        for job in self:
            name = '%s (%s)' % (job.name, job.sequence)
            result.append((job.id, name))

        return result

class DataMigrateDocumentNumber(models.Model):
    _name = "data.migrate.document.number"

    # fields ------------------------------------------------------------------
    model = fields.Char(string='Model', required=True)
    field_name = fields.Char(
        string='Field name', default='name', required=True
    )
    name_real = fields.Char(
        string='Real name', required=True, help='Name in old database'
    )
    name_temp = fields.Text(
        string='Temoporary name', help='Temorary name assigned in new database'
    )
    old_record_id = fields.Integer(
        string='Old record ID', help='Record ID in old database'
    )
    new_record_id = fields.Integer(
        string='New record ID', help='Record ID in new database', required=True
    )

    _sql_constraints = [
        ('new_record_unique', 'unique(model, field_name, new_record_id)',
         'Model name, field name and new record id bust be unique in migrate document number!'),
    ]