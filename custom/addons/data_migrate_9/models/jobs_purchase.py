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
    # purchase orders
    # -----------------------------------------------------------------
    @api.model
    def PurchaseOrder(self, cr2):
        order_obj = self.env['purchase.order']
        cr2.execute("""select id from purchase_order
        where state not in ('cancel') order by id""")
        order_ids2 = [i[0] for i in cr2.fetchall() if i and i[0] or False]
        if not order_ids2:
            raise UserError(_("""Unable to fetch purchase orders
            from %s""") % self.other_db_name)
        c = 0
        for order_id2 in order_ids2:
            c += 1
            if c in (1, len(order_ids2)) or c % 5 == 0:
                _logger.debug(
                    'Migrating %s/%s purchase orders' % (c, len(order_ids2))
                )
            vals = self.PurchaseOrderVals9(cr2, order_id2)
            lines = self.PurchaseOrderLineVals9(cr2, order_id2)
            order_line = [(0, 0, v) for v in lines]
            vals.update({'order_line': order_line})
            name = vals.get('name', False)
            assert name, 'Need order number here'

            args = [('name', '=', name)]
            if not order_obj.search_count(args):
                order_obj.create(vals)

        return True

    @api.model
    def PurchaseOrderVals9(self, cr2, order_id2):
        """
        Fetches purchase orders from old database and prepares dict to create()
        or write() on new database
        :param cr2: cursor to old database
        :param order_id2: int, old database sale order record ID
        :return: dict
        """
        sql = """
        select
            amount_tax -- 0
            ,amount_total -- 1
            ,amount_untaxed -- 2
            ,company_id -- 3
            ,currency_id -- 4
            ,date_approve -- 5
            ,date_order -- 6
            ,dest_address_id -- 7
            ,fiscal_position_id -- 8
            ,group_id -- 9
            ,incoterm_id -- 10
            ,invoice_status -- 11
            ,message_last_post -- 12
            ,name -- 13
            ,notes -- 14
            ,origin -- 15
            ,partner_id -- 16
            ,partner_ref -- 17
            ,payment_term_id -- 18
            ,picking_type_id -- 19
            ,requisition_id -- 20
            ,state -- 21
            ,"x_DosarID" -- 22
        from purchase_order where id = %s
        """ % order_id2
        cr2.execute(sql)
        res = cr2.fetchall()
        if not res:
            raise UserError(_("""Unable to fetch sale order
            from %s (ID %s)""") % (self.other_db_name, order_id2))
        vals = {}
        for r in res:
            amount_tax = r[0]
            amount_total = r[1]
            amount_untaxed = r[2]
            company_id2 = r[3]
            currency_id2 = r[4]
            date_approve = r[5]
            date_order = r[6]
            dest_address_id2 = r[7]
            fiscal_position_id2 = r[8]
            #group_id2 = r[9]
            #incoterm_id2 = r[10]
            invoice_status = r[11]
            message_last_post = r[12]
            name = r[13]
            notes = r[14]
            origin = r[15]
            partner_id2 = r[16]
            partner_ref = r[17]
            payment_term_id2 = r[18]
            #picking_type_id2 = r[19]
            #requisition_id2 = r[20]
            state = r[21]
            dosar_id2 = r[22]

            partner_id = self.IdVersion10(cr2, 'res.partner',
                ('name', 'vat', 'nrc', 'company_id', 'is_company'),
                partner_id2
            )

            dest_address_id = False
            if dest_address_id2:
                dest_address_id = self.IdVersion10(cr2, 'res.partner',
                    ('name', 'vat', 'nrc', 'company_id', 'is_company'),
                    partner_id2
                )

            company_id = False
            if company_id2:
                company_id = self.IdVersion10(
                    cr2, 'res.company', ('name',), company_id2
                )

            payment_term_id = False
            if payment_term_id2:
                payment_term_id = self.IdVersion10(
                    cr2, 'account.payment.term', ('name',), payment_term_id2
                )

            fiscal_position_id = False
            if fiscal_position_id2:
                fiscal_position_id = self.IdVersion10(
                    cr2, 'account.fiscal.position', ('name', 'company_id'),
                    fiscal_position_id2
                )

            currency_id = self.IdVersion10(
                cr2, 'res.currency', ('name',), currency_id2
            )

            dosar_id = False
            if dosar_id2 and dosar_id2 != 0:
                dosar_id = self.IdVersion10(
                    cr2, 'helpan_dosar.helpan_dosar', ('dosarID',), dosar_id2,
                    table='helpan_dosar_helpan_dosar'
                )

            vals.update({
                'amount_tax': amount_tax,
                'amount_total': amount_total,
                'amount_untaxed': amount_untaxed,
                'company_id': company_id,
                'currency_id': currency_id,
                'date_approve': date_approve,
                'date_order': date_order,
                'dest_address_id': dest_address_id,
                'fiscal_position_id': fiscal_position_id,
                #'group_id': group_id,
                #'incoterm_id': incoterm_id,
                'invoice_status': invoice_status,
                'message_last_post': message_last_post,
                'name': name,
                'notes': notes,
                'origin': origin,
                'partner_id': partner_id,
                'partner_ref': partner_ref,
                'payment_term_id': payment_term_id,
                'picking_type_id': 1,  # helpan only !!!
                #'requisition_id': requisition_id,
                'state': state,
                'dosar_id': dosar_id,

            })
            break

        return vals

    @api.model
    def PurchaseOrderLineVals9(self, cr2, order_id2):
        """ Fetches purchase order line from old database
        :param cr2: cursor to old database
        :param order_id2: int, old database sale order record ID
        :return: list of dicts
        """
        lines = []

        sql = """
        select
            account_analytic_id -- 0
            ,company_id -- 1
            ,currency_id -- 2
            ,date_planned -- 3
            ,"Dosar" -- 4
            ,name -- 5
            ,order_id -- 6
            ,partner_id -- 7
            ,price_subtotal -- 8
            ,price_tax -- 9
            ,price_total -- 10
            ,price_unit -- 11
            ,product_id -- 12
            ,product_qty -- 13
            ,product_uom -- 14
            ,qty_invoiced -- 15
            ,qty_received -- 16
            ,quantity_tendered -- 17
            ,id -- 18
        from purchase_order_line where order_id = %s
        order by id
        """ % order_id2
        cr2.execute(sql)
        res = cr2.fetchall()
        res = res or []

        for r in res:
            #account_analytic_id = r[0]
            company_id2 = r[1]
            currency_id2 = r[2]
            date_planned = r[3]
            dosar_id2 = r[4]
            name = r[5]
            order_id = r[6]
            partner_id2 = r[7]
            price_subtotal = r[8]
            price_tax = r[9]
            price_total = r[10]
            price_unit = r[11]
            product_id2 = r[12]
            product_qty = r[13]
            product_uom2 = r[14]
            qty_invoiced = r[15]
            qty_received = r[16]
            #quantity_tendered = r[17]
            line_id = r[18]

            partner_id = False
            if partner_id2:
                partner_id = self.IdVersion10(cr2, 'res.partner',
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

            product_id = self.IdVersion10Product(
                cr2, product_id2, what='product'
            )
            product_uom = self.IdVersion10(
                cr2, 'product.uom', ('name',), product_uom2
            )
            # check uom categories
            ref = 'PO line name %s, vernine order_id %s' % (name, order_id)
            check_ok = self.UomCategoryDefault(
                product_id, product_uom, ref, do_raise=False
            )
            if not check_ok:
                product_uom = self.SwitchUomDefault(product_id)

            dosar_id = False
            if dosar_id2 and dosar_id2 != 0:
                dosar_id = self.IdVersion10(
                    cr2, 'helpan_dosar.helpan_dosar', ('dosarID',), dosar_id2,
                    table = 'helpan_dosar_helpan_dosar'
                )

            vals = {
                #'account_analytic_id': account_analytic_id,
                'company_id': company_id,
                'currency_id': currency_id,
                'date_planned': date_planned,
                'dosar_id': dosar_id,
                'name': name,
                'partner_id': partner_id,
                'price_subtotal': price_subtotal,
                'price_tax': price_tax,
                'price_total': price_total,
                'price_unit': price_unit,
                'product_id': product_id,
                'product_qty': product_qty,
                'product_uom': product_uom,
                'qty_invoiced': qty_invoiced,
                'qty_received': qty_received,
            }

            sql = """select account_tax_id from
            account_tax_purchase_order_line_rel
            where purchase_order_line_id = %s""" % line_id
            cr2.execute(sql)
            taxes_id = []
            for tax_id2 in [t[0] for t in cr2.fetchall() if t and t[0] or False]:
                tax_id = self.IdVersion10(
                    cr2, 'account.tax', ('name',), tax_id2
                )
                taxes_id.append(tax_id)
            if taxes_id:
                vals.update({'taxes_id': [(6, 0, taxes_id)]})
            lines.append(vals)

        return lines

    @api.model
    def SwitchUomDefault(self, product_id):
        """ Returns product's default uom """
        assert product_id, 'Need product_id here'
        product = self.env['product.product'].browse(product_id)

        return product.uom_id.id


    @api.model
    def PurchaseOrderPre(self, cr2):
        return True