from odoo import api, fields, models, _
import sys
from odoo.exceptions import UserError, ValidationError
from ..zk import ZK, const
sys.path.append("zk")

class BiometricDeviceWizard(models.TransientModel):
    _name = 'biometric.device.wizard'
    
    biometric_id = fields.Many2one('biometric.config', string='Biometric Device', required=True)
    opertaion_type = fields.Selection([('update','Update'),('scan','Scan')], string="Type")

    @api.multi
    def confirm_update_with_biometric(self):
        employee_id = self._context.get('active_id')
        employee_obj = self.env['hr.employee'].browse(employee_id)
        ip = self.biometric_id.device_ip
        port = self.biometric_id.port
        conn = None
        zk = ZK(ip, port=port, timeout=5)

        try:
            conn = zk.connect()
            conn.disable_device()
            zk.set_user(employee_obj.id, str(employee_obj.name), 0, '', '1', str(employee_obj.id))
            conn.enable_device()
            print 'User Added'
            raise UserError(_("Employee Added Successfully"))
        except Exception, e:
            print "Process terminate : {}".format(e)
            raise UserError(_(e))
        finally:
            if conn:
                conn.disconnect()
        
    @api.multi
    def confirm_scan_with_biometric(self):
        employee_id = self._context.get('active_id')
        ip = self.biometric_id.device_ip
        port = self.biometric_id.port
        conn = None
        zk = ZK(ip, port=port, timeout=5)

        try:
            employee_id_list = []
            conn = zk.connect()
            conn.disable_device()
            users = conn.get_users()
            for user in users:
                device_user_id = int(format(user.uid))
                employee_id_list.append(device_user_id)
            in_the_list = employee_id in employee_id_list
            if in_the_list == True:
                enrollment_dic = zk.enroll_user(str(employee_id))
                conn.enable_device()
                status = enrollment_dic.get('status')
                if status == True:
                    print 'Place your finger'
                    raise UserError(_("Place your finger on the Biometric Device"))
                else:
                    print 'Finger already placed'
                    raise UserError(_("Finger already placed"))
            else:
                raise UserError(_("Please sync the employee and try again later"))
        except Exception, e:
            print "Process terminate : {}".format(e)
            raise UserError(_(e))
        finally:
            if conn:
                conn.disconnect()
    

class SuccessWizard(models.TransientModel):
    _name = 'success.wizard'