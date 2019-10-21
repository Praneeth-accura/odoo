from odoo import fields, api, models, _
from odoo.exceptions import UserError
import base64, os, xlsxwriter
from odoo.tools import misc
from datetime import datetime, timedelta


class TaxReports(models.TransientModel):
    _name = 'tax.reports'

    report_type = fields.Selection([('debit_and_credit_notes', 'Debit & Credit Notes'),
                                    ('import_input_vat', 'Import-Input VAT'),
                                    ('local_purchase', 'Local Purchase'),
                                    ('sales_output_vat', 'Sales-Output VAT')], string="Report Types")
    start_date = fields.Date(string="From Date")
    end_date = fields.Date(string="To Date")
    report_file = fields.Binary(string="File", readonly=True)
    report_name = fields.Text(string="File Name")
    is_printed = fields.Boolean('Printed', default=False)

    def print_xlsx_report(self):
        """Passing to each function according to the report type"""
        if self.report_type == 'debit_and_credit_notes':
            fl = self.print_debit_and_credit_notes_report()
        elif self.report_type == 'import_input_vat':
            fl = self.print_import_input_vat_report()
        elif self.report_type == 'local_purchase':
            fl = self.print_local_purchase_report()
        elif self.report_type == 'sales_output_vat':
            fl = self.print_sales_output_vat_report()
        else:
            # Raises User Error if report is empty
            raise UserError('Invalid Report Type.')

        #  formatting the report
        my_report_data = open(fl, 'rb+')
        f = my_report_data.read()
        output = base64.encodestring(f)
        cr, uid, context = self.env.args
        ctx = dict(context)
        ctx.update({'report_file': output})
        ctx.update({'file': fl})
        self.env.args = cr, uid, misc.frozendict(context)
        self.report_name = fl
        self.report_file = ctx['report_file']
        self.is_printed = True

        #  returning the report
        result = {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'tax.reports',
            'target': 'new',
            'context': ctx,
            'res_id': self.id,
        }
        os.remove(fl)
        return result

    def print_debit_and_credit_notes_report(self):
        """Report for DEBIT and CREDIT notes"""
        # creating name of the report
        fl = os.path.join(os.path.dirname(__file__),
                          'Debit and Credit Notes Tax Report'+'.xlsx')
        # creating a workbook
        workbook = xlsxwriter.Workbook(fl)
        # adding a worksheet
        worksheet = workbook.add_worksheet()
        worksheet.set_landscape()

        # Layout
        bold = workbook.add_format({'bold': True, 'border': 1,
                                    'align': 'center'})
        # Layout
        font_left = workbook.add_format({'align': 'left',
                                         'border': 1,
                                         'font_size': 12})
        # Layout
        font_center = workbook.add_format({'align': 'center',
                                           'border': 1,
                                           'valign': 'vcenter',
                                           'font_size': 12})
        # Layout
        font_bold_center = workbook.add_format({'align': 'center',
                                                'border': 1,
                                                'valign': 'vcenter',
                                                'font_size': 12,
                                                'bold': True,
                                                'bg_color': '#668cff'})
        # Layout
        border = workbook.add_format({'border': 1})

        # Setting column length and widths
        worksheet.set_column('J:XFD', None, None, {'hidden': True})
        worksheet.set_column('A:J', 25, border)
        worksheet.set_row(0, 20)

        row = 1
        col = 0

        # Column Heading
        worksheet.merge_range(row, col+0, row+1, col+0, "Serial No", font_bold_center)
        worksheet.merge_range(row, col+1, row+1, col+1, "TIN No", font_bold_center)
        worksheet.merge_range(row, col+2, row+1, col+2, "Invoice Date", font_bold_center)
        worksheet.merge_range(row, col+3, row+1, col+3, "Invoice No", font_bold_center)
        worksheet.merge_range(row, col+4, row+1, col+4, "Tax Credit / Tax Debit Note", font_bold_center)
        worksheet.merge_range(row, col+5, row+1, col+5, "Date of Tax Credit / Tax Debit Note", font_bold_center)
        worksheet.merge_range(row, col+6, row+1, col+6, "Tax Credit No. / Tax Debit Note No.", font_bold_center)
        worksheet.merge_range(row, col+7, row+1, col+7, "Value of Tax Credit Note / Tax Debit Note", font_bold_center)
        worksheet.merge_range(row, col+8, row+1, col+8, "VAT Amount", font_bold_center)
        worksheet.merge_range(row, col+9, row+1, col+9, "Issued By Me", font_bold_center)

        col = 0
        row = 3
        serial_no = 1

        # Column data
        for invoice in self.env['account.invoice'].search(
                [('type', 'in', ['out_refund', 'in_invoice']), ('state', '=', 'paid'), ('date_invoice', '>=', self.start_date),
                 ('date_invoice', '<=', self.end_date), ('amount_tax', '>', 0)]):
            worksheet.write(row, col, serial_no, font_center)
            worksheet.write(row, col + 1, invoice.partner_id.vat, font_center)
            worksheet.write(row, col + 2, datetime.strptime(invoice.date_invoice, '%Y-%m-%d').strftime('%m/%d/%y'),
                            font_center)
            worksheet.write(row, col + 3, invoice.origin, font_center)
            worksheet.write(row, col + 4, "Credit" if invoice.type == 'out_refund' else ("Debit" if invoice.type == 'in_refund' else ""))
            worksheet.write(row, col + 5, datetime.strptime(invoice.date_invoice, '%Y-%m-%d').strftime('%m/%d/%y'), font_center)
            worksheet.write(row, col + 6, invoice.number, font_center)
            worksheet.write(row, col + 7, invoice.amount_untaxed, font_center)
            worksheet.write(row, col + 8, invoice.normal_tax, font_center)
            worksheet.write(row, col + 9, "", font_center)

            serial_no += 1
            row += 1

        # closing workbook
        workbook.close()
        return fl

    def print_import_input_vat_report(self):
        """Report for Import vats"""
        # creating name of the report
        fl = os.path.join(os.path.dirname(__file__),
                          'Import - Input Vat' + '.xlsx')
        # creating a workbook
        workbook = xlsxwriter.Workbook(fl)
        # creating a worksheet
        worksheet = workbook.add_worksheet()
        worksheet.set_landscape()

        # Layout
        bold = workbook.add_format({'bold': True, 'border': 1,
                                    'align': 'center'})
        # Layout
        font_left = workbook.add_format({'align': 'left',
                                         'border': 1,
                                         'font_size': 12})
        # Layout
        font_center = workbook.add_format({'align': 'center',
                                           'border': 1,
                                           'valign': 'vcenter',
                                           'font_size': 12})
        # Layout
        font_bold_center = workbook.add_format({'align': 'center',
                                                'border': 1,
                                                'valign': 'vcenter',
                                                'font_size': 12,
                                                'bold': True,
                                                'bg_color': '#668cff'})
        # Layout
        border = workbook.add_format({'border': 1})

        # Setting column length and widths
        worksheet.set_column('I:XFD', None, None, {'hidden': True})
        worksheet.set_column('A:I', 25, border)
        worksheet.set_row(0, 20)

        row = 1
        col = -1

        # Report Heading Columns
        worksheet.merge_range(row, col + 1, row + 1, col + 1, "Serial No", font_bold_center)
        worksheet.merge_range(row, col + 2, row + 1, col + 2, "Cusdec Date", font_bold_center)
        worksheet.merge_range(row, col + 3, row + 1, col + 3, "Cusdec No", font_bold_center)
        worksheet.merge_range(row, col + 4, row + 1, col + 4, "Cusdec Serial ID", font_bold_center)
        worksheet.merge_range(row, col + 5, row + 1, col + 5, "Cusdec Reg Date", font_bold_center)
        worksheet.merge_range(row, col + 6, row + 1, col + 6, "Cusdec Office ID", font_bold_center)
        worksheet.merge_range(row, col + 7, row + 1, col + 7, "VAT Deferred", font_bold_center)
        worksheet.merge_range(row, col + 8, row + 1, col + 8, "VAT Upfront", font_bold_center)
        worksheet.merge_range(row, col + 9, row + 1, col + 9, "Disallowed VAT", font_bold_center)

        col = 0
        row = 3
        serial_no = 1

        # Report Data
        for invoice in self.env['account.invoice'].search(
                [('type', '=', 'in_invoice'), ('state', '=', 'paid'), ('date_invoice', '>=', self.start_date),
                 ('date_invoice', '<=', self.end_date), ('amount_tax', '>', 0), ('type_of_customer', '=', 'foreign')]):
            worksheet.write(row, col, serial_no, font_center)
            worksheet.write(row, col + 1, datetime.strptime(invoice.date_invoice, '%Y-%m-%d').strftime('%m/%d/%y'),
                            font_center)
            worksheet.write(row, col + 2, invoice.number, font_center)
            worksheet.write(row, col + 3, invoice.partner_id.vat, font_center)
            worksheet.write(row, col + 4, invoice.crusdec_id, font_center)
            worksheet.write(row, col + 5, invoice.crusdec_date, font_center)
            worksheet.write(row, col + 6, invoice.crusdec_office_id)
            worksheet.write(row, col + 7, invoice.amount_untaxed, font_center)
            worksheet.write(row, col + 8, invoice.normal_tax, font_center)
            worksheet.write(row, col + 9, invoice.vat_disallowed, font_center)

            serial_no += 1
            row += 1

        # Closing Workbook
        workbook.close()
        return fl

    def print_local_purchase_report(self):
        # creating name for the report
        fl = os.path.join(os.path.dirname(__file__),
                          'Local Purchase' + '.xlsx')
        # creating a workbook
        workbook = xlsxwriter.Workbook(fl)
        # creating a worksheet
        worksheet = workbook.add_worksheet()
        worksheet.set_landscape()

        # layout
        bold = workbook.add_format({'bold': True, 'border': 1,
                                    'align': 'center'})
        # layout
        font_left = workbook.add_format({'align': 'left',
                                         'border': 1,
                                         'font_size': 12})
        # layout
        font_center = workbook.add_format({'align': 'center',
                                           'border': 1,
                                           'valign': 'vcenter',
                                           'font_size': 12})
        # layout
        font_bold_center = workbook.add_format({'align': 'center',
                                                'border': 1,
                                                'valign': 'vcenter',
                                                'font_size': 12,
                                                'bold': True,
                                                'bg_color': '#668cff'})
        # layout
        border = workbook.add_format({'border': 1})

        # setting column heading and width
        worksheet.set_column('I:XFD', None, None, {'hidden': True})
        worksheet.set_column('A:I', 25, border)
        worksheet.set_row(0, 20)

        row = 1
        col = -1

        # column heading
        worksheet.merge_range(row, col + 1, row + 1, col + 1, "Serial No", font_bold_center)
        worksheet.merge_range(row, col + 2, row + 1, col + 2, "Invoice Date", font_bold_center)
        worksheet.merge_range(row, col + 3, row + 1, col + 3, "Tax Invoice No", font_bold_center)
        worksheet.merge_range(row, col + 4, row + 1, col + 4, "Supplier's TIN", font_bold_center)
        worksheet.merge_range(row, col + 5, row + 1, col + 5, "Name of the Supplier", font_bold_center)
        worksheet.merge_range(row, col + 6, row + 1, col + 6, "Description", font_bold_center)
        worksheet.merge_range(row, col + 7, row + 1, col + 7, "Value of purchase", font_bold_center)
        worksheet.merge_range(row, col + 8, row + 1, col + 8, "VAT Amount",
                              font_bold_center)
        worksheet.merge_range(row, col + 9, row + 1, col + 9, "Disallowed VAT Amount", font_bold_center)

        col = 0
        row = 3
        serial_no = 1

        # column data
        for invoice in self.env['account.invoice'].search(
                [('type', '=', 'in_invoice'), ('state', '=', 'paid'), ('date_invoice', '>=', self.start_date),
                 ('date_invoice', '<=', self.end_date), ('amount_tax', '>', 0), ('type_of_customer', '=', 'local')]):
            worksheet.write(row, col, serial_no, font_center)
            worksheet.write(row, col + 1, datetime.strptime(invoice.date_invoice, '%Y-%m-%d').strftime('%m/%d/%y'),
                            font_center)
            worksheet.write(row, col + 2, invoice.number, font_center)
            worksheet.write(row, col + 3, invoice.partner_id.vat, font_center)
            worksheet.write(row, col + 4, invoice.partner_id.name, font_center)
            worksheet.write(row, col + 5, invoice.name, font_center)
            worksheet.write(row, col + 6, invoice.amount_untaxed, font_center)
            worksheet.write(row, col + 7, invoice.normal_tax, font_center)

            serial_no += 1
            row += 1

        # closing workbook
        workbook.close()
        return fl

    @api.multi
    def print_sales_output_vat_report(self):
        """Report for Output vats"""
        # creating name of the report
        fl = os.path.join(os.path.dirname(__file__),
                          'Local Purchase' + '.xlsx')
        # creating a workbook
        workbook = xlsxwriter.Workbook(fl)
        # creating a worksheet
        worksheet = workbook.add_worksheet()
        worksheet.set_landscape()

        # layout
        bold = workbook.add_format({'bold': True, 'border': 1,
                                    'align': 'center'})
        # layout
        font_left = workbook.add_format({'align': 'left',
                                         'border': 1,
                                         'font_size': 12})
        # layout
        font_center = workbook.add_format({'align': 'center',
                                           'border': 1,
                                           'valign': 'vcenter',
                                           'font_size': 12})
        # layout
        font_bold_center = workbook.add_format({'align': 'center',
                                                'border': 1,
                                                'valign': 'vcenter',
                                                'font_size': 12,
                                                'bold': True,
                                                'bg_color': '#99ccff'})
        # layout
        border = workbook.add_format({'border': 1})

        # setting column headings
        worksheet.set_column('H:XFD', None, None, {'hidden': True})
        worksheet.set_column('A:H', 25, border)
        worksheet.set_row(0, 20)

        row = 1
        col = -1

        # Report column headings
        worksheet.merge_range(row, col + 1, row + 1, col + 1, "Serial No", font_bold_center)
        worksheet.merge_range(row, col + 2, row + 1, col + 2, "Invoice Date", font_bold_center)
        worksheet.merge_range(row, col + 3, row + 1, col + 3, "Tax Invoice No", font_bold_center)
        worksheet.merge_range(row, col + 4, row + 1, col + 4, "Purchaser's TIN", font_bold_center)
        worksheet.merge_range(row, col + 5, row + 1, col + 5, "Name of the Purchaser", font_bold_center)
        worksheet.merge_range(row, col + 6, row + 1, col + 6, "Description", font_bold_center)
        worksheet.merge_range(row, col + 7, row + 1, col + 7, "Value of supply", font_bold_center)
        worksheet.merge_range(row, col + 8, row + 1, col + 8, "VAT Amount", font_bold_center)

        col = 0
        row = 3
        serial_no = 1

        # report data
        for invoice in self.env['account.invoice'].search([('type', '=', 'out_invoice'), ('state', '=', 'paid'), ('date_invoice', '>=', self.start_date), ('date_invoice', '<=', self.end_date), ('amount_tax', '>', 0)]):
            worksheet.write(row, col, serial_no, font_center)
            worksheet.write(row, col + 1, datetime.strptime(invoice.date_invoice, '%Y-%m-%d').strftime('%m/%d/%y'), font_center)
            worksheet.write(row, col + 2, invoice.number, font_center)
            worksheet.write(row, col + 3, invoice.partner_id.vat, font_center)
            worksheet.write(row, col + 4, invoice.partner_id.name, font_center)
            worksheet.write(row, col + 5, invoice.name, font_center)
            worksheet.write(row, col + 6, invoice.amount_untaxed + invoice.nbt_tax, font_center)
            worksheet.write(row, col + 7, invoice.normal_tax, font_center)

            serial_no += 1
            row += 1

        # closing the workbook
        workbook.close()
        return fl

    @api.multi
    def action_back(self):
        """Method for back button"""
        if self._context is None:
            self._context = {}
        self.is_printed = False
        # Returns to the below action
        result = {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'tax.reports',
            'target': 'new',
        }
        return result
