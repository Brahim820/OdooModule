# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools, _
from odoo.exceptions import UserError

class CurrencyRate(models.Model):
    _inherit = "res.currency.rate"

    @api.model
    def get_currency_rate(self, currency_id, date, company_id=False, company_strict=False):
        """
        Will return currency rate for given date and, if provided, given company
        First appliance if for setting field value in
        account_invoice.currency_converions_rate

        If param company_strict is True and company_id is provided:
        Method will look for rates defined for that specific company. If none is
        found, will return 0.0

        If param company_strict is NOT TRUE and company_id is provided:
        Method will look for rates defined for that specific company. If none is
        found, will search again but for rates where company_id is not defined.
        If even then rate is not found, will return 0.0

        Args:
            self:
            currency_id: int, currency record ID
            date: date, as string. On which date should method search rates
            company_id: int, company record ID
            company_strict: bool, if set to True, method will search rates
            explicitly matching company ID

        Returns:
            float, Valid currency rate
        """
        assert currency_id, 'Need currency_id here'
        assert isinstance(currency_id, (int, long)),\
            'Param currency_id must be int'
        assert date, 'Need param date here'

        if company_strict and not company_id:
            msg = u'Param company_strict is True so param company_id is '
            msg += u'mandatory'
            raise UserError(msg)
        company_sql = ""
        if company_id:
            assert isinstance(company_id, (int, long)), 'Param company_id (if provided) must be int'
            if company_strict:
                # must return rate fo this specific company
                company_sql = " and company_id = %s" % company_id

        sql = """
        select rate from res_currency_rate where
            currency_id = %s
            and name <= %s
            %s
        order by name desc limit 1
        """
        self._cr.execute(sql, (currency_id, date, company_sql))
        res = self._cr.fetchone()
        rate = res and res[0] or 0.0

        if not rate and not company_strict and company_id:
            # didn't found rate for specified company - run one more time to
            # check if there is rate without company defined
            company_sql = " and company_id is null"
            sql = """
            select rate from res_currency_rate where
                currency_id = %s
                and name <= '%s'
                %s
            order by name desc limit 1
            """ % (currency_id, date, company_sql)
            self._cr.execute(sql)
            res = self._cr.fetchone()
            rate = res and res[0] or 0.0

        return rate
