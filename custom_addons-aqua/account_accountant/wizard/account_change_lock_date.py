from odoo import models, fields, api


class AccountChangeLockDate(models.TransientModel):
    """
    This model will be used to get lock date information from the user
    """
    _name = 'account.change.lock.date'
    _description = 'Change lock date'

    period_lock_date = fields.Date(
        string='Lock Date for Non-Advisers',
        default=lambda self: self.env.user.company_id.period_lock_date,
        help='Only users with the Adviser role can edit accounts prior to and inclusive of this date. Use it for period locking inside an open fiscal year, for example.')
    fiscalyear_lock_date = fields.Date(
        string='Lock Date for All Users',
        default=lambda self: self.env.user.company_id.fiscalyear_lock_date,
        help='No users, including Advisers, can edit accounts prior to and inclusive of this date. Use it for fiscal year locking for example.')

    @api.multi
    def change_lock_date(self):
        """
        update lock dates details in the company
        """
        self.env.user.company_id.write({'period_lock_date': self.period_lock_date, 'fiscalyear_lock_date': self.fiscalyear_lock_date})
        return {'type': 'ir.actions.act_window_close'}
