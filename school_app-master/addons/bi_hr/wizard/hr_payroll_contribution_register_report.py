# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime
from dateutil import relativedelta

from odoo import api, fields, models
from odoo.exceptions import UserError, AccessError


class PayslipLinesContributionRegister(models.TransientModel):
	_inherit = 'payslip.lines.contribution.register'
	employee_id = fields.Many2one('hr.employee',  string='Employee') 
	
	@api.multi
	def print_report_excel(self):
		active_ids = self.env.context.get('active_ids', [])
		datas = {
			 'ids': active_ids,
			 'model': 'hr.contribution.register',
			 'form': self.read()[0]
		}
		return self.env['report'].get_action([], 'bi_hr_tp.excel.payslip.xlsx', data=datas)
		
