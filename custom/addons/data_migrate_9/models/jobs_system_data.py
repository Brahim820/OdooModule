# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# This file is created by gordan.cuic@gmail.com

from openerp import api, fields, models, _, osv
from odoo.exceptions import UserError
import collections
import logging

_logger = logging.getLogger(__name__)


class DataMigrateOrder(models.Model):
    _inherit = "data.migrate.order"

    # -----------------------------------------------------------------
    # sequences
    # -----------------------------------------------------------------
    @api.model
    def DoneDocumentJobs(self):
        """ Returns ordered dict of sequence: line browse_record representing
        done jobs that are related to some document like invoice or sale order
        """
        document_jobs = ['so01_post', 'inv01_post']
        jobs = collections.OrderedDict()
        self.ensure_one()
        if not self.line_ids:
            msg = _('''There are no jobs in this migration order''')
            raise UserError(msg)
        for step in self.line_ids:
            if step.state == 'done' and step.job_id.code in document_jobs:
                jobs[step.job_id.sequence] = step
        if not jobs:
            msg = _('''There are no document related jobs that are "done" in
            this migration order''')
            raise UserError(msg)

        return jobs

    @api.model
    def Sequence9(self, cr2, model):
        sequences = []
        ir_sequence_ids2 = self.ModelSequences9(cr2, model)
        sql = """
        select
            active -- 0
            ,code -- 1
            ,company_id -- 2
            ,implementation -- 3
            ,name -- 4
            ,number_increment -- 5
            ,number_next -- 6
            ,padding -- 7
            ,prefix -- 8
            ,suffix -- 9
            ,use_date_range -- 10
            ,id -- 11
        from ir_sequence
        where id in (%s)
        """ % ', '.join(map(str, ir_sequence_ids2))
        cr2.execute(sql)
        res = cr2.fetchall()
        for sequence in res:
            vals = {}
            for r in sequence:
                active = r[0]
                code = r[1]
                company_id2 = r[2]
                implementation = r[3]
                name = r[4]
                number_increment = r[5]
                number_next = r[6]
                padding = r[7]
                prefix = r[8]
                suffix = r[9]
                use_date_range = r[10]
                sequence_id2 = r[11]

                company_id = False
                if company_id2:
                    company_id = self.IdVersion10(
                        cr2, 'res.company', ('name',), company_id2
                    )

                vals.update({
                    'active': active,
                    'code': code,
                    'company_id': company_id,
                    'implementation': implementation,
                    'name': name,
                    'number_increment': number_increment,
                    'number_next': number_next,
                    'padding': padding,
                    'prefix': prefix,
                    'suffix': suffix,
                    'use_date_range': use_date_range,
                })

                if model == 'account.invoice':
                    cr2.execute("""select id from account_journal where
                    sequence_id = %s""" % sequence_id2)
                    journal_ids2 = [i[0] for i in cr2.fetchall() if i and i[0] or False]
                    assert journal_ids2,\
                        'Invoice journal should have at least one sequence'
                    assert len(journal_ids2) > 1,\
                        'Invoice journal should have only one sequence'

                    journal_id = self.IdVersion10(
                        cr2, 'account.journal', ('code',), journal_ids2[0]
                    )
                    search_key, search_value = 'journal_id', journal_id
                else:
                    search_key, search_value = 'code', code

                vals.update({'search_via': [search_key, search_value]})
                break

            sequences.append(vals)

        return sequences

    @api.model
    def ModelSequences9(self, cr2, model):
        """ Return ir_sequence record IDs in version 9 database """
        assert model, 'Need model here'
        assert isinstance(model, (str, unicode)), 'Var model must be string'

        if model == 'sale.order':
            cr2.execute("""select id from ir_sequence where code = '%s'
            """ % model)
            ids = [i[0] for i in cr2.fetchall() if i and i[0] or False]
        elif model == 'account.invoice':
            pass
        else:
            raise UserError("Uncovered model %s" % model)

        return ids

    @api.model
    def SequencesUpdate(self, cr2):
        # check done jobs related to documents
        for step in self.DoneDocumentJobs():
            if step.job_id.code == 'so01_post':
                model = 'sale.order'
            elif step.job_id.code == 'inv01_post':
                model = 'account.invoice'

            next_number = self.Sequence9(cr2, model)
            if not next_number:
                _logger.debug("""No next number in version 9 db for %s
                """ % model)

        return True
