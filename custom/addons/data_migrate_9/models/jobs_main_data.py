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

    # -----------------------------------------------------------------
    # currency
    # -----------------------------------------------------------------
    @api.model
    def Currencies(self, cr2):
        # pre-check Account decimal_precision
        dp_obj = self.env['decimal.precision']
        rate_obj = self.env['res.currency.rate']
        args = [('name', '=', 'Account')]
        if not dp_obj.search_count(args):
            dp_obj.create({'name': 'Account', 'digits': 2})
        sql = "select id from res_currency order by id"
        cr2.execute(sql)
        currency_ids2 = [i[0] for i in cr2.fetchall() if i and i[0] or False]
        if not currency_ids2:
            raise UserError(_("""Unable to fetch currencies from %s
            """) % self.other_db_name)
        currency_obj = self.env['res.currency']
        for currency_id2 in currency_ids2:

            vals = self.CurrenciesVals9(cr2, currency_id2)
            name = vals.get('name', False)
            assert name, 'Need currency name here'

            self._cr.execute("""select id from res_currency
            where name = '%s'""" % name)
            currs = self._cr.fetchone()
            currency_id = currs and currs[0] or False
            if currency_id:
                active = vals.get('active', False)
                symbol = vals.get('symbol', False)
                rounding = vals.get('rounding', False)
                position = vals.get('position', False)
                self._cr.execute("""
                    update res_currency set
                        active = %s, symbol = '%s', rounding = %s,
                        position = '%s'
                    where id = %s
                    """ % (
                        active, symbol, rounding or 0.0,
                        position or '', currency_id
                    )
                )
            else:
                if not vals.get('symbol', False):
                    vals.update({'symbol': 'XX'})
                currency = currency_obj.create(vals)
                currency_id = currency.id

            # currency rates --------------------------------------------------
            cr2.execute("""select name, company_id, rate
            from res_currency_rate where currency_id = %s;
            """ % currency_id2)
            res = cr2.fetchall()
            for r in res:
                name = r[0]
                company_id2 = r[1]
                rate_amount = r[2]

                company_id = self.IdVersion10(
                    cr2, 'res.company', ('name',), company_id2
                )

                args = [('currency_id', '=', currency_id),
                        ('company_id', '=', company_id),
                        ('name', '=', name)]
                if rate_obj.search_count(args):
                    rate = rate_obj.search(args)
                    rate.ensure_one()
                    rate.write({'rate': rate_amount})
                else:
                    rate_obj.create({
                        'name': name, 'company_id': company_id,
                        'currency_id': currency_id, 'rate': rate_amount,
                    })


        return True

    @api.model
    def CurrenciesVals9(self, cr2, currency_id2):
        """
        Fetches currencies from old database and prepares dict to create() or
        write() on new database
        :param cr2: cursor to old database
        :param currency_id2: int, old database currency record ID
        :return: dict
        """
        sql = """select
            name -- 0
            ,symbol -- 1
            ,rounding -- 2
            ,active -- 3
            ,position -- 4
        from res_currency where id = %s
        """ % currency_id2
        cr2.execute(sql)
        res = cr2.fetchall()
        if not res:
            raise UserError(_("""Unable to fetch currencies
            from %s (ID %s)""") % (self.other_db_name, currency_id2))
        vals = {}
        for r in res:
            name, symbol, rounding, active = r[0], r[1], r[2], r[3]
            position = r[4]
            vals.update({
                'name': name, 'symbol': symbol, 'rounding': rounding,
                'active': active, 'position': position
            })

        return vals

    # -----------------------------------------------------------------
    # country
    # -----------------------------------------------------------------
    @api.model
    def Countries(self, cr2):
        sql = "select id from res_country order by id"
        cr2.execute(sql)
        country_ids2 = [i[0] for i in cr2.fetchall() if i and i[0] or False]
        if not country_ids2:
            raise UserError(_("""Unable to fetch countries from %s
            """) % self.other_db_name)
        country_obj = self.env['res.country']
        for country_id2 in country_ids2:
            vals = self.CountriesVals9(cr2, country_id2)
            code = vals.get('code', False)
            if not code:
                # some countries had no code (like ROMAINA, even though
                # that country was already in country records
                continue
            args = [('code', '=', code)]
            if country_obj.search_count(args):
                countries = country_obj.search(args)
                countries.ensure_one()
                countries.write(vals)
            else:
                country_obj.create(vals)

        return True

    @api.model
    def CountriesVals9(self,  cr2, country_id2):
        """
        Fetches countries from old database and prepares dict to create() or
        write() on new database
        :param cr2: cursor to old database
        :param country_id2: int, old database country record ID
        :return: dict
        """
        sql = """select
            code -- 0
            ,name -- 1
            ,currency_id -- 2
            ,address_format --  3
            ,phone_code -- 4
        from res_country where id = %s
        """ % country_id2
        cr2.execute(sql)
        res = cr2.fetchall()
        if not res:
            raise UserError(_("""Unable to fetch countries
            from %s (ID %s)""") % (self.other_db_name, country_id2))
        vals = {}
        for r in res:
            code, name, currency_id2, address_format = r[0], r[1], r[2], r[3]
            phone_code = r[4]

            currency_id = False
            if currency_id2:
                currency_id = self.IdVersion10(
                    cr2, 'res.currency', ('name',), currency_id2
                )

            vals.update({
                'code': code, 'name': name, 'currency_id': currency_id,
                'address_format': address_format, 'phone_code': phone_code,
            })

        return vals

    # -----------------------------------------------------------------
    # country states
    # -----------------------------------------------------------------
    @api.model
    def CountryStates(self, cr2):
        state_obj = self.env['res.country.state']
        sql = "select id from res_country_state order by id"
        cr2.execute(sql)
        state_ids2 = [i[0] for i in cr2.fetchall() if i and i[0] or False]
        if not state_ids2:
            raise UserError(_("""Unable to
            fetch states from %s""") % self.other_db_name)
        for state_id2 in state_ids2:
            vals = self.CountryStatesVals9(cr2, state_id2)

            code = vals.get('code', False)
            assert code, 'Need state code here'
            country_id = vals.get('country_id', False)
            assert country_id, 'Need country_id here'

            args = [('code', '=', code),
                    ('country_id', '=', country_id)]
            if state_obj.search_count(args):
                state_ids = state_obj.search(args)
                state_ids.ensure_one()
                del vals['country_id']
                state_ids.write(vals)
            else:
                state_obj.create(vals)

        return True

    @api.model
    def CountryStatesVals9(self, cr2, state_id2):
        """
        Fetches country states from old database and prepares dict to create()
        or write() on new database
        :param cr2: cursor to old database
        :param state_id2: int, old database state record ID
        :return: dict
        """
        sql = """select code, name, country_id
        from res_country_state where id = %s
        """ % state_id2
        cr2.execute(sql)
        res = cr2.fetchall()
        if not res:
            raise UserError(_("""Unable to fetch states data
            from %s (ID %s)""") % (self.other_db_name, state_id2))
        vals = {}
        for r in res:
            code, name, country_id2 = r[0], r[1], r[2]
            if country_id2:
                country_id = self.IdVersion10(
                    cr2, 'res.country', ('code', 'name'), country_id2
                )
                if not country_id:
                    raise UserError(_("""Unable to find matching
                    country in new database"""))
            else:
                country_id = False
            vals.update({
                'code': code, 'name': name, 'country_id': country_id
            })

        return vals

    # -----------------------------------------------------------------
    # company
    # -----------------------------------------------------------------
    @api.model
    def Company(self, cr2):
        sql = """
        select id from res_company where parent_id is null
        order by id
        """
        cr2.execute(sql)
        company_ids2 = [i[0] for i in cr2.fetchall() if i and i[0] or False]
        if not company_ids2:
            raise UserError(_("""Unable to fetch master company from %s
            """) % self.other_db_name)

        company_obj = self.env['res.company']
        for company_id2 in company_ids2:
            vals = self.CompanyVals9(cr2, company_id2)
            if company_id2 == 1:
                args = [('id', '=', company_id2)]
                companies = company_obj.search(args)
                companies.ensure_one()
                companies.write(vals)
            else:
                name = vals.get('name', False)
                assert name, 'Need company name here'
                args = [('name', '=', name)]
                if company_obj.search_count(args):
                    companies = company_obj.search(args)
                    companies.ensure_one()
                    companies.write(vals)
                else:
                    company_obj.create(vals)
        return True

    @api.model
    def CompanyVals9(self, cr2, company_id2):
        """
        Fetches company data from old database and prepares dict to create()
        or write() on new database
        :param cr2: cursor to old database
        :param company_id2: int, old database company record ID
        :return: dict
        """
        sql = """
        select
            comp.name -- 0
            ,comp.rml_header1 -- 1
            ,comp.company_registry -- 2
            ,comp.partner_id -- 3

            ,comp.currency_id -- 4
            ,comp.currency_exchange_journal_id -- 5
            ,comp.vat_check_vies -- 6
            ,comp.anglo_saxon_accounting -- 7
            ,comp.bank_account_code_prefix -- 8
            ,comp.cash_account_code_prefix -- 9
            ,comp.accounts_code_digits -- 10
            ,comp.tax_calculation_rounding_method -- 11

            ,comp.timesheet_range -- 12
            ,comp.timesheet_max_difference -- 13

            ,comp.po_lead -- 14
            ,comp.po_double_validation -- 15
            ,comp.po_double_validation_amount -- 16
            ,comp.manufacturing_lead -- 17
            ,comp.security_lead -- 18
            ,comp.sale_note -- 19

            ,comp.overdue_msg -- 20

            ,part.street -- 21
            ,part.street2 -- 22
            ,part.city -- 23
            ,part.state_id -- 24
            ,part.zip -- 25
            ,part.country_id -- 26
            ,part.website -- 27
            ,part.phone -- 28
            ,part.fax -- 29
            ,part.email -- 30
            ,part.vat -- 31

        from res_company comp
        left join res_partner part on comp.partner_id = part.id
        where comp.id = %s""" % company_id2
        cr2.execute(sql)
        res = cr2.fetchall()
        if not res:
            raise UserError(_("""Unable to fetch company data
            from %s (ID %s)""") % (self.other_db_name, company_id2))
        vals = {}
        for r in res:
            name = r[0]
            rml_header1 = r[1]
            company_registry = r[2]

            currency_id2 = r[4]
            currency_exchange_journal_id = r[5]
            vat_check_vies = r[6] or False
            anglo_saxon_accounting = r[7]
            bank_account_code_prefix = r[8]
            cash_account_code_prefix = r[9]
            accounts_code_digits = r[10]
            tax_calculation_rounding_method = r[11]

            street = r[21]
            street2 = r[22]
            city = r[23]
            state_id2 = r[24] or False
            zip = r[25]
            country_id2 = r[26]  # skip country
            website = r[27]
            phone = r[28]
            fax = r[29]
            email = r[30]
            vat = r[31]

            currency_id = self.IdVersion10(
                cr2, 'res.currency', ('name',), currency_id2
            )

            state_id = False
            if state_id2:
                state_id = self.IdVersion10(
                    cr2, 'res.country.state', ('code', 'country_id'), state_id2
                )

            vals.update({
                'name': name, 'rml_header1': rml_header1,
                'company_registry': company_registry,

                'currency_id': currency_id,
                'vat_check_vies': vat_check_vies,
                'anglo_saxon_accounting': anglo_saxon_accounting,
                'bank_account_code_prefix': bank_account_code_prefix,
                'cash_account_code_prefix': cash_account_code_prefix,
                'accounts_code_digits': accounts_code_digits,
                'tax_calculation_rounding_method': tax_calculation_rounding_method,

                'street': street,
                'street2': street2,
                'city': city,
                'state_id': state_id,
                'zip': zip,
                'website': website,
                'phone': phone,
                'fax': fax,
                'email': email,
                'vat': vat,
            })

        return vals
    # -----------------------------------------------------------------
    # users
    # -----------------------------------------------------------------
    @api.model
    def Users(self, cr2):
        users_obj = self.env['res.users']
        sql = """
        select id from res_users where id != 1 and login not in (
            'public', 'portaltemplate'
        )"""
        cr2.execute(sql)
        user_ids2 = [i[0] for i in cr2.fetchall() if i and i[0] or False]
        if not user_ids2:
            raise UserError(_("""Unable to
            fetch users from %s""") % self.other_db_name)
        for user_id2 in user_ids2:
            vals = self.UsersVals9(cr2, user_id2)
            login = vals.get('login', False)
            assert login, 'Need user login name here'

            args = [('login', '=', login)]
            if users_obj.search_count(args):
                users = users_obj.search(args)
                users.ensure_one()
                users.write(vals)
                user = users[0]
            else:
                user = users_obj.create(vals)
            assert isinstance(user.id, (int, long)), 'User must be int'

            # update groups
            group_ids = self.UserGroupsVals9(cr2, user_id2)
            if not group_ids:
                continue

            sql = """delete from res_groups_users_rel
            where uid = %s;""" % user.id
            self._cr.execute(sql)
            for gid in group_ids:
                sql = """insert into res_groups_users_rel
                (uid, gid) values (%s, %s);""" % (user.id, gid)
                self._cr.execute(sql)

        return True

    @api.model
    def UsersVals9(self, cr2, user_id2):
        """
        Fetches user data from old database and prepares dict to create()
        or write() on new database
        :param cr2: cursor to old database
        :param user_id2: int, old database user record ID
        :return: dict
        """
        sql = """
        select
            u.active -- 0
            ,u.login -- 1
            ,u.password -- 2
            ,u.company_id -- 3
            ,u.partner_id -- 4
            ,u.share -- 5
            ,u.signature -- 6
            ,u.action_id -- 7
            ,u.password_crypt -- 8
            ,u.alias_id -- 9
            ,u.chatter_needaction_auto -- 10
            ,u.sale_team_id -- 11
            ,u.target_sales_done -- 12
            ,u.target_sales_won -- 13
            ,u.target_sales_invoiced -- 14

            ,p.name -- 15
            ,p.email -- 16
        from res_users u
        left join res_partner p on u.partner_id = p.id
        where u.id = %s
        """ % (user_id2,)
        cr2.execute(sql)
        res = cr2.fetchall()
        if not res:
            raise UserError(_("""Unable to fetch users data
            from %s (ID %s)""") % (self.other_db_name, user_id2))
        vals = {}
        for r in res:
            active = r[0]
            login = r[1]
            password = r[2]
            company_id2 = r[3]
            share = r[5]
            signature = r[6]
            password_crypt = r[8]
            chatter_needaction_auto = r[10]
            target_sales_done = r[12]
            target_sales_won = r[13]
            target_sales_invoiced = r[14]

            partner_name = r[15]
            partner_email = r[16]

            company_id = self.IdVersion10(
                cr2, 'res.company', ('name',), company_id2
            )

            vals.update({
                'active': active,
                'login': login,
                'password': password,
                'company_id': company_id,
                'share': share,
                'signature': signature,
                'password_crypt': password_crypt,
                'chatter_needaction_auto': chatter_needaction_auto,
                'target_sales_done': target_sales_done,
                'target_sales_won': target_sales_won,
                'target_sales_invoiced': target_sales_invoiced,

                'name': partner_name,
                'email': partner_email,
            })


        return vals

    @api.model
    def UserGroupsVals9(self, cr2, user_id2):
        """
        Fetches user access groups from old database and locates matching groups
        records in new database
        :param cr2: cursor to old database
        :param user_id2: int, old database user record ID
        :return: list, group IDs that this user needs to have in new database
        """
        group_ids = []
        sql = """
        select gid from res_groups_users_rel where uid = %s;
        """ % user_id2
        cr2.execute(sql)
        res = cr2.fetchall()
        if not res:
            # break -----------------------------------------------------------
            return []

        skip_these = ['group_configuration', 'group_advance_bidding',
            'group_light_multi_company', 'group_website_designer',
            'group_website_publisher','group_uos',
        ]
        mapped_groups_xmls = {
            'group_fleet_manager': 'fleet_group_manager',
            'group_fleet_user': 'fleet_group_user',
        }
        for r in res:
            group_id2 = r[0]
            if not group_id2:
                continue
            sql = """select name, module from ir_model_data
            where model = 'res.groups' and res_id = %s""" % group_id2
            cr2.execute(sql)
            xml_res = cr2.fetchall()
            if not xml_res:
                raise UserError(_("""Unable to find ir_model_data record for
                group ID %s in old database""") % group_id2)
            if len(xml_res) > 1:
                raise UserError(_("""Found multiple ir_model_data records for
                group ID %s in old database""") % group_id2)

            xml_name, xml_module = False, False
            for i in xml_res:
                xml_name = i[0]
                xml_module = i[1]

            if xml_name in skip_these:
                continue
            if xml_name in mapped_groups_xmls:
                xml_name = mapped_groups_xmls.get(xml_name)

            if 'group_hr_' in xml_name and xml_module == 'base':
                xml_module = 'hr'
            elif xml_name in ('group_sale_manager', 'group_sale_salesman_all_leads', 'group_sale_salesman'):
                xml_module = 'sales_team'
            elif xml_name in ('group_lead_automation_manager', 'group_lead_automation_user'):
                xml_module = 'marketing_campaign'
            elif xml_name in ('group_equipment_manager'):
                xml_module = 'maintenance'
            elif xml_name in ('group_locations') and xml_module == 'stock':
                xml_name = 'group_stock_multi_locations'

            imd = self.env['ir.model.data'].search([
                ('model', '=', 'res.groups'), ('name', '=', xml_name),
                ('module', '=', xml_module)]
            )
            if not imd:
                raise UserError(_("""Unable to find ir_model_data record in new
                database for name %s.%s""") % (xml_module,xml_name))
            imd.ensure_one()
            res_id = imd.res_id
            assert isinstance(res_id, (int, long)), 'res_id must be int'
            group_ids.append(res_id)

        return group_ids

    @api.model
    def UserPost(self, cr2):
        """ Update related partner data """
        users_obj = self.env['res.users']
        args = [('id', '!=', 1)]
        if users_obj.search_count(args):
            verten_data = []
            partner_obj = self.env['res.partner']
            for user in users_obj.search(args):
                if user.partner_id:
                    verten_data.append((user.login, user.partner_id.id))
            for login, partner_id in verten_data:
                sql = """
                select vat,nrc from res_partner where id = (
                    select partner_id from res_users where
                    login = '%s'
                )
                """ % login
                cr2.execute(sql)
                res = cr2.fetchone()
                if not res:
                    continue
                vat, nrc = res[0], res[1]
                vals = {}
                if vat:
                    vals.update({'vat': vat})
                if nrc:
                    vals.update({'nrc': nrc})
                if not vals:
                    continue
                partner = partner_obj.search([('id', '=', partner_id)])
                partner.ensure_one()
                partner.write(vals)

        return True

    # -----------------------------------------------------------------
    # pre partners
    # -----------------------------------------------------------------
    @api.model
    def PartnersPre(self, cr2):
        """ Partner titles """
        title_obj = self.env['res.partner.title']
        cr2.execute("select id from res_partner_title order by id")
        title_ids2 = [i[0] for i in cr2.fetchall() if i and i[0] or False]
        if title_ids2:
            _logger.debug('Migrating %s titles' % len(title_ids2))
            for title_id2 in title_ids2:
                vals = self.PartnerTitleVals9(cr2, title_id2)
                name = vals.get('name', False)
                assert name, 'Need partner title name here'
                args = [('name', '=', name)]
                if title_obj.search_count(args):
                    titles = title_obj.search(args)
                    titles.ensure_one()
                    titles.write(vals)
                else:
                    title_obj.create(vals)
        else:
            _logger.debug('No res_partner_title in old database')

        return True

    @api.model
    def PartnerTitleVals9(self, cr2, title_id2):
        """
        Fetches partner titles from old database and prepares dict to create()
        or write() on new database
        :param cr2: cursor to old database
        :param title_id2: int, old database partner title record ID
        :return: dict
        """
        sql = """select
            name, shortcut
        from res_partner_title where id = %s
        """ % title_id2
        cr2.execute(sql)
        res = cr2.fetchall()
        if not res:
            raise UserError(_("""Unable to fetch partner titles
            from %s (ID %s)""") % (self.other_db_name, title_id2))
        vals = {}
        for r in res:
            name, shortcut = r[0], r[1]
            vals.update({'name': name, 'shortcut': shortcut})
            break

        return vals

    # -----------------------------------------------------------------
    # partners
    # -----------------------------------------------------------------
    @api.model
    def Partners(self, cr2):
        partner_obj = self.env['res.partner']
        sql = """
        select id from res_partner where id not in (
            select distinct(partner_id) from res_users
        ) and id not in (
            select distinct(partner_id) from res_company
        )
        """
        cr2.execute(sql)
        partner_ids2 = [i[0] for i in cr2.fetchall() if i and i[0] or False]
        if not partner_ids2:
            raise UserError(_("""Unable to
            fetch partners from %s""") % self.other_db_name)

        c = 0
        for partner_id2 in partner_ids2:
            c += 1
            if c in (1, len(partner_ids2)) or c % 50 == 0:
                _logger.debug(
                    'Migrating %s/%s partners' % (c, len(partner_ids2))
                )
            vals = self.PartnersVals9(cr2, partner_id2)
            name = vals.get('name', False)
            assert name, 'Need partner name here'
            active = vals.get('active', False)
            is_company = vals.get('is_company', False)
            company_id = vals.get('company_id', False)
            vat = vals.get('vat', False)
            args = [('name', '=', name), ('active', '=', active),
                    ('is_company', '=', is_company),
                    ('company_id', '=', company_id), ('vat', '=', vat)]
            if partner_obj.search_count(args):
                partner_obj.search(args).write(vals)
            else:
                partner_obj.create(vals)

        return True

    def PartnersVals9(self, cr2, partner_id2):
        """
        Fetches partners from old database and prepares dict to create()
        or write() on new database
        :param cr2: cursor to old database
        :param partner_id2: int, old database partner record ID
        :return: dict
        """
        sql = """
        select
            name -- 0
            ,company_id -- 1
            ,comment -- 2
            ,function -- 3
            ,create_date -- 4
            ,color -- 5
            ,company_type -- 6
            ,date -- 7
            ,street -- 8
            ,city -- 9
            ,display_name -- 10
            ,zip -- 11
            ,title -- 12
            ,country_id -- 13
            ,parent_id -- 14
            ,supplier -- 15
            ,ref -- 16
            ,email -- 17
            ,is_company -- 18
            ,website -- 19
            ,customer -- 20
            ,fax -- 21
            ,street2 -- 22
            ,barcode -- 23
            ,employee -- 24
            ,active -- 25
            ,credit_limit -- 26
            ,tz -- 27
            ,lang -- 28
            ,phone -- 29
            ,mobile -- 30
            ,type -- 31
            ,use_parent_address -- 32
            ,user_id -- 33
            ,vat -- 34
            ,birthdate -- 35
            ,state_id -- 36
            ,commercial_partner_id -- 37
            ,notify_email -- 38
            ,message_last_post -- 39
            ,opt_out -- 40
            ,signup_type -- 41
            ,signup_expiration -- 42
            ,signup_token -- 43
            ,team_id -- 44
            ,last_time_entries_checked -- 45
            ,debit_limit -- 46
            ,nrc -- 47
            ,age -- 48
            ,birth_date -- 49
            ,calendar_last_notif_ack -- 50
            ,picking_warn -- 51
            ,sale_warn -- 52
            ,purchase_warn -- 53
            ,picking_warn_msg -- 54
            ,invoice_warn_msg -- 55
            ,invoice_warn -- 56
            ,purchase_warn_msg -- 57
            ,sale_warn_msg -- 58
        from res_partner where id = %s
        order by name
        """ % partner_id2
        cr2.execute(sql)
        res = cr2.fetchall()
        if not res:
            raise UserError(_("""Unable to fetch partner data
            from %s (ID %s)""") % (self.other_db_name, partner_id2))
        vals = {}
        for r in res:
            name = r[0]
            company_id2 = r[1]
            comment = r[2]
            function = r[3]
            create_date = r[4]
            color = r[5]
            company_type = r[6]
            date = r[7]
            street = r[8]
            city = r[9]
            display_name = r[10]
            zip = r[11]
            title = r[12]
            country_id2 = r[13]
            supplier = r[15]
            ref = r[16]
            email = r[17]
            is_company = r[18]
            website = r[19]
            customer = r[20]
            fax = r[21]
            street2 = r[22]
            barcode = r[23]
            employee = r[24]
            active = r[25]
            credit_limit = r[26]
            tz = r[27]
            lang = r[28]
            phone = r[29]
            mobile = r[30]
            type = r[31]
            use_parent_address = r[32]
            user_id2 = r[33]
            vat = r[34]
            birthdate = r[35]
            state_id2 = r[36]
            notify_email = r[38]
            message_last_post = r[39]
            opt_out = r[40]
            signup_type = r[41]
            signup_expiration = r[42]
            signup_token = r[43]
            last_time_entries_checked = r[45]
            debit_limit = r[46]
            nrc = r[47]
            age = r[48]
            birth_date = r[49]
            calendar_last_notif_ack = r[50]
            picking_warn = r[51]
            sale_warn = r[52]
            purchase_warn = r[53]
            picking_warn_msg = r[54]
            invoice_warn_msg = r[55]
            invoice_warn = r[56]
            purchase_warn_msg = r[57]
            sale_warn_msg = r[58]

            if company_id2:
                company_id = self.IdVersion10(
                    cr2, 'res.company', ('name',), company_id2
                )
                if not company_id:
                    raise UserError(_("""Unable to find matching
                    company in new database"""))
            else:
                company_id = False

            if country_id2:
                country_id = self.IdVersion10(
                    cr2, 'res.country', ('code', 'name'), country_id2
                )
                if not country_id:
                    raise UserError(_("""Unable to find matching
                    country in new database"""))
            else:
                country_id = False

            if user_id2:
                if user_id2 == 1:
                    user_id = 1  # admin user (do not migrate)
                else:
                    user_id = self.IdVersion10(
                        cr2, 'res.users', ('login',), user_id2
                    )
                    if not user_id:
                        raise UserError(_("""Unable to find matching
                        user in new database"""))
            else:
                user_id = False

            if state_id2:
                state_id = self.IdVersion10(
                    cr2, 'res.country.state', ('code', 'country_id'), state_id2
                )
                if not state_id:
                    raise UserError(_("""Unable to find matching state in new
                    database"""))
            else:
                state_id = False

            vals.update({
                'name': name,
                'company_id': company_id,
                'comment': comment,
                'function': function,
                'create_date': create_date,
                'color': color,
                'company_type': company_type,
                'date': date,
                'street': street,
                'city': city,
                'display_name': display_name,
                'zip': zip,
                'title': title,
                'country_id': country_id,
                'supplier': supplier,
                'ref': ref,
                'email': email,
                'is_company': is_company,
                'website': website,
                'customer': customer,
                'fax': fax,
                'street2': street2,
                'barcode': barcode,
                'employee': employee,
                'active': active,
                'credit_limit': credit_limit,
                'tz': tz,
                'lang': lang,
                'phone': phone,
                'mobile': mobile,
                'type': type,
                #'use_parent_address': use_parent_address,
                'user_id': user_id,
                'vat': vat,
                #'birthdate': birthdate,
                'state_id': state_id,
                'notify_email': notify_email,
                'message_last_post': message_last_post,
                'opt_out': opt_out,
                'signup_type': signup_type,
                'signup_expiration': signup_expiration,
                'signup_token': signup_token,
                'last_time_entries_checked': last_time_entries_checked,
                'debit_limit': debit_limit,
                'nrc': nrc,
                #'age': age,
                #'birth_date': birth_date,
                'calendar_last_notif_ack': calendar_last_notif_ack,
                'picking_warn': picking_warn,
                'sale_warn': sale_warn,
                'purchase_warn': purchase_warn,
                'picking_warn_msg': picking_warn_msg,
                'invoice_warn_msg': invoice_warn_msg,
                'invoice_warn': invoice_warn,
                'purchase_warn_msg': purchase_warn_msg,
                'sale_warn_msg': sale_warn_msg,

            })

        return vals

    # -----------------------------------------------------------------
    # partners post
    # -----------------------------------------------------------------
    @api.model
    def PartnersPost(self, cr2):
        # contacts ----------------------------------------------------
        partner_obj = self.env['res.partner']
        sql = """
        select
            supplier,is_company,type,id,customer,function,
            commercial_partner_id,parent_id, customer,
            street, street2, zip, city, state_id, country_id,
            website, phone, mobile, fax, email, title
        from res_partner where parent_id is not null
        """
        cr2.execute(sql)
        res = cr2.fetchall()
        for r in res:
            supplier = r[0]
            is_company, ttype, partner_id2 = r[1], r[2], r[3]
            customer, function, parent_id2 = r[4], r[5], r[6]
            commercial_partner_id2, customer = r[7], r[8]

            street, street2, zzip = r[9], r[10], r[11]
            city, state_id2, country_id2 = r[12], r[13], r[14]

            website, phone, mobile = r[15], r[16], r[17]
            fax, email, title2 = r[18], r[19], r[20]

            parent_id = self.IdVersion10(cr2, 'res.partner',
                ('name', 'vat', 'nrc', 'company_id', 'is_company'),
                parent_id2
            )

            partner_id = self.IdVersion10(cr2, 'res.partner',
                ('name', 'vat', 'nrc', 'company_id', 'is_company'),
                partner_id2
            )

            country_id = False
            if country_id2:
                country_id = self.IdVersion10(
                    cr2, 'res.country', ('code', 'name'), country_id2
                )

            state_id = False
            if state_id2:
                state_id = self.IdVersion10(
                    cr2, 'res.country.state', ('code', 'country_id'), state_id2
                )

            title = False
            if title2:
                title = self.IdVersion10(
                    cr2, 'res.partner.title', ('name',), title2
                )

            partner = partner_obj.browse(partner_id)
            partner.ensure_one()
            partner.write({
                'is_company': is_company, 'type': ttype, 'customer': customer,
                'supplier': supplier, 'function': function,
                'parent_id': parent_id, 'street': street, 'street2': street2,
                'zip': zzip, 'city': city, 'state_id': state_id,
                'country_id': country_id, 'website': website, 'phone': phone,
                'mobile': mobile, 'fax': fax, 'email': email, 'title': title,
            })


        # res bank ----------------------------------------------------
        bank_obj = self.env['res.bank']
        partner_bank_obj = self.env['res.partner.bank']
        sql = """
        select bic from res_bank where bic is not null order by bic
        """
        cr2.execute(sql)
        bics = [b[0] for b in cr2.fetchall() if b and b[0] or False]
        c = 0
        for bic in bics:
            c += 1
            _logger.debug(
                'Migrating %s/%s banks' % (c, len(bics))
            )
            args = [('bic', '=', bic)]
            if not bank_obj.search_count(args):
                sql = """
                select
                    active -- 0
                    ,bic -- 1
                    ,city -- 2
                    ,country -- 3
                    ,email -- 4
                    ,fax -- 5
                    ,name -- 6
                    ,phone -- 7
                    ,state -- 8
                    ,street -- 9
                    ,street2 -- 10
                    ,zip -- 11
                    ,id -- 12
                from res_bank where bic = '%s'
                """ % bic
                cr2.execute(sql)
                r = cr2.fetchone()

                bic = r[1]
                city = r[2]
                country2 = r[3]
                email = r[4]
                fax = r[5]
                name = r[6]
                phone = r[7]
                state2 = r[8]
                street = r[9]
                street2 = r[10]
                zip = r[11]
                bank_id2 = r[12]

                country = False
                if country2:
                    country = self.IdVersion10(
                        cr2, 'res.country', ('code', 'name'), country2
                    )
                state = False
                if state2:
                    state = self.IdVersion10(
                        cr2, 'res.country.state', ('code', 'country_id'), state2
                    )

                bank = bank_obj.create({
                    'active': True,
                    'bic': bic,
                    'city': city,
                    'country': country,
                    'email': email,
                    'fax': fax,
                    'name': name,
                    'phone': phone,
                    'state': state,
                    'street': street,
                    'street2': street2,
                    'zip': zip,
                })
            else:
                bank = bank_obj.search(args)
                sql = """
                select id from res_bank where bic = '%s' and active is True
                """ % bic
                cr2.execute(sql)
                res = [i[0] for i in cr2.fetchall() if i and i[0] or False]
                assert res, 'Need res_bank ID here from old db'
                assert len(res) == 1, 'Found more than one res_bank record for bic'
                bank_id2 = res[0]

            # res parnter bank ----------------------------------------
            sql = """
            select
                acc_number -- 0
                ,bank_id -- 1
                ,company_id -- 2
                ,currency_id -- 3
                ,partner_id -- 4
                ,sanitized_acc_number -- 5
                ,sequence -- 6
            from res_partner_bank
            where bank_id = %s
            """ % bank_id2
            cr2.execute(sql)
            res = cr2.fetchall()
            for r in res:
                acc_number = r[0]
                company_id2 = r[2]
                currency_id2 = r[3]
                partner_id2 = r[4]
                sanitized_acc_number = r[5]
                assert sanitized_acc_number, 'Need bank account number'
                sequence = r[6]

                partner_id = False
                if partner_id2:
                    partner_id = self.IdVersion10(
                        cr2, 'res.partner',
                        ('name', 'vat', 'nrc', 'company_id', 'is_company'),
                        partner_id2
                    )

                company_id = False
                if company_id2:
                    company_id = self.IdVersion10(
                        cr2, 'res.company', ('name',), company_id2
                    )

                currency_id = False
                if currency_id2:
                    currency_id = self.IdVersion10(
                        cr2, 'res.currency', ('name',), currency_id2
                    )

                vals = {
                    'acc_number': acc_number,
                    'bank_id': bank.id,
                    'company_id': company_id,
                    'currency_id': currency_id,
                    'partner_id': partner_id,
                    'sanitized_acc_number': sanitized_acc_number,
                    'sequence': sequence
                }
                args = [('sanitized_acc_number', '=', sanitized_acc_number)]
                if not partner_bank_obj.search_count(args):
                    partner_bank_obj.create(vals)

        return True


    # -----------------------------------------------------------------
    # product uoms and uom categories
    # -----------------------------------------------------------------
    @api.model
    def Uom(self, cr2):
        # product_uom_categ -------------------------------------------
        _logger.debug('Migrating Unit of measure categories')
        categ_obj = self.env['product.uom.categ']
        cr2.execute("select name from product_uom_categ order by name")
        categ_names2 = [i[0] for i in cr2.fetchall() if i and i[0] or False]
        if not categ_names2:
            raise UserError(_("""Unable to fetch product uom categories
            from %s""") % self.other_db_name)
        for categ_name2 in categ_names2:
            categ_name = self.mapped_uom_category(categ_name2)
            assert categ_name, 'Need uom category name here'
            args = [('name', '=', categ_name)]
            if not categ_obj.search_count(args):
                categ_obj.create({'name': categ_name})
        _logger.debug('Migrating Unit of measures')

        # product_uom -------------------------------------------------
        uom_obj = self.env['product.uom']
        cr2.execute("select id from product_uom order by id")
        uom_ids2 = [i[0] for i in cr2.fetchall() if i and i[0] or False]
        if not uom_ids2:
            raise UserError(_("""Unable to fetch product uoms
            from %s""") % self.other_db_name)
        new_inserted = []
        for uom_id2 in uom_ids2:
            vals = self.UomVals9(cr2, uom_id2)
            name = vals.get('name', False)
            assert name, 'Need uom name here'
            name = self.mapped_uom_name(name)
            assert name, 'Need mapped uom name here'
            args = [('name', '=', name)]
            if uom_obj.search_count(args):
                uoms = uom_obj.search(args)
                uoms.ensure_one()
                uoms.write(vals)
            else:
                if name not in new_inserted:
                    uom_obj.create(vals)
                new_inserted.append(name)

        return True

    @api.model
    def UomVals9(self, cr2, uom_id2):
        """
        Fetches product uoms from old database and prepares dict to create()
        or write() on new database
        :param cr2: cursor to old database
        :param uom_id2: int, old database product uom record ID
        :return: dict
        """
        sql = """
        select
            name -- 0
            ,rounding -- 1
            ,active -- 2
            ,factor -- 3
            ,uom_type -- 4
            ,category_id -- 5
        from product_uom where id = %s
        """ % uom_id2
        cr2.execute(sql)
        res = cr2.fetchall()
        if not res:
            raise UserError(_("""Unable to fetch product uoms
            from %s (ID %s)""") % (self.other_db_name, uom_id2))
        vals = {}
        for r in res:
            name2 = r[0]
            rounding = r[1]
            active = r[2]
            factor = r[3]
            uom_type = r[4]
            category_id2 = r[5]

            name = self.mapped_uom_name(name2)
            category_id = self.IdVersion10(
                cr2, 'product.uom.categ', ('name',), category_id2
            )
            if not category_id:
                raise UserError(_("""Unable to find matching
                product uom category in new database"""))

            vals.update({
                'name': name,
                'rounding': rounding,
                'active': active,
                'factor': factor,
                'uom_type': uom_type,
                'category_id': category_id,
            })
            break

        return vals

    @staticmethod
    def mapped_uom_category(categ_name2):
        mapped = {
            'Unit': 'Unit',
            'Weight': 'Weight',
            'Working Time': 'Working Time',
            'Length / Distance': 'Length / Distance',
            'Volume': 'Volume',
            'ML': 'Volume',
            'SET': 'Unit',
            'KG': 'Weight',
            'BUCATI': 'Unit',
            'Unsorted / Imported': 'Unit',
            'Units': 'Unit',
            'MP': 'Unit',
            'SAC': 'Unit',
            'LITRI': 'Volume',
            'Unsorted/Imported Units': 'Unit',
            #'Bucăţi': 'Unit',  # UTF issue
        }
        if categ_name2[:2].lower() == 'bu':
            categ_name = 'Unit'
        else:
            categ_name = mapped.get(categ_name2, categ_name2)

        return categ_name

    @staticmethod
    def mapped_uom_name(vernine_uom):
        # This is only for HELPAN
        verten_uom = False

        if vernine_uom[:3].lower() in ('bua', 'buc'):
            verten_uom = 'Unit(s)'
        elif vernine_uom[:2].lower() == 'kg':
            verten_uom = 'kg'
        elif vernine_uom.lower() == 'litri':
            verten_uom = 'Liter(s)'
        elif vernine_uom.lower() in ('metri', 'metri liniari'):
            verten_uom = 'm'
        elif vernine_uom in ('MP', 'mp'):
            verten_uom = 'mp'
        elif vernine_uom.lower() in 'set':
            verten_uom = 'set'
        elif vernine_uom[:4].lower() in 'unit':
            verten_uom = 'Unit(s)'
        else:
            verten_uom = vernine_uom

        return verten_uom
    # -----------------------------------------------------------------
    # products
    # -----------------------------------------------------------------
    @api.model
    def Product(self, cr2):
        product_obj = self.env['product.product']
        cr2.execute("select id from product_product order by id")
        product_ids2 = [i[0] for i in cr2.fetchall() if i and i[0] or False]

        # test
        # product_ids2 = [176]

        if not product_ids2:
            raise UserError(_("""Unable to fetch products
            from %s""") % self.other_db_name)
        c = 0
        for product_id2 in product_ids2:
            c += 1
            if c in (1, len(product_ids2)) or c % 100 == 0:
                _logger.debug(
                    'Migrating %s/%s products' % (c, len(product_ids2))
                )
            vals = self.ProductVals9(cr2, product_id2)
            name = vals.get('name', False)
            assert name, 'Need product name here'
            company_id = vals.get('company_id', False)
            uom_id = vals.get('uom_id', False)
            assert uom_id, 'Need uom_id here'
            uom_po_id = vals.get('uom_po_id', False)
            if uom_po_id:
                # check if same categ
                uom_obj = self.env['product.uom']
                uom = uom_obj.browse(uom_id)
                uom_po = uom_obj.browse(uom_po_id)
                if uom.category_id.id != uom_po.category_id.id:
                    # don't migrate purchase uom if in diff category
                    # than default uom
                    vals.update({'uom_po_id': uom_id})
                    # msg = """'%s' has diff category for uom '%s' and
                    # purchase uom '%s'
                    # """ % (name, uom.name, uom_po.name)
                    # raise UserError(msg)

            # force everything to be active
            vals.update({'active': True})

            default_code = vals.get('default_code', False)
            args = [('name', '=', name), ('uom_id', '=', uom_id),
                    ('company_id', '=', company_id),
                    ('default_code', '=', default_code)]
            if product_obj.search_count(args):
                product = product_obj.search(args)
                product.ensure_one()
                product.write(vals)
            else:
                product_obj.create(vals)

        return True

    @api.model
    def ProductVals9(self, cr2, product_id2):
        """
        Fetches products from old database and prepares dict to create()
        or write() on new database
        :param cr2: cursor to old database
        :param product_id2: int, old database product record ID
        :return: dict
        """
        sql = """
        select
            -- product_product
            p.default_code -- 0
            ,p.name_template -- 1
            ,p.message_last_post -- 2
            ,p.barcode -- 3
            ,p.volume -- 4
            -- product_template
            ,t.warranty -- 5
            ,t.list_price -- 6
            ,t.weight -- 7
            ,t.sequence -- 8
            ,t.color -- 9
            ,t.uom_id -- 10
            ,t.description_purchase -- 11
            ,t.sale_ok -- 12
            ,t.categ_id -- 13
            ,t.product_manager -- 14
            ,t.message_last_post -- 15
            ,t.company_id -- 16
            ,t.state -- 17
            ,t.uom_po_id -- 18
            ,t.description_sale -- 19
            ,t.description -- 20
            ,t.volume -- 21
            ,t.active -- 22
            ,t.rental -- 23
            ,t.name -- 24
            ,t.type -- 25
            ,t.description_picking -- 26
            ,t.sale_delay -- 27
            ,t.tracking -- 28
            ,t.purchase_method -- 29
            ,t.purchase_ok -- 30
            ,t.purchase_requisition -- 31
            ,t.asset_category_id -- 32
            ,t.deferred_revenue_category_id -- 33
            ,t.track_service -- 34
            ,t.invoice_policy -- 35
            ,t.intrastat_id -- 36
            ,t.purchase_line_warn_msg -- 37
            ,t.sale_line_warn_msg -- 38
            ,t.purchase_line_warn -- 39
            ,t.sale_line_warn -- 40
            ,1 as some1 -- t.website_description -- 41
            ,1 as some2 -- t.quote_description -- 42
            ,t.produce_delay -- 43
            ,p.product_tmpl_id -- 44
        from product_product p
        left join product_template t on p.product_tmpl_id = t.id
        where p.id = %s order by t.name
        """ % product_id2
        cr2.execute(sql)
        res = cr2.fetchall()
        if not res:
            raise UserError(_("""Unable to fetch products
            from %s (ID %s)""") % (self.other_db_name, product_id2))
        vals = {}
        for r in res:
            # product_product
            default_code = r[0]
            #name_template = r[1]
            message_last_post = r[2]
            barcode = r[3]
            volume = r[4]
            # product_template
            warranty = r[5]
            list_price = r[6]
            weight = r[7]
            sequence = r[8]
            color = r[9]
            uom_id2 = r[10]
            description_purchase = r[11]
            sale_ok = r[12]
            categ_id2 = r[13]
            #product_manager2 = r[14]  # this is m2o
            message_last_post = r[15]
            company_id2 = r[16]
            #state = r[17]
            uom_po_id2 = r[18]
            description_sale = r[19]
            description = r[20]
            volume = r[21]
            active = r[22]
            rental = r[23]
            name = r[24]
            type = r[25]
            description_picking = r[26]
            sale_delay = r[27]
            tracking = r[28]
            purchase_method = r[29]
            purchase_ok = r[30]
            #purchase_requisition = r[31]
            asset_category_id2 = r[32]
            deferred_revenue_category_id2 = r[33]
            track_service = r[34]
            invoice_policy = r[35]
            intrastat_id2 = r[36]
            purchase_line_warn_msg = r[37]
            sale_line_warn_msg = r[38]
            purchase_line_warn = r[39]
            sale_line_warn = r[40]
            #website_description = r[41]
            #quote_description = r[42]
            produce_delay = r[43]
            product_tmpl_id2 = r[44]

            if invoice_policy and invoice_policy == 'cost':
                invoice_policy = 'order'

            # translatable fields
            lang, model_name = 'ro_RO', 'product.template'
            name = self.translated_value(cr2, lang, model_name, name,
                res_id=product_tmpl_id2, field_name='name'
            )
            if description:
                description = self.translated_value(
                    cr2, lang, model_name, description, res_id=product_tmpl_id2,
                    field_name='description'
                )
            else:
                description = False

            if description_sale:
                description_sale = self.translated_value(
                    cr2, lang, model_name, description_sale,
                    res_id=product_tmpl_id2, field_name='description_sale'
                )
            else:
                description_sale = False

            if description_purchase:
                description_purchase = self.translated_value(
                    cr2, lang, model_name, description_purchase,
                    res_id=product_tmpl_id2, field_name='description_purchase'
                )
            else:
                description_purchase = False

            if description_picking:
                description_picking = self.translated_value(
                    cr2, lang, model_name, description_picking,
                    res_id=product_tmpl_id2, field_name='description_picking'
                )
            else:
                description_picking = False

            uom_id = self.IdVersion10(
                cr2, 'product.uom', ('name',), uom_id2
            )

            uom_po_id = self.IdVersion10(
                cr2, 'product.uom', ('name',), uom_po_id2
            )

            if company_id2:
                company_id = self.IdVersion10(
                    cr2, 'res.company', ('name',), company_id2
                )
            else:
                company_id = False

            categ_id = self.IdVersion10(
                cr2, 'product.category', ('name',), categ_id2
            )

            vals.update({
                # product_product
                'default_code': default_code,
                'barcode': barcode,
                # product_template
                'warranty': warranty,
                'list_price': list_price,
                'weight': weight,
                'sequence': sequence,
                'color': color,
                'uom_id': uom_id,
                'description_purchase': description_purchase,
                'sale_ok': sale_ok,
                'categ_id': categ_id,
                'message_last_post': message_last_post,
                'company_id': company_id,
                'uom_po_id': uom_po_id,
                'description_sale': description_sale,
                'description': description,
                'volume': volume,
                'active': active,
                'rental': rental,
                'name': name,
                'type': type,
                'description_picking': description_picking,
                'sale_delay': sale_delay,
                'tracking': tracking,
                'purchase_method': purchase_method,
                'purchase_ok': purchase_ok,
                'track_service': track_service,
                'invoice_policy': invoice_policy,
                'purchase_line_warn_msg': purchase_line_warn_msg,
                'sale_line_warn_msg': sale_line_warn_msg,
                'purchase_line_warn': purchase_line_warn,
                'sale_line_warn': sale_line_warn,
                'produce_delay': produce_delay,
            })

            # taxes -----------------------------------------------------------
            sql = """select tax_id from product_taxes_rel
            where prod_id = %s""" % product_id2
            cr2.execute(sql)
            taxes_id = []
            for tax_id2 in [t[0] for t in cr2.fetchall() if t and t[0] or False]:
                tax_id = self.IdVersion10(
                    cr2, 'account.tax', ('name',), tax_id2
                )
                taxes_id.append(tax_id)
            if taxes_id:
                vals.update({'taxes_id': [(6, 0, taxes_id)]})

            sql = """select tax_id from product_supplier_taxes_rel
            where prod_id = %s""" % product_id2
            cr2.execute(sql)
            supplier_taxes_id = []
            for tax_id2 in [t[0] for t in cr2.fetchall() if t and t[0] or False]:
                tax_id = self.IdVersion10(
                    cr2, 'account.tax', ('name',), tax_id2
                )
                supplier_taxes_id.append(tax_id)
            if supplier_taxes_id:
                vals.update({'supplier_taxes_id': [(6, 0, supplier_taxes_id)]})
            break

        return vals
