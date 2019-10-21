from odoo import api, fields, models
import sys
from datetime import datetime, timedelta
import math
from datetime import datetime, timedelta, time

class OverTimeWizard(models.TransientModel):
    _name = 'overtime.calc.wizard'

    def calculate_ot(self):
        self.env['hr.employee'].monthly_overtime_calculation_server_action()