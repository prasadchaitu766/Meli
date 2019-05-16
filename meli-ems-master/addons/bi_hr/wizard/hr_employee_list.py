from odoo import api, fields, models
from odoo.exceptions import UserError

class EmployeeList(models.TransientModel):
	_name = "employee.list"
	_description = "Employee List"

	company_id = fields.Many2one('school.school', string='Campus', required=True)

	@api.multi
	def generated_employee_list(self):
		# if self.company_id:
		employee_search = self.env['hr.employee'].search([('school_id', '=', self.company_id.id)])
		# raise UserError(str(employee_search))
		return self.env["report"].get_action(employee_search, 'bi_hr.report_employee_new')
