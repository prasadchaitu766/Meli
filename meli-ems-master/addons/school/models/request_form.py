from datetime import datetime
from odoo import models, fields, api
from odoo.exceptions import ValidationError,UserError

class ExamEligible(models.Model):
	_name = "exam.eligible"
	_rec_name = "student_name_id"
	_description = "Exam Eligiblity"
	_order = "id desc"

	student_name_id = fields.Many2one('student.student',"Student Name",store=True)
	standard_id = fields.Many2one('school.standard', 'Class',compute='_compute_student_school')
	note = fields.Text(string='Reason')
	state = fields.Selection([('draft','New'),
		('in_progress','In Progress'),
		('approve','Approved'),
		('rejected','Rejected')], index='true', default='draft')
	date = fields.Date(readonly=True, default=fields.Date.context_today, string="Date")

	@api.depends('student_name_id')
	def _compute_student_school(self):
		for file in self:
			if file.student_name_id:
				file.standard_id = file.student_name_id.standard_id.id
	
	@api.multi
	def set_start(self):
		self.write({'state': 'in_progress'})
		self.send_mail_template()

	@api.multi
	def send_mail_template(self):
		# Find the e-mail template
		template = self.env.ref('school.exam_eligibility_request_mail')
		# You can also find the e-mail template like this:
		# template = self.env['ir.model.data'].get_object('mail_template_demo', 'example_email_template')
 
		# Send out the e-mail template to the user
		self.env['mail.template'].browse(template.id).send_mail(self.id)
		

	@api.multi
	def set_approve(self):
		elig_var = self.env['exam.percentage'].search([('exam_percentage_id.standard_id','=',self.standard_id.id),('student_id','=',self.student_name_id.id)])
		student_eligible = self.env['student.student'].search([('standard_id','=',self.standard_id.id),('id','=',self.student_name_id.id)])
		for line in elig_var:
			line.write({'eligible':True})
		for res in student_eligible:
			res.write({'eligible':True})
		self.write({'state': 'approve'})

	@api.multi
	def set_reject(self):
		self.write({'state': 'rejected'})

	@api.multi
	def set_to_reset(self):
		self.write({'state': 'draft'})

	@api.multi
	def unlink(self):
		for rec in self:
			if rec.state != 'draft':
				raise ValidationError(('''You cannot delete this request!'''))
		return super(ExamEligible, self).unlink()

