# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models, fields, _
from odoo.exceptions import UserError, ValidationError


class WizardBiLedger(models.TransientModel):
	_name = 'bi.employee.ledger'

	# def _default_employee(self):
	#     return self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)

	start_date = fields.Datetime(required=True)
	end_date = fields.Datetime(required=True)
	employee_id = fields.Many2one('hr.employee', "Employee")
	company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.user.company_id)

	@api.onchange('employee_id')
	def onchange_employee(self):
		if self.employee_id:
			self.company_id = self.employee_id.company_id.id

	@api.multi
	def print_Excel_report(self,vals):
		invoice_obj = self.env['check.date'].search([])
		if invoice_obj:
			invoice_obj[-1].write(
							{'start_date':self.start_date,
							'end_date':self.end_date,
							# 'employee_id':self.employee_id.id,
							'company_id':self.company_id.id,
							})
		if not invoice_obj:
			invoice_obj.create(
							{'start_date':self.start_date,
							'end_date':self.end_date,
							# 'employee_id':self.employee_id.id,
							'company_id':self.company_id.id,
							})

		return self.env["report"].get_action(self, 'account.bi.employee.ledger.xlsx')

class CheckDate(models.Model):
	_name = 'check.date'

	start_date = fields.Date('From Date',default=fields.Datetime.now(), required=True)
	end_date = fields.Date('To Date',default=fields.Datetime.now(),required=True)
	employee_id = fields.Many2one('hr.employee', "Employee", required=True)
	company_id = fields.Many2one('res.company', string='Company', required=True)

