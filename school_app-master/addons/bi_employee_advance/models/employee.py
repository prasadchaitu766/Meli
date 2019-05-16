from odoo import api, fields, models, _
from odoo.exceptions import UserError
from xml.dom.minidom import ReadOnlySequentialNamedNodeMap
#==================================================
# Class : BiEmployeeSalary
# Description : Employee Salary Details
#==================================================
class BiEmployeeSalary(models.Model):
	_name = "bi.employee.salary"
	_description = "Employee Salary Details"
	_order = "id desc"

	def _get_employee_id(self):
		# assigning the related employee of the logged in user
		employee_rec = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
		return employee_rec.id

	name = fields.Char(string="Sequence No", required=True, Index= True, default=lambda self:('New'), readonly=True)
	state = fields.Selection([
		('draft', 'Draft'),
		('request', 'Request'),
		('reject', 'Rejected'),
		('approve', 'Approval'),
		('paid', 'Paid'),
		], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', default='draft')

	employee_id = fields.Many2one('hr.employee', string = "Employee",required=True,readonly=True,states={'draft': [('readonly', False)]}, default=_get_employee_id)
	design_id = fields.Many2one('hr.job', string='Designation', required=True,readonly=True,states={'draft': [('readonly', False)]})
	amount = fields.Float(string="Request Amount",readonly=True,states={'draft': [('readonly', False)]})
	request_date = fields.Date(string="Request Date", required=True,readonly=True,states={'draft': [('readonly', False)]})
	confirm_date = fields.Date(string="Confirm Date")
	confirm_manager = fields.Many2one('res.users',string="Confirm Manager",readonly=True)
	note = fields.Text(string="Reason",readonly=True,states={'draft': [('readonly', False)]})         
	company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env['res.company']._company_default_get('bi.employee.salary'),readonly=True,states={'draft': [('readonly', False)]})
	account_no = fields.Char("Account Number")
	ifsc_code = fields.Char("Ifsc Code")
	department_id = fields.Char("Department")

	@api.onchange('employee_id')
	def onchange_employee_id(self):
		if self.employee_id:
			self.design_id=self.employee_id.job_id
			self.account_no=self.employee_id.bank_account_no
			self.ifsc_code=self.employee_id.ifs_code
			self.department_id=self.employee_id.department_id.name
			self.company_id=self.employee_id.company_id.id


	@api.model
	def create(self, vals):
		if vals.get('name', _('New')) == _('New'):
			if 'company_id' in vals:
				vals['name'] = self.env['ir.sequence'].with_context(force_company=vals['company_id']).next_by_code('bi.employee.salary') or _('New')
			else:
				vals['name'] = self.env['ir.sequence'].next_by_code('bi.employee.salary') or _('New')

		result = super(BiEmployeeSalary, self).create(vals)
		return result

	
	@api.multi
	def button_request(self):
		self.write({'state': 'request'})
		self.send_mail_template()

	@api.multi
	def send_mail_template(self):
		# Find the e-mail template
		template = self.env.ref('bi_employee_advance.advance_salary_request_mail')
		# You can also find the e-mail template like this:
		# template = self.env['ir.model.data'].get_object('mail_template_demo', 'example_email_template')
 
		# Send out the e-mail template to the user
		self.env['mail.template'].browse(template.id).send_mail(self.id)


	@api.multi
	def button_reject(self):
		self.write({'state': 'reject'})

	@api.multi
	def button_approve(self):
		self.write({
			'confirm_date':fields.Date.today(),
			'confirm_manager':self.env.user.id,
			'state': 'approve'})

	@api.multi
	def button_paid(self):		
		self.write({'state': 'paid'})

	@api.onchange('employee_id')
	def _onchange_employee_id(self):
		if self.employee_id:
			self.dept_id  = self.employee_id.department_id


class HrPayslip(models.Model):
	_inherit = "hr.payslip"
	@api.multi
	def compute_sheet(self):
		for payslip in self:
			advance_amount= 0.0
			advance = self.env['bi.employee.salary'].search([('employee_id','=',payslip.employee_id.id),('confirm_date','>=',payslip.date_from),('confirm_date','<=',payslip.date_to),('state','=','paid')])
			for res in advance:
				payslip_input= self.env['hr.payslip.input'].search([('payslip_id','=',payslip.id),('code','=','ADV')])
				if payslip_input:
					advance_amount+=res.amount
				payslip_input.write({
					'amount':advance_amount
					})
			# if advance and not payslip_input:
			# 	self.env['hr.payslip.input'].create({
			# 		'name':'Salary Advance',
			# 		'code':'ADV',
			# 		'amount':advance.amount,
			# 		'contract_id':payslip.contract_id.id,
			# 		'payslip_id':payslip.id
			# 		})  
		result = super(HrPayslip, self).compute_sheet()           
		return True
	# @api.multi
	# def unlink(self):
	# 	for order in self:
	# 		if order.state not in ('draft'):
	# 			raise UserError(_('You can not delete Passport bookings'))
	# 	return super(BiPassportBooking, self).unlink()
