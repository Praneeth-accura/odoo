from odoo import api, fields, models, _
from odoo.addons.base.res.res_partner import _tz_get
import sys
from datetime import datetime, timedelta
import pytz
from odoo.exceptions import UserError, ValidationError
from ..zk import ZK, const
sys.path.append("zk")

def represent_int(s):
    try:
        int(s)
        return True
    except ValueError:
        return False


class BiometricDeviceConfig(models.Model):
    _name = 'biometric.config'

    name = fields.Char(string='Name', required=True)
    device_ip = fields.Char(string='Device IP', required=True)
    port = fields.Integer(string='Port', required=True)

    @api.one
    def test_device_connection(self):
        conn = None
        zk = ZK(self.device_ip, port=self.port, timeout=5)

        try:
            print 'Connecting to device ...'
            conn = zk.connect()
            print 'Disabling device ...'
            conn.disable_device()
            print 'Firmware Version: : {}'.format(conn.get_firmware_version())
            # print '--- Get User ---'
            users = conn.get_users()
            for user in users:
                privilege = 'User'
                if user.privilege == const.USER_ADMIN:
                    privilege = 'Admin'

                print '- UID #{}'.format(user.uid)
                print '  Name       : {}'.format(user.name)
                print '  Privilege  : {}'.format(privilege)
                print '  Password   : {}'.format(user.password)
                print '  Group ID   : {}'.format(user.group_id)
                print '  User  ID   : {}'.format(user.user_id)

            print "Voice Test ..."
            conn.test_voice()
            print 'Enabling device ...'
            conn.enable_device()
            raise UserError(_("Connection Success"))
        except Exception, e:
            print "Process terminate : {}".format(e)
            raise UserError(_(e))
        finally:
            if conn:
                conn.disconnect()

    @api.multi
    def sync_employees(self):
        conn = None
        zk = ZK(self.device_ip, port=self.port, timeout=5)

        try:
            employees = self.env['hr.employee'].search([])
            for employee in employees:
                conn = zk.connect()
                conn.disable_device()
                zk.set_user(employee.id, str(employee.name), 0, '', '1', str(employee.id))
                conn.enable_device()
                print 'User Added'
            raise UserError(_("Sync Employee Success"))
        except Exception, e:
            print "Process terminate : {}".format(e)
            raise UserError(_(e))
        finally:
            if conn:
                conn.disconnect()

    @api.multi
    def delete_users(self):
        conn = None
        zk = ZK(self.device_ip, port=self.port, timeout=5)

        try:
            employees = self.env['hr.employee'].search([])
            for employee in employees:
                conn = zk.connect()
                conn.disable_device()
                conn.delete_user(uid=employee.id)
                conn.enable_device()
                print 'User Deleted'
            raise UserError(_("Device User Deletion Successful"))
        except Exception, e:
            print "Process terminate : {}".format(e)
            raise UserError(_(e))
        finally:
            if conn:
                conn.disconnect()

    @api.multi
    def download_attendance_log(self):
        attend_obj = self.env['attendance.log']
        ip = self.device_ip
        port = self.port
        conn = None
        zk = ZK(ip, port=port, timeout=5)
        try:
            conn = zk.connect()
            conn.disable_device()
            attendances = conn.get_attendance()
            conn.enable_device()
            if attendances:
                for attendance in attendances:
                    record = str(attendance).split('/')
                    result = represent_int(record[0].split('>')[1])
                    if result == False:
                        pass
                    else:
                        employee_id = int(record[0].split('>')[1])
                        punching_time = datetime.strptime(record[1].split('>')[1].strip(), '%Y-%m-%d %H:%M:%S') - timedelta(hours=5, minutes=30)
                        status = record[2].split('>')[1].strip()
                        existing_record = attend_obj.search([
                            ('employee_id', '=', employee_id),
                            ('punching_time', '=', str(punching_time))
                        ])
                        if existing_record:
                            pass
                        else:
                            vals = {
                                'employee_id': employee_id,
                                'punching_time': punching_time,
                                'date': datetime.strptime(record[1].split('>')[1].strip(), '%Y-%m-%d %H:%M:%S').date(),
                                'status': status,
                                'device': self.id,
                                'is_calculated': False
                            }
                            attend_obj.create(vals)
                return{'name': 'Success Message',
                       'type': 'ir.actions.act_window',
                       'res_model': 'success.wizard',
                       'view_mode': 'form',
                       'view_type': 'form',
                       'target': 'new'}
            else:
                print 'No attendance data'
                raise UserError(_("No attendance data to download"))
        except Exception, e:
            print "Process terminate : {}".format(e)
            raise UserError(_(e))
        finally:
            if conn:
                conn.disconnect()
        return True

    @api.multi
    def download_attendance_log_for_monthly_ot(self, device):
        attend_obj = self.env['attendance.log']
        ip = device.device_ip
        port = device.port
        conn = None
        zk = ZK(ip, port=port, timeout=5)
        try:
            conn = zk.connect()
            conn.disable_device()
            attendances = conn.get_attendance()
            conn.enable_device()
            if attendances:
                for attendance in attendances:
                    record = str(attendance).split('/')
                    result = represent_int(record[0].split('>')[1])
                    if result == False:
                        pass
                    else:
                        employee_id = int(record[0].split('>')[1])
                        punching_time = datetime.strptime(record[1].split('>')[1].strip(), '%Y-%m-%d %H:%M:%S') - timedelta(hours=5, minutes=30)
                        status = record[2].split('>')[1].strip()
                        existing_record = attend_obj.search([
                            ('employee_id', '=', employee_id),
                            ('punching_time', '=', str(punching_time))
                        ])
                        if existing_record:
                            pass
                        else:
                            vals = {
                                'employee_id': employee_id,
                                'punching_time': punching_time,
                                'date': datetime.strptime(record[1].split('>')[1].strip(), '%Y-%m-%d %H:%M:%S').date(),
                                'status': status,
                                'device': device.id,
                                'is_calculated': False
                            }
                            attend_obj.create(vals)

                print("successfully downloaded")

                return{'name': 'Success Message',
                       'type': 'ir.actions.act_window',
                       'res_model': 'success.wizard',
                       'view_mode': 'form',
                       'view_type': 'form',
                       'target': 'new'}
            else:
                print 'No attendance data'
                raise UserError(_("No attendance data to download"))
        except Exception, e:
            print "Process terminate : {}".format(e)
            raise UserError(_(e))
        finally:
            if conn:
                conn.disconnect()
        return True