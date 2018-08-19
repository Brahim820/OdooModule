# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# This file is created by gordan.cuic@gmail.com

import openerp
from openerp import api, fields, models, _, osv
from openerp.osv.orm import setup_modifiers
from lxml import etree


class SaleOrder(models.Model):
    _inherit = "sale.order"

    # fields ------------------------------------------------------------------
    print_with_spec = fields.Boolean(string='Print with specification?')

    @api.multi
    def print_quotation_with_spec(self):
        """
        For printing quote or sale order with product specification and images
        in the second page. Other than changing document's state, method will
        set print_with_spec field to True
        """
        self.filtered(lambda s: s.state == 'draft').write({'state': 'sent'})
        self.write({'print_with_spec': True})
        return self.env['report'].get_action(self, 'sale.report_saleorder')

    @api.multi
    def print_quotation(self):
        self.filtered(lambda s: s.state == 'draft').write({'state': 'sent'})
        self.write({'print_with_spec': False})
        return self.env['report'].get_action(self, 'sale.report_saleorder')


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'
    desc_html = fields.Html('Description HTML')

    def _get_product_desc(self):
        """ Returns product description (specification) in html. Sequence:
        1. desc_variant_html
        2. desc_template_html
        3. description_sale
        """

        def _has_html(this):
            """ Helper to test if html field has any real content """
            # TODO: there must be a better way to check if html has any real content, not just only empty elements
            has = False
            if this and this not in (u'<p><br></p>', '<p><br></p>'):
                has = True

            return has

        desc_html = False
        if _has_html(self.product_id.desc_variant_html):
            desc_html = self.product_id.desc_variant_html
        elif _has_html(self.product_id.desc_template_html):
            desc_html = self.product_id.desc_template_html
        elif self.product_id.description_sale:
            desc_html = self.product_id.description_sale

        if not desc_html:
            desc_html = self.name
        else:
            if self.product_id.default_code:
                desc_html_pref = u'[%s] %s' % (
                    self.product_id.default_code, self.product_id.name
                )
            else:
                desc_html_pref = u'%s' % self.product_id.name
            desc_html = desc_html_pref + desc_html

        return desc_html

    @api.multi
    @api.onchange('product_id')
    def product_id_change(self):
        res = super(SaleOrderLine, self).product_id_change()
        if self.product_id:
            self.update({'desc_html': self._get_product_desc()})

        return res

    @api.multi
    def write(self, vals):
        """ Updates desc_html just in case if it's been tempered with """
        vals.update({'desc_html': self._get_product_desc()})
        res = super(SaleOrderLine, self).write(vals)
        return res

    @api.model
    def create(self, vals):
        """ Updates desc_html just in case if it's been tempered with """
        if 'desc_html' not in vals or not vals['desc_html']:
            vals.update({'desc_html': self._get_product_desc()})
        res = super(SaleOrderLine, self).create(vals)
        return res


class product_template(models.Model):
    """ Adding html fields for stylized description"""
    _inherit = "product.template"

    # fields ------------------------------------------------------------------
    desc_template_html = fields.Html('Template description HTML')
    attachment_ids = fields.Many2many(
        'ir.attachment', 'product_template_attachment_img_rel',
        'product_template_id', 'attachment_id', 'Additional images'
    )


class Product(models.Model):
    _inherit = "product.product"

    # fields ------------------------------------------------------------------
    desc_variant_html = fields.Html('Variant description HTML')

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        """ Hiding desc_template_html if view is form and related to
         product variant (product.product model) """
        res = super(Product, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar,
            submenu=submenu
        )
        if view_type == 'form':
            doc = etree.XML(res['arch'])
            if doc.xpath("//page[@name='desc_template']"):
                node = doc.xpath("//page[@name='desc_template']")[0]
                node.set('invisible', '1')
                setup_modifiers(node)
                res['arch'] = etree.tostring(doc)
            if doc.xpath("//page[@name='additional_template_images']"):
                node = doc.xpath("//page[@name='additional_template_images']")[0]
                node.set('invisible', '1')
                setup_modifiers(node)
                res['arch'] = etree.tostring(doc)

        return res
