from datetime import datetime, timedelta
from odoo import api, fields, models, _
import time


class Project(models.Model):

    _name = "project.project"
    _description = "Adding new fields to the project"
    _inherit = ['project.project']

    def _get_default_stage_id(self):
        """ Gives default stage_id """
        project_task_type_obj = self.env['project.task.type'].search([('name', '=', 'New')])
        if not project_task_type_obj:
            return False
        return project_task_type_obj.id

    stage_id = fields.Many2one('project.task.type', string='Stage', track_visibility='onchange', index=True,
                               default=_get_default_stage_id, readonly=True)
    date_deadline = fields.Datetime(string='Dead Line', required=True)
    done_date = fields.Datetime(string='Done Date', readonly=True)

    def set_to_new(self):
        self.write({'stage_id': 1,
                    'done_date': False})

    def set_to_inprogress(self):
        self.write({'stage_id': 2, 'done_date': None})
        for project_tasks in self.env['project.task'].search([('project_id', '=', self.id), ('stage_id', '!=', 3)]):
            project_tasks.write({'stage_id': 2,
                                 'done_date': False})

    def set_to_done(self):
        self.write({'stage_id': 3, 'done_date': datetime.now()})
        for project_tasks in self.env['project.task'].search([('project_id', '=', self.id)]):
            project_tasks.write({'stage_id': 3,
                                 'done_date': datetime.now()})


class Tasks(models.Model):
    _inherit = 'project.task'

    def _get_default_stage_id(self):
        """ Gives default stage_id """
        project_id = self.env.context.get('default_project_id')
        if not project_id:
            return False
        return self.stage_find(project_id, [('fold', '=', False)])

    stage_id = fields.Many2one('project.task.type', string='Stage', track_visibility='onchange', index=True,
                               default=_get_default_stage_id, group_expand='_read_group_stage_ids', domain=[],
                               copy=False, readonly=True)

    @api.model
    def create(self, vals):
        vals['stage_id'] = 1
        return super(Tasks, self).create(vals)

    def set_to_new(self):
        self.write({'stage_id': 1})

    def set_to_inprogress(self):
        self.write({'stage_id': 2})

    def set_to_done(self):
        self.write({'stage_id': 3,})
