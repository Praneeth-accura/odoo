# -*- coding: utf-8 -*-
# Copyright (C) 2019-praneeth

from odoo import models


class InventoryReportWithValueDifferentExcel(models.AbstractModel):
    _name = 'report.inherit_invoice_aqua.report_value_different_document_xls'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, lines):
        for obj in lines:
            worksheet = workbook.add_worksheet('Variance Report With Value (' + obj.name + ')')
            worksheet.set_landscape()

            font_left = workbook.add_format({'align': 'left', 'font_size': 12})
            font_center = workbook.add_format({'align': 'center', 'valign': 'vcenter', 'font_size': 12})
            font_right = workbook.add_format({'num_format': '#,##0.00', 'align': 'right', 'valign': 'right', 'font_size': 12})
            font_bold_center = workbook.add_format({'align': 'center', 'valign': 'vcenter', 'font_size': 12, 'bold': True})
            border = workbook.add_format({'border': 1})

            worksheet.set_column('A:B', 25)
            worksheet.set_column('C:D', 25)
            worksheet.set_column('E:F', 25)
            worksheet.set_column('G:H', 25)
            worksheet.set_row(0, 25)

            row = 0
            col = 0
            worksheet.write(row + 1, col, 'Product', font_bold_center)
            worksheet.write(row + 1, col + 1, 'UOM', font_bold_center)
            worksheet.write(row + 1, col + 2, 'Location', font_bold_center)
            worksheet.write(row + 1, col + 3, 'Theoretical Quantity', font_bold_center)
            worksheet.write(row + 1, col + 4, 'Real Quantity ', font_bold_center)
            worksheet.write(row + 1, col + 5, 'Difference Quantity ', font_bold_center)
            worksheet.write(row + 1, col + 6, 'Value Quantity ', font_bold_center)

            for record in obj.line_ids:
                worksheet.write(row + 2, col, record.product_id.display_name, font_left)
                worksheet.write(row+2, col+1, record.product_uom_id.name, font_center)
                worksheet.write(row+2, col+2, record.location_id.display_name, font_center)
                worksheet.write(row+2, col+3, record.theoretical_qty, font_center)
                worksheet.write(row+2, col+4, record.product_qty, font_center)
                worksheet.write(row+2, col+5, record.different_qty, font_center)
                worksheet.write(row+2, col+6, record.cost_prices, font_center)
                row += 1


class InventoryReportWithExcel(models.AbstractModel):
    _name = 'report.inherit_invoice_aqua.report_document_xls'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, lines):
        for obj in lines:
            worksheet = workbook.add_worksheet('Variance Report (' + obj.name + ')')
            worksheet.set_landscape()

            font_left = workbook.add_format({'align': 'left', 'font_size': 12})
            font_center = workbook.add_format({'align': 'center', 'valign': 'vcenter', 'font_size': 12})
            font_right = workbook.add_format(
                {'num_format': '#,##0.00', 'align': 'right', 'valign': 'right', 'font_size': 12})
            font_bold_center = workbook.add_format(
                {'align': 'center', 'valign': 'vcenter', 'font_size': 12, 'bold': True})
            border = workbook.add_format({'border': 1})

            worksheet.set_column('A', 50)
            worksheet.set_column('B:C:D', 25)
            worksheet.set_column('E:F', 25)
            worksheet.set_column('G:H', 25)
            worksheet.set_row(0, 25)

            row = 0
            col = 0
            worksheet.write(row + 1, col, 'Product', font_bold_center)
            worksheet.write(row + 1, col + 1, 'UOM', font_bold_center)
            worksheet.write(row + 1, col + 2, 'Location', font_bold_center)
            worksheet.write(row + 1, col + 3, 'Theoretical Quantity', font_bold_center)
            worksheet.write(row + 1, col + 4, 'Real Quantity ', font_bold_center)
            worksheet.write(row + 1, col + 5, 'Difference Quantity ', font_bold_center)

            for record in obj.line_ids:
                worksheet.write(row + 2, col, record.product_id.display_name, font_left)
                worksheet.write(row + 2, col + 1, record.product_uom_id.name, font_center)
                worksheet.write(row + 2, col + 2, record.location_id.display_name, font_center)
                worksheet.write(row + 2, col + 3, record.theoretical_qty, font_center)
                worksheet.write(row + 2, col + 4, record.product_qty, font_center)
                worksheet.write(row + 2, col + 5, record.different_qty, font_center)
                row += 1
