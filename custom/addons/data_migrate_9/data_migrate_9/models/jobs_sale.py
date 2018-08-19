# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# This file is created by gordan.cuic@gmail.com

from openerp import api, fields, models, _, osv
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)

class DataMigrateOrder(models.Model):
    _inherit = "data.migrate.order"

    # -----------------------------------------------------------------
    # pre sale orders
    # -----------------------------------------------------------------
    @api.model
    def SaleOrderPre(self, cr2):
        # price lists -------------------------------------------------
        list_obj = self.env['product.pricelist']
        cr2.execute("""select
            id, name, company_id, currency_id, active
        from product_pricelist order by id""")
        res = cr2.fetchall()
        if not res:
            raise UserError(_("""Unable to fetch product price list
            from %s""") % self.other_db_name)
        done_lists = {}
        for r in res:
            list_id2 = r[0]
            name = r[1]
            company_id2 = r[2]
            currency_id2 = r[3]
            active = r[4]

            company_id = False
            if company_id2:
                company_id = self.IdVersion10(
                    cr2, 'res.company', ('name',), company_id2
                )

            currency_id = self.IdVersion10(
                cr2, 'res.currency', ('name',), currency_id2
            )

            vals = {
                'name': name, 'company_id': company_id,
                'currency_id': currency_id, 'active': active,
            }

            args = [('name', '=', name), ('active', '=', active)]
            if list_id2 == 1:
                done_lists[name] = (list_id2, list_id2)
            elif list_obj.search_count(args):
                lists = list_obj.search(args)
                lists.ensure_one()
                lists.write(vals)
                # (old list ID, new list ID)
                done_lists[name] = (list_id2, lists.id)
            else:
                # (old list ID, new list ID)
                done_lists[name] = (list_id2, list_obj.create(vals))

        # price lists items -------------------------------------------
        for name, tt in done_lists.items():
            list_id2 = tt[0]
            if not isinstance(tt[1], (int, long)):
                pricelist_id = tt[1].id
            else:
                pricelist_id = tt[1]
            item_obj = self.env['product.pricelist.item']
            cr2.execute("""select id from product_pricelist_item
            where pricelist_id = %s order by id""" % list_id2)
            item_ids2 = [i[0] for i in cr2.fetchall() if i and i[0] or False]
            c = 0
            for item_id2 in item_ids2:
                c += 1
                if c in (1, len(item_ids2)) or c % 50 == 0:
                    _logger.debug(
                        'Migrating %s/%s price list items' % (c, len(item_ids2))
                    )
                vals = self.PricelistItemVals9(cr2, item_id2)
                self.PricelistItemBic(vals, name)
                product_tmpl_id = vals.get('product_tmpl_id', False)
                product_id = vals.get('product_id', False)
                categ_id = vals.get('categ_id', False)
                date_start = vals.get('date_start', False)
                date_end = vals.get('date_end', False)
                args = [('product_tmpl_id', '=', product_tmpl_id),
                        ('product_id', '=', product_id),
                        ('categ_id', '=', categ_id),
                        ('pricelist_id', '=', pricelist_id),
                        ('date_start', '=', date_start),
                        ('date_end', '=', date_end)]
                if item_obj.search_count(args):
                    item = item_obj.search(args)
                    item.ensure_one()
                    item.write(vals)
                    item._onchange_applied_on()
                    item._onchange_compute_price()
                else:
                    item = item_obj.create(vals)
                    item.ensure_one()
                    item._onchange_applied_on()
                    item._onchange_compute_price()
        # payment terms -----------------------------------------------
        term_obj = self.env['account.payment.term']
        sql = """
        select
            name, company_id, note, active, id
        from account_payment_term order by name
        """
        cr2.execute(sql)
        res = cr2.fetchall()
        created = []
        for r in res:
            name2, company_id2, note = r[0], r[1], r[2]
            active = r[3] or False
            term_id2 = r[4]
            name = self.translated_value(
                cr2, 'ro_RO', 'account.payment.term', name2,
                res_id=term_id2, field_name='name'
            )
            if (name, active) in created:
                continue
            company_id = False
            if company_id2:
                company_id = self.IdVersion10(
                    cr2, 'res.company', ('name',), company_id2
                )
            vals = {
                'name': name, 'company_id': company_id, 'note': note,
                'active': active,
            }
            args = [('name', '=', name), ('active', '=', active)]
            if term_obj.search_count(args):
                term = term_obj.search(args)
                term.ensure_one()
                term.write(vals)
            else:
                term_obj.create(vals)
                created.append((name, active))

        # product packaging -------------------------------------------
        pack_obj = self.env['product.packaging']
        sql = """select
            name, sequence, qty, product_tmpl_id
        from product_packaging order by name"""
        cr2.execute(sql)
        res = cr2.fetchall()
        for r in res:
            name, sequence, qty = r[0], r[1], r[2]
            product_tmpl_id2 = r[3]

            tempalte_id = self.IdVersion10Product(
                cr2, product_tmpl_id2, what='template'
            )
            vals = {
                'name': name, 'sequence': sequence, 'qty': qty,
                'product_tmpl_id': tempalte_id,
            }
            args = [('product_tmpl_id', '=', tempalte_id)]
            if pack_obj.search_count(args):
                pack_obj.ensure_one()
                pack_obj.write(vals)
            else:
                pack_obj.create(vals)

        return True

    @api.model
    def PricelistItemVals9(self, cr2, item_id2):
        """
        Fetches price list items from old database and prepares dict to create()
        or write() on new database
        :param cr2: cursor to old database
        :param item_id2: int, old database price list item record ID
        :return: dict
        """
        sql = """
        select
            applied_on -- 0
            ,base -- 1
            ,base_pricelist_id -- 2
            ,categ_id -- 3
            ,company_id -- 4
            ,compute_price -- 5
            ,create_date -- 6
            ,create_uid -- 7
            ,currency_id -- 8
            ,date_end -- 9
            ,date_start -- 10
            ,fixed_price -- 11
            ,id -- 12
            ,min_quantity -- 13
            ,percent_price -- 14
            ,price_discount -- 15
            ,pricelist_id -- 16
            ,price_max_margin -- 17
            ,price_min_margin -- 18
            ,price_round -- 19
            ,price_surcharge -- 20
            ,product_id -- 21
            ,product_tmpl_id -- 22
            ,sequence -- 23
            ,write_date -- 24
            ,write_uid -- 25
        from product_pricelist_item where id = %s
        """ % item_id2
        cr2.execute(sql)
        res = cr2.fetchall()
        if not res:
            raise UserError(_("""Unable to fetch product pricelist item
            from %s (ID %s)""") % (self.other_db_name, item_id2))
        vals = {}
        for r in res:
            applied_on = r[0]
            base = r[1]
            base_pricelist_id2 = r[2]
            categ_id2 = r[3]
            company_id2 = r[4]
            compute_price = r[5]
            currency_id2 = r[8]
            date_end = r[9]
            date_start = r[10]
            fixed_price = r[11]
            min_quantity = r[13]
            percent_price = r[14]
            price_discount = r[15]
            pricelist_id2 = r[16]
            price_max_margin = r[17]
            price_min_margin = r[18]
            price_round = r[19]
            price_surcharge = r[20]
            product_id2 = r[21]
            product_tmpl_id2 = r[22]
            sequence = r[23]

            if base_pricelist_id2:
                base_pricelist_id = self.IdVersion10(
                    cr2, 'product.pricelist', ('name',), base_pricelist_id2
                )
            else:
                base_pricelist_id = False

            if categ_id2:
                categ_id = self.IdVersion10(
                    cr2, 'product.category', ('name',), categ_id2
                )
            else:
                categ_id = False

            if company_id2:
                company_id = self.IdVersion10(
                    cr2, 'res.company', ('name',), company_id2
                )
            else:
                company_id = False

            if currency_id2:
                currency_id = self.IdVersion10(
                    cr2, 'res.currency', ('name',), currency_id2
                )
            else:
                currency_id = False

            if pricelist_id2:
                pricelist_id = self.IdVersion10(
                    cr2, 'product.pricelist', ('name',), pricelist_id2
                )
            else:
                pricelist_id = False

            if product_id2:
                product_id = self.IdVersion10Product(
                    cr2, product_id2, what='product'
                )
            else:
                product_id = False

            if product_tmpl_id2:
                product_tmpl_id = self.IdVersion10Product(
                    cr2, product_tmpl_id2, what='template'
                )
            else:
                product_tmpl_id = False


            vals.update({
                'applied_on': applied_on,
                'base': base,
                'base_pricelist_id': base_pricelist_id,
                'categ_id': categ_id,
                'company_id': company_id,
                'compute_price': compute_price,
                'currency_id': currency_id,
                'date_end': date_end,
                'date_start': date_start,
                'fixed_price': fixed_price,
                'min_quantity': min_quantity,
                'percent_price': percent_price,
                'price_discount': price_discount,
                'pricelist_id': pricelist_id,
                'price_max_margin': price_max_margin,
                'price_min_margin': price_min_margin,
                'price_round': price_round,
                'price_surcharge': price_surcharge,
                'product_id': product_id,
                'product_tmpl_id': product_tmpl_id,
                'sequence': sequence,
            })
            break

        return vals

    # -----------------------------------------------------------------
    # sale orders
    # -----------------------------------------------------------------
    @api.model
    def SaleOrder(self, cr2):
        order_obj = self.env['sale.order']
        cr2.execute("select id from sale_order order by id")
        order_ids2 = [i[0] for i in cr2.fetchall() if i and i[0] or False]
        if not order_ids2:
            raise UserError(_("""Unable to fetch sale orders
            from %s""") % self.other_db_name)
        c = 0
        for order_id2 in order_ids2:
            c += 1
            if c in (1, len(order_ids2)) or c % 5 == 0:
                _logger.debug(
                    'Migrating %s/%s sale orders' % (c, len(order_ids2))
                )
            vals = self.SaleOrderVals9(cr2, order_id2)
            lines = self.SaleOrderLineVals9(cr2, order_id2)
            order_line = [(0, 0, v) for v in lines]
            vals.update({'order_line': order_line})
            name = vals.get('name', False)
            assert name, 'Need order number here'

            args = [('name', '=', name)]
            if not order_obj.search_count(args):
                order_obj.create(vals)

        return True

    @api.model
    def SaleOrderVals9(self, cr2, order_id2):
        """
        Fetches sale orders from old database and prepares dict to create()
        or write() on new database
        :param cr2: cursor to old database
        :param order_id2: int, old database sale order record ID
        :return: dict
        """
        sql = """
        select
            origin -- r[0]
            ,team_id -- r[1]
            ,client_order_ref -- r[2]
            ,date_order -- r[3]
            ,partner_id -- r[4]
            ,procurement_group_id -- r[5]
            ,amount_untaxed -- r[6]
            ,message_last_post -- r[7]
            ,company_id -- r[8]
            ,note -- r[9]
            ,state -- r[10]
            ,pricelist_id -- r[11]
            ,project_id -- r[12]
            ,amount_tax -- r[13]
            ,validity_date -- r[14]
            ,payment_term_id -- r[15]
            ,partner_invoice_id -- r[16]
            ,user_id -- r[17]
            ,fiscal_position_id -- r[18]
            ,amount_total -- r[19]
            ,invoice_status -- r[20]
            ,name -- r[21]
            ,partner_shipping_id -- r[22]
            ,campaign_id -- r[23]
            ,opportunity_id -- r[24]
            ,medium_id -- r[25]
            ,source_id -- r[26]
            ,picking_policy -- r[27]
            ,incoterm -- r[28]
            ,warehouse_id -- r[29]
            ,carrier_id -- r[30]
            ,delivery_price -- r[31]
            ,invoice_shipping_on_delivery -- r[32]
            ,1 as some1 -- quote_viewed -- r[33]
            ,1 as some2 -- require_payment -- r[34]
            ,1 as some3 -- access_token -- r[35]
            ,1 as some4 -- website_description -- r[36]
            ,1 as some5 -- template_id -- r[37]
            ,"x_Dosar" -- r[38]
        from sale_order where id = %s
        """ % order_id2
        cr2.execute(sql)
        res = cr2.fetchall()
        if not res:
            raise UserError(_("""Unable to fetch sale order
            from %s (ID %s)""") % (self.other_db_name, order_id2))
        vals = {}
        for r in res:
            origin = r[0]
            team_id2 = r[1]
            client_order_ref = r[2]
            date_order = r[3]
            partner_id2 = r[4]
            #procurement_group_id2 = r[5]
            amount_untaxed = r[6]
            message_last_post = r[7]
            company_id2 = r[8]
            note = r[9]
            state = r[10]
            pricelist_id2 = r[11]
            #project_id2 = r[12]
            amount_tax = r[13]
            validity_date = r[14]
            payment_term_id2 = r[15]
            partner_invoice_id2 = r[16]
            user_id2 = r[17]
            fiscal_position_id2 = r[18]
            amount_total = r[19]
            invoice_status = r[20]
            name = r[21]
            partner_shipping_id2 = r[22]
            campaign_id2 = r[23]
            #opportunity_id2 = r[24]
            medium_id2 = r[25]
            source_id2 = r[26]
            picking_policy = r[27]
            incoterm2 = r[28]
            warehouse_id2 = r[29]
            carrier_id2 = r[30]
            delivery_price = r[31]
            invoice_shipping_on_delivery = r[32]
            quote_viewed = r[33]
            require_payment = r[34]
            access_token = r[35]
            website_description = r[36]
            template_id2 = r[37]
            x_Dosar = r[38]

            team_id = False
            if team_id2:
                team_id = self.IdVersion10(
                    cr2, 'crm.team', ('name',), team_id2
                )

            partner_id = self.IdVersion10(cr2, 'res.partner',
                ('name', 'vat', 'nrc', 'company_id', 'is_company'),
                partner_id2
            )

            company_id = False
            if company_id2:
                company_id = self.IdVersion10(
                    cr2, 'res.company', ('name',), company_id2
                )

            pricelist_id = False
            if pricelist_id2:
                pricelist_id = self.IdVersion10(
                    cr2, 'product.pricelist', ('name',), pricelist_id2
                )

            payment_term_id = False
            if payment_term_id2:
                payment_term_id = self.IdVersion10(
                    cr2, 'account.payment.term', ('name',), payment_term_id2
                )

            partner_invoice_id = False
            if partner_invoice_id2:
                partner_invoice_id = self.IdVersion10(cr2, 'res.partner',
                    ('name', 'vat', 'nrc', 'company_id', 'is_company'),
                    partner_invoice_id2
                )

            partner_shipping_id = False
            if partner_shipping_id2:
                partner_shipping_id = self.IdVersion10(cr2, 'res.partner',
                    ('name', 'vat', 'nrc', 'company_id', 'is_company'),
                    partner_shipping_id2
                )

            user_id = False
            if user_id2:
                if user_id2 == 1:
                    user_id = 1
                else:
                    user_id = self.IdVersion10(
                        cr2, 'res.users', ('login',), user_id2
                    )

            fiscal_position_id = False
            if fiscal_position_id2:
                fiscal_position_id = self.IdVersion10(
                    cr2, 'account.fiscal.position', ('name', 'company_id'),
                    fiscal_position_id2
                )
            '''
            campaign_id = False
            if campaign_id2:
                campaign_id = self.IdVersion10(
                    cr2, 'utm.campaign', ('name',),
                    campaign_id2
                )

            opportunity_id = False
            if opportunity_id2:
                opportunity_id = self.IdVersion10(
                    cr2, 'crm.lead', ('name', 'partner_id'),
                    opportunity_id2
                )

            medium_id = False
            if medium_id2:
                medium_id = self.IdVersion10(
                    cr2, 'utm.medium', ('name', 'active'),
                    medium_id2
                )

            source_id = False
            if source_id2:
                source_id = self.IdVersion10(
                    cr2, 'utm.source', ('name',),
                    source_id2
                )

            incoterm = False
            if incoterm2:
                incoterm = self.IdVersion10(
                    cr2, 'stock.incoterms', ('name','code'),
                    incoterm2
                )

            warehouse_id = False
            if warehouse_id2:
                warehouse_id = self.IdVersion10(
                    cr2, 'stock.warehouse', ('code', 'name'),
                    warehouse_id2
                )

            carrier_id = False
            if carrier_id2:
                carrier_id = self.IdVersion10(
                    cr2, 'stock.warehouse', ('code', 'name'),
                    carrier_id2
                )

            template_id = False
            if template_id2:
                template_id = self.IdVersion10(
                    cr2, 'sale.quote.template', ('name',),
                    template_id2
                )
            '''

            vals.update({
                'origin': origin,
                'team_id': team_id,
                'client_order_ref': client_order_ref,
                'date_order': date_order,
                'partner_id': partner_id,
                'amount_untaxed': amount_untaxed,
                'message_last_post': message_last_post,
                'company_id': company_id,
                'note': note,
                'state': state,
                'pricelist_id': pricelist_id,
                'amount_tax': amount_tax,
                'validity_date': validity_date,
                'payment_term_id': payment_term_id,
                'partner_invoice_id': partner_invoice_id,
                'user_id': user_id,
                'fiscal_position_id': fiscal_position_id,
                'amount_total': amount_total,
                'invoice_status': invoice_status,
                'name': name,
                'partner_shipping_id': partner_shipping_id,
                'picking_policy': picking_policy,
                #'delivery_price': delivery_price,
                #'invoice_shipping_on_delivery': invoice_shipping_on_delivery,
                #'quote_viewed': quote_viewed,
                #'require_payment': require_payment,
                #'access_token': access_token,
                #'website_description': website_description,
                #'template_id': template_id,
                #'x_Dosar': x_Dosar,
            })
            break

        return vals

    @api.model
    def SaleOrderLineVals9(self, cr2, order_id2):
        """ Fetches sale order line from old database
        :param cr2: cursor to old database
        :param order_id2: int, old database sale order record ID
        :return: list of dicts
        """
        lines = []

        sql = """
        select
            categ_sequence -- 0
            ,company_id -- 1
            ,create_date -- 2
            ,create_uid -- 3
            ,currency_id -- 4
            ,customer_lead -- 5
            ,discount -- 6
            ,id -- 7
            ,invoice_status -- 8
            ,is_delivery -- 9
            ,name -- 10
            ,order_id -- 11
            ,order_partner_id -- 12
            ,price_reduce -- 13
            ,price_subtotal -- 14
            ,price_tax -- 15
            ,price_total -- 16
            ,price_unit -- 17
            ,product_id -- 18
            ,product_packaging -- 19
            ,product_uom -- 20
            ,product_uom_qty -- 21
            ,qty_delivered -- 22
            ,qty_invoiced -- 23
            ,qty_to_invoice -- 24
            ,route_id -- 25
            ,sale_layout_cat_id -- 26
            ,salesman_id -- 27
            ,sequence -- 28
            ,state -- 29
            ,1 as some5 -- website_description -- 30
        from sale_order_line where order_id = %s
        order by sequence
        """ % order_id2
        cr2.execute(sql)
        res = cr2.fetchall()
        if not res:
            raise UserError(_("""Unable to fetch sale order lines
            from %s (order ID %s)""") % (self.other_db_name, order_id2))

        for r in res:
            categ_sequence = r[0]
            company_id2 = r[1]
            currency_id2 = r[4]
            #customer_lead = r[5]
            discount = r[6]
            line_id = r[7]
            invoice_status = r[8]
            is_delivery = r[9]
            name = r[10]
            #order_id = r[11]
            order_partner_id2 = r[12]
            price_reduce = r[13]
            price_subtotal = r[14]
            price_tax = r[15]
            price_total = r[16]
            price_unit = r[17]
            product_id2 = r[18]
            product_packaging = r[19]
            product_uom2 = r[20]
            product_uom_qty = r[21]
            qty_delivered = r[22]
            qty_invoiced = r[23]
            qty_to_invoice = r[24]
            #route_id2 = r[25]
            sale_layout_cat_id2 = r[26]
            salesman_id2 = r[27]
            sequence = r[28]
            state = r[29]
            website_description = r[30]

            order_partner_id = False
            if order_partner_id2:
                order_partner_id = self.IdVersion10(cr2, 'res.partner',
                    ('name', 'vat', 'nrc', 'company_id', 'is_company'),
                    order_partner_id2
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

            salesman_id = False
            if salesman_id2:
                if salesman_id2 == 1:
                    salesman_id = 1
                else:
                    salesman_id = self.IdVersion10(
                        cr2, 'res.users', ('login',), salesman_id2
                    )

            product_id = self.IdVersion10Product(
                cr2, product_id2, what='product'
            )
            product_uom = self.IdVersion10(
                cr2, 'product.uom', ('name',), product_uom2
            )

            vals = {
                #'categ_sequence': categ_sequence,
                'company_id': company_id,
                'currency_id': currency_id,
                #'customer_lead': customer_lead,
                'discount': discount,
                'invoice_status': invoice_status,
                #'is_delivery': is_delivery,
                'name': name,
                'order_partner_id': order_partner_id,
                'price_reduce': price_reduce,
                'price_subtotal': price_subtotal,
                'price_tax': price_tax,
                'price_total': price_total,
                'price_unit': price_unit,
                'product_id': product_id,
                'product_packaging': product_packaging,
                'product_uom': product_uom,
                'product_uom_qty': product_uom_qty,
                'qty_delivered': qty_delivered,
                'qty_invoiced': qty_invoiced,
                'qty_to_invoice': qty_to_invoice,
                #'route_id': route_id,
                #'sale_layout_cat_id': sale_layout_cat_id,
                'salesman_id': salesman_id,
                'sequence': sequence,
                'state': state,
                #'website_description': website_description,
            }

            sql = """select account_tax_id from account_tax_sale_order_line_rel
            where sale_order_line_id = %s""" % line_id
            cr2.execute(sql)
            taxes_id = []
            for tax_id2 in [t[0] for t in cr2.fetchall() if t and t[0] or False]:
                tax_id = self.IdVersion10(
                    cr2, 'account.tax', ('name',), tax_id2
                )
                taxes_id.append(tax_id)
            if taxes_id:
                vals.update({'tax_id': [(6, 0, taxes_id)]})
            lines.append(vals)

        return lines
