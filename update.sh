#!/usr/bin/env bash
sudo -u odoo /odoo/odoo-server/odoo-bin --stop-after-init -u helpan_dosar -d Test --no-xmlrpc --addons-path=./custom/addons,/odoo/odoo-server/addons
                                              -c /etc/odoo/openerp-server.conf

sudo -u odoo /usr/bin/python2.7 /odoo/odoo-server/odoo.py --stop-after-init  -u helpan_dosar  --no-xmlrpc --addons-path=./addons,../custom/addons


sudo -u odoo /odoo/odoo-server/odoo.py --stop-after-init -u invoice_helpan -d HELPAN --no-xmlrpc  --addons-path=./custom/addons,/odoo/odoo-server/addons

sudo -u odoo /odoo/odoo-server/odoo.py --stop-after-init -u helpan_dosar -d HELPAN --no-xmlrpc  --addons-path=./custom/addons,/odoo/odoo-server/addons


sudo -u odoo /odoo/odoo-server/odoo.py --stop-after-init -u helpan_teava -d HELPAN --no-xmlrpc  --addons-path=./custom/addons,/odoo/odoo-server/addons
