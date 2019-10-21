# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from itertools import groupby
from datetime import datetime, timedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.misc import formatLang
from odoo.tools import html2plaintext
import odoo.addons.decimal_precision as dp
import time


class crm_helpdesk(models.Model):

    _name = "crm.helpdesk"
    _description = "Help Desk Services"
    _order = "priority,date desc"
    _inherit = ['mail.thread']

    id = fields.Integer(string='ID', readonly=True)
    name = fields.Char(string='Subject', required=True)
    active = fields.Boolean(string='Active', default=lambda *a: 1)
    action_next = fields.Char(string='Next Action')
    date_action_next = fields.Datetime(string='Next Action Date')
    description = fields.Text(string='Description')
    resolution = fields.Text(string='Resolution')
    create_date = fields.Datetime(string='Creation Date', readonly=True)
    write_date = fields.Datetime(string='Update Date', readonly=True)
    date_deadline = fields.Date(string='Deadline')
    date_closed = fields.Datetime(string='Closed', readonly=True)
    date = fields.Date(string='Date', select=True,
                           default=lambda *a: time.strftime('%Y-%m-%d'))
    categ_id = fields.Many2one('crm.helpdesk.category', 'Category')
    priority = fields.Selection([
        ('0', 'Low'),
        ('1', 'Normal'),
        ('2','High')
    ], 'Priority', default='1')
    type_action = fields.Selection([
        ('correction', 'Corrective Action'),
        ('prevention','Preventive Action')
    ], string='Action Type')
    user_id = fields.Many2one(comodel_name='res.users', string='Responsible', track_visibility='always',
                              default=lambda self: self.env.user)
    colod = fields.Many2one(comodel_name='res.company', string='Company',
                            default=lambda self: self.env['res.company']._company_default_get('crm.case'))
    partner_id = fields.Many2one(comodel_name='res.partner', string='Customer', required='True',
                                 domain="[('customer','=',True)]")
    email_cc = fields.Text(string='Watchers Emails', size=252,
                           help="These email addresses will be added to the CC field of all inbound and outbound "
                                "emails for this record before being sent. Separate multiple email addresses "
                                "with a comma")
    email_from = fields.Char(string='Email', size=128, help="Destination email for email gateway.", required=True)
    partner_phone = fields.Char('Phone')
    stage_id = fields.Selection([
        ('new', 'New'),
        ('open', 'Open'),
        ('closed', 'Closed'),
        ('incomplete', 'Incomplete')
    ], string='Stage', track_visibility='onchange', default='new')
    cause = fields.Text(string='Root Cause')
    technician_id = fields.Many2one(comodel_name='crm.helpdesk.technician', string='Assign Technician', required=True)
    address = fields.Char(string='Address', index=True, related='technician_id.address')
    phone_log_lines = fields.One2many(comodel_name='crm.phone.calls', inverse_name='crm_helpdesk_id',
                                      string='Phone Log', required=True)
    department_id = fields.Many2one(comodel_name='crm.departments', string='Department', required=True)
    job_type = fields.Selection([('visit', 'Site Visit'), ('remote', 'Remote'), ('installation', 'Installation'), ('service', 'Service'), ('sale', 'Sale')], string='Job Type', default='remote')
    current_assigned_task = fields.Float(string='No. Of Task Assigned')
    token_no = fields.Char(string='Token No', readonly=True)
    calendar_start_date = fields.Datetime(string='Calendar Start Date', required=True)
    calendar_end_date = fields.Datetime(string='Calendar End Date', required=True)
    machine_type = fields.Selection([('RO_Classic','RO Classic'),('RO_Under_sink','RO Under sink'),('RO_Top','RO Oga Counter Top (ET)'),
    	('HotCold','Hot & Cold Machine'),('RO300','RO 300'),('RO400','RO 400'),('RO500','RO 500'),('RO1500','RO 1500'),('RO3000','RO 3000'),
    	('RO4500','RO 4500'),('RO6000','RO 6000'),('RO12000','RO 12000'),('RO300S','RO 300 & softner'),('RO300SM','RO 300,Softner & Multimedia'),
    	('RO400S','RO 400 & softner'),('RO400SM','RO 400,Softner & Multimedia'),('RO500S','RO 500 & softner'),
    	('RO500SM','RO 500,Softner & Multimedia'),('844','8” 44” Softner System'),('1054','10” 54” Softner System'),
    	('1465','14” 65” Softner System')],string='Machine Type')

    # Email create function
    def create_email(self, vals):
        # get the mail pool
        mail_pool = self.env['mail.mail']

        # email body & footer
        if 'stage_id' in vals:
            if vals.get('stage_id') == 'open':
                if self.stage_id == 'incomplete':
                    technician_id = self.technician_id
                    body = ("<p>Your previous assigned person has been changed. Token No: %s</p>" % self.token_no)
                    body += ("<p><strong>New Assigned Person:</strong> %s</p>" % technician_id.name)

                    body_tech = ("<p>You have assigned to a new claim. Token No: %s</p>" % self.token_no)
                    body_tech += ("<p><strong>Reason:</strong> %s</p>" % self.name)
                    body_tech += ("<p><strong>Responsible:</strong> %s</p>" % self.user_id.name)
                    body_tech += ("<p><strong>Customer:</strong> %s</p>" % self.partner_id.name)
                    body_tech += ("<p><strong>Customer Contact No:</strong> %s</p>" % self.partner_id.phone)
                    body_tech += ("<p><strong>Customer Email:</strong> %s</p>" % self.partner_id.email)
                    body_tech += ("<p><strong>Customer Address:</strong> %s</p>" % str(self.partner_id.street) + str(self.partner_id.street2 or " ") + str(self.partner_id.city or " "))
                else:
                    body = ("<p>Your claim is successfully opened. Token No: %s</p>" % self.token_no)
                    body += ("<p><strong>Assigned Person:</strong> %s</p>" % self.technician_id.name)

                    body_tech = ("<p>You have assigned to a new claim. Token No: %s</p>" % self.token_no)
                    body_tech += ("<p><strong>Reason:</strong> %s</p>" % self.name)
                    body_tech += ("<p><strong>Responsible:</strong> %s</p>" % self.user_id.name)
                    body_tech += ("<p><strong>Customer:</strong> %s</p>" % self.partner_id.name)
                    body_tech += ("<p><strong>Customer Contact No:</strong> %s</p>" % self.partner_id.phone)
                    body_tech += ("<p><strong>Customer Email:</strong> %s</p>" % self.partner_id.email)
                    body_tech += ("<p><strong>Customer Address:</strong> %s</p>" % str(self.partner_id.street) + str(self.partner_id.street2 or " ") + str(self.partner_id.city or " "))

            elif vals.get('stage_id') == 'closed':
                body = ("<p>Your claim is successfully closed. Token No: %s</p>" % self.token_no)

                body_tech = ("<p>Your assigned claim Successfully closed. Token No: %s</p>" % self.token_no)
            else:
                return False
        else:
            if self.stage_id == 'open':
                technician_id = self.env['crm.helpdesk.technician'].browse(vals['technician_id'])
                body = ("<p>Your previous assigned person has been changed. Token No: %s</p>" % self.token_no)
                body += ("<p><strong>New Assigned Person:</strong> %s</p>" % technician_id.name)

                body_tech = ("<p>You have assigned to a new claim. Token No: %s</p>" % self.token_no)
                body_tech += ("<p><strong>Reason:</strong> %s</p>" % self.name)
                body_tech += ("<p><strong>Responsible:</strong> %s</p>" % self.user_id.name)
                body_tech += ("<p><strong>Customer:</strong> %s</p>" % self.partner_id.name)
                body_tech += ("<p><strong>Customer Contact No:</strong> %s</p>" % self.partner_id.phone)
                body_tech += ("<p><strong>Customer Email:</strong> %s</p>" % self.partner_id.email)
                body_tech += ("<p><strong>Customer Address:</strong> %s</p>" % str(self.partner_id.street) + str(self.partner_id.street2 or " ") + str(self.partner_id.city or " "))
            else:
                return False

        footer = "<br>Thank You,<br>"
        footer += "%s\n" % self.colod.name

        # compose the email
        compose_email = {
            'email_to': self.email_from,
            'email_cc': self.department_id.user_id.email,
            'subject': 'Token: ' + self.token_no,
            'body_html': body + footer,
            'helpdesk_id': self.id
        }

        if self.department_id.user_id.email:
            emails = self.department_id.user_id.email + "," + "dileepa@onestep.lk"
        else:
            emails = "dileepa@onestep.lk"

        # compose the email technician
        compose_email_tech = {
            'email_to': self.technician_id.email,
            'email_cc': emails,
            'subject': 'Token: ' + self.token_no,
            'body_html': body_tech + footer,
            'helpdesk_id': self.id
        }

        # email creation
        mail_id = mail_pool.create(compose_email)
        # email creation technician
        mail_pool.create(compose_email_tech)

        return mail_id

    # Technician Email create function
    def create_email_tech(self, vals):
        # get the mail pool
        mail_pool = self.env['mail.mail']

        # email body & footer
        body = ("<p>Your previously assigned Token: %s has been assigned to another technician</p>" % self.token_no)
        body += ("<p><strong>Please ignore the Token No:</strong> %s</p>" % self.token_no)

        footer = "<br>Thank You,<br>"
        footer += "%s\n" % self.colod.name

        # compose the email
        compose_email = {
            'email_to': self.technician_id.email,
            'subject': 'Token: ' + self.token_no,
            'body_html': body + footer,
            'helpdesk_id': self.id
        }

        # email creation
        mail_id = mail_pool.create(compose_email)

        return mail_id

    # Get the assigned task number
    @api.onchange('technician_id')
    def technician_onchange(self):
        if self.technician_id:
            token_count = len(self.search([('technician_id', '=', self.technician_id.id), ('stage_id', '=', 'open')]))
            if token_count >= 5:
                raise UserError(_('You cannot assign this technician for this token. \n Maximum number of assigned '
                                  'tasks exceeded. \n Assigned task count-%d'%(token_count)))
                return False
            else:
                self.current_assigned_task = token_count

    # Get the related email for the partner
    @api.onchange('partner_id')
    def partner_onchange(self):
        if self.partner_id:
            department_ids = []
            technician_ids = []
            no_department_ids = []
            no_technician_ids = []
            if self.partner_id.assigned_departments:
                # append ids for the department_ids list
                for department in self.partner_id.assigned_departments:
                    department_ids.append(department.id)
                self.department_id = department_ids

            if self.partner_id.assigned_technicians:
                # append ids for the technician_ids list
                for technician in self.partner_id.assigned_technicians:
                    technician_ids.append(technician.id)
                self.technician_id = technician_ids

            if self.partner_id.assigned_departments:
                tec_ids = self.env['crm.helpdesk.technician'].search([])
                for tec_id in tec_ids:
                    no_technician_ids.append(tec_id.id)

                result = {'value': {'email_from': self.partner_id.email, 'partner_phone': self.partner_id.phone},
                          'domain': {'department_id': [('id', '=', department_ids)],
                                     'technician_id': [('id', '=', no_technician_ids)]
                                     }
                          }
            elif self.partner_id.assigned_technicians:
                dep_ids = self.env['crm.departments'].search([])
                for dep_id in dep_ids:
                    no_department_ids.append(dep_id.id)

                result = {'value': {'email_from': self.partner_id.email, 'partner_phone': self.partner_id.phone},
                          'domain': {'technician_id': [('id', '=', technician_ids)],
                                     'department_id': [('id', '=', no_department_ids)]
                                     }
                          }
            elif self.partner_id.assigned_departments and self.partner_id.assigned_technicians:
                result = {'value': {'email_from': self.partner_id.email, 'partner_phone': self.partner_id.phone},
                          'domain': {'department_id': [('id', '=', department_ids)],
                                     'technician_id': [('id', '=', technician_ids)]
                                     }
                          }
            else:
                tec_ids = self.env['crm.helpdesk.technician'].search([])
                for tec_id in tec_ids:
                    no_technician_ids.append(tec_id.id)
                dep_ids = self.env['crm.departments'].search([])
                for dep_id in dep_ids:
                    no_department_ids.append(dep_id.id)
                result = {'value': {'email_from': self.partner_id.email, 'partner_phone': self.partner_id.phone},
                          'domain': {'department_id': [('id', '=', no_department_ids)],
                                     'technician_id': [('id', '=', no_technician_ids)]
                                     }
                          }

            return result

    @api.multi
    @api.onchange('partner_id')
    def onchange_partner_id(self, email=False):
        if not self.partner_id:
            return {'value': {'email_from': False, 'partner_phone': False}}
        address = self.pool.get('res.partner').browse(self.partner_id)
        return {'value': {'email_from': address.email, 'partner_phone': address.phone}}

    @api.model
    def create(self, vals):
        # Validations
        if vals['date_action_next'] is not False:
            token_date = datetime.strptime(vals.get('date'), '%Y-%m-%d').date()
            next_action_date = datetime.strptime(vals.get('date_action_next'), '%Y-%m-%d %H:%M:%S').date()
            if token_date > next_action_date:
                raise UserError(_('Next Action Date cannot be a backdate against the Date.'))

        # Get the assigned tasks for the related technician
        token_count = len(self.search([('technician_id', '=', vals.get('technician_id')), ('stage_id', '=', 'open')]))
        vals['current_assigned_task'] = token_count

        # Get the sequence number
        vals['token_no'] = self.env['ir.sequence'].next_by_code('help.desk')

        # context: no_log, because subtype already handle this
        return super(crm_helpdesk, self).create(vals)

    @api.multi
    def message_new(self,msg, custom_values=None):
        if custom_values is None:
            custom_values = {}
        desc = html2plaintext(msg.get('body')) if msg.get('body') else ''
        defaults = {
            'name': msg.get('subject') or _("No Subject"),
            'description': desc,
            'email_from': msg.get('from'),
            'email_cc': msg.get('cc'),
            'partner_id': msg.get('author_id', False),
        }
        if msg.get('priority'):
            defaults['priority'] = msg.get('priority')
        defaults.update(custom_values)
        return super(crm_helpdesk, self).message_new(msg, custom_values=defaults)

    @api.multi
    def write(self, vals):
        # Validations
        if 'stage_id' in vals:
            if vals['stage_id'] == 'open':
                # check the previos stage
                current_stage = self.stage_id
                if current_stage == 'closed':
                    raise UserError(_('You can not reopen the token.'))

        if 'date_action_next' in vals:
            if 'date' in vals:
                token_date = datetime.strptime(vals.get('date'), '%Y-%m-%d').date()
            else:
                token_date = datetime.strptime(self.date, '%Y-%m-%d').date()

            next_action_date = datetime.strptime(vals.get('date_action_next'), '%Y-%m-%d %H:%M:%S').date()
            if token_date > next_action_date:
                raise UserError(_('Next Action Date cannot be a backdate against the Date.'))

        # if change the technician resend the email
        if 'technician_id' in vals and self.stage_id == 'open':
            self.create_email(vals)
        elif 'technician_id' in vals and self.stage_id == 'incomplete':
            self.create_email_tech(vals)
        elif 'stage_id' in vals:
            self.create_email(vals)
        else:
            pass

        return super(crm_helpdesk, self).write(vals)

    # Closed the ticket
    @api.multi
    def action_closed(self):
        self.write({'stage_id': 'closed'})
        return True

    # Incomplete the ticket
    @api.multi
    def action_incomplete(self):
        self.write({'stage_id': 'incomplete'})
        return True

    # Open the ticket
    @api.multi
    def action_open(self):

        att = {
               'state': 'accepted',
               'common_name': self.technician_id.user_id.name or False,
               'partner_id': self.technician_id.user_id.partner_id.id or False,

               'email': self.technician_id.user_id.email or False,
        }
        user_id = self._uid
        data = {
            'name': self.name,
            'user_id': user_id or False,
            'start': datetime.strptime(self.calendar_start_date, '%Y-%m-%d %H:%M:%S'),
            'state': 'open',
            'res_id': 0,
            'allday': False,
            'privacy': 'public',
            'duration': 0.5,
            'stop': datetime.strptime(self.calendar_end_date, '%Y-%m-%d %H:%M:%S'),
            'description': False,
            'attendee_ids': [(0, 0, att)],
            'partner_ids': self.technician_id.user_id.partner_id.ids or False,
        }
        self.env['calendar.event'].create(data)
        last_record = self.env['calendar.attendee'].search([])
        last_record.create(att)
        event = self.env['calendar.event'].search([], order='id desc', limit=1)
        self._cr.execute(""" INSERT INTO calendar_event_res_partner_rel (calendar_event_id, res_partner_id)
                                       VALUES (%s, %s) """, (event.id, self.technician_id.user_id.partner_id.id))

        self.write({'stage_id': 'open'})

