
#-*- coding:utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models
from odoo.report import render_report

# class payroll_advice_report(models.AbstractModel):
#     _inherit = 'report.l10n_in_hr_payroll.report_payrolladvice'
    
    # def get_detail(self, line_ids):
    #     result = []
    #     self.total_bysal = 0.00
    #     for l in line_ids:
    #         res = {}
    #         res.update({
    #                 'name': l.employee_id.name,
    #                 'acc_no': l.name,
    #                 'designation': l.employee_id.job_id.name,
    #                 'department': l.employee_id.department_id.name,
    #                 'ifsc_code': l.ifsc_code,
    #                 'bysal': l.bysal,
    #                 'debit_credit': l.debit_credit,
    #                 })
    #         self.total_bysal += l.bysal
    #         result.append(res)
    #     return result
   