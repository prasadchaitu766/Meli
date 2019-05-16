from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError
from odoo import api, fields, models,_

class EmployeeNorm(models.Model):
	_name = 'employee.norms'
	_rec_name = 'employee_id'

	employee_id = fields.Many2one('hr.employee', "Employee")
	designation_id = fields.Many2one('hr.job', "Designation")
	norm_ids = fields.One2many('employee.norms.line', 'norm_line_id', "Employee Norms")

	@api.onchange('employee_id')
	def _onchange_employee(self):		
		if self.employee_id:			
			self.designation_id = self.employee_id.job_id.id

class EmployeeNormLine(models.Model):
	_name = 'employee.norms.line'

	norm_line_id = fields.Many2one('employee_id.norms', "Norm Line")
	conditon = fields.Text("Conditions")
