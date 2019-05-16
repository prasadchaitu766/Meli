from openerp import models, fields, api
from openerp.exceptions import except_orm, Warning, RedirectWarning
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError, ValidationError
import time
from odoo.tools.translate import _

class hr_loan(models.Model):
	_name = 'hr.loan'
	_inherit = ['mail.thread','ir.needaction_mixin']
	_description= "HR Loan Request"
	_order = "id desc"
	def _get_employee_id(self):
		# assigning the related employee of the logged in user
		employee_rec = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
		return employee_rec.id
	
	
	# @api.one		
	# def _compute_amount(self):
	# 	total_paid_amount = 0.00
	# 	for loan in self:
	# 		for line in loan.loan_line_ids:
	# 			if line.paid == True:
	# 				if line.advance_amount:
	# 					total_paid_amount +=line.paid_amount + line.advance_amount
	# 				else:
	# 					total_paid_amount +=line.paid_amount
	# 		balance_amount =loan.loan_amount - total_paid_amount
	# 		self.total_amount = loan.loan_amount
	# 		self.balance_amount = balance_amount
	# 		self.total_paid_amount = total_paid_amount

	
	@api.one		
	def _compute_amount(self):
		total_paid_amount = 0.00
		for loan in self:
			for line in loan.loan_line_ids:
				if line.paid == True:
					if line.advance_amount:
						total_paid_amount +=line.paid_amount + line.advance_amount
					else:
						total_paid_amount +=line.paid_amount
			
			balance_amount =loan.loan_amount - total_paid_amount
			self.total_amount = loan.loan_amount
			self.balance_amount = balance_amount
			self.total_paid_amount = total_paid_amount
			self.extra_balance_amount = balance_amount
			
			
			
	@api.one
	def _get_old_loan(self):
		old_amount = 0.00
		for loan in self.search([('employee_id','=',self.employee_id.id), ('state','=','approve')]):
			if loan.id != self.id:
				old_amount += loan.balance_amount
		self.loan_old_amount = old_amount

	
	def _get_default_treasury_id(self):
		if self._context.get('treasury_account_id') or self._context.get('_get_default_treasury_id'):
			return self._context.get('treasury_account_id') or self._context.get('_get_default_treasury_id')

	name = fields.Char(string="Loan Name", default="/", readonly=True)
	date = fields.Date(string="Date Request", default=fields.Date.today(), readonly=True)
	employee_id = fields.Many2one('hr.employee', string="Employee", required=True,default=_get_employee_id)
	parent_id = fields.Many2one('hr.employee', related= "employee_id.parent_id", string="Manager")
	department_id = fields.Many2one('hr.department', related="employee_id.department_id", readonly=True, string="Department")
	job_id = fields.Many2one('hr.job', related="employee_id.job_id", readonly=True, string="Job Position")
	emp_salary = fields.Float(string="Employee Salary",related="employee_id.contract_id.wage", readonly=True)
	loan_old_amount = fields.Float(string="Old Loan Amount Not Paid", compute='_get_old_loan')
	emp_account_id = fields.Many2one('account.account', string="Employee Account", readonly=True,default=lambda self: self.env['account.account'].search([('internal_type', '=', 'payable'), ('deprecated', '=', False)], limit=1))
	treasury_account_id = fields.Many2one('account.account', string="Treasury Account",default=lambda self: self.env['account.account'].search([('internal_type', '=', 'receivable'), ('deprecated', '=', False)], limit=1))
	journal_id = fields.Many2one('account.journal', string="Journal",default=lambda self: self.env['account.journal'].search([], limit=1))
	loan_amount = fields.Float(string="Loan Amount", required=True)
	total_amount = fields.Float(string="Total Amount", readonly=True, compute='_compute_amount')
	balance_amount = fields.Float(string="Balance Amount", compute='_compute_amount')
	extra_balance_amount = fields.Float(string="Balance Amount", compute='_compute_amount', store=True)
	total_paid_amount = fields.Float(string="Total Paid Amount", compute='_compute_amount')
	no_month = fields.Integer(string="No Of Month", default=1)
	payment_start_date = fields.Date(string="Start Date of Payment", required=True, default=fields.Date.today())
	loan_line_ids = fields.One2many('hr.loan.line', 'loan_id', string="Loan Line", index=True)
	entry_count = fields.Integer(string="Entry Count", compute = 'compute_entery_count')
	move_id = fields.Many2one('account.move', string="Entry Journal", readonly=True)
	code = fields.Char("Code", related="employee_id.code", readonly=True)
	state = fields.Selection([
		('draft','Draft'),
		('approve','Approved'),
		('refuse','Refused'),
	], string="State", default='draft', track_visibility='onchange', copy=False,)
	account_no = fields.Char("Account Number", related="employee_id.bank_account_id.acc_number", readonly=True)
	
			
	
	
	@api.model
	def create(self, values):
		values['name'] = self.env['ir.sequence'].get('hr.loan.req') or ' '
		res = super(hr_loan, self).create(values)
		res.send_mail_template()
		return res
	
	
	@api.multi
	def send_mail_template(self):
		# Find the e-mail template
		template = self.env.ref('hr_loan.loan_request_mail')
		# You can also find the e-mail template like this:
		# template = self.env['ir.model.data'].get_object('mail_template_demo', 'example_email_template')
 
		# Send out the e-mail template to the user
		self.env['mail.template'].browse(template.id).send_mail(self.id)
	


	@api.multi
	def action_refuse(self):
		return self.write({'state': 'refuse'})
		
		
	@api.multi
	def action_set_to_draft(self):
		return self.write({'state': 'draft'})
	
	@api.multi	
	def onchange_employee_id(self, employee_id=False):
		old_amount = 0.00
		if employee_id:
			for loan in self.search([('employee_id','=',employee_id), ('state','=','approve')]):
				if loan.id != self.id:
					old_amount += loan.balance_amount
			return {
				'value':{
					'loan_old_amount':old_amount}
			}	
			

	
	@api.multi
	def action_approve(self):
		self.write({'state': 'approve'})
		if not self.emp_account_id or not self.treasury_account_id or not self.journal_id:
			raise except_orm('Warning', "You must enter employee account & Treasury account and journal to approve ")
		if not self.loan_line_ids:
			raise except_orm('Warning', 'You must compute Loan Request before Approved')
		
		can_close = False
		loan_obj = self.env['hr.loan']
		move_obj = self.env['account.move']
		move_line_obj = self.env['account.move.line']
		currency_obj = self.env['res.currency']
		timenow = time.strftime('%Y-%m-%d')
		line_ids = []
		debit_sum = 0.0
		credit_sum = 0.0
		for loan in self:
			company_currency = loan.employee_id.company_id.currency_id.id
			current_currency = self.env.user.company_id.currency_id.id
			amount = loan.loan_amount
			loan_name = loan.employee_id.name
			reference = loan.name
			journal_id = loan.journal_id.id
			move = {
				'narration': loan_name,
				'ref': reference,
				'journal_id': journal_id,
				'date': timenow,
				'state': 'posted',
				'school_id':self.employee_id.school_id.id,
			}
			
			debit_account_id = loan.treasury_account_id.id
			credit_account_id = loan.emp_account_id.id
			if debit_account_id:
				debit_line = (0, 0, {
					'name': loan_name,
					'account_id': debit_account_id,
					'journal_id': journal_id,
					'date': timenow,
					'debit': amount > 0.0 and amount or 0.0,
					'credit': amount < 0.0 and -amount or 0.0,
				})
				line_ids.append(debit_line)
				debit_sum += debit_line[2]['debit'] - debit_line[2]['credit']
			if credit_account_id:
				credit_line = (0, 0, {
					'name': loan_name,
					'account_id': credit_account_id,
					'journal_id': journal_id,
					'date': timenow,
					'debit': amount < 0.0 and -amount or 0.0,
					'credit': amount > 0.0 and amount or 0.0,
				})
				line_ids.append(credit_line)
				credit_sum += credit_line[2]['credit'] - credit_line[2]['debit']
			move.update({'line_ids': line_ids})
			move_id = move_obj.create(move)
			return self.write({'move_id': move_id.id})
			
		return True
	
		
	
	@api.multi
	def compute_loan_line(self):
		loan_line = self.env['hr.loan.line']
		loan_line.search([('loan_id','=',self.id)]).unlink()
		for loan in self:
			date_start_str = datetime.strptime(loan.payment_start_date,'%Y-%m-%d')
			counter = 1
			amount_per_time = loan.loan_amount / loan.no_month
			for i in range(1, loan.no_month + 1):
				line_id = loan_line.create({
					'paid_date':date_start_str, 
					'paid_amount': amount_per_time,
					'employee_id': loan.employee_id.id,
					'loan_id':loan.id})
				counter += 1
				date_start_str = date_start_str + relativedelta(months = 1)
				
		return True
	

	@api.model
	@api.multi
	def compute_entery_count(self):
		count = 0
		entry_count = self.env['account.move.line'].sudo().search_count([('loan_id','=',self.id)])
		self.entry_count = entry_count
	
	@api.multi
	def button_reset_balance_total(self):
		total_paid_amount = 0.00
		for loan in self:
			for line in loan.loan_line_ids:
				if line.paid == True:
					total_paid_amount +=line.paid_amount
			balance_amount =loan.loan_amount - total_paid_amount
			self.write({'total_paid_amount':total_paid_amount,'balance_amount':balance_amount})

			
			
