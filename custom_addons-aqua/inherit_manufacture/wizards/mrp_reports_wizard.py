from odoo import fields, api, models, _
from odoo.exceptions import UserError
import base64, os, xlsxwriter
from odoo.tools import misc
from datetime import datetime, timedelta


class TaxReports(models.TransientModel):
    _name = 'mrp.reports'

    sale_order_id = fields.Many2one('sale.order', 'Sale Order')
    report_file = fields.Binary(string="File", readonly=True)
    report_name = fields.Text(string="File Name")
    is_printed = fields.Boolean('Printed', default=False)

    def print_xlsx_report(self):
        # calling below function
        report = self.print_mrp_report()

        my_report_data = open(report, 'rb+')  # opening the file and assigning to a variable
        file = my_report_data.read()  # reading the file
        output = base64.encodestring(file)  # encoding the file
        cr, uid, context = self.env.args
        ctx = dict(context)
        ctx.update({'report_file': output})  # adding to the context
        ctx.update({'file': report})  # adding to the context
        self.env.args = cr, uid, misc.frozendict(context)
        self.report_name = report  # assigning values to the field
        self.report_file = ctx['report_file']
        self.is_printed = True  # assigning values to the field

        # calling the action and assigning it to variable
        result = {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mrp.reports',
            'target': 'new',
            'context': ctx,
            'res_id': self.id,
        }
        os.remove(report)
        return result  # returning the action

    def print_mrp_report(self):
        report = os.path.join(os.path.dirname(__file__), 'MRP' + '.xlsx')  # creating the name of the file
        workbook = xlsxwriter.Workbook(report)  # creating a workbook
        worksheet = workbook.add_worksheet()  # creating a worksheet
        worksheet.set_landscape()

        # font layout, border, text-center, background-color, bold
        font_bold_center = workbook.add_format({'align': 'center',
                                                'border': 1,
                                                'valign': 'vcenter',
                                                'font_size': 12,
                                                'bold': True,
                                                'bg_color': '#99ccff'})
        # font layout, bold
        border = workbook.add_format({'border': 1})

        # Hiding Unwanted columns
        worksheet.set_column('I:XFD', None, None, {'hidden': True})
        # Setting border for the column
        worksheet.set_column('A:I', 25, border)
        worksheet.set_row(0, 20)

        row = 1
        col = 0

        # looping all manufacture orders where sale order is equal to the selected sale order
        for order in self.env['mrp.production'].search([('sale_order_id', '=', self.sale_order_id.id)]):
            # Heading of the reports
            worksheet.write(row, col, "Order", font_bold_center)
            worksheet.write(row, col + 1, "MRP Order Number", font_bold_center)
            worksheet.write(row, col + 2, "Product Name", font_bold_center)
            worksheet.write(row, col + 3, "Quantity To Produce", font_bold_center)
            worksheet.write(row, col + 4, "Bill of Material", font_bold_center)
            worksheet.write(row, col + 5, "Routing", font_bold_center)
            worksheet.write(row, col + 6, "Deadline Start", font_bold_center)
            worksheet.write(row, col + 7, "Responsible", font_bold_center)
            worksheet.write(row, col + 8, "Source", font_bold_center)

            row += 1
            # Manufacture Orders
            worksheet.write(row, col, order.sale_order_id.name)
            worksheet.write(row, col + 1, order.name)
            worksheet.write(row, col + 2, order.product_id.name)
            worksheet.write(row, col + 3, order.product_qty)
            worksheet.write(row, col + 4, order.bom_id.display_name)
            worksheet.write(row, col + 5, order.routing_id.name)
            worksheet.write(row, col + 6, order.date_planned_start)
            worksheet.write(row, col + 7, order.user_id.name)
            worksheet.write(row, col + 8, order.origin)

            row += 1
            # Manufacture orders lines
            worksheet.write(row, col + 2, "Product Name", font_bold_center)
            worksheet.write(row, col + 3, "Unit of Measure", font_bold_center)
            worksheet.write(row, col + 4, "To Consume", font_bold_center)
            worksheet.write(row, col + 5, "Reserved", font_bold_center)
            worksheet.write(row, col + 6, "Consumed", font_bold_center)

            row += 1
            # printing all lines in manufacture order
            for line in order.move_raw_ids:
                # Manufacture order lines
                worksheet.write(row, col + 2, line.product_id.name)
                worksheet.write(row, col + 3, line.product_uom.name)
                worksheet.write(row, col + 4, line.product_uom_qty)
                worksheet.write(row, col + 5, line.reserved_availability)
                worksheet.write(row, col + 6, line.quantity_done)

                row += 1

        row += 2

        # Closing the workbook
        workbook.close()
        return report

    @api.multi
    def action_back(self):
        """This function revert back to the wizard"""
        if self._context is None:
            self._context = {}
        self.is_printed = False  # assigning values to the field
        result = {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mrp.reports',
            'target': 'new',
        }
        return result  # returning the action
