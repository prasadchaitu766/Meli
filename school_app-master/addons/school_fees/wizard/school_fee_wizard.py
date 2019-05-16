from odoo import api, fields, models
from odoo.exceptions import UserError

class SchoolReportWizard(models.TransientModel):	
	_name = 'school.month.report'
	
	start_date = fields.Date(required=True)
	end_date = fields.Date(required=True)
	school_id = fields.Many2one('school.school', string="Campus")
	fees_id = fields.Many2one('student.fees.structure.line', string="Type")
	semester_id = fields.Many2one('standard.semester', string="Semester")


	@api.multi
	def generate_report(self,data):
		data['form'] = {}
		data['form'].update(self.read(['start_date','end_date','school_id','fees_id','semester_id'])[0])
		return self.env["report"].get_action(self, 'school_fees.type_wise', data=data)
