# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# This file is created by gordan.cuic@gmail.com

from openerp import api, fields, models, _, osv
from odoo.exceptions import UserError
import psycopg2
import logging

_logger = logging.getLogger(__name__)

class DataMigrateOrder(models.Model):
    _inherit = "data.migrate.order"

    @api.model
    def InvoicePre(self, cr2):
        # accounts ------------------------------------------------------------
        account_obj = self.env['account.account']
        cr2.execute("""
        select id from account_account order by code
        """)
        account_ids2 = [a[0] for a in cr2.fetchall() if a and a[0] or False]
        c = 0
        for account_id2 in account_ids2:
            c += 1
            if c in (1, len(account_ids2)) or c % 100 == 0:
                _logger.debug(
                    'Migrating %s/%s accounts' % (c, len(account_ids2))
                )
            vals = self.AccountVals9(cr2, account_id2)
            code = vals.get('code', False)
            assert code, 'Need account code here'
            if account_obj.search_count([('code', '=', code)]):
                account = account_obj.search([('code', '=', code)])
                account.ensure_one()
                del vals['code']
                account.write(vals)
            else:
                account_obj.create(vals)

        # journals ------------------------------------------------------------
        journal_obj = self.env['account.journal']
        cr2.execute("select id from account_journal order by id")
        journal_ids2 = [i[0] for i in cr2.fetchall() if i and i[0] or False]
        if not journal_ids2:
            raise UserError(_("""Unable to fetch account journals
            from %s""") % self.other_db_name)
        _logger.debug('Migrating %s journals' % len(journal_ids2))
        for journal_id2 in journal_ids2:
            vals = self.JournalVals9(cr2, journal_id2)
            code = vals.get('code', False)
            assert code, 'Need journal code here'

            # check currency consistency --------------------------------------
            currency_id = vals.get('currency_id', False)
            if currency_id:
                debit_currency_id, credit_currency_id = False, False
                debit_id = vals.get('default_debit_account_id', False)
                credit_id = vals.get('default_credit_account_id', False)
                if debit_id:
                    account = account_obj.browse(debit_id)
                    account.ensure_one()
                    debit_currency_id = account.currency_id and \
                                        account.currency_id.id or False
                if credit_id:
                    account = account_obj.browse(debit_id)
                    account.ensure_one()
                    credit_currency_id = account.currency_id and \
                                         account.currency_id.id or False
                self.JournalBic({
                    'journal_currency_id': currency_id,
                    'debit_currency_id': debit_currency_id,
                    'credit_currency_id': credit_currency_id,
                }, code)

            args = [('code', '=', code)]
            if journal_obj.search_count(args):
                del vals['code']
                journal = journal_obj.search(args)
                journal.ensure_one()
                journal.write(vals)
            else:
                journal_obj.create(vals)

        return True

    @api.model
    def AccountVals9(self, cr2, account_id2):
        """
        Fetches accounts from old database and prepares dict to create()
        or write() on new database
        :param cr2: cursor to old database
        :param account_id2: int, old database account record ID
        :return: dict
        """
        sql = """
        select
            code -- 0
            ,company_id -- 1
            ,currency_id -- 2
            ,deprecated -- 3
            ,internal_type -- 4
            ,last_time_entries_checked -- 5
            ,name -- 6
            ,note -- 7
            ,reconcile -- 8
            ,user_type_id -- 9
        from account_account where id = %s
        """ % account_id2
        cr2.execute(sql)
        res = cr2.fetchall()
        if not res:
            raise UserError(_("""Unable to fetch journals
            from %s (ID %s)""") % (self.other_db_name, account_id2))
        vals = {}
        for r in res:
            code = r[0]
            company_id2 = r[1]
            currency_id2 = r[2]
            deprecated = r[3] or False
            internal_type = r[4]
            last_time_entries_checked = r[5]
            name = r[6]
            note = r[7]
            reconcile = r[8] or False
            user_type_id2 = r[9]

            currency_id = False
            if currency_id2:
                currency_id = self.IdVersion10(
                    cr2, 'res.currency', ('name',), currency_id2
                )

            company_id = self.IdVersion10(
                cr2, 'res.company', ('name',), company_id2
            )

            user_type_id = self.IdVersion10(
                cr2, 'account.account.type', ('name',), user_type_id2
            )

            vals.update({
                'code': code,
                'company_id': company_id,
                'currency_id': currency_id,
                'deprecated': deprecated,
                'internal_type': internal_type,
                'last_time_entries_checked': last_time_entries_checked,
                'name': name,
                'note': note,
                'reconcile': reconcile,
                'user_type_id': user_type_id,
            })
            break

        return vals


    @api.model
    def JournalVals9(self, cr2, journal_id2):
        """
        Fetches journals from old database and prepares dict to create()
        or write() on new database
        :param cr2: cursor to old database
        :param journal_id2: int, old database journal record ID
        :return: dict
        """
        sql = """
        select
            at_least_one_inbound -- 0
            ,at_least_one_outbound -- 1
            ,bank_account_id -- 2
            ,bank_statements_source -- 3
            ,code -- 4
            ,company_id -- 5
            ,currency_id -- 6
            ,default_credit_account_id -- 7
            ,default_debit_account_id -- 8
            ,display_on_footer -- 9
            ,group_invoice_lines -- 10
            ,loss_account_id -- 11
            ,name -- 12
            ,profit_account_id -- 13
            ,refund_sequence -- 14
            ,refund_sequence_id -- 15
            ,sequence -- 16
            ,sequence_id -- 17
            ,show_on_dashboard -- 18
            ,type -- 19
            ,update_posted -- 20
        from account_journal where id = %s
        """ % journal_id2
        cr2.execute(sql)
        res = cr2.fetchall()
        if not res:
            raise UserError(_("""Unable to fetch journals
            from %s (ID %s)""") % (self.other_db_name, journal_id2))
        vals = {}
        for r in res:
            at_least_one_inbound = r[0] or False
            at_least_one_outbound = r[1] or False
            bank_account_id2 = r[2]
            bank_statements_source = r[3]
            code = r[4]
            company_id2 = r[5]
            currency_id2 = r[6]
            default_credit_account_id2 = r[7]
            default_debit_account_id2 = r[8]
            display_on_footer = r[9]
            group_invoice_lines = r[10]
            loss_account_id2 = r[11]
            name = r[12]
            profit_account_id2 = r[13]
            show_on_dashboard = r[18]
            ttype = r[19]
            update_posted = r[20] or False

            refund_sequence = r[14]
            sequence = r[16] or False

            bank_account_id = False
            if bank_account_id2:
                bank_account_id = self.IdVersion10(
                    cr2, 'res.partner.bank', ('sanitized_acc_number',),
                    bank_account_id2
                )

            '''
            # this is for forcing journal to have currency defined
            if not currency_id2:
                cr2.execute("""
                select id from res_currency where name = 'RON'
                """)
                curr = cr2.fetchone()
                assert curr, 'Need default currency here'
                assert len(curr) == 1, 'Got multiple default currencies here'
                currency_id2 = curr[0]
            currency_id = self.IdVersion10(
                cr2, 'res.currency', ('name',), currency_id2
            )
            '''
            currency_id = False
            if currency_id2:
                currency_id = self.IdVersion10(
                    cr2, 'res.currency', ('name',), currency_id2
                )

            company_id = self.IdVersion10(
                cr2, 'res.company', ('name',), company_id2
            )

            default_credit_account_id = False
            if default_credit_account_id2:
                default_credit_account_id = self.IdVersion10(
                    cr2, 'account.account', ('code', 'company_id'),
                    default_credit_account_id2
                )
            default_debit_account_id = False
            if default_debit_account_id2:
                default_debit_account_id = self.IdVersion10(
                    cr2, 'account.account', ('code', 'company_id'),
                    default_debit_account_id2
                )
            loss_account_id = False
            if loss_account_id2:
                loss_account_id = self.IdVersion10(
                    cr2, 'account.account', ('code', 'company_id'),
                    loss_account_id2
                )
            profit_account_id = False
            if profit_account_id2:
                profit_account_id = self.IdVersion10(
                    cr2, 'account.account', ('code', 'company_id'),
                    profit_account_id2
                )

            vals.update({
                'at_least_one_inbound': at_least_one_inbound,
                'at_least_one_outbound': at_least_one_outbound,
                'bank_account_id': bank_account_id,
                'bank_statements_source': bank_statements_source,
                'code': code,
                'company_id': company_id,
                'currency_id': currency_id,
                'default_credit_account_id': default_credit_account_id,
                'default_debit_account_id': default_debit_account_id,
                'display_on_footer': display_on_footer,
                'group_invoice_lines': group_invoice_lines,
                'loss_account_id': loss_account_id,
                'name': name,
                'profit_account_id': profit_account_id,
                'refund_sequence': refund_sequence,
                'sequence': sequence,
                'show_on_dashboard': show_on_dashboard,
                'type': ttype,
                'update_posted': update_posted,
            })
            break

        return vals


    @api.model
    def Invoice(self, cr2):
        invoice_obj = self.env['account.invoice']
        document_number_obj = self.env['data.migrate.document.number']

        # check consistency ---------------------------------------------------
        self.MoreInvoicesOnePaymentCheck9(cr2)

        # get key -------------------------------------------------------------
        kkey = self.RecordKey(
            cr2, 'account_invoice', where="where state not in ('cancel')"
        )
        assert kkey, 'Unable to calc unique record key'

        cr2.execute(
            """select id from account_invoice
            where state not in ('cancel') order by id"""
        )


        '''
        # test
        cr2.execute("""select id from account_invoice
        where number in ('HP-2692')
        order by id
        """)
        '''

        invoice_ids2 = [i[0] for i in cr2.fetchall() if i and i[0] or False]
        if not invoice_ids2:
            raise UserError(_("""Unable to fetch invoices
            from %s""") % self.other_db_name)
        c = 0
        for invoice_id2 in invoice_ids2:
            c += 1
            if c in (1, len(invoice_ids2)) or c % 100 == 0:
                _logger.debug(
                    'Migrating %s/%s invoices' % (c, len(invoice_ids2))
                )
            vals_ten, payment_data = self.InvoiceVals9(cr2, invoice_id2)

            # insert to draft state -------------------------------------------
            state2 = vals_ten.get('state', False)
            assert state2, 'Need state from old db here'
            vals_ten.update({'state': 'draft'})

            # get lines -------------------------------------------------------
            lines = self.InvoiceLineVals9(cr2, invoice_id2)
            invoice_line_ids = [(0, 0, v) for v in lines]
            vals_ten.update({'invoice_line_ids': invoice_line_ids})

            # do it -----------------------------------------------------------
            name = vals_ten.get('name', False)
            invoice_number = vals_ten.get('number', False)
            partner_id = vals_ten.get('partner_id', False)
            assert partner_id, 'Need partner_id here'
            amount_total = vals_ten.get('amount_total', 0.0)

            company_id = vals_ten.get('company_id', False)
            journal_id = vals_ten.get('journal_id', False)
            ttype = vals_ten.get('type', False)
            date_invoice = vals_ten.get('date', False)

            number2 = vals_ten.get('number', False)
            move_id2 = vals_ten.get('move_id', False)
            move_name2 = vals_ten.get('move_name', False)
            for fld in ('number', 'move_id', 'move_name'):
                if fld in vals_ten:
                    del vals_ten[fld]

            # after modifying number update, search only via invoice number
            args = [('name', '=', name), ('number', '=', invoice_number),
                    ('company_id', '=', company_id),
                    ('journal_id', '=', journal_id), ('type', '=', ttype),
                    ('partner_id', '=', partner_id),
                    ('date', '=', date_invoice),
                    ('amount_total', '=', amount_total)]

            if not invoice_obj.search_count(args):
                invoice = invoice_obj.create(vals_ten)
                invoice.ensure_one()
                if state2 == 'draft':
                    continue
                if state2 == 'proforma2':
                    invoice.action_invoice_proforma2()
                    continue

                # push invoice work flow --------------------------------------
                if not number2:
                    msg = """Invoice old id %s open or paid, but no number?
                    """ % invoice_id2
                    raise UserError(msg)
                if not move_name2:
                    msg = """Invoice old id %s open or paid, but no move name?
                    """ % invoice_id2
                    raise UserError(msg)

                invoice.action_invoice_open()

                document_number_obj.create({
                    'model': 'account.invoice', 'field_name': 'number',
                    'name_temp': invoice.number,
                    'name_real': invoice_number,
                    'old_record_id': invoice_id2,
                    'new_record_id': invoice.id,
                })

                move = invoice.move_id
                document_number_obj.create({
                    'model': 'account.invoice', 'field_name': 'move_name',
                    'name_temp': move.name,
                    'name_real': move_name2,
                    'old_record_id': invoice_id2,
                    'new_record_id': invoice.id,
                })
                document_number_obj.create({
                    'model': 'account.move', 'field_name': 'name',
                    'name_temp': move.name,
                    'name_real': move_name2,
                    'old_record_id': move_id2,
                    'new_record_id': move.id,
                })
                if name:
                    document_number_obj.create({
                        'model': 'account.move', 'field_name': 'ref',
                        'name_temp': False,
                        'name_real': name,
                        'old_record_id': move_id2,
                        'new_record_id': move.id,
                    })

                # process payments --------------------------------------------
                if not payment_data:
                    continue

                for data in payment_data:
                    self.RecordInvoicePayment(data, invoice)

        return True

    @api.model
    def RecordInvoicePayment(self, data, invoice):
        """ Creates account_payment record for given invoice """
        assert invoice, 'Need invoice here'
        assert data, 'Need payment data dict here'

        invoice.ensure_one()

        id2 = data.get('id2', False)
        assert id2, 'Need old id here'

        name2 = data.get('name', False)
        assert name2, 'Need old name here'

        state = data.get('state', False)
        assert state, 'Need state here'

        move_name2 = data.get('move_name', False)
        if state == 'posted':
            assert move_name2, 'Need old move_name here'

        ref2 = data.get('move_ref', False)

        journal_id = data.get('journal_id', False)
        assert journal_id, 'Need journal here'

        amount = data.get('amount', 0.0)
        assert amount and amount != 0.0, 'Need amount here'

        currency_id = data.get('currency_id', False)
        assert currency_id, 'Need currency here'

        payment_date = data.get('payment_date', False)
        assert payment_date, 'Need payment_date here'

        payment_method_id = data.get('payment_method_id', False)
        assert payment_method_id, 'Need payment_method_id here'

        payment_type = data.get('payment_type', False)
        assert payment_type, 'Need payment_type here'

        partner_type = data.get('partner_type', False)
        assert partner_type, 'Need partner_type here'

        partner_id = data.get('partner_id', False)
        assert partner_id, 'Need partner_id here'

        if invoice.state != 'open':
            raise UserError("""
            Invoice type "%s", old payment id %s, must be in open state
            """ % (invoice.type, id2))

        payment = self.env['account.payment'].create({
            'invoice_ids': [(4, invoice.id, None)],
            'company_id': invoice.company_id and invoice.company_id.id or False,
            'journal_id': journal_id, 'amount': amount,
            'currency_id': currency_id, 'payment_date': payment_date,
            'payment_method_id': payment_method_id,
            'payment_type': payment_type, 'partner_type': partner_type,
            'partner_id': partner_id,
        })

        document_number_obj = self.env['data.migrate.document.number']
        document_number_obj.create({
            'model': 'account.payment', 'field_name': 'name',
            'name_temp': payment.name,
            'name_real': name2,
            'old_record_id': id2,
            'new_record_id': payment.id,
        })

        if state == 'posted':
            payment.post()

            # modify names ----------------------------------------------------
            obj = self.env['account.move.line']
            amls = obj.search([('payment_id', '=', payment.id)])
            move = amls[0].move_id
            document_number_obj.create({
                'model': 'account.move', 'field_name': 'name',
                'name_temp': move.name,
                'name_real': move_name2,
                'old_record_id': False,
                'new_record_id': move.id,
            })
            if ref2:
                document_number_obj.create({
                    'model': 'account.move', 'field_name': 'ref',
                    'name_temp': move.ref,
                    'name_real': ref2,
                    'old_record_id': False,
                    'new_record_id': move.id,
                })

        return True

    @api.model
    def InvoiceVals9(self, cr2, invoice_id2):
        """
        Fetches invoices from old database and prepares dict to create()
        or write() on new database
        :param cr2: cursor to old database
        :param invoice_id2: int, old database invoice record ID
        :return: dict
        """
        sql = """
        select
            account_id -- 0
            ,amount_tax -- 1
            ,amount_total -- 2
            ,amount_total_company_signed -- 3
            ,amount_total_signed -- 4
            ,amount_untaxed -- 5
            ,amount_untaxed_signed -- 6
            ,comment -- 7
            ,commercial_partner_id -- 8
            ,company_id -- 9
            ,create_date -- 10
            ,create_uid -- 11
            ,currency_id -- 12
            ,date -- 13
            ,date_due -- 14
            ,date_invoice -- 15
            ,fiscal_position_id -- 16
            ,id -- 17
            ,incoterms_id -- 18
            ,journal_id -- 19
            ,message_last_post -- 20
            ,move_id -- 21
            ,move_name -- 22
            ,name -- 23
            ,number -- 24
            ,origin -- 25
            ,partner_bank_id -- 26
            ,partner_id -- 27
            ,payment_term_id -- 28
            ,purchase_id -- 29
            ,reconciled -- 30
            ,reference -- 31
            ,reference_type -- 32
            ,residual -- 33
            ,residual_company_signed -- 34
            ,residual_signed -- 35
            ,sent -- 36
            ,state -- 37
            ,team_id -- 38
            ,type -- 39
            ,user_id -- 40
            ,write_date -- 41
            ,write_uid -- 42
            ,"x_CursEuro" -- 43
            ,"x_dosar2" -- 44
        from account_invoice where id = %s
        """ % invoice_id2
        cr2.execute(sql)
        res = cr2.fetchall()
        if not res:
            raise UserError(_("""Unable to fetch invoices
            from %s (ID %s)""") % (self.other_db_name, invoice_id2))
        vals_ten, payment_data = {}, []
        for r in res:
            account_id2 = r[0]
            amount_tax = r[1]
            amount_total = r[2]
            amount_total_company_signed = r[3]
            amount_total_signed = r[4]
            amount_untaxed = r[5]
            amount_untaxed_signed = r[6]
            comment = r[7]
            commercial_partner_id2 = r[8]
            company_id2 = r[9]
            currency_id2 = r[12]
            date = r[13]
            date_due = r[14]
            date_invoice = r[15]
            fiscal_position_id2 = r[16]
            #incoterms_id2 = r[18]
            journal_id2 = r[19]
            message_last_post = r[20]
            move_id2 = r[21]
            move_name2 = r[22]
            name = r[23]
            number2 = r[24]
            origin = r[25]
            partner_bank_id2 = r[26]
            partner_id2 = r[27]
            payment_term_id2 = r[28]
            #purchase_id2 = r[29]
            reconciled = r[30]
            reference = r[31]
            reference_type = r[32]
            residual = r[33]
            residual_company_signed = r[34]
            residual_signed = r[35]
            sent = r[36]
            state = r[37]
            team_id2 = r[38]
            type = r[39]
            user_id2 = r[40]
            exchange_rate = r[43]
            dosar_id2 = r[44]

            account_id = self.IdVersion10(
                cr2, 'account.account', ('code', 'company_id'), account_id2
            )

            partner_id = self.IdVersion10(cr2, 'res.partner',
                ('name', 'vat', 'nrc', 'company_id', 'is_company'),
                partner_id2
            )

            company_id = self.IdVersion10(
                cr2, 'res.company', ('name',), company_id2
            )

            partner_bank_id = False
            if partner_bank_id2:
                partner_bank_id = self.IdVersion10(
                    cr2, 'res.partner.bank', ('sanitized_acc_number',),
                    partner_bank_id2
                )

            journal_id = self.IdVersion10(
                cr2, 'account.journal', ('code',), journal_id2
            )

            if commercial_partner_id2:
                commercial_partner_id = self.IdVersion10(cr2, 'res.partner',
                    ('name', 'vat', 'nrc', 'company_id', 'is_company'),
                    commercial_partner_id2
                )

            currency_id = False
            if currency_id2:
                currency_id = self.IdVersion10(
                    cr2, 'res.currency', ('name',), currency_id2
                )

            fiscal_position_id = False
            if fiscal_position_id2:
                fiscal_position_id = self.IdVersion10(
                    cr2, 'account.fiscal.position', ('name', 'company_id'),
                    fiscal_position_id2
                )

            payment_term_id = False
            if payment_term_id2:
                payment_term_id = self.IdVersion10(
                    cr2, 'account.payment.term', ('name',), payment_term_id2
                )

            team_id = False
            if team_id2:
                team_id = self.IdVersion10(
                    cr2, 'crm.team', ('name',), team_id2
                )

            user_id = False
            if user_id2:
                if user_id2 == 1:
                    user_id = 1
                else:
                    user_id = self.IdVersion10(
                        cr2, 'res.users', ('login',), user_id2
                    )

            dosar_id = False
            if dosar_id2 and dosar_id2 != 0:
                dosar_id = self.IdVersion10(
                    cr2, 'helpan.dosar', ('internal_identify',), dosar_id2
                )

            vals_ten.update({
                'account_id': account_id,
                'amount_tax': amount_tax,
                'amount_total': amount_total,
                'amount_total_company_signed': amount_total_company_signed,
                'amount_total_signed': amount_total_signed,
                'amount_untaxed': amount_untaxed,
                'amount_untaxed_signed': amount_untaxed_signed,
                'comment': comment,
                'commercial_partner_id': commercial_partner_id,
                'company_id': company_id,
                'currency_id': currency_id,
                'date': date,
                'date_due': date_due,
                'date_invoice': date_invoice,
                'fiscal_position_id': fiscal_position_id,
                #'incoterms_id': incoterms_id,
                'journal_id': journal_id,
                'message_last_post': message_last_post,
                'move_id': move_id2,
                'move_name': move_name2,
                'name': name,
                'number': number2,
                'origin': origin,
                'partner_bank_id': partner_bank_id,
                'partner_id': partner_id,
                'payment_term_id': payment_term_id,
                #'purchase_id': purchase_id,
                'reconciled': reconciled,
                'reference': reference,
                'reference_type': reference_type,
                'residual': residual,
                'residual_company_signed': residual_company_signed,
                'residual_signed': residual_signed,
                'sent': sent,
                'state': state,
                'team_id': team_id,
                'type': type,
                'user_id': user_id,
                'exchange_rate': exchange_rate,
                'dosar_id': dosar_id,
            })

            if state == 'paid':
                sql = """
                select
                    pay.journal_id -- 0
                    ,pay.payment_date -- 1
                    ,pay.amount -- 2
                    ,pay.currency_id -- 3
                    ,pay.payment_method_id -- 4
                    ,pay.payment_type -- 5
                    ,pay.partner_type -- 6
                    ,pay.partner_id -- 7
                    ,pay.name -- 8
                    ,pay.id -- 9
                    ,pay.state -- 10
                    ,pay.company_id -- 11
                from account_invoice_payment_rel rel
                left join account_payment pay on rel.payment_id = pay.id
                where rel.invoice_id = %s;
                """ % invoice_id2
                cr2.execute(sql)
                res_payment = cr2.fetchall()
                if not res_payment:
                    break
                for r in res_payment:
                    journal_id2 = r[0]
                    date = r[1]
                    payment_amount = r[2]
                    payment_currency_id2 = r[3]
                    payment_method_id2 = r[4]
                    payment_type = r[5]
                    partner_type = r[6]
                    payment_partner_id2 = r[7]
                    name = r[8]
                    payment_id2 = r[9]
                    state = r[10]
                    company_id2 = r[11]

                    company_id = False
                    if company_id2:
                        company_id = self.IdVersion10(
                            cr2, 'res.company', ('name',), company_id2
                        )

                    journal_id = self.IdVersion10(
                        cr2, 'account.journal', ('code',), journal_id2
                    )

                    payment_currency_id = self.IdVersion10(
                        cr2, 'res.currency', ('name',), payment_currency_id2
                    )

                    # check currency in invoice ve currency in payment
                    if currency_id2 != payment_currency_id2:
                        amount_currency = self.amount_convert_currency(
                            cr2, payment_amount, payment_currency_id2,
                            currency_id2, date, company_id2
                        )
                        payment_amount = amount_currency

                    payment_method_id = self.IdVersion10(
                        cr2, 'account.payment.method', ('name', 'payment_type'),
                        payment_method_id2
                    )

                    if not payment_partner_id2:
                        payment_partner_id2 = partner_id2  # use invoice partner
                    partner_id = self.IdVersion10(cr2, 'res.partner',
                        ('name', 'vat', 'nrc', 'company_id', 'is_company'),
                       payment_partner_id2
                    )

                    if state == 'posted':
                        cr2.execute("""
                        select m.name, m.ref
                        from account_move m where m.id = (
                            select distinct(move_id) from account_move_line aml
                            where aml.payment_id = %s
                        )""" % payment_id2)
                        res_payment_move = cr2.fetchone()

                        move_name = res_payment_move[0] or False
                        move_ref = res_payment_move[1] or False
                    else:
                        move_name, move_ref = False, False

                    payment_data.append({
                        'payment_date': date, 'amount': payment_amount,
                        'currency_id': payment_currency_id,
                        'journal_id': journal_id,
                        'payment_method_id': payment_method_id,
                        'payment_type': payment_type,
                        'partner_type': partner_type, 'partner_id': partner_id,
                        'name': name, 'move_name': move_name, 'state': state,
                        'move_ref': move_ref, 'id2': payment_id2,
                        'company_id': company_id,
                    })
            break

        return vals_ten, payment_data

    @api.model
    def InvoiceLineVals9(self, cr2, invoice_id2):
        """ Fetches invoice line from old database
        :param cr2: cursor to old database
        :param invoice_id2: int, old database invoice record ID
        :return: list of dicts
        """
        lines = []
        sql = """
        select
            account_analytic_id -- 0
            ,account_id -- 1
            ,asset_category_id -- 2
            ,asset_end_date -- 3
            ,asset_mrr -- 4
            ,asset_start_date -- 5
            ,categ_sequence -- 6
            ,company_id -- 7
            ,currency_id -- 8
            ,discount -- 9
            ,"Dosar" -- 10
            ,invoice_id -- 11
            ,name -- 12
            ,origin -- 13
            ,partner_id -- 14
            ,price_subtotal -- 15
            ,price_subtotal_signed -- 16
            ,price_unit -- 17
            ,product_id -- 18
            ,purchase_line_id -- 19
            ,quantity -- 20
            ,sale_layout_cat_id -- 21
            ,sequence -- 22
            ,uom_id -- 23
            ,id -- 24
        from account_invoice_line where invoice_id = %s
        """ % invoice_id2
        cr2.execute(sql)
        res = cr2.fetchall()
        if not res:
            raise UserError(_("""Unable to fetch invoice lines
            from %s (order ID %s)""") % (self.other_db_name, invoice_id2))

        for r in res:
            account_id2 = r[1]
            categ_sequence = r[6]
            company_id2 = r[7]
            currency_id2 = r[8]
            discount = r[9]
            dosar_id2 = r[10]
            name = r[12]
            origin = r[13]
            partner_id2 = r[14]
            price_subtotal = r[15]
            price_subtotal_signed = r[16]
            price_unit = r[17]
            product_id2 = r[18]
            quantity = r[20]
            sequence = r[22]
            uom_id2 = r[23]
            line_id = r[24]

            account_id = self.IdVersion10(
                cr2, 'account.account', ('code', 'company_id'), account_id2
            )

            partner_id = False
            if partner_id2:
                partner_id = self.IdVersion10(cr2, 'res.partner',
                    ('name', 'vat', 'nrc', 'company_id', 'is_company'),
                    partner_id2
                )

            company_id = self.IdVersion10(
                cr2, 'res.company', ('name',), company_id2
            )

            currency_id = False
            if currency_id2:
                currency_id = self.IdVersion10(
                    cr2, 'res.currency', ('name',), currency_id2
                )

            product_id = False
            if product_id2:
                product_id = self.IdVersion10Product(
                    cr2, product_id2, what='product'
                )
            uom_id = False
            if uom_id2:
                uom_id = self.IdVersion10(
                    cr2, 'product.uom', ('name',), uom_id2
                )

            dosar_id = False
            if dosar_id2 and dosar_id2 != 0:
                dosar_id = self.IdVersion10(
                    cr2, 'helpan.dosar', ('internal_identify',), dosar_id2
                )

            vals = {
                'account_id': account_id,
                #'categ_sequence': categ_sequence,
                'company_id': company_id,
                'currency_id': currency_id,
                'discount': discount,
                'dosar_id': dosar_id,
                'name': name,
                'origin': origin,
                'partner_id': partner_id,
                'price_subtotal': price_subtotal,
                'price_subtotal_signed': price_subtotal_signed,
                'price_unit': price_unit,
                'product_id': product_id,
                'quantity': quantity,
                'sequence': sequence,
                'uom_id': uom_id,

            }

            sql = """select tax_id from account_invoice_line_tax
            where invoice_line_id = %s""" % line_id
            cr2.execute(sql)
            taxes_id = []
            for tax_id2 in [t[0] for t in cr2.fetchall() if t and t[0] or False]:
                tax_id = self.IdVersion10(
                    cr2, 'account.tax', ('name',), tax_id2
                )
                taxes_id.append(tax_id)
            if taxes_id:
                vals.update({'invoice_line_tax_ids': [(6, 0, taxes_id)]})

            lines.append(vals)

        return lines

    @api.model
    def InvoicePost(self, cr2):
        use_sufix = True
        transfer_sufix = ' #66' if use_sufix else ''

        self._cr.execute("""select new_record_id,name_real,old_record_id
        from data_migrate_document_number where model = 'account.invoice'
        and field_name = 'number'
        """)
        res = self._cr.fetchall()
        _logger.debug('Updating %s invoice numbers' % len(res))
        for r in res:
            invoice_id = r[0]
            invoice_number = r[1]
            invoice_id2 = r[2]
            self.UpdateName(
                'account_invoice', invoice_id, invoice_number + transfer_sufix,
                unique_field='number'
            )

            cr2.execute("""
            select move_id from account_invoice where id = %s and
            move_id is not null
            """ % invoice_id2)
            move_id2 = cr2.fetchone()
            move_id2 = move_id2 and move_id2[0] or False
            if move_id2:
                # move name ---------------------------------------------------
                self._cr.execute("""select new_record_id,name_real
                from data_migrate_document_number where model = 'account.move'
                and old_record_id = %s and field_name = 'name'
                """ % move_id2)
                res_invoice_move = self._cr.fetchone()
                if res_invoice_move:
                    move_id = res_invoice_move[0] or False
                    name = res_invoice_move[1] or False
                    if name and move_id:
                        self.UpdateName(
                            'account_move', move_id, name + transfer_sufix
                        )

                # move ref ----------------------------------------------------
                self._cr.execute("""select new_record_id,name_real
                from data_migrate_document_number where model = 'account.move'
                and old_record_id = %s and field_name = 'ref'
                """ % move_id2)
                res_invoice_move_ref = self._cr.fetchone()
                if res_invoice_move_ref:
                    move_id = res_invoice_move_ref[0] or False
                    ref = res_invoice_move_ref[1] or False
                    if ref and move_id:
                        self.UpdateName(
                            'account_move', move_id, ref, unique_field='ref'
                        )
                        self._cr.execute("""update account_move_line set
                        ref = '%s' where move_id = %s""" % (ref, move_id))

        # payment -------------------------------------------------------------
        self._cr.execute("""select new_record_id,name_real,old_record_id
        from data_migrate_document_number where model = 'account.payment'
        and field_name = 'name'
        """)
        res = self._cr.fetchall()
        _logger.debug('Updating %s payment numbers' % len(res))
        for r in res:
            payment_id = r[0]
            name = r[1]
            if not name:
                continue
            payment_id2 = r[2]
            self.UpdateName(
                'account_payment', payment_id, name + transfer_sufix
            )

            cr2.execute("""select distinct(move_id) from account_move_line
            where payment_id = %s""" % payment_id2)
            res_payment_move = [i[0] for i in cr2.fetchall() if i and i[0] or False]
            for move_id2 in res_payment_move:
                # move name ---------------------------------------------------
                self._cr.execute("""select new_record_id,name_real
                from data_migrate_document_number where model = 'account.move'
                and old_record_id = %s and field_name = 'name'
                """ % move_id2)
                res_invoice_move_2 = self._cr.fetchone()
                if res_invoice_move_2:
                    move_id = res_invoice_move_2[0] or False
                    name = res_invoice_move_2[1] or False
                    if name and move_id:
                        self.UpdateName(
                            'account_move', move_id, name + transfer_sufix
                        )

        return True

    @staticmethod
    def amount_convert_currency(cr2, amount_src, currency_src_id, currency_dest_id, on_date, company_id):
        if currency_src_id != currency_dest_id:
            curr_ids = [currency_src_id, currency_dest_id]
            query = """
                SELECT c.id, (
                    SELECT r.rate FROM res_currency_rate r
                    WHERE
                        r.currency_id = c.id AND r.name <= %s
                        AND (r.company_id IS NULL OR r.company_id = %s)
                    ORDER BY r.company_id, r.name DESC LIMIT 1
                ) AS rate
                FROM res_currency c WHERE c.id IN %s"""
            cr2.execute(query, (on_date, company_id, tuple(curr_ids)))
            currency_rates = dict(cr2.fetchall())
            src_rate = currency_rates.get(currency_src_id, 1.0) or 1.0
            dest_rate = currency_rates.get(currency_dest_id, 1.0) or 1.0
            rate = dest_rate / src_rate
        else:
            rate = 1.0

        return round(amount_src * rate, 2)