class hr_loan_line(models.Model):
	_name="hr.loan.line"
	_description = "HR Loan Request Line"
	
	
	paid_date = fields.Date(string="Payment Date", required=True)
	employee_id = fields.Many2one('hr.employee', string="Employee")
	paid_amount= fields.Float(string="Paid Amount", required=True)
	paid = fields.Boolean(string="Paid")
	advance_amount = fields.Float(string="Additional Amount")
	notes = fields.Text(string="Notes")
	loan_id =fields.Many2one('hr.loan', string="Loan Ref.", ondelete='cascade')
	payroll_id = fields.Many2one('hr.payslip', string="Payslip Ref.")
	
	
	@api.one
	def action_paid_amount(self):
		context = self._context
		can_close = False
		loan_obj = self.env['hr.loan']
		move_obj = self.env['account.move']
		move_line_obj = self.env['account.move.line']
		currency_obj = self.env['res.currency']
		created_move_ids = []
		loan_ids = []
		timenow = time.strftime('%Y-%m-%d')
		line_ids = []
		debit_sum = 0.0
		credit_sum = 0.0
		
		for line in self:
			# if line.loan_id.state != 'approve':
			# 	raise except_orm('Warning', "Loan Request must be approved")
			paid_date = line.paid_date
			company_currency = line.employee_id.company_id.currency_id.id
			current_currency = self.env.user.company_id.currency_id.id
			amount = line.paid_amount
			loan_name = line.employee_id.name
			reference = line.loan_id.name
			journal_id = line.loan_id.journal_id.id
			move = {
				'narration': loan_name,
				'ref': reference,
				'journal_id': journal_id,
				'date': timenow,
				'state': 'posted',
			}
			
			debit_account_id = line.loan_id.treasury_account_id.id
			credit_account_id = line.loan_id.emp_account_id.id
			
			
			if debit_account_id:
				debit_line = (0, 0, {
					'name': loan_name,
					'account_id': debit_account_id,
					'journal_id': journal_id,
					'date': timenow,
					'debit': amount > 0.0 and amount or 0.0,
					'credit': amount < 0.0 and -amount or 0.0,
					'loan_id':line.loan_id.id,
				})
				line_ids.append(debit_line)
				debit_sum += debit_line[2]['debit'] - debit_line[2]['credit']

			
			
			if credit_account_id:
				credit_line = (0, 0, {
					'name': loan_name,
					'account_id': credit_account_id,
					'journal_id': journal_id,
					'date': timenow,
					'debit': amount < 0.0 and -amount or 0.0,
					'credit': amount > 0.0 and amount or 0.0,
					'loan_id':line.loan_id.id,
				})
				line_ids.append(credit_line)
				credit_sum += credit_line[2]['credit'] - credit_line[2]['debit']
			
			move.update({'line_ids': line_ids})
			move_id = move_obj.create(move)
			return self.write({'paid': True})
		return True
		
	
	
	
class hr_employee(models.Model):
	_inherit = "hr.employee"
	
	@api.model
	@api.multi
	def _compute_loans(self):
		count = 0
		loan_remain_amount = 0.00
		loan_ids = self.env['hr.loan'].search([('employee_id','=',self.id)])
		for loan in loan_ids:
			loan_remain_amount +=loan.balance_amount
			count +=1
		self.loan_count = count
		self.loan_amount = loan_remain_amount
	
	
	loan_amount= fields.Float(string="loan Amount", compute ='_compute_loans')
	loan_count = fields.Integer(string="Loan Count", compute = '_compute_loans')
	
	
class account_move_line(models.Model):
	_inherit = "account.move.line"
	
	loan_id = fields.Many2one('hr.loan', string="Loan")