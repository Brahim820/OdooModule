# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# This file is created by gordan.cuic@gmail.com

from openerp import api, fields, models, _, osv
from datetime import date

class AccountInvoice(models.Model):
    _inherit = "account.invoice"

    def __init__(self, pool, cr):
        super(AccountInvoice, self).__init__(pool, cr)
        self.report_statement_totals = {}
        self.report_statement_lines = {}

    # fields ------------------------------------------------------------------
    print_payment_spec = fields.Boolean(
        string='Print payments specification to?'
    )

    @api.multi
    def invoice_print_payments_specification(self):
        """ Inheritance. Modification: setting payments specification printing
            to on, so invoice report will have additional page with payments
            specification
        """
        self.ensure_one()
        self.write({'print_payment_spec': True})

        return super(AccountInvoice, self).invoice_print()


    @api.multi
    def invoice_print(self):
        """ Inheritance. Modification: setting payments specification printing
            to off - changes in this module will not effect invoice report
        """
        self.ensure_one()
        self.write({'print_payment_spec': False})

        return super(AccountInvoice, self).invoice_print()

    @staticmethod
    def resolve_invoice_partner(partner):
        """
        Resolves partner. There are cases when invoice is issued to person
        (contact) which by default is not company - that partner has parent
        partner which represents her or his company

        :param partner: browse record, partner to whom invoice is related to
        :return: int, partner ID
        """
        partner_id = partner.id
        if not partner.is_company and partner.parent_id:
            partner_id = partner.parent_id.id

        return partner_id

    @api.multi
    def payments_report_data(self):
        self.ensure_one()

        def _subtract_dates(date_maturity):
            today = date.today()
            diff = (today - fields.Date.from_string(date_maturity)).days
            return diff

        obj = self.env['report.account.report_overdue']
        partner_id = self.resolve_invoice_partner(self.partner_id)
        totals, lines_to_display = {}, {}

        lines = obj.get_account_move_lines_wrapper([partner_id])
        company_currency = self.env.user.company_id.currency_id
        lines_to_display[partner_id] = {}
        totals[partner_id] = {}
        for line_tmp in lines[partner_id]:
            line = line_tmp.copy()
            currency = line['currency_id'] and self.env['res.currency'].browse(
                line['currency_id']
            ) or company_currency
            if currency not in lines_to_display[partner_id]:
                lines_to_display[partner_id][currency] = []
                totals[partner_id][currency] = dict(
                    (fn, 0.0) for fn in ['due', 'paid', 'mat', 'total']
                )
            if line['debit'] and line['currency_id']:
                line['debit'] = line['amount_currency']
            if line['credit'] and line['currency_id']:
                line['credit'] = line['amount_currency']
            if line['mat'] and line['currency_id']:
                line['mat'] = line['amount_currency']
            line['diff'] = _subtract_dates(line['date_maturity'])
            lines_to_display[partner_id][currency].append(line)
            if not line['blocked']:
                debit, credit = line['debit'], line['credit']
                totals[partner_id][currency]['due'] += debit
                totals[partner_id][currency]['paid'] += credit
                totals[partner_id][currency]['mat'] += line['mat']
                totals[partner_id][currency]['total'] += debit - credit

        # order by  date_maturity
        report_statement_lines = {}
        for partner_id, currency_dct in lines_to_display.items():
            currency_dct_sorted = {}
            for currency, invoices in currency_dct.items():
                invoices = sorted(invoices, key=lambda k: k["date_maturity"])
                currency_dct_sorted[currency] = invoices
            report_statement_lines[partner_id] = currency_dct_sorted

        # writ this down to self to avoid multiple method calls
        self.report_statement_lines = report_statement_lines
        self.report_statement_totals = totals

        return lines_to_display


class ReportOverdue(models.AbstractModel):
    _inherit = 'report.account.report_overdue'

    @api.model
    def get_account_move_lines_wrapper(self, partner_ids):
        res = self._get_account_move_lines(partner_ids)
        return res
