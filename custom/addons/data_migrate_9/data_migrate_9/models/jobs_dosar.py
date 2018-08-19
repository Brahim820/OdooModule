# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# This file is created by gordan.cuic@gmail.com

from openerp import api, fields, models, _, osv
import logging

_logger = logging.getLogger(__name__)


class DataMigrateOrder(models.Model):
    _inherit = "data.migrate.order"

    # -----------------------------------------------------------------
    # helpan_dosar
    # -----------------------------------------------------------------
    @api.model
    def HelpanDosar(self, cr2):
        dosarID_new_ids = {}
        dosar_obj = self.env['helpan.dosar']
        cr2.execute("""
        select
            name, "DataCrearii", "dosarID", initiator
        from helpan_dosar_helpan_dosar
        order by "dosarID"
        """)
        res = cr2.fetchall()
        for r in res:
            name = r[0]
            date_created = r[1]
            internal_identify = r[2]
            initiator = r[3]
            args = [('internal_identify' '=', internal_identify)]
            if dosar_obj.search_count(args):
                dosar = dosar_obj.search(args)
            else:
                dosar = dosar_obj.create({
                    'name': name, 'date_created': date_created,
                    'internal_identify': internal_identify,
                    'initiator': initiator
                })
            dosar.ensure_one()
            dosarID_new_ids[internal_identify] = dosar.id

        assert dosarID_new_ids, 'Need old-new mapped dict here'

        return True
