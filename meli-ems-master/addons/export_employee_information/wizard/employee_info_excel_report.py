##############################################################################
#
#    Bassam Infotech LLP.
#    Copyright (C) 2017-TODAY Bassam Infotech LLP(<https://www.bassaminfotech.com>).
#    Author: Redouane ADADI(<https://www.bassaminfotech.com>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    It is forbidden to publish, distribute, sublicense, or sell copies
#    of the Software or modified copies of the Software.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from odoo import api, fields, models, _
import xlwt, xlsxwriter
import base64


class EmployeeInfoExcelReport(models.TransientModel):
    _name = 'employee.info.excel.report'
    _description = 'Employee Information Excel Report'

    school_id = fields.Many2one('school.school', string='Campus', required=True)

    @api.multi
    def generated_excel_report(self, record):
        employee_obj = self.env['hr.employee']
        employee_search = employee_obj.search([('school_id', '=', self.school_id.id)])
        workbook = xlwt.Workbook()

        # Style for Excel Report
        style0 = xlwt.easyxf('font: name Times New Roman bold on; align: horiz left; borders: top double; pattern: pattern solid', num_format_str='#,##0.00')
        style1 = xlwt.easyxf('font:bold True, color Yellow , height 480;  borders:top double; align: horiz center; pattern: pattern solid, fore_colour gray25;', num_format_str='#,##0.00')
        style2 = xlwt.easyxf('font:bold True, color Aqua, height 480;  borders:top double; align: horiz center; pattern: pattern solid, fore_colour gray25;', num_format_str='#,##0.00')
        styletitle = xlwt.easyxf(
            'font:bold True, color Orange, height 400;  borders: top double; align: horiz center; pattern: pattern solid, fore_colour gray25;',
            num_format_str='#,##0.00')
        sheet = workbook.add_sheet("Employee Information List")

        sheet.write_merge(0, 0, 0, 10, 'PUBLIC INFORMATION', style2)

        sheet.write_merge(1, 1, 1, 5, 'Contact Information', style1)
        sheet.write_merge(1, 1, 6, 10, 'Position', style1)

        sheet.write(2, 0, 'Name', styletitle)
        sheet.write(2, 1, 'Working Address', styletitle)
        sheet.write(2, 2, 'Work Mobile', styletitle)
        sheet.write(2, 3, 'Working Location', styletitle)
        sheet.write(2, 4, 'Working Email', styletitle)
        sheet.write(2, 5, 'Working Phone', styletitle)
        sheet.write(2, 6, 'Department', styletitle)
        sheet.write(2, 7, 'Job Title', styletitle)
        sheet.write(2, 8, 'Manager', styletitle)
        sheet.write(2, 9, 'Coach', styletitle)
        sheet.write(2, 10, 'Working Time', styletitle)

        sheet.col(0).width = 700 * (len('Name') + 1)
        sheet.col(1).width = 700 * (len('Working Address') + 1)
        sheet.col(3).width = 700 * (len('Working Mobile') + 1)
        sheet.col(4).width = 700 * (len('Working Location') + 1)
        sheet.col(5).width = 700 * (len('Working Email') + 1)
        sheet.col(6).width = 700 * (len('Working Phone') + 1)
        sheet.col(7).width = 700 * (len('Department') + 1)
        sheet.col(8).width = 700 * (len('Job Title') + 1)
        sheet.col(9).width = 700 * (len('Manager') + 1)
        sheet.col(10).width = 700 * (len('Working Time') + 1)
        sheet.row(0).height_mismatch = True
        sheet.row(0).height = 256 * 2
        sheet.row(1).height = 256 * 2
        sheet.row(2).height = 256 * 2

        row = 3
        for rec in employee_search:
            sheet.write(row, 0, rec.name, style0)
            sheet.write(row, 1, rec.address_id.name, style0)
            sheet.write(row, 2, rec.mobile_phone, style0)
            sheet.write(row, 3, rec.work_location, style0)
            sheet.write(row, 4, rec.work_email, style0)
            sheet.write(row, 5, rec.work_phone, style0)
            sheet.write(row, 6, rec.department_id.name, style0)
            sheet.write(row, 7, rec.job_id.name, style0)
            sheet.write(row, 8, rec.parent_id.name, style0)
            sheet.write(row, 9, rec.coach_id.name, style0)
            sheet.write(row, 10, rec.calendar_id.name, style0)
            row +=1
        workbook.save('/tmp/employee_info_list.xls')
        result_file = open('/tmp/employee_info_list.xls', 'rb').read()
        attachment_id = self.env['wizard.emp.info.excel.report'].create({
            'name': 'Employee Information.xls',
            'report': base64.encodestring(result_file)
        })

        return {
            'name': _('Notification'),
            'context': self.env.context,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'wizard.emp.info.excel.report',
            'res_id': attachment_id.id,
            'data': None,
            'type': 'ir.actions.act_window',
            'target': 'new'
        }


class WizardEmployeeInformationExcelReport(models.TransientModel):
    _name = 'wizard.emp.info.excel.report'

    name = fields.Char('File Name', size=64)
    report = fields.Binary('Prepared File', filters='.xls', readonly=True)
