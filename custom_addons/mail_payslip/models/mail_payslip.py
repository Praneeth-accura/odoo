# -*- coding: utf-8 -*-

from odoo import tools, models, fields, api, exceptions, _
from PyPDF2 import PdfFileWriter, PdfFileReader
from datetime import datetime, date
import time
import io
import base64

class mail_payslip_wizard(models.TransientModel):
    _name = 'mail.payslip.wizard'

    def _get_payslips(self):
        return self.env['hr.payslip'].browse(self._context.get('active_ids'))

    payslip_ids = fields.Many2many('hr.payslip', string="Payslips", required=True,
        default=_get_payslips)

    def generte_encrypted_pdf(self, payslip, password):
        #pdf_string = self.env['ir.actions.report'].render_qweb_pdf([], '')
        report = self.env.ref('os_hr_payroll_reports.action_report_salary_payslip')
        #self.env['mail.template'].
        pdf_string = report.sudo().render_qweb_pdf([payslip.id])[0]

        # write the payslip PDF content into a "memory file"
        unencrypted_file = io.BytesIO()
        unencrypted_file.write(pdf_string)

        # make a copy of the PDF file, and encrypt it
        pdf_file_reader = PdfFileReader(unencrypted_file)
        pdf_file_writer = PdfFileWriter()
        for page in pdf_file_reader.pages:
            pdf_file_writer.addPage(page)
        pdf_file_writer.encrypt(password)

        # write the encrypted payslip PDF content into a "memory file"
        encrypted_file = io.BytesIO()
        pdf_file_writer.write(encrypted_file)
        unencrypted_file.close()

        return encrypted_file

    @api.multi
    def send_via_mail(self):
        if not self.env.user.email:
            raise exceptions.UserError(
                _('Email required, Please configure your mail address in '
                  'Preferences to be able to send outgoing mails.'))

        for payslip in self.payslip_ids:
            if not payslip.employee_id.work_email:
                pass

            # generate a password to be set on the encrypted payslip
            # last 4 digits of the employee's identification number or 'odoo'
            identification_id = payslip.employee_id.identification_id
            password = payslip.employee_id.name[:4] + (identification_id[-4:] if identification_id else "odoo")

            encrypted_payslip_pdf = self.generte_encrypted_pdf(payslip, str(password))
            self.create_mail_with_attachment(payslip, encrypted_payslip_pdf)

    def create_mail_with_attachment(self, payslip, payslip_pdf):
        """create the mail with attachment"""
        month_year = tools.ustr(datetime.fromtimestamp(time.mktime(time.strptime(payslip.date_from, "%Y-%m-%d"))).strftime('%B-%Y'))
        body_html = _("""Hello %s,
            <br/><br/>Please find your Salary Slip for %s in attachment.<br/><br/>
            Regards,<br/>
            %s.
            <br/>
            <font style="font-size: 9px;">**Your Password is your name's first four char plus your identification numbers last four char.<br/>
            Example: Your name is Turkesh and your identification numbers is TPA151590, So your Password will be Turk1590.<br/>
            **If you have not submitted any id your last char will be odoo so password will be Turkodoo.</font>
            """ % (payslip.employee_id.name, month_year, self.env.user.name))

        mail_id = self.env['mail.mail'].create({
            'email_from': self.env.user.email,
            'email_to': payslip.employee_id.work_email,
            'subject': 'Your Salary Slip for %s' % month_year,
            'body_html': body_html,
        })
        attachment = self.env['ir.attachment'].create({
            'name': 'Salary Slip of %s for %s' % (payslip.employee_id.name, month_year),
            'datas_fname': "payslip.pdf",
            'datas': base64.b64encode(payslip_pdf.getvalue()),
            'res_model': 'mail.mail',
            'res_id': mail_id.id,
        })
        mail_id.write({'attachment_ids': [(6, 0, [attachment.id])]})
        mail_id.send()
        payslip_pdf.close()
