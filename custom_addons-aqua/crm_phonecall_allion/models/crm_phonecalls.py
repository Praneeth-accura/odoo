from datetime import datetime, timedelta
from odoo import api, fields, models, _
import time


class CrmPhoneCalls(models.Model):

    _name = "crm.phone.calls"
    _description = "Phone calls"
    _inherit = ['mail.thread']

    date_action_last = fields.Datetime(string='Last Action', readonly=True)
    date_action_next = fields.Datetime(string='Next Action', readonly=True)
    create_date = fields.Datetime(string='Creation Date', readonly=True, select=True,
                                  help='Sales team to which Case belongs to.')
    section_id = fields.Many2one(comodel_name='crm.case.section', string='Sales Team', select=True,
                                 help='Sales team to which Case belongs to.')
    user_id = fields.Many2one(comodel_name='res.users', required=True, string='Responsible', default=lambda self: self.env.user)
    partner_id = fields.Many2one(comodel_name='res.partner', string='Contact', required=True)
    company_id = fields.Many2one(comodel_name='res.company', string='Company')
    description = fields.Text(string='Description')
    state = fields.Selection(
        [('open', 'Confirmed'),
         ('cancel', 'Cancelled'),
         ('pending', 'Pending'),
         ('done', 'Held')
         ], string='Status', readonly=True, help='The status is set to Confirmed, when a case is created.\n'
                                                 'When the call is over, the status is set to Held.\n'
                                                 'If the callis not applicable anymore, the status can be set to '
                                                 'Cancelled.', default='open')
    email_from = fields.Char(string='Email', size=128, help="These people will receive email.")
    date_open = fields.Datetime(string='Opened', readonly=True)
    # phone call fields
    name = fields.Char(string='Call Summary', required=True)
    active = fields.Boolean(string='Active', required=False, default=True)
    duration = fields.Float(string='Duration', help='Duration in minutes and seconds.')
    # category_id = fields.Many2one(comodel_name='crm.case.categ', string='Category', domain="['|',"
    #                                                                                     "('section_id','=',section_id),"
    #                                                                                     "('section_id','=',False),"
    #                                                                                     "('object_id.model', '=', "
    #                                                                                     "'crm.phonecall')]")
    partner_phone = fields.Char(string='Phone')
    partner_mobile = fields.Char(string='Mobile')
    priority = fields.Selection(
        [('0', 'Low'),
         ('1', 'Normal'),
         ('2', 'High')], string='Priority', default='1')
    date_closed = fields.Datetime(string='Closed', readonly=True)
    date = fields.Datetime(string='Date', default=lambda *a: time.strftime('%Y-%m-%d'), required=True)
    opportunity_id = fields.Many2one(comodel_name='crm.lead', string='Lead/Opportunity')
    crm_helpdesk_id = fields.Many2one(comodel_name='crm.helpdesk', string='Help Deatsk')

    @api.model
    def create(self, vals):
        if vals.get('user_id'):
            common_namee = vals.get('user_id')
            name = vals.get('name')
            obj = self.env['res.users'].browse(common_namee)
            common_name = obj


            att = {
                   'state': 'accepted',
                   'common_name': obj.partner_id.name or False,
                   'partner_id': obj.partner_id.id or False,

                   'email': obj.partner_id.email or False,
            }
            user_id = self._uid
            data = {
                'name': name,
                'user_id': user_id or False,
                'start': vals.get('date'),
                'state': 'open',
                'res_id': 0,
                'allday': False,
                'privacy': 'public',
                'duration': 0.5,
                'stop': datetime.strptime(vals.get('date'),'%Y-%m-%d %H:%M:%S'),
                'description': False,
                'attendee_ids': [(0, 0, att)],
                'partner_ids': obj.partner_id.ids or False,
            }
            self.env['calendar.event'].create(data)
            last_record = self.env['calendar.attendee'].search([])
            last_record.create(att)
            event = self.env['calendar.event'].search([], order='id desc', limit=1)
            self._cr.execute(""" INSERT INTO calendar_event_res_partner_rel (calendar_event_id, res_partner_id)
                                           VALUES (%s, %s) """, (event.id, obj.partner_id.id))
            return super(CrmPhoneCalls, self).create(vals)