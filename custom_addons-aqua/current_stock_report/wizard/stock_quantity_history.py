# -*- coding: utf-8 -*-
# Copyright (C) 2017-Today  Technaureus Info Solutions(<http://technaureus.com/>).

from odoo import api, fields, models, _
from datetime import datetime,date
import xlsxwriter
import base64
from odoo.tools import misc
import os

class StockQuantityHistory(models.TransientModel):
    _inherit = 'stock.quantity.history'
    
    
    report_choose = fields.Selection([('normal','Normal'),
                                      ('custom','Advanced')],
                                      default='normal', string='Report')
    stock_type = fields.Selection([('warehouse','By Warehouse'),
                                   ('loc','By Location')],
                                   default='warehouse')
    warehouse_ids = fields.Many2many('stock.warehouse', string="Warehouse") 
    location_ids = fields.Many2many('stock.location', string="Location", domain=[('usage','!=','view')])
    report_file = fields.Binary('File', readonly=True)
    report_name = fields.Text(string='File Name')
    is_printed = fields.Boolean('Is Printed', default=False)

    def print_report(self, fl=None):
        fl = self.print_report_data()
        my_report_data = open(fl, 'rb+')
        f = my_report_data.read()
        output = base64.encodestring(f)
        cr, uid, context = self.env.args
        ctx = dict(context)
        ctx.update({'report_file': output})
        ctx.update({'file': fl})
        self.env.args = cr, uid, misc.frozendict(context)
        ## To remove those previous saved report data from table. To avoid unwanted storage
        #         self._cr.execute("TRUNCATE report_export_xlsx CASCADE")
        os.remove(fl)
        self.report_name = fl
        self.report_file = ctx['report_file']
        self.is_printed = True

        result = {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'stock.quantity.history',
            'target': 'new',
            'context': ctx,
            'res_id': self.id,
        }
        return result

    def print_stock_report(self):
        fl = self.generate_xlsx_report()
        my_report_data = open(fl,'rb+')
        f = my_report_data.read()
        output = base64.encodestring(f)
        cr, uid, context = self.env.args
        ctx = dict(context)
        ctx.update({'report_file': output})
        ctx.update({'file': fl})
        self.env.args = cr, uid, misc.frozendict(context)
        ## To remove those previous saved report data from table. To avoid unwanted storage
