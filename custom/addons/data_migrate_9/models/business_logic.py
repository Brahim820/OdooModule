# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# This file is created by gordan.cuic@gmail.com

from openerp import api, fields, models, _, osv
from odoo.exceptions import UserError

class DataMigrateOrder(models.Model):
    """ Here are methods that check business logic """

    _inherit = "data.migrate.order"

    @staticmethod
    def MoreInvoicesOnePaymentCheck9(cr2):
        """ It's ok if one invoice has more than one payment but one payment
        can not have more than one invoice. This check is done in version 9
         database """
        cr2.execute("""
        with this as (
            select payment_id,count(*) as cnt from
            account_invoice_payment_rel group by payment_id
        )
        select count(*) from this where cnt > 1;
        """)
        res = cr2.fetchone()
        cnt = res and res[0] or False
        if cnt:
            msg = """There are payments that are related to more than one
            invoice"""
            raise UserError(msg)

        return True

    @staticmethod
    def PricelistItemBic(data, name):
        """ Appliance and price computation policy checkup """

        # appliance -----------------------------------------------------------
        applied_on = data.get('applied_on', False)
        assert applied_on, 'applied_on is mandatory'
        product_id = data.get('product_id', False)
        product_tmpl_id = data.get('product_tmpl_id', False)
        categ_id = data.get('categ_id', False)

        if applied_on == '0_product_variant' and not product_id:
            msg = """When applied on '0_product_variant', product_id is
            mandatory (ref: %s)""" % name
            raise UserError(msg)
        elif applied_on == '1_product' and not product_tmpl_id:
            msg = """When applied on '1_product', product_tmpl_id is
            mandatory (ref: %s)""" % name
            raise UserError(msg)
        elif applied_on == '2_product_category' and not categ_id:
            msg = """When applied on '2_product_category', categ_id is
            mandatory (ref: %s)""" % name
            raise UserError(msg)

        # price policy --------------------------------------------------------
        compute_price = data.get('compute_price', False)
        if compute_price:
            percent_price = data.get('percent_price', False)
            fixed_price = data.get('fixed_price', False)
            if compute_price == 'fixed' and fixed_price <= 0:
                msg = """When compute price is 'fixed', fixed price must be
                greater than zero (ref: %s)""" % name
                raise UserError(msg)
            elif compute_price == 'percentage' and percent_price <= 0:
                msg = """When compute price is 'fixed', percent price must be
                greater than zero (ref: %s)""" % name
                raise UserError(msg)

        return True

    @staticmethod
    def JournalBic(data, name):
        journal_currency_id = data.get('journal_currency_id', False)
        debit_currency_id = data.get('debit_currency_id', False)
        credit_currency_id = data.get('credit_currency_id', False)
        if journal_currency_id:
            if debit_currency_id and debit_currency_id != journal_currency_id:
                msg = """Journal currency diff than default debit account
                currency (ref: %s)""" % name
                raise UserError(msg)
            if credit_currency_id and credit_currency_id != journal_currency_id:
                msg = """Journal currency diff than default credit account
                currency (ref: %s)""" % name
                raise UserError(msg)

        return True

    @api.model
    def UomCategoryDefault(self, product_id, uom_id, ref, do_raise=True):
        """
        Checks if used uom's category is the same as product's default uom
        category.
        :param product_id: int, product_product record ID in version 10
        :param uom_id: int, used product_uom record ID in version 10. This uom
        is not the one that is related to product as default but the one used in
         document lines (such as pickings and purchase orders)
        :return: boolean, True
        """
        assert product_id, 'Need product_id here'
        assert uom_id, 'Need uom_id here'
        assert ref, 'Need ref here'

        if do_raise is None:
            do_raise = False

        check_ok = True
        product_obj = self.env['product.product']
        uom_obj = self.env['product.uom']
        product = product_obj.browse(product_id)
        product.ensure_one()
        default_categ_id = product.uom_id.category_id

        document_uom = uom_obj.browse(uom_id)
        document_uom.ensure_one()
        used_categ_id = document_uom.category_id
        if default_categ_id != used_categ_id:
            if do_raise:
                msg = '''Used uom [%s] %s category "%s" differs from default one
                [%s] %s %s!

                Ref: %s''' % (
                    document_uom.id, document_uom.name,
                    document_uom.category_id.name, uom_id, product.uom_id.name,
                    product.uom_id.category_id.name, ref
                )
                raise UserError(msg)
            else:
                check_ok = False

        return check_ok
