from odoo.tools.translate import _
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
from odoo import tools, api
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo import api, fields, models, _
import logging
from odoo.osv import  osv
from odoo import SUPERUSER_ID


class crm_lead(models.Model):
    """ CRM Lead Case """
    _inherit = "crm.lead"
    
    @api.multi
    def task_count(self):
        task_obj = self.env['project.task']
        self.task_number = task_obj.search_count([('lead_id', 'in', [a.id for a in self])])

    task_number = fields.Integer(compute='task_count', string='Tasks')


class crm_task_wizard(models.TransientModel):
    _name = 'crm.task.wizard'

    def get_name(self):
        ctx = dict(self._context or {})
        active_id = ctx.get('active_id')
        crm_brw = self.env['crm.lead'].browse(active_id)
        name = crm_brw.name
        return name
    
    project_id = fields.Many2one('project.project','Project')
    dead_line = fields.Datetime('Deadline', required=True)
    name = fields.Char('Task Name', default=get_name)
    user_id = fields.Many2one('res.users', 'Assigned To', default=lambda self: self.env.uid, index=True,
                              track_visibility='always')
    description = fields.Html(string='Description')
    comment = fields.Text(string='Comment')
    
    @api.one
    def create_task(self):
        ctx = dict(self._context or {})

        common_name = self.user_id.partner_id
        active_id = ctx.get('active_id')
        crm_brw = self.env['crm.lead'].browse(active_id)

        # Get ID of stage "New"
        project_task_type_obj = self.env['project.task.type'].search([('name', '=', 'New')])

        vals = {'name': self.name,
                'project_id': self.project_id.id or False,
                'user_id': self.user_id.id or False,
                'date_deadline': self.dead_line or False,
                'partner_id': crm_brw.partner_id.id or False,
                'lead_id': crm_brw.id or False,
                'description': self.description or False,
                'comment': self.comment or False,
                'stage_id': project_task_type_obj.id or False
                }
        self.env['project.task'].create(vals)

        # att = {'state': 'accepted',
        #        'common_name': self.user_id.partner_id.name,
        #        'partner_id': self.user_id.partner_id.id,
        #        'email': self.user_id.partner_id.email,
        #        }
        # data = {
        #     'name': self.name,
        #     'user_id': self._uid or False,
        #     'start': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        #     'state': 'open',
        #     'res_id': 0,
        #     'allday': False,
        #     'privacy': 'public',
        #     'duration': 0.5,
        #     'stop': (datetime.strptime(self.dead_line, "%Y-%m-%d") - timedelta(hours=5, minutes=30)) or (datetime.now() - timedelta(hours=5, minutes=30)),
        #     'description': self.description or False,
        #     'attendee_ids': [(0, 0, att)],
        # }
        # self.env['calendar.event'].with_context(common_name = common_name).create(data)
        # last_record = self.env['calendar.attendee'].search([], order='id desc', limit=1)
        # last_record.write(att)


class project_Task(models.Model):
    _inherit = 'project.task'


    def _get_default_stage_id(self):
        """ Gives default stage_id """
        project_id = self.env.context.get('default_project_id')
        if not project_id:
            project_task_type_obj = self.env['project.task.type'].search([('name', '=', 'New')])
            return project_task_type_obj.id
        return self.stage_find(project_id, [('fold', '=', False)])
    
    lead_id = fields.Many2one('crm.lead', 'Opportunity')
    comment = fields.Text(string='Comment')
    stage_id = fields.Many2one('project.task.type', string='Stage', track_visibility='onchange', index=True,
                               default=_get_default_stage_id, group_expand='_read_group_stage_ids',
                               domain="[('project_ids', '=', project_id)]", copy=False)

    date_deadline = fields.Datetime(string='Deadline', index=True, copy=False, required=True)
    date_start = fields.Datetime(string='Start Date', index=True, copy=False, required=True)
    project_id = fields.Many2one('project.project',
                                 string='Project',
                                 default=lambda self: self.env.context.get('default_project_id'),
                                 index=True,
                                 track_visibility='onchange',
                                 change_default=True, required=True)
    user_id = fields.Many2one('res.users',
                              string='Assigned to',
                              default=lambda self: self.env.uid,
                              index=True, track_visibility='always', required=True)

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
                'start': datetime.strptime(vals.get('date_start'), '%Y-%m-%d %H:%M:%S'),
                'state': 'open',
                'res_id': 0,
                'allday': False,
                'privacy': 'public',
                'duration': 0.5,
                'stop': datetime.strptime(vals.get('date_deadline'), '%Y-%m-%d %H:%M:%S'),
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
            return super(project_Task, self).create(vals)


class CrmCalendarInherit(models.Model):
    _inherit = 'calendar.event'

    def _get_partner_ids(self):
        if self._context.get('common_name'):
            partners = self._context['common_name']
            return partners
        else:
            pass

    partner_ids = fields.Many2many('res.partner', 'calendar_event_res_partner_rel', string='Attendees', states={'done': [('readonly', True)]}, default=_get_partner_ids)



