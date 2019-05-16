
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError
from odoo import api, fields, models,_

class BiEmployeeLedger(models.Model):
	_name = 'bi.employee.ledger'
	_rec_name = "employee_id"

	@api.onchange('employee_id')
	def _onchange_employee(self):		
		if self.employee_id:			
			self.company_id = self.employee_id.company_id.id


	date_from = fields.Date(string="Date From")
	date_to = fields.Date(string="Date To")
	employee_id = fields.Many2one('hr.employee',string="Employee")
	company_id = fields.Many2one('res.company',string="Company")
	line_ids = fields.One2many('bi.employee.ledger.line','line_id')

	@api.multi
	def show_ledger(self):
		amount_allowance = 0	
		amount_deduction = 0
		ledger = self.env['bi.employee.ledger.line']
		for slip in self:
			emp = self.env['hr.payslip'].search([('date_to','>=',slip.date_from),('date_to','<=',slip.date_to),('employee_id','=',slip.employee_id.id),('state','=','done')],limit=1)				
			if emp:
				for line in self.env['hr.payslip.line'].search([('slip_id','=',emp.id),('employee_id','=',emp.employee_id.id)]):					
				
					if line.category_id.name == 'Allowance':														
						amount_allowance += line.amount				
					if line.category_id.name == 'Deduction':					
						amount_deduction += line.amount				
			vals = {
					'line_id':slip.id,
					'allowance':amount_allowance,
					'deduction':amount_deduction
				   }
			ledger.search([('line_id', '=',slip.id)]).unlink()

			ledger.create(vals)
			

class BiEmployeeLedgerLine(models.Model):
	_name = 'bi.employee.ledger.line'

	line_id = fields.Many2one('bi.employee.ledger')
	allowance = fields.Float(string="Allowance")
	deduction = fields.Float(string="Deductions")

	@api.multi
	def unlink(self):
		return super(BiEmployeeLedgerLine, self).unlink()