#         self._cr.execute("TRUNCATE report_export_xlsx CASCADE")
        os.remove(fl)
        self.report_name = fl
        self.report_file = ctx['report_file']
        self.is_printed = True
        
        result = {
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'stock.quantity.history',
                'target': 'new',
                'context': ctx,
                'res_id': self.id,
        }
        return result

    @api.multi
    def print_report_data(self):
        stock_type = self.stock_type
        report_type = self.compute_at_date

        if stock_type == 'warehouse':
            fl = os.path.join(os.path.dirname(__file__), 'Inventory (By Warehouse-' + self.date + ').xlsx')
        else:
            fl = os.path.join(os.path.dirname(__file__), 'Inventory (By Location-' + self.date + ').xlsx')
        workbook = xlsxwriter.Workbook(fl)
        worksheet = workbook.add_worksheet()
        worksheet.set_landscape()

        format1 = workbook.add_format(
            {'font_size': 14, 'bottom': True, 'right': True, 'left': True, 'top': True, 'align': 'vcenter',
             'bold': True})
        format11 = workbook.add_format(
            {'font_size': 12, 'align': 'center', 'right': True, 'left': True, 'bottom': True, 'top': True,
             'bold': True})
        format21 = workbook.add_format(
            {'font_size': 10, 'align': 'center', 'right': True, 'left': True, 'bottom': True, 'top': True,
             'bold': True})
        format3 = workbook.add_format({'bottom': True, 'top': True, 'font_size': 12})
        font_size_8 = workbook.add_format({'bottom': True, 'top': True, 'right': True, 'left': True, 'font_size': 8})
        red_mark = workbook.add_format({'bottom': True, 'top': True, 'right': True, 'left': True, 'font_size': 8,
                                        'bg_color': 'red'})
        justify = workbook.add_format({'bottom': True, 'top': True, 'right': True, 'left': True, 'font_size': 12})
        format3.set_align('center')
        font_size_8.set_align('center')
        justify.set_align('justify')
        format1.set_align('center')
        red_mark.set_align('center')
        worksheet.merge_range('A3:H3', 'Report Date: ' + str(datetime.now().strftime("%Y-%m-%d %H:%M %p")), format1)
        worksheet.merge_range('A4:H4', 'Product Information', format11)
        worksheet.set_column('A:A', 15)

        # row = 2
        # col = 0
        #
        # row += 2

        if stock_type == 'loc':
            locations = self.get_locations(self.location_ids.ids)
            if report_type == 0:
                count = len(locations[0]) * 5 + 7
            else:
                count = len(locations[0]) * 4 + 7
            worksheet.merge_range(2, 8, 2, count, 'Locations', format1)
            w_col_no = 7
            w_col_no1 = 8
            for i in locations[0]:
                if report_type == 0:
                    w_col_no = w_col_no + 5
                    worksheet.merge_range(3, w_col_no1, 3, w_col_no, i, format11)
                    w_col_no1 = w_col_no1 + 5
                else:
                    w_col_no = w_col_no + 4
                    worksheet.merge_range(3, w_col_no1, 3, w_col_no, i, format11)
                    w_col_no1 = w_col_no1 + 4
            worksheet.write(4, 0, 'Internal Reference', format21)
            worksheet.merge_range(4, 1, 4, 3, 'Name', format21)
            worksheet.merge_range(4, 4, 4, 5, 'Category', format21)
            worksheet.write(4, 6, 'Cost Price', format21)
            worksheet.write(4, 7, 'Vendors', format21)
            p_col_no1 = 8
            for i in locations[0]:
                if report_type == 0:
                    worksheet.write(4, p_col_no1, 'Incoming', format21)
                    worksheet.write(4, p_col_no1 + 1, 'Outgoing', format21)
                    worksheet.write(4, p_col_no1 + 2, 'Available', format21)
                    worksheet.write(4, p_col_no1 + 3, 'Virtual', format21)
                    worksheet.write(4, p_col_no1 + 4, 'Valuation', format21)
                    p_col_no1 = p_col_no1 + 5
                else:
                    worksheet.write(4, p_col_no1, 'Received', format21)
                    worksheet.write(4, p_col_no1 + 1, 'Delivered', format21)
                    worksheet.write(4, p_col_no1 + 2, 'Available', format21)
                    worksheet.write(4, p_col_no1 + 3, 'Valuation', format21)
                    p_col_no1 = p_col_no1 + 4
            prod_row = 5
            prod_col = 0
            for i in locations[1]:
                get_line = self.get_lines_location(i)
                for each in get_line:
                    if each['internal_ref']:
                        worksheet.write(prod_row, prod_col, each['internal_ref'], font_size_8)
                    else:
                        worksheet.write(prod_row, prod_col, '*no-reference*', font_size_8)
                    worksheet.merge_range(prod_row, prod_col + 1, prod_row, prod_col + 3, each['name'], font_size_8)
                    worksheet.merge_range(prod_row, prod_col + 4, prod_row, prod_col + 5, each['category'], font_size_8)
                    worksheet.write(prod_row, prod_col + 6, each['cost_price'], font_size_8)
                    worksheet.write(prod_row, prod_col + 7, each['vendor_name'], font_size_8)
                    prod_row = prod_row + 1
                break
            prod_row = 5
            prod_col = 8
            for i in locations[1]:
                get_line = self.get_lines_location(i)
                for each in get_line:
                    if each['incoming'] < 0:
                        worksheet.write(prod_row, prod_col, each['incoming'], red_mark)
                    else:
                        worksheet.write(prod_row, prod_col, each['incoming'], font_size_8)
                    if each['outgoing'] < 0:
                        worksheet.write(prod_row, prod_col + 1, each['outgoing'], red_mark)
                    else:
                        worksheet.write(prod_row, prod_col + 1, each['outgoing'], font_size_8)
                    if each['available'] < 0:
                        worksheet.write(prod_row, prod_col + 2, each['available'], red_mark)
                    else:
                        worksheet.write(prod_row, prod_col + 2, each['available'], font_size_8)
                    if report_type == 0:
                        if each['virtual'] < 0:
                            worksheet.write(prod_row, prod_col + 3, each['virtual'], red_mark)
                        else:
                            worksheet.write(prod_row, prod_col + 3, each['virtual'], font_size_8)
                        if each['total_value'] < 0:
                            worksheet.write(prod_row, prod_col + 4, each['total_value'], red_mark)
                        else:
                            worksheet.write(prod_row, prod_col + 4, each['total_value'], font_size_8)
                    else:
                        if each['total_value'] < 0:
                            worksheet.write(prod_row, prod_col + 3, each['total_value'], red_mark)
                        else:
                            worksheet.write(prod_row, prod_col + 3, each['total_value'], font_size_8)
                    prod_row = prod_row + 1
                prod_row = 5
                if report_type == 0:
                    prod_col = prod_col + 5
                else:
                    prod_col = prod_col + 4
        else:
            warehouses = self.get_warehouse(self.warehouse_ids.ids)
            if report_type == 0:
                count = len(warehouses[0]) * 5 + 7
            else:
                count = len(warehouses[0]) * 4 + 7
            worksheet.merge_range(2, 8, 2, count, 'Warehouses', format1)
            w_col_no = 7
            w_col_no1 = 8
            for i in warehouses[0]:
                if report_type == 0:
                    w_col_no = w_col_no + 5
                    worksheet.merge_range(3, w_col_no1, 3, w_col_no, i, format11)
                    w_col_no1 = w_col_no1 + 5
                else:
                    w_col_no = w_col_no + 4
                    worksheet.merge_range(3, w_col_no1, 3, w_col_no, i, format11)
                    w_col_no1 = w_col_no1 + 4
            worksheet.write(4, 0, 'Internal Reference', format21)
            worksheet.merge_range(4, 1, 4, 3, 'Name', format21)
            worksheet.merge_range(4, 4, 4, 5, 'Category', format21)
            worksheet.write(4, 6, 'Cost Price', format21)
            worksheet.write(4, 7, 'Vendors', format21)
            p_col_no1 = 8
            for i in warehouses[0]:
                if report_type == 0:
                    worksheet.write(4, p_col_no1, 'Incoming', format21)
                    worksheet.write(4, p_col_no1 + 1, 'Outgoing', format21)
                    worksheet.write(4, p_col_no1 + 2, 'Available', format21)
                    worksheet.write(4, p_col_no1 + 3, 'Virtual', format21)
                    worksheet.write(4, p_col_no1 + 4, 'Valuation', format21)
                    p_col_no1 = p_col_no1 + 5
                else:
                    worksheet.write(4, p_col_no1, 'Received', format21)
                    worksheet.write(4, p_col_no1 + 1, 'Delivered', format21)
                    worksheet.write(4, p_col_no1 + 2, 'Available', format21)
                    worksheet.write(4, p_col_no1 + 3, 'Valuation', format21)
                    p_col_no1 = p_col_no1 + 4
            prod_row = 5
            prod_col = 0
            for i in warehouses[1]:
                get_line = self.get_lines_warehouse(i)
                for each in get_line:
                    if each['internal_ref']:
                        worksheet.write(prod_row, prod_col, each['internal_ref'], font_size_8)
                    else:
                        worksheet.write(prod_row, prod_col, '*no-reference*', font_size_8)
                    worksheet.merge_range(prod_row, prod_col + 1, prod_row, prod_col + 3, each['name'], font_size_8)
                    worksheet.merge_range(prod_row, prod_col + 4, prod_row, prod_col + 5, each['category'], font_size_8)
                    worksheet.write(prod_row, prod_col + 6, each['cost_price'], font_size_8)
                    worksheet.write(prod_row, prod_col + 7, each['vendor_name'], font_size_8)
                    prod_row = prod_row + 1
                break
            prod_row = 5
            prod_col = 8
            for i in warehouses[1]:
                get_line = self.get_lines_warehouse(i)
                for each in get_line:
                    if each['incoming'] < 0:
                        worksheet.write(prod_row, prod_col, each['incoming'], red_mark)
                    else:
                        worksheet.write(prod_row, prod_col, each['incoming'], font_size_8)
                    if each['outgoing'] < 0:
                        worksheet.write(prod_row, prod_col + 1, each['outgoing'], red_mark)
                    else:
                        worksheet.write(prod_row, prod_col + 1, each['outgoing'], font_size_8)
                    if each['available'] < 0:
                        worksheet.write(prod_row, prod_col + 2, each['available'], red_mark)
                    else:
                        worksheet.write(prod_row, prod_col + 2, each['available'], font_size_8)
                    if report_type == 0:
                        if each['virtual'] < 0:
                            worksheet.write(prod_row, prod_col + 3, each['virtual'], red_mark)
                        else:
                            worksheet.write(prod_row, prod_col + 3, each['virtual'], font_size_8)
                        if each['total_value'] < 0:
                            worksheet.write(prod_row, prod_col + 4, each['total_value'], red_mark)
                        else:
                            worksheet.write(prod_row, prod_col + 4, each['total_value'], font_size_8)
                    else:
                        if each['total_value'] < 0:
                            worksheet.write(prod_row, prod_col + 3, each['total_value'], red_mark)
                        else:
                            worksheet.write(prod_row, prod_col + 3, each['total_value'], font_size_8)
                    prod_row = prod_row + 1
                prod_row = 5
                if report_type == 0:
                    prod_col = prod_col + 5
                else:
                    prod_col = prod_col + 4

        workbook.close()
        return fl

    def get_warehouse(self, ids):
        l1 = []
        l2 = []
        if ids:
            obj = self.env['stock.warehouse'].search([('id', 'in', ids)])
            for j in obj:
                l1.append(j.name)
                l2.append(j.id)
        return l1, l2
    
    def get_locations(self, ids):
        l1 = []
        l2 = []
        locations = self.env['stock.location'].search([])
        if ids:
            obj = self.env['stock.location'].search([('id', 'in', ids)])
            for j in obj:
                l1.append(j.name)
                l2.append(j.id)
                for loc in locations:
                    if j.id == loc.location_id.id:
                        flag = 0
                        for k in obj:
                            if loc.id == k.id:
                                flag = 1
                        if flag == 0:
                            l1.append(loc.name)
                            l2.append(loc.id)
        return l1, l2
    
    def get_lines_location(self, location):
        report_type = self.compute_at_date
        to_date = self.date
        context = {'location':location}
        if report_type == 1:
            context['to_date'] = to_date
        lines = []
        stock_history = self.env['product.product'].search([])
        for obj in stock_history:
            product = self.env['product.product'].browse(obj.id)
            if report_type == 1:
                res_available = product.with_context(context)._product_available_done()
                incoming = res_available[product.id]['incoming_qty']
                outgoing = res_available[product.id]['outgoing_qty']
                virtual_available = 0
                available_qty = incoming - outgoing
                total_value = available_qty * product.standard_price
            else:
                virtual_available = product.with_context(context).virtual_available
                available_qty = product.with_context(context).qty_available
                total_value = available_qty * product.standard_price
                incoming = product.with_context(context).incoming_qty
                outgoing = product.with_context(context).outgoing_qty
            vendors = ''
            for seller_id in product.seller_ids:
                name = seller_id.name.name
                vendors = vendors + name + ', '
            vals = {
                'internal_ref': product.default_code,
                'name': product.name,
                'vendor_name': vendors,
                'category': product.categ_id.name,
                'cost_price': product.standard_price,
                'available': available_qty,
                'virtual': virtual_available,
                'incoming': incoming,
                'outgoing': outgoing,
                'total_value': total_value,
            }
            lines.append(vals)
        return lines
    
    def get_lines_warehouse(self, warehouse):
        report_type = self.compute_at_date
        to_date = self.date
        context = {'warehouse':warehouse}
        if report_type == 1:
            context['to_date'] = to_date
        lines = []
        stock_history = self.env['product.product'].search([])
        for obj in stock_history:
            product = self.env['product.product'].browse(obj.id)
            if report_type == 1:
                res_available = product.with_context(context)._product_available_done()
                incoming = res_available[product.id]['incoming_qty']
                outgoing = res_available[product.id]['outgoing_qty']
                virtual_available = 0
                # available_qty = incoming - outgoing
                available_qty = res_available[product.id]['qty_available']
                total_value = available_qty * product.standard_price
            else:
                virtual_available = product.with_context(context).virtual_available
                available_qty = product.with_context(context).qty_available
                total_value = available_qty * product.standard_price
                incoming = product.with_context(context).incoming_qty
                outgoing = product.with_context(context).outgoing_qty
            vendors = ''
            for seller_id in product.seller_ids:
                name = seller_id.name.name
                vendors = vendors + name + ', '
            vals = {
                'internal_ref': product.default_code,
                'name': product.name,
                'vendor_name': vendors,
                'category': product.categ_id.name,
                'cost_price': product.standard_price,
                'available': available_qty,
                'virtual': virtual_available,
                'incoming': incoming,
                'outgoing': outgoing,
                'total_value': total_value,
            }
            lines.append(vals)
        return lines
    
    def generate_xlsx_report(self):
        stock_type = self.stock_type
        if stock_type == 'warehouse':
            fl = os.path.join(os.path.dirname(__file__),'Inventory (By Warehouse-'+self.date+').xlsx')
        else:
            fl = os.path.join(os.path.dirname(__file__), 'Inventory (By Location-'+self.date+').xlsx')
        workbook = xlsxwriter.Workbook(fl)
        report_type = self.compute_at_date
        sheet = workbook.add_worksheet('Stock Info')
        format1 = workbook.add_format({'font_size': 14, 'bottom': True, 'right': True, 'left': True, 'top': True, 'align': 'vcenter', 'bold': True})
        format11 = workbook.add_format({'font_size': 12, 'align': 'center', 'right': True, 'left': True, 'bottom': True, 'top': True, 'bold': True})
        format21 = workbook.add_format({'font_size': 10, 'align': 'center', 'right': True, 'left': True,'bottom': True, 'top': True, 'bold': True})
        format3 = workbook.add_format({'bottom': True, 'top': True, 'font_size': 12})
        font_size_8 = workbook.add_format({'bottom': True, 'top': True, 'right': True, 'left': True, 'font_size': 8})
        red_mark = workbook.add_format({'bottom': True, 'top': True, 'right': True, 'left': True, 'font_size': 8,
                                        'bg_color': 'red'})
        justify = workbook.add_format({'bottom': True, 'top': True, 'right': True, 'left': True, 'font_size': 12})
        format3.set_align('center')
        font_size_8.set_align('center')
        justify.set_align('justify')
        format1.set_align('center')
        red_mark.set_align('center')
        sheet.merge_range('A3:H3', 'Report Date: ' + str(datetime.now().strftime("%Y-%m-%d %H:%M %p")), format1)
        sheet.merge_range('A4:H4', 'Product Information', format11)
        sheet.set_column('A:A', 15)
        if stock_type == 'loc':
            locations = self.get_locations(self.location_ids.ids)
            if report_type == 0:
                count = len(locations[0]) * 5 + 7
            else:
                count = len(locations[0]) * 4 + 7
            sheet.merge_range(2, 8, 2, count, 'Locations', format1)
            w_col_no = 7
            w_col_no1 = 8
            for i in locations[0]:
                if report_type == 0:
                    w_col_no = w_col_no + 5
                    sheet.merge_range(3, w_col_no1, 3, w_col_no, i, format11)
                    w_col_no1 = w_col_no1 + 5
                else:
                    w_col_no = w_col_no + 4
                    sheet.merge_range(3, w_col_no1, 3, w_col_no, i, format11)
                    w_col_no1 = w_col_no1 + 4
            sheet.write(4, 0, 'Internal Reference', format21)
            sheet.merge_range(4, 1, 4, 3, 'Name', format21)
            sheet.merge_range(4, 4, 4, 5, 'Category', format21)
            sheet.write(4, 6, 'Cost Price', format21)
            sheet.write(4, 7, 'Vendors', format21)
            p_col_no1 = 8
            for i in locations[0]:
                if report_type == 0:
                    sheet.write(4, p_col_no1, 'Incoming', format21)
                    sheet.write(4, p_col_no1 + 1, 'Outgoing', format21)
                    sheet.write(4, p_col_no1 + 2, 'Available', format21)
                    sheet.write(4, p_col_no1 + 3, 'Virtual', format21)
                    sheet.write(4, p_col_no1 + 4, 'Valuation', format21)
                    p_col_no1 = p_col_no1 + 5
                else:
                    sheet.write(4, p_col_no1, 'Received', format21)
                    sheet.write(4, p_col_no1 + 1, 'Delivered', format21)
                    sheet.write(4, p_col_no1 + 2, 'Available', format21)
                    sheet.write(4, p_col_no1 + 3, 'Valuation', format21)
                    p_col_no1 = p_col_no1 + 4
            prod_row = 5
            prod_col = 0
            for i in locations[1]:
                get_line = self.get_lines_location(i)
                for each in get_line:
                    if each['internal_ref']:
                        sheet.write(prod_row, prod_col, each['internal_ref'], font_size_8)
                    else:
                        sheet.write(prod_row, prod_col, '*no-reference*', font_size_8)
                    sheet.merge_range(prod_row, prod_col + 1, prod_row, prod_col + 3, each['name'], font_size_8)
                    sheet.merge_range(prod_row, prod_col + 4, prod_row, prod_col + 5, each['category'], font_size_8)
                    sheet.write(prod_row, prod_col + 6, each['cost_price'], font_size_8)
                    sheet.write(prod_row, prod_col + 7, each['vendor_name'], font_size_8)
                    prod_row = prod_row + 1
                break
            prod_row = 5
            prod_col = 8
            for i in locations[1]:
                get_line = self.get_lines_location(i)
                for each in get_line:
                    if each['incoming'] < 0:
                        sheet.write(prod_row, prod_col, each['incoming'], red_mark)
                    else:
                        sheet.write(prod_row, prod_col, each['incoming'], font_size_8)
                    if each['outgoing'] < 0:
                        sheet.write(prod_row, prod_col + 1, each['outgoing'], red_mark)
                    else:
                        sheet.write(prod_row, prod_col + 1, each['outgoing'], font_size_8)
                    if each['available'] < 0:
                        sheet.write(prod_row, prod_col + 2, each['available'], red_mark)
                    else:
                        sheet.write(prod_row, prod_col + 2, each['available'], font_size_8)
                    if report_type == 0:
                        if each['virtual'] < 0:
                            sheet.write(prod_row, prod_col + 3, each['virtual'], red_mark)
                        else:
                            sheet.write(prod_row, prod_col + 3, each['virtual'], font_size_8)
                        if each['total_value'] < 0:
                            sheet.write(prod_row, prod_col + 4, each['total_value'], red_mark)
                        else:
                            sheet.write(prod_row, prod_col + 4, each['total_value'], font_size_8)
                    else:
                        if each['total_value'] < 0:
                            sheet.write(prod_row, prod_col + 3, each['total_value'], red_mark)
                        else:
                            sheet.write(prod_row, prod_col + 3, each['total_value'], font_size_8)
                    prod_row = prod_row + 1
                prod_row = 5
                if report_type == 0:
                    prod_col = prod_col + 5
                else:
                    prod_col = prod_col + 4
        else:
            warehouses = self.get_warehouse(self.warehouse_ids.ids)
            if report_type == 0:
                count = len(warehouses[0]) * 5 + 7
            else:
                count = len(warehouses[0]) * 4 + 7
            sheet.merge_range(2, 8, 2, count, 'Warehouses', format1)
            w_col_no = 7
            w_col_no1 = 8
            for i in warehouses[0]:
                if report_type == 0:
                    w_col_no = w_col_no + 5
                    sheet.merge_range(3, w_col_no1, 3, w_col_no, i, format11)
                    w_col_no1 = w_col_no1 + 5
                else:
                    w_col_no = w_col_no + 4
                    sheet.merge_range(3, w_col_no1, 3, w_col_no, i, format11)
                    w_col_no1 = w_col_no1 + 4
            sheet.write(4, 0, 'Internal Reference', format21)
            sheet.merge_range(4, 1, 4, 3, 'Name', format21)
            sheet.merge_range(4, 4, 4, 5, 'Category', format21)
            sheet.write(4, 6, 'Cost Price', format21)
            sheet.write(4, 7, 'Vendors', format21)
            p_col_no1 = 8
            for i in warehouses[0]:
                if report_type == 0:
                    sheet.write(4, p_col_no1, 'Incoming', format21)
                    sheet.write(4, p_col_no1 + 1, 'Outgoing', format21)
                    sheet.write(4, p_col_no1 + 2, 'Available', format21)
                    sheet.write(4, p_col_no1 + 3, 'Virtual', format21)
                    sheet.write(4, p_col_no1 + 4, 'Valuation', format21)
                    p_col_no1 = p_col_no1 + 5
                else:
                    sheet.write(4, p_col_no1, 'Received', format21)
                    sheet.write(4, p_col_no1 + 1, 'Delivered', format21)
                    sheet.write(4, p_col_no1 + 2, 'Available', format21)
                    sheet.write(4, p_col_no1 + 3, 'Valuation', format21)
                    p_col_no1 = p_col_no1 + 4
            prod_row = 5
            prod_col = 0
            for i in warehouses[1]:
                get_line = self.get_lines_warehouse(i)
                for each in get_line:
                    if each['internal_ref']:
                        sheet.write(prod_row, prod_col, each['internal_ref'], font_size_8)
                    else:
                        sheet.write(prod_row, prod_col, '*no-reference*', font_size_8)
                    sheet.merge_range(prod_row, prod_col + 1, prod_row, prod_col + 3, each['name'], font_size_8)
                    sheet.merge_range(prod_row, prod_col + 4, prod_row, prod_col + 5, each['category'], font_size_8)
                    sheet.write(prod_row, prod_col + 6, each['cost_price'], font_size_8)
                    sheet.write(prod_row, prod_col + 7, each['vendor_name'], font_size_8)
                    prod_row = prod_row + 1
                break
            prod_row = 5
            prod_col = 8
            for i in warehouses[1]:
                get_line = self.get_lines_warehouse(i)
                for each in get_line:
                    if each['incoming'] < 0:
                        sheet.write(prod_row, prod_col, each['incoming'], red_mark)
                    else:
                        sheet.write(prod_row, prod_col, each['incoming'], font_size_8)
                    if each['outgoing'] < 0:
                        sheet.write(prod_row, prod_col + 1, each['outgoing'], red_mark)
                    else:
                        sheet.write(prod_row, prod_col + 1, each['outgoing'], font_size_8)
                    if each['available'] < 0:
                        sheet.write(prod_row, prod_col + 2, each['available'], red_mark)
                    else:
                        sheet.write(prod_row, prod_col + 2, each['available'], font_size_8)
                    if report_type == 0:
                        if each['virtual'] < 0:
                            sheet.write(prod_row, prod_col + 3, each['virtual'], red_mark)
                        else:
                            sheet.write(prod_row, prod_col + 3, each['virtual'], font_size_8)
                        if each['total_value'] < 0:
                            sheet.write(prod_row, prod_col + 4, each['total_value'], red_mark)
                        else:
                            sheet.write(prod_row, prod_col + 4, each['total_value'], font_size_8)
                    else:
                        if each['total_value'] < 0:
                            sheet.write(prod_row, prod_col + 3, each['total_value'], red_mark)
                        else:
                            sheet.write(prod_row, prod_col + 3, each['total_value'], font_size_8)
                    prod_row = prod_row + 1
                prod_row = 5
                if report_type == 0:
                    prod_col = prod_col + 5
                else:
                    prod_col = prod_col + 4
        return fl

    @api.multi
    def action_back(self):
        cr, uid, context = self.env.args
        ctx = dict(context)
        if self._context is None:
            self._context = {}
        self.is_printed = False
        ctx.update({'compute_at_date': 0})
        result = {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'stock.quantity.history',
            'target': 'new',
            'context': ctx,
        }
        return result
    
    