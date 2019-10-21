# -*- coding: utf-8 -*-

from . import models
from . import wizard

import logging

from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)


def uninstall_hook(cr, registry):
    """when uninstall this module all changes related to the accounting will be reset"""
    env = api.Environment(cr, SUPERUSER_ID, {})

    menus_to_remove = [("account.menu_finance_entries", "account.group_account_manager", "account.group_account_user"),
                       ("account.menu_finance_configuration", "account.group_account_user", "account.group_account_manager"),
                       ("account.menu_finance_reports", "account.group_account_user", "account.group_account_manager")]

    # reset menu items
    for menu_xmlids in menus_to_remove:
        try:
            menu = env.ref(menu_xmlids[0])
            menu.write({'groups_id': [(3, env.ref(menu_xmlids[1]).id), (4, env.ref(menu_xmlids[2]).id)]})
        except ValueError as e:
            _logger.warning(e)

    # reset Adviser group to Show Full Accounting Features
    try:
        group_user = env.ref("account.group_account_user")
        group_user.write({'name': "Show Full Accounting Features",
                          'implied_ids': [(3, env.ref('account.group_account_invoice').id)],
                          'category_id': env.ref("base.module_category_hidden").id})
    except ValueError as e:
            _logger.warning(e)

    # reset Accountant group to Billing Manager
    try:
        group_manager = env.ref("account.group_account_manager")
        group_manager.write({'name': "Billing Manager",
                             'implied_ids': [(4, env.ref("account.group_account_invoice").id),
                                             (3, env.ref("account.group_account_user").id)]})
    except ValueError as e:
            _logger.warning(e)