class res_partner(models.Model):

    _inherit = 'res.partner'

    @api.multi
    def _claim_count(self):
        for claim in self:
            claim_ids = self.env['crm.helpdesk'].search([('partner_id','=',claim.id)])
            claim.claim_count = len(claim_ids)

    @api.multi
    def claim_button(self):
        self.ensure_one()
        return {
            'name': 'Partner Claim',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'crm.claim',
            'domain': [('partner_id', '=', self.id)],
        }

    claim_count = fields.Integer(string='# Claims', compute='_claim_count')

class crm_helpdesk_category(models.Model):
    _name = "crm.helpdesk.category"
    _description = "Category of Help Desk"

    name = fields.Char('Name', required=True, translate=True)
    team_id = fields.Many2one('crm.team', 'Sales Team')

class crm_helpdesk_technician(models.Model):

    _name = "crm.helpdesk.technician"
    _description = "Technician of Help Desk"

    name = fields.Char(string='Name', required=True, translate=True)
    phone = fields.Char(string='Phone Number')
    mobile = fields.Char(string='Mobile Number', required=True)
    address = fields.Char(string='Address', translate=True)
    email = fields.Char(string='Email', required=True)
    user_id = fields.Many2one(comodel_name='res.users', string='Related User')

    @api.model
    def create(self, vals):
        user_data = {
            'name': vals['name'],
            'active': True,
            'login': vals['email'],
            'email': vals['email'],
            # 'company_id': self.colod.id,
            'create_uid': self.user_id.id,
            'write_uid': self.user_id.id,
            'display_groups_suggestions': False,
            'share': False
        }
        user_id = self.env['res.users'].sudo().create(user_data)

        vals.update({
            'user_id': user_id.id})

        return super(crm_helpdesk_technician, self).create(vals)


class mail_mail(models.Model):

    _name = "mail.mail"
    _description = "Adding new fields to the mail class"
    _inherit = ['mail.mail']

