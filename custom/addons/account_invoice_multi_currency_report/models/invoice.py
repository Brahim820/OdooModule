# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError

class AccountInvoiceLine(models.Model):
    _inherit = "account.invoice.line"

    @api.one
    @api.depends('price_unit', 'discount', 'product_id', 'invoice_id.state',
                 'invoice_id.partner_id', 'invoice_id.currency_id',
                 'invoice_id.company_id')
    def _compute_price_company_currency(self):
        """ Recalculates price unit in company's default currency if invoice
        currency is different"""
        price = self.price_unit * (1 - (self.discount or 0.0) / 100.0)
        invoice_currency = self.invoice_id.currency_id or False
        company_currency = self.invoice_id.company_id.currency_id
        if invoice_currency and invoice_currency != company_currency:
            converted_price = invoice_currency.compute(price, company_currency)
        else:
            converted_price = price

        self.price_unit_company_currency = converted_price

    price_unit_company_currency = fields.Monetary(
        string='Price company currency', currency_field='company_currency_id',
        store=True, readonly=True, compute='_compute_price_company_currency',
        help="Product's unit price in company's default currency"
    )

class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    @api.one
    @api.depends('state', 'partner_id', 'currency_id', 'company_id')
    def _get_rate_invoice_date(self):
        """ Fetches currency conversion rate that is/was valid on invoice date
        """
        invoice_currency = self.currency_id or False
        company_currency = self.company_id.currency_id
        if invoice_currency and invoice_currency != company_currency:
            date = self.date_invoice
            rates_obj = self.env['res.currency.rate']
            rate = rates_obj.get_currency_rate(
                invoice_currency.id, date, company_id=self.company_id.id
            )
        else:
            rate = 1.0

        # this will actually show inverted
        # TODO create configuration entry that would allow choosing which
        # currency is expressed in which 1 EUR = 0.2234 RON or
        # 1 RON = 4.4762 EUR
        inverted = True
        if inverted:
            rate = round(1 / rate, 6)

        self.currency_converions_rate = rate

    # fields ------------------------------------------------------------------
    currency_converions_rate = fields.Float(
        digits=(12, 6), compute='_get_rate_invoice_date', store=True
    )
