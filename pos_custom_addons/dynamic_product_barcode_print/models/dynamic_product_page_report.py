# -*- coding: utf-8 -*-
# Copyright (C) 2017-Today  Technaureus Info Solutions(<http://technaureus.com/>).

from odoo import models, api, _
from reportlab.graphics.barcode import createBarcodeDrawing
from base64 import b64encode
import math
from reportlab.graphics import barcode
from odoo.exceptions import Warning, UserError


class dynamic_product_page_report_temp(models.AbstractModel):
    _name = 'report.dynamic_product_barcode_print.dynamic_prod_page_rpt'

    def _draw_style(self, data):
        return 'width:' + str(data['form']['col_width']) + 'mm !important;height:' + str(data['form']['col_height']) + 'mm !important; margin: 0px 0px 0px 0px; padding: 0px; overflow: hidden !important; text-overflow: ellipsis !important;'
 
    def get_cell_number(self, from_row, from_col, col_no):
        return ((from_row - 1) * col_no + from_col - 1)
 
    def _draw_table(self, data):
        product_list = []
        if data['form']['product_ids']:
            cell_no = self.get_cell_number(data['form']['from_row'], data['form']['from_col'], int(data['form']['col_no']))
            box_needed = int(cell_no) or 0
            for product_data in self.env['product.page.label.qty'].browse(data['form']['product_ids']):
                if product_data.product_id:
                    box_needed += int(product_data.qty)
                    product_list.append(product_data)
            cell_record = self.create_list(product_list, int(cell_no))
            _table =  self.create_table(box_needed, cell_record, data)
            return _table
 
    def _get_barcode(self, value, type, data):
        barcode_str = ''
        if data['form']['with_barcode'] and value and type:
            try:
                barcode_str = createBarcodeDrawing(
                                    type, value=value, format='png', width=int(data['form']['barcode_height']),
                                    height=int(data['form']['barcode_width']), humanReadable = data['form']['humanReadable'])
            except Exception:
                return ''
            barcode_str = barcode_str.asString('png')
            barcode_str = "<img style='width:"+str(data['form']['display_width'])+"px;height:"+str(data['form']['display_height'])+"px;'src=data:image/png;base64,{0}".format(b64encode(barcode_str))+"</img>"
        return barcode_str
# 
    def create_list(self, products, cell_no):
        model = ''
        if self._context.get('active_model') == 'sale.order':
            model = 'sale.order.line'
        elif self._context.get('active_model') == 'purchase.order':
            model = 'purchase.order.line'
        elif self._context.get('active_model') == 'stock.picking':
            model = 'stock.move'
        elif self._context.get('active_model') == 'account.invoice':
            model = 'account.invoice.line'
        product_data = {}
        for prod in products:
            if prod.line_id:
                if model:
                    line_brw = self.env[model].browse(prod.line_id)
                    for qty in range(0,int(prod.qty)):
                        product_data.update({cell_no: {'product_id': line_brw}})
                        cell_no += 1
            elif prod.product_id and not prod.line_id:
                for qty in range(0,int(prod.qty)):
                    product_data.update({cell_no: {'product_id': prod.product_id}})
                    cell_no += 1
        return product_data
# 
    def create_table(self, box_needed, cell_record, data):
        no_of_col = int(data['form']['col_no'])
        product_table = []
        for tr_no in range(1, int(math.ceil(float(box_needed) / no_of_col + 1))):
            product_dict = {}
            for td_no in range(1, no_of_col + 1):
                cellno = self.get_cell_number(tr_no, td_no, no_of_col)
#                 if cell_record.has_key(cellno):
                if cellno in cell_record.keys():
                    product_id = cell_record.get(cellno).get('product_id')
#                     if product_dict.has_key(tr_no):
                    if tr_no in product_dict.keys():
                        product_dict[tr_no].append(product_id)
                    else:
                        product_dict[tr_no] = [product_id]
                else:
#                     if product_dict.has_key(tr_no):
                    if tr_no in product_dict.keys():
                        product_dict[tr_no].append(False)
                    else:
                        product_dict[tr_no] = [False]
            product_table.append(product_dict)
        return product_table
 
    def _get_price(self, product, pricelist_id=None):
        price = 0
        if product:
            price = product.list_price
            if pricelist_id:
                price = pricelist_id.price_get(product.id, 1.0)
                if price and isinstance(price, dict):
                    price = price.get(pricelist_id.id)
        return price
     
    @api.model
    def get_report_values(self, docids, data=None):
        report_obj = self.env['ir.actions.report']
        report = report_obj._get_report_from_name('dynamic_product_barcode_print.dynamic_prod_page_rpt')
        return {
            'doc_ids': self.env["wizard.product.page.report"].browse(data["ids"]),
            'doc_model': report.model,
            'docs': self,
            'draw_table': self._draw_table,
            'get_barcode': self._get_barcode,
            'draw_style': self._draw_style,
            'get_price': self._get_price,
            'data': data
        }

