import uuid

from itertools import groupby
from datetime import datetime, timedelta
from werkzeug.urls import url_encode

from odoo import api, fields, models, _
from odoo.exceptions import UserError, AccessError
from odoo.osv import expression
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT

from odoo.tools.misc import formatLang

from odoo.addons import decimal_precision as dp


class CrmLeadLost(models.TransientModel):

    _inherit = ['crm.lead.lost']

    @api.multi
    def action_lost_reason_apply(self):
        leads = self.env['crm.lead'].browse(self.env.context.get('active_ids'))
        # Get the lost stage id
        stage_obj = self.env['crm.stage'].search([('name', '=', 'Lost')])
        leads.write({'lost_reason': self.lost_reason_id.id,
                     'stage_id': stage_obj.id})
        return leads.action_set_lost()