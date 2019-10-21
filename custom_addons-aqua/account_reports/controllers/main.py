# -*- coding: utf-8 -*-

from odoo import http
from odoo.http import content_disposition, request
from odoo.addons.web.controllers.main import _serialize_exception
from odoo.tools import html_escape

import json


class FinancialReportController(http.Controller):

    @http.route('/account_reports', type='http', auth='user', methods=['POST'], csrf=False)
    def ooa_get_report(self, model, options, output_format, token, financial_id=None, **kw):
        """
        return relevant files to download
        """
        uid = request.session.uid
        report_obj = request.env[model].sudo(uid)
        options = json.loads(options)
        if financial_id:
            # if exist financial year get report using it
            report_obj = report_obj.browse(int(financial_id))
        report_name = report_obj.ooa_get_report_filename(options)
        try:

            # return excel report
            if output_format == 'xlsx':
                response = request.make_response(
                    None,
                    headers=[
                        ('Content-Type', 'application/vnd.ms-excel'),
                        ('Content-Disposition', content_disposition(report_name + '.xlsx'))
                    ]
                )
                report_obj.ooa_get_xlsx(options, response)

            # return pdf report
            if output_format == 'pdf':
                response = request.make_response(
                    report_obj.ooa_get_pdf(options),
                    headers=[
                        ('Content-Type', 'application/pdf'),
                        ('Content-Disposition', content_disposition(report_name + '.pdf'))
                    ]
                )

            # return data as xml
            if output_format == 'xml':
                content = report_obj.ooa_get_xml(options)
                response = request.make_response(
                    content,
                    headers=[
                        ('Content-Type', 'application/vnd.sun.xml.writer'),
                        ('Content-Disposition', content_disposition(report_name + '.xml')),
                        ('Content-Length', len(content))
                    ]
                )

            # return data as xaf
            if output_format == 'xaf':
                content = report_obj.ooa_get_xaf(options)
                response = request.make_response(
                    content,
                    headers=[
                        ('Content-Type', 'application/vnd.sun.xml.writer'),
                        ('Content-Disposition', 'attachment; filename=' + report_name + '.xaf;'),
                        ('Content-Length', len(content))
                    ]
                )

            # return data as text file
            if output_format == 'txt':
                content = report_obj.ooa_get_txt(options)
                response = request.make_response(
                    content,
                    headers=[
                        ('Content-Type', 'text/plain'),
                        ('Content-Disposition', content_disposition(report_name + '.txt')),
                        ('Content-Length', len(content))
                    ]
                )

            # return data as csv file
            if output_format == 'csv':
                content = report_obj.ooa_get_csv(options)
                response = request.make_response(
                    content,
                    headers=[
                        ('Content-Type', 'text/csv'),
                        ('Content-Disposition', 'attachment; filename=' + report_name + '.csv;'),
                        ('Content-Length', len(content))
                    ]
                )

            # return data as zip file
            if output_format == 'zip':
                content = report_obj.ooa__get_zip(options)
                response = request.make_response(
                    content,
                    headers=[
                        ('Content-Type', 'application/zip'),
                        ('Content-Disposition', 'attachment; filename=' + report_name + '.zip'),
                    ]
                )
                # send whole file in once
                response.direct_passthrough = True
            response.set_cookie('fileToken', token)
            return response

        # if occur exception, catch it
        except Exception as e:
            se = _serialize_exception(e)
            error = {
                'code': 200,
                'message': 'Odoo Server Error',
                'data': se
            }
            return request.make_response(html_escape(json.dumps(error)))
