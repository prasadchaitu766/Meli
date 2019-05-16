# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


import time
from datetime import datetime, timedelta
from dateutil import relativedelta
import babel
from email.utils import formataddr
from odoo.osv import expression
from odoo.exceptions import UserError, ValidationError
from odoo import api, fields, models, tools, SUPERUSER_ID
from odoo.tools.translate import _
from odoo.tools import float_compare, float_is_zero

class HrContract(models.Model):
	
	_inherit = 'hr.contract'
	_rec_name = 'employee_id'

	@api.depends('wage','dearness_allowance','house_rent_allowance','special_allowance')
	def _compute_salary(self):
		offered_salary = 0.0
		for line in self:
			line.update({

				'offered_salary':(line.wage + line.dearness_allowance + line.house_rent_allowance + line.special_allowance)
			})
	
	dearness_allowance = fields.Float(string='Dearness Allowance')
	house_rent_allowance = fields.Float(string='House Rent Allowance')
	special_allowance = fields.Float(string='Special allowance')
	code = fields.Char("Code")
	name = fields.Char('Contract Reference', required=False)	
	hr_rules_ids = fields.Many2many('hr.salary.rule', 'bi_contract_rule_rel', 'contract_id', 'rule_id', string='Selected Rule', domain=[('consider','=', True)])
	company_id = fields.Many2one('res.company', related='employee_id.company_id',string='Company', store=True)
	offered_salary = fields.Monetary(compute='_compute_salary', string="Offered Salary", readonly=True, store=True)
	currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.user.company_id.currency_id)
	employee_grat_ids = fields.One2many('gratuity.employee', 'gratuity_id', "Grautity")
	date_of_join= fields.Date("Date of Joining", related='employee_id.date_of_join')
	# security_dp_amount = fields.Float("Security Deposit")
	
	@api.onchange('employee_id')
	def change_employee_id(self):
			self.code = self.employee_id.code

	@api.onchange('employee_id')
	def change_join_id(self):
		for line in self.employee_grat_ids:
			# raise UserError(_(str(line)))
			line.date_of_join = self.employee_id.date_of_join


class Gratuity(models.Model):
	_name = "gratuity.employee"

	gratuity_id = fields.Many2one('hr.contract', "Gratuity")
	date_of_join = fields.Date("Date of Joining", default=lambda self: fields.Datetime.now(),readonly=True)
	total_month = fields.Char("Total Working", compute="_compute_total_months")
	gratuity_amount = fields.Float("Gratuity Amount")
	# dearness_allowance = fields.Float(string='Dearness Allowance', related='gratuity_id.dearness_allowance')
	# wage = fields.Float('Wage', related='gratuity_id.wage')
	amount = fields.Monetary(string="Amount", readonly=True, compute="_compute_gratuity", track_visibility='always',store=True)
	currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.user.company_id.currency_id)

	@api.depends('date_of_join')
	def _compute_total_months(self):
		for res in self:
			month = year = 0
			if res.date_of_join:
				date1 = datetime.strptime(str(res.date_of_join), '%Y-%m-%d')
				date2 = datetime.strptime(str(fields.Date.context_today(self)), '%Y-%m-%d')
				r = relativedelta.relativedelta(date2, date1)
				year = r.years
				month = r.months
				res.update({
						   'total_month': str(year)+' Years '+str(month)+' Months' 
						   })
	
	@api.depends('gratuity_id.wage','gratuity_id.dearness_allowance','date_of_join')
	def _compute_gratuity(self):
		for res in self:
			month = year = amount=0.0
			if res.date_of_join:
				date1 = datetime.strptime(str(res.date_of_join), '%Y-%m-%d')
				date2 = datetime.strptime(str(fields.Date.context_today(self)), '%Y-%m-%d')
				r = relativedelta.relativedelta(date2, date1)
				year = r.years
				month = r.months
				if month <10:
					year_data = year+float(month)/10
					# c= open("/home/administrator/error.txt", "a")
					# c.write("inside first:"+str(year_data))
					# c.close()			
				else:
					year_data = year+float(month)/100
					# c= open("/home/administrator/error.txt", "a")
					# c.write("inside 2:"+str(year_data))
					# c.close()	
				
				total = (res.gratuity_id.wage+res.gratuity_id.dearness_allowance)*year_data
				amount = (total*15)/26
				# raise UserError((str(amount)))
			res.update({
				'gratuity_amount':amount,

				})




class HrSalaryRule(models.Model):

	_inherit = "hr.salary.rule"

	consider = fields.Boolean(string="To Be Consider")	

	@api.model
	def create(self, vals):
		result = super(HrSalaryRule, self).create(vals)
		result.get_sequence()
		return result	

	@api.multi
	def get_sequence(self):
		sequence_line = []
		line = self.env['hr.salary.rule'].search([])
		for seq in line:
			sequence_line.append(seq.sequence)
		max_seq = max(sequence_line)
		self.sequence = str(max_seq + 1)

class Employee(models.Model):

	_inherit = "hr.employee"
	
	@api.multi
	def _compute_salary(self):
		for res in self:
			employee_id = res.id
			contract_obj=self.env["hr.contract"]
			contract_id = contract_obj.search([('employee_id','=',employee_id)],order="id desc",limit=1)
			res.offered_salary=contract_id.offered_salary

	@api.one
	@api.depends('state')
	def _active_emp(self):
		if self.state in ('draft','blacklist'):
			self.active = True
		else:
			self.active = False
	  
	category_ids = fields.Many2many('hr.employee.category', 'employee_category_rel', 'emp_id', 'category_id', string='Category')
	
	code = fields.Char(string="Code", required=True, readonly=True, default=lambda self: _('New'))
	religion = fields.Selection([
		('hindu', 'Hindu'),
		('muslim', 'Muslim'),
		('christian', 'Christian')
	], "Religion")
	state = fields.Selection([
		('draft','Employee'),
		('resign','Resignation'),
		('terminate','Terminated'),
		('blacklist','Blacklist'),
		('layoff','Layoff'),
		],string='Status', default='draft', readonly=True)	
	date_of_join= fields.Date("Date of Joining")
	idcard_no = fields.Char("ID Card No")
	licensecard_no = fields.Char("License Card No")
	home_address = fields.Text("Home Address")
	address_home_id = fields.Many2one('res.partner', string='Related Partner')

	phone_no = fields.Char("Phone No")
	qualification = fields.Char("Qualification")
	other_state = fields.Boolean(string="Other State", default=False)
	resign_date = fields.Date("Resign Date")
	approve_id = fields.Many2many('res.users', 'leave_approveuser_rel', 'user_id', 'approval_id')
	currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.user.company_id.currency_id)
	offered_salary = fields.Monetary(string='Offered Salary',compute='_compute_salary')
	vaccation_date = fields.Date(string='Next Vaccation Date')
	is_teacher = fields.Boolean('Is Teacher')
	school_id = fields.Many2one('school.school', "Campus", store=True)
	warning_ids = fields.One2many('employee.warning.line','warning_id')
	is_examiner = fields.Boolean('Is Examiner')
	employee_status = fields.Selection([
		('full','Full Time'),
		('part','Part Time'),
		('casual','Casual'),
		],string='Employee Status', default='full')
	line_manager_id = fields.Many2one('hr.employee',string="Line Manager")
	guarantor_name = fields.Char(string='Guarantor Name')
	address = fields.Char(string="Address")
	email = fields.Char(string='Email')
	phone_no = fields.Char(string="Phone No")
	lang_ids = fields.Many2many('bi.languages.known','employee_lang_rel', 'lang_id', string="Languages")

	qualification_id = fields.Many2one('bi.qualification', string="Qualification")
	year_of_pass = fields.Char(string="Year of Passing")
	subject = fields.Char(string="Specialisation/Subject")	
	university = fields.Char(string="School/College/University Degree")
	note = fields.Text()

	work_exp = fields.Char(string="Work Experience")
	no_of_years = fields.Char(string="No of Years")
	organisation = fields.Char(string="Organisation")
	job_response = fields.Char(string="Job Responsibility")

	bank_id = fields.Char(string="Bank Name")
	branch_id = fields.Char(string="Branch")
	account_name = fields.Char(string="Account Name")
	bank_account_no = fields.Char(string="Bank Account No.")
	ifs_code = fields.Char(string="IFS Code")

	# active_emp = fields.Boolean(string="Active", compute='_active_emp')
	active = fields.Boolean('Active', compute='_active_emp')
	holiday_ids = fields.One2many('hr.holidays','employee_id', domain=[('state','=','validate'),('type','=','remove')])
	security_dp_amount = fields.Float("Security Deposit")

	@api.onchange('line_manager_id')
	def onchange_line_manager_id(self):
		self.parent_id = self.line_manager_id.id

	@api.onchange('school_id')
	def onchange_school_id(self):
		if self.school_id:
			self.address_id = self.school_id.partner_id.id
			self.work_location = self.school_id.state_id.name


	@api.model
	def name_search(self, name, args=None, operator='ilike', limit=100):
		args = args or []
		domain = []
		if name:
			domain = ['|', ('name', '=ilike', name + '%'), ('code', operator, name)]
			if operator in expression.NEGATIVE_TERM_OPERATORS:
				domain = ['&', '!'] + domain[1:]
		jobs = self.search(domain + args, limit=limit)
		return jobs.name_get()

	@api.multi
	@api.depends('name','code')
	def name_get(self):
		result = []

		for res in self:
			name = str(res.code) + ' - ' + str(res.name)
			result.append((res.id, name))
		
		return result

	@api.model
	def create(self, vals):
		if vals.get('code', _('New')) == _('New'):
			vals['code'] = self.env['ir.sequence'].next_by_code('hr.employee.code') or _('New')			
		employee_id = super(Employee, self).create(vals)	
		user_obj = self.env['res.users']
		user_vals = {'name': employee_id.name,
					 'login': employee_id.work_email,
					 'email': employee_id.work_email,
					 'user_type':'staff',
					 }
		# ctx_vals = {'teacher_create': True,
		# 			'school_id': employee_id.school_id.company_id.id}
		user_id = user_obj.sudo().create(user_vals)
		user_id.partner_id.write({'customer':False})
		# teacher_id.employee_id.write({'user_id': user_id.id})
		employee_id.user_id = user_id.id
		if employee_id.is_teacher == True:	
			# raise UserError(str(employee_id.resource_id.user_id))					
			var = {
					'name': employee_id.name,
					'school_id':employee_id.school_id.id,
					'employee_id':employee_id.id,
					# 'user_id':employee_id.user_id.id,
					'subject_id':False,
					'address_id':employee_id.address_id.id,
					'mobile_phone':employee_id.mobile_phone,
					'work_location':employee_id.work_location,
					'work_email':employee_id.work_email,
					'department_id':employee_id.department_id.id,
					'job_id':employee_id.job_id.id
					}
			self.env['school.teacher'].create(var)
			emp_grp = self.env.ref('base.group_user')
			admission_group = self.env.ref('school.group_school_teacher')
			new_grp_list = [admission_group.id, emp_grp.id]
			user_id.write({'groups_id': [(6, 0, new_grp_list)]})
		if employee_id.is_examiner == True:
			exam = {
					'name': employee_id.name,
					'school_id':employee_id.school_id.id,
					'employee_id':employee_id.id,
					# 'user_id':employee_id.user_id.id,
					'subject_id':False,
					'examiner':employee_id.is_examiner,
					'address_id':employee_id.address_id.id,
					'mobile_phone':employee_id.mobile_phone,
					'work_location':employee_id.work_location,
					'work_email':employee_id.work_email,
					'department_id':employee_id.department_id.id,
					'job_id':employee_id.job_id.id
					}
			self.env['school.teacher'].create(exam)
			emp_grp = self.env.ref('base.group_user')
			admission_group = self.env.ref('school.group_school_teacher')
			new_grp_list = [admission_group.id, emp_grp.id]
			user_id.write({'groups_id': [(6, 0, new_grp_list)]})
		return employee_id

	@api.multi
	def write(self, vals):
		employee_id =  super(Employee, self).write(vals)
		employee = self.env['school.teacher'].search([('employee_id','=',self.id)])
		if vals.get('is_teacher',False) == True and not employee:
			# raise UserError(str(self.company_id.id))					
			var = {
					'name': self.name,
					'school_id':self.school_id.id,
					'employee_id':self.id,
					# 'user_id':employee_id.user_id.id,
					'subject_id':False,
					'address_id':self.address_id.id,
					'mobile_phone':self.mobile_phone,
					'work_location':self.work_location,
					'work_email':self.work_email,
					'department_id':self.department_id.id,
					'job_id':self.job_id.id
					}
		#	raise UserError(str(var))

			self.env['school.teacher'].create(var)
		if vals.get('is_examiner',False) == True and not employee:
			# raise UserError(str(self.company_id.id))					
			var1 = {
					'name': self.name,
					'school_id':self.school_id.id,
					'employee_id':self.id,
					# 'user_id':employee_id.user_id.id,
					'subject_id':False,
					'examiner':True,
					'address_id':self.address_id.id,
					'mobile_phone':self.mobile_phone,
					'work_location':self.work_location,
					'work_email':self.work_email,
					'department_id':self.department_id.id,
					'job_id':self.job_id.id
					}
			# raise UserError(str(var1))

			self.env['school.teacher'].create(var1)
		# elif teacher_id == True:
		# 	raise UserError(str())
		# employee.unlink()
		return employee_id

class BiQualification(models.Model):
	_name = 'bi.qualification'
	_description = 'Qualification'
	_rec_name = "qualification"

	qualification = fields.Char(string="Qualification")

class BiLanguagesKnown(models.Model):
	_name = 'bi.languages.known'
	_description = 'Languages'
	_rec_name = "lang_id"

	lang_id = fields.Char(string="Languages")


class EmployeeWarningLine(models.Model):
	_name = 'employee.warning.line'
	_description = 'Warning'

	warning_id = fields.Many2one('hr.employee')
	sequence_ref = fields.Integer('No.', compute="_sequence_ref")
	note = fields.Char('Warning Message')

	@api.depends('warning_id.warning_ids', 'warning_id.warning_ids.note')
	def _sequence_ref(self):
		for line in self:
			no = 0
			for l in line.warning_id.warning_ids:
				no += 1
				l.sequence_ref = no

class HrPayslip(models.Model):
	_inherit = 'hr.payslip'
	_description = 'Pay Slip'

	@api.multi
	def compute_sheet(self):
		payslip = super(HrPayslip, self).compute_sheet()
		for payslip in self:			
			salary_stucture_rule =[]
			for rule in payslip.struct_id.rule_ids:
				if rule.consider == True:
					salary_stucture_rule.append(rule.id)
			salary_contract_rule = []
			for rule in payslip.contract_id.hr_rules_ids:
				salary_contract_rule.append(rule.id)
			total_rule = list(set(salary_stucture_rule) - set(salary_contract_rule))
			if total_rule:
				payslip_line = self.env['hr.payslip.line'].search([('slip_id','=',payslip.id),('salary_rule_id','in',total_rule)])
				if payslip_line:
					payslip_line.write({'amount':0.0})	
			payslip_line = self.env['hr.payslip.line'].search([('slip_id','=',payslip.id),('code','=','LE')])
			td_100 = self.env['hr.payslip.worked_days'].search([('payslip_id','=',payslip.id),('code','=','TD100')])
			work_100 = self.env['hr.payslip.worked_days'].search([('payslip_id','=',payslip.id),('code','=','WORK100')])
			if payslip_line and td_100 and work_100:				
				if td_100.number_of_days!=work_100.number_of_days: 							
					payslip_line.write({'amount':0.0})

			ttyme = datetime.fromtimestamp(time.mktime(time.strptime(payslip.date_to, "%Y-%m-%d")))	
			locale = self.env.context.get('lang') or 'en_US'		
			payslip.write({'name':_('Salary Slip of %s for %s') % (payslip.employee_id.name, tools.ustr(babel.dates.format_date(date=ttyme, format='MMMM-y', locale=locale))),})		
		for payslip in self:
			payslip_line = self.env['hr.payslip.line'].search([('slip_id','=',payslip.id),('category_id.name','=','Deduction')])
			ded = sum(p.amount for p in payslip_line)
			payslip_line = self.env['hr.payslip.line'].search([('slip_id','=',payslip.id),('code','=','TED')])
			if payslip_line and ded:
				payslip_line.write({'amount':ded})
			payslip_input= self.env['hr.payslip.input'].search([('payslip_id','=',payslip.id),('code','=','TD1')])
			td_amount = 0.0	
			if payslip.contract_id.wage >= 0 and payslip.contract_id.wage <= 5000:
				payslip_input.write({'amount':td_amount})
			payslip_input= self.env['hr.payslip.input'].search([('payslip_id','=',payslip.id),('code','=','TD2')])
			td_amount1 = 0.0
			if payslip.contract_id.wage > 5000 and payslip.contract_id.wage <= 12500:
				amount1 = (payslip.contract_id.wage-5000)*0.02
				# per_amount1 = amount1/100
				td_amount1 += amount1
				payslip_input.write({'amount':td_amount1})
			payslip_input= self.env['hr.payslip.input'].search([('payslip_id','=',payslip.id),('code','=','TD3')])
			td_amount2 = 0.0
			if payslip.contract_id.wage > 12500 and payslip.contract_id.wage <= 100000:
				amount2 = (((payslip.contract_id.wage-12500)*0.10)+150)
				# per_amount2 = amount2/100
				td_amount2 += amount2
				payslip_input.write({'amount':td_amount2})
			payslip_input= self.env['hr.payslip.input'].search([('payslip_id','=',payslip.id),('code','=','TD4')])
			td_amount3 = 0.0
			if payslip.contract_id.wage > 100000:
				amount3 = (((payslip.contract_id.wage-100000)*0.20)+8900)
				# per_amount3 = amount3/100
				td_amount3 += amount3
				payslip_input.write({'amount':td_amount3})
			payslip_input= self.env['hr.payslip.input'].search([('payslip_id','=',payslip.id),('code','=','SDT')])
			if payslip_input and payslip.contract_id.state == 'open':
				security_amount = 0.0
				for line in payslip.line_ids:
					if line.category_id.name == 'Net':
						amount = line.amount*5
						prcnt_amount = amount/100
						security_amount += prcnt_amount
						# payslip.contract_id.security_dp_amount += security_amount
						if payslip.employee_id.security_dp_amount < line.amount:
							payslip_input.write({
												'amount':security_amount,
												})

		return True

	@api.model
	def get_worked_day_lines(self, contract_ids, date_from, date_to):
		"""
		@param contract_ids: list of contract id
		@return: returns a list of dict containing the input that should be applied for the given contract between date_from and date_to
		"""

		def was_on_leave_interval(employee_id, date_from, date_to):
			date_from = fields.Datetime.to_string(date_from.date())
			date_to = fields.Datetime.to_string(date_to.date())
			sql = """SELECT id from hr_holidays where state = 'validate' and 
			type = 'remove' and	employee_id ="""+str(employee_id) + """ and date_to::DATE >= '"""+str(date_to)+"""' and		
			date_from::DATE <= '""" + str(date_from) +"""' limit 1"""
			result= self.env.cr.execute(sql)	
			res=self.env.cr.fetchone()
			if res:
				return self.env['hr.holidays'].search([('id', '=', res[0])])
			else:
				return self.env['hr.holidays'].search([('id', '=', False)])
			return self.env['hr.holidays'].search([
				('state', '=', 'validate'),
				('employee_id', '=', employee_id),
				('type', '=', 'remove'),
				('date_from', '<=', date_from),
				('date_to', '>=', date_to)
			], limit=1)
		# Total working days for employee wise(decrease Holidays)
		def was_on_holiday_interval(date_from, date_to):
			date_from = fields.Datetime.to_string(date_from)
			date_to = fields.Datetime.to_string(date_to)
			return self.env['hr.holidays.public.line'].search([ 
				('date', '<=', date_from),
				('date', '>=', date_to)
			], limit=1)
		
		# Total working days for employee wise(decrease Holidays)
		def was_on_attendance_interval(employee_id,date_from, date_to):
			date_from = fields.Datetime.to_string(date_from)
			date_to = fields.Datetime.to_string(date_to)
			return self.env['hr.attendance'].search([ 
				('employee_id', '=', employee_id),
				('check_in', '<=', date_from),
				('check_out', '>=', date_to)
			], limit=1)
		# Total working days for employee wise(decrease leaves)	

		def total_days_interval(employee_id,date_from, date_to, weeklyoffdates):
			# date_from = fields.Datetime.to_string(date_from)
			# date_to = fields.Datetime.to_string(date_to)
			present_count = 0.0
			half_present_count = 0.0
			weekly_present = 0.0
			present_count = self.env['hr.attendance'].search_count([ 
				('employee_id', '=', employee_id),
				('att_status', '=', 'Present'),
				('att_date', '>=', date_from),
				('att_date', '<=', date_to),
				('att_date','not in', weeklyoffdates)
			])
			
			half_present_count = self.env['hr.attendance'].search_count([ 
				('employee_id', '=', employee_id),
				('att_status', '=', '1/2Present'),
				('att_date', '>=', date_from),
				('att_date', '<=', date_to),
				('att_date','not in', weeklyoffdates)
			])	
			weekly_off_present = self.env['hr.attendance'].search_count([ 
				('employee_id', '=', employee_id),				
				('att_date', '>=', date_from),
				('att_date', '<=', date_to),
				('att_date','in', weeklyoffdates)
			])						
			weekly_off_half_present = self.env['hr.attendance'].search_count([ 
				('employee_id', '=', employee_id),	
				('att_status', 'ilike', '1/2'),			
				('att_date', '>=', date_from),
				('att_date', '<=', date_to),
				('att_date','in', weeklyoffdates)
			])
			absent = self.env['hr.attendance'].search_count([ 
				('employee_id', '=', employee_id),
				('att_status', '=', 'Absent'),
				('att_punch', '=', ''),
				('att_date', '>=', date_from),
				('att_date', '<=', date_to),
				('att_date','not in', weeklyoffdates)
			])
			absentpunch = self.env['hr.attendance'].search_count([ 
				('employee_id', '=', employee_id),
				('att_status', '=', 'Absent'),
				('att_punch', '!=', ''),
				('att_date', '>=', date_from),
				('att_date', '<=', date_to),
				('att_date','not in', weeklyoffdates)
			])
			if weekly_off_present:		
				weekly_off_present = weekly_off_present - weekly_off_half_present	
			total_count = present_count + half_present_count
			
			return total_count,present_count,half_present_count,weekly_off_present,weekly_off_half_present,absent,absentpunch
		# designation = self.env['hr.job'].browse(self.env['ir.values'].get_default('hr.payroll.config.settings', 'designation_id'))		
		res = []
		#fill only if the contract as a working schedule linked
		uom_day = self.env.ref('product.product_uom_day', raise_if_not_found=False)
		for contract in self.env['hr.contract'].browse(contract_ids).filtered(lambda contract: contract.working_hours):
			uom_hour = contract.employee_id.resource_id.calendar_id.uom_id or self.env.ref('product.product_uom_hour', raise_if_not_found=False)
			interval_data = []
			holidays = self.env['hr.holidays']
			attendances = {
				 'name': _("Normal Working Days paid at 100%"),
				 'sequence': 1,
				 'code': 'WORK100',
				 'number_of_days': 0.0,
				 'number_of_hours': 0.0,
				 'contract_id': contract.id,
			}
			# Public Holiday List-Bassam changes
			publicholiday = {
				 'name': _("Public Holiday paid at 100%"),
				 'sequence': 2,
				 'code': 'PUB100',
				 'number_of_days': 0.0,
				 'number_of_hours': 0.0,
				 'contract_id': contract.id,
			}

			
			leaves = {}
			
			totalleaves = {
				 'name': _("Total Leaves"),
				 'sequence': 9,
				 'code': 'LEAVES100',
				 'number_of_days': 0.0,
				 'number_of_hours': 0.0,
				 'contract_id': contract.id,
			}
			

			day_from = fields.Datetime.from_string(date_from)
			day_to = fields.Datetime.from_string(date_to)
			nb_of_days_month = (day_to - day_from).days + 1
			if contract.employee_id.date_of_join:
				if date_from < contract.employee_id.date_of_join:
					day_from = fields.Datetime.from_string(contract.employee_id.date_of_join)
					date_from = fields.Datetime.from_string(contract.employee_id.date_of_join)
			if contract.employee_id.resign_date:
				if date_to > contract.employee_id.resign_date:
					day_to = fields.Datetime.from_string(contract.employee_id.resign_date)
					date_to = fields.Datetime.from_string(contract.employee_id.resign_date)
			nb_of_days = (day_to - day_from).days + 1

			holiday_data = []
			total_sundays = 0
			weeklyoffdates = []
			attendance_data = []
			total_days = []
			# Gather all intervals and holidays
			for day in range(0, nb_of_days):
				working_intervals_on_day = contract.working_hours.get_working_intervals_of_day(start_dt=day_from + timedelta(days=day))             
				for interval in working_intervals_on_day:
					
					interval_data.append((interval, was_on_leave_interval(contract.employee_id.id, interval[0], interval[1])))
					holiday_data.append((interval, was_on_holiday_interval(interval[0], interval[1])))
					attendance_data.append((interval, was_on_attendance_interval(contract.employee_id.id, interval[0], interval[1])))
					
				# For adding sundays in total working days - Bassam01
				if not working_intervals_on_day:
					total_sundays += 1  
					weeklyoffdates.append(day_from + timedelta(days=day))   
			# Weekly Off List-Bassam changes
			weeklyoff = {
				 'name': _("Weekly Off"),
				 'sequence': 4,
				 'code': 'WOFF100',
				 'number_of_days': 0.0,
				 'number_of_hours': 0.0,
				 'contract_id': contract.id,
			}
			# Extract information from previous data. A working interval is considered:
			# - as a leave if a hr.holiday completely covers the period
			# - as a working period instead
			overtime_hours = 0.0
			holiday_id = False
			hours = 1
			for interval, holiday in interval_data:
				holidays |= holiday
				hours = (interval[1] - interval[0]).total_seconds() / 3600.0
				if holiday:
					attendances['number_of_hours'] += hours #Only emergency Bassam remove next time correct leavr
					if holiday_id != holiday.id:
						if abs(holiday.number_of_days) -int(abs(holiday.number_of_days)) > 0.0:
							hours =hours/2
							#attendances['number_of_hours'] += get_worked_day_lines
						holiday_id = holiday.id
					#if he was on leave, fill the leaves dict
					totalleaves['number_of_hours']+= hours
					if holiday.holiday_status_id.name in leaves:
						leaves[holiday.holiday_status_id.name]['number_of_hours'] += hours
					else:
						leaves[holiday.holiday_status_id.name] = {
							'name': holiday.holiday_status_id.name,
							'sequence': 5,
							'code': holiday.holiday_status_id.name,
							'number_of_days': 0.0,
							'number_of_hours': hours,
							'contract_id': contract.id,
						}
				else:
					attendances['number_of_hours'] += hours
					

			
			for interval1, public_holiday in holiday_data:              
				#add the input vals to tmp (increment if existing)
				hours = (interval1[1] - interval1[0]).total_seconds() / 3600.0
				if public_holiday:  
				   weeklyoffdates.append(public_holiday.date)              
				   # public holiday list
				   publicholiday['number_of_hours']+= hours
				   publicholiday['name'] += ' ' + public_holiday.name + '/' + str(public_holiday.date) + ', '
			
			for interval2,over_time in attendance_data:				
				#add the input vals to tmp (increment if existing)
				if over_time.check_out and over_time.check_in:
					att_hour = (fields.Datetime.from_string(over_time.check_out) - fields.Datetime.from_string(over_time.check_in)).total_seconds() / 3600.0
				
					if att_hour:
						# if contract.employee_id.job_id.id == designation.id:
						if att_hour > uom_hour.factor:
							overtime_hours += (att_hour-uom_hour.factor)
			
					
					


			overtime = {
				 'name': _("Overtime"),
				 'sequence': 6,
				 'code': 'OT100',
				 'number_of_days': 0.0,
				 'number_of_hours': overtime_hours,
				 'contract_id': contract.id,
			}

			totaldays = {
				 'name': _("Total Days / Month"),
				 'sequence': 7,
				 'code': 'TD100',
				 'number_of_days': nb_of_days_month,
				 'number_of_hours':nb_of_days_month*uom_hour.factor,
				 'contract_id': contract.id,
			}
			
			# Public Holiday List-Bassam changes
			total_present,present_count,half_present_count,weekly_off_present,weekly_off_half_present,absent,absentpunch = total_days_interval(contract.employee_id.id,date_from, date_to, weeklyoffdates)
			total_present = total_present*uom_hour.factor
			weeklypresent = {
				 'name': _("Weekly off/Public holiday Present-"+str(weekly_off_present) +"  Half Present :"+str(weekly_off_half_present)),
				 'sequence': 8,
				 'code': 'WP100',
				 'number_of_days': 0.0,
				 'number_of_hours':(weekly_off_present*uom_hour.factor)+(float(weekly_off_half_present)/2)*uom_hour.factor ,
				 'contract_id': contract.id,
			}
			# Attendance From Machine changes
			attendance_from_machine = {
				 'name': _("From Machine- Full Present : "+str(present_count) +"  Half Present :"+str(half_present_count)),
				 'sequence': 3,
				 'code': 'ATD100',
				 'number_of_days': 0.0,
				 'number_of_hours': (present_count*uom_hour.factor)+(float(half_present_count)/2)*uom_hour.factor ,
				 'contract_id': contract.id,
			}
			absent_count = {
				 'name': _("From Machine- Absent"),
				 'sequence': 10,
				 'code': 'AC100',
				 'number_of_days': 0.0,
				 'number_of_hours':absent*uom_hour.factor ,
				 'contract_id': contract.id,
			}
			absent_punch = {
				 'name': _("From Machine- Absent with punching Problem"),
				 'sequence': 11,
				 'code': 'AP100',
				 'number_of_days': 0.0,
				 'number_of_hours':absentpunch*uom_hour.factor ,
				 'contract_id': contract.id,
			}
			totalmachineleaves = {
				 'name': _("Total Machine Leaves"),
				 'sequence': 12,
				 'code': 'ML100',
				 'number_of_days': 0.0,
				 'number_of_hours': (absent*uom_hour.factor)+(absentpunch*uom_hour.factor)+((float(half_present_count)/2)*uom_hour.factor),
				 'contract_id': contract.id,
			}
			# raise UserError(str(date_to))
			machine_total_leave =(absent*uom_hour.factor)+(absentpunch*uom_hour.factor)+((float(half_present_count)/2)*uom_hour.factor)
			if machine_total_leave:
				if machine_total_leave != float(hours/2):
					attendances['number_of_hours'] -= (machine_total_leave-hours)

			# For adding sundays in total working days - Bassam01
			if  total_sundays:				
				attendances['number_of_hours'] += (uom_hour.factor*total_sundays)
				weeklyoff['number_of_hours'] = (uom_hour.factor*total_sundays)
			if half_present_count > 0:
				half_present_count = float(half_present_count)/2 or 0.0
				half_present_count = half_present_count*uom_hour.factor
			
			# Clean-up the results=
			leaves = [value for key, value in leaves.items()]
			# leaves
			# if leaves:
			# 	attendances['number_of_hours'] += hours
			for data in [attendances] + leaves + [publicholiday]+[attendance_from_machine]+[weeklyoff]+[overtime]+[totaldays]+[weeklypresent]+[totalleaves]+[absent_count]+[absent_punch]+[totalmachineleaves]:
				data['number_of_days'] = uom_hour._compute_quantity(data['number_of_hours'], uom_day)\
					if uom_day and uom_hour\
					else data['number_of_hours'] / 10.5
				res.append(data)
		
		return res


	@api.depends('line_ids.total')
	def _amount_all(self):
		
		for order in self:
			amount_basic = amount_allowance = amount_deduction = amount_dallowance = 0.0
			for line in order.line_ids:
				if line.category_id.name == 'Basic':
					amount_basic += line.total
				elif line.category_id.name == 'Allowance':
					amount_allowance += line.total
				elif line.category_id.name == 'Deduction':
					amount_deduction += line.total
				elif line.category_id.name == 'DAllowance':
					amount_dallowance += line.total

			order.update({
				'amount_total': ((amount_basic + amount_allowance + amount_dallowance)- amount_deduction),
				})


	@api.depends('line_ids.total')
	def _compute_amount_da(self):
		
		for order in self:
			amount_allowance = amount_deduction = 0.0
			for line in order.line_ids:
				if line.category_id.name == 'Allowance':
					amount_allowance += line.total
				elif line.category_id.name == 'Deduction':
					amount_deduction += line.total
			
			order.update({
				'amount_allowance': amount_allowance,
				'amount_deduction': amount_deduction,
				})

	amount_allowance = fields.Monetary(string="Amount Allowance", readonly=True, store=True, compute="_compute_amount_da", track_visibility='always')
	amount_deduction = fields.Monetary(string="Amount Deduction", readonly=True, store=True, compute="_compute_amount_da", track_visibility='always')
	

	@api.depends('line_ids.total')
	def _earning_amount(self):
		for order in self:
			amount_gross=amount_allowance = 0.0
			for line in order.line_ids:
				if line.category_id.name == 'Gross':
					amount_gross += line.total
				elif line.salary_rule_id.appears_on_payslip == True:
					if line.category_id.name == 'Allowance':
						amount_allowance += line.total
			order.update({
				'total_earning' : amount_allowance + amount_gross,
				})

	@api.depends('line_ids.total')
	def _deduction_amount(self):
		for order in self:
			amount_deduction = 0.0
			for line in order.line_ids:
				if line.salary_rule_id.appears_on_payslip == True:
					if line.category_id.name == 'Deduction':
						amount_deduction += line.total
			order.update({
				'total_deduction' : amount_deduction,
				})



	amount_total = fields.Monetary(string='Net',store=True, readonly=True, compute='_amount_all', track_visibility='always')	
	currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.user.company_id.currency_id)	
	company_id = fields.Many2one('res.company', string='Company', readonly=True, copy=False,
		states={'draft': [('readonly', False)]})
	total_earning = fields.Monetary(string='Earning', readonly=True, compute='_earning_amount', track_visibility='always')
	total_deduction = fields.Monetary(string='Deduction', readonly=True, compute='_deduction_amount', track_visibility='always')
	school_id = fields.Many2one('school.school', 'Campus')

	@api.multi
	def action_payslip_done(self):
		precision = self.env['decimal.precision'].precision_get('Payroll')
		for slip in self:
			line_ids = []
			debit_sum = 0.0
			credit_sum = 0.0
			date = slip.date or slip.date_to

			name = _('Payslip of %s') % (slip.employee_id.name)
			move_dict = {
				'narration': name,
				'ref': slip.number,
				'journal_id': slip.journal_id.id,
				'date': date,
				'school_id':slip.payslip_run_id.school_id.id
			}
			for line in slip.details_by_salary_rule_category:
				amount = slip.credit_note and -line.total or line.total
				if float_is_zero(amount, precision_digits=precision):
					continue
				debit_account_id = line.salary_rule_id.account_debit.id
				credit_account_id = line.salary_rule_id.account_credit.id

				if debit_account_id:
					debit_line = (0, 0, {
						'name': line.name,
						'partner_id': line._get_partner_id(credit_account=False),
						'account_id': debit_account_id,
						'journal_id': slip.journal_id.id,
						'date': date,
						'debit': amount > 0.0 and amount or 0.0,
						'credit': amount < 0.0 and -amount or 0.0,
						'analytic_account_id': line.salary_rule_id.analytic_account_id.id,
						'tax_line_id': line.salary_rule_id.account_tax_id.id,
					})
					line_ids.append(debit_line)
					debit_sum += debit_line[2]['debit'] - debit_line[2]['credit']

				if credit_account_id:
					credit_line = (0, 0, {
						'name': line.name,
						'partner_id': line._get_partner_id(credit_account=True),
						'account_id': credit_account_id,
						'journal_id': slip.journal_id.id,
						'date': date,
						'debit': amount < 0.0 and -amount or 0.0,
						'credit': amount > 0.0 and amount or 0.0,
						'analytic_account_id': line.salary_rule_id.analytic_account_id.id,
						'tax_line_id': line.salary_rule_id.account_tax_id.id,
						
					})
					
					line_ids.append(credit_line)
					credit_sum += credit_line[2]['credit'] - credit_line[2]['debit']

			if float_compare(credit_sum, debit_sum, precision_digits=precision) == -1:
				acc_id = slip.journal_id.default_credit_account_id.id
				if not acc_id:
					raise UserError(_('The Expense Journal "%s" has not properly configured the Credit Account!') % (slip.journal_id.name))
				adjust_credit = (0, 0, {
					'name': _('Adjustment Entry'),
					'partner_id': False,
					'account_id': acc_id,
					'journal_id': slip.journal_id.id,
					'date': date,
					'debit': 0.0,
					'credit': debit_sum - credit_sum,
					
				})

				line_ids.append(adjust_credit)

			elif float_compare(debit_sum, credit_sum, precision_digits=precision) == -1:
				acc_id = slip.journal_id.default_debit_account_id.id
				if not acc_id:
					raise UserError(_('The Expense Journal "%s" has not properly configured the Debit Account!') % (slip.journal_id.name))
				adjust_debit = (0, 0, {
					'name': _('Adjustment Entry'),
					'partner_id': False,
					'account_id': acc_id,
					'journal_id': slip.journal_id.id,
					'date': date,
					'debit': credit_sum - debit_sum,
					'credit': 0.0,
					
				})
				line_ids.append(adjust_debit)
			move_dict['line_ids'] = line_ids
			move = self.env['account.move'].create(move_dict)
			slip.write({'move_id': move.id, 'date': date,'school_id':slip.payslip_run_id.school_id.id})
			move.post()
		return self.write({'state': 'done'})
class Holidays(models.Model):

	_inherit = "hr.holidays"
	def _default_start_time(self):
		import datetime as dt
		mytime = dt.datetime.strptime('0330','%H%M').time()
		mydatetime = dt.datetime.combine(dt.date.today(), mytime)       
		return mydatetime
	def _default_end_time(self):
		import datetime as dt
		mytime = dt.datetime.strptime('1400','%H%M').time()
		mydatetime = dt.datetime.combine(dt.date.today(), mytime)
		return mydatetime

	company_id = fields.Many2one('res.company',"Company")
	# create_date = fields.Many2one("Request Date")
	absent_employee = fields.Many2one('hr.employee', "Employee(In absence duty takes overby)")

	@api.onchange('employee_id')
	def onchange_company_id(self):
		self.company_id = self.employee_id.company_id

	date_from = fields.Datetime('Start Date', readonly=True, index=True, copy=False,
		states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]}, default=_default_start_time)
	date_to = fields.Datetime('End Date', readonly=True, copy=False,
		states={'draft': [('readonly', False)], 'confirm': [('readonly', False)]}, default=_default_end_time)


	@api.model
	def create(self, values):
		""" Override to avoid automatic logging of creation """
		employee_id = values.get('employee_id', False)
		if not self._check_state_access_right(values):
			raise AccessError(_('You cannot set a leave request as \'%s\'. Contact a human resource manager.') % values.get('state'))
		if not values.get('department_id'):
			values.update({'department_id': self.env['hr.employee'].browse(employee_id).department_id.id})
		holiday = super(Holidays, self.with_context(mail_create_nolog=True, mail_create_nosubscribe=True)).create(values)
		holiday.add_follower(employee_id)
		holiday.send_mail_template()
		return holiday
	@api.multi
	def send_mail_template(self):
		# Find the e-mail template
		template = self.env.ref('bi_hr.leave_request_mail')
		# You can also find the e-mail template like this:
		# template = self.env['ir.model.data'].get_object('mail_template_demo', 'example_email_template')
 
		# Send out the e-mail template to the user
		self.env['mail.template'].browse(template.id).send_mail(self.id)
	# @api.multi
	# def action_approve(self):
	# 	if "Annual" in self.holiday_status_id.name:
	# 		holiday_status_obj = self.env['hr.holidays.status'].search([('name','=',self.holiday_status_id.name)])
	# 		start_day = datetime.strptime(str(holiday_status_obj.start_date), '%Y-%m-%d %H:%M:%S')
	# 		end_day = datetime.strptime(str(holiday_status_obj.end_date), '%Y-%m-%d %H:%M:%S')      
	# 		today = datetime.today()
	# 		date_start = datetime(today.year, (today.month)-1, start_day.day).strftime('%Y-%m-%d')
	# 		date_end = datetime(today.year, today.month, end_day.day).strftime('%Y-%m-%d')
	# 		hr_attendance_obj = self.env['hr.attendance'].search_count([('att_date','>=',date_start),
	# 										('att_date','<=',date_end),('att_status','=',"Absent"),
	# 										('employee_id','=',self.employee_id.id)])
			
			

	# 		if hr_attendance_obj < self.holiday_status_id.leaves_per_month:
				
	# 			if not self.env.user.has_group('hr_holidays.group_hr_holidays_user'):
	# 				raise UserError(_('Only an HR Officer or Manager can approve leave requests.'))

	# 			manager = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
	# 			for holiday in self:
	# 				if holiday.state != 'confirm':
	# 					raise UserError(_('Leave request must be confirmed ("To Approve") in order to approve it.'))

	# 				if holiday.double_validation:
	# 					return holiday.write({'state': 'validate1', 'manager_id': manager.id if manager else False})
	# 				else:
	# 					holiday.action_validate()
	# 		else:
	# 			raise UserError("Already took an annual leave this month")

		
	# 	else:


	# 		if not self.env.user.has_group('hr_holidays.group_hr_holidays_user'):
	# 			raise UserError(_('Only an HR Officer or Manager can approve leave requests.'))

	# 		manager = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
	# 		for holiday in self:
	# 			if holiday.state != 'confirm':
	# 				raise UserError(_('Leave request must be confirmed ("To Approve") in order to approve it.'))

	# 			if holiday.double_validation:
	# 				return holiday.write({'state': 'validate1', 'manager_id': manager.id if manager else False})
	# 			else:
	# 				holiday.action_validate()



class HrPayslipRun(models.Model):
	_inherit = 'hr.payslip.run'
	_description = 'Payslip Batches'

	company_id = fields.Many2one('res.company',"Company")
	school_id = fields.Many2one('school.school', 'Campus')

	@api.onchange('school_id')
	def onchange_company_id(self):
		ttyme = datetime.fromtimestamp(time.mktime(time.strptime(self.date_end, "%Y-%m-%d")))	
		locale = self.env.context.get('lang') or 'en_US'
		if self.school_id:
			self.name = ('Salary on %s ') % (tools.ustr(babel.dates.format_date(date=ttyme, format='MMMM-y', locale=locale))) + str(self.school_id.name)

	@api.multi
	def create_advice(self):
		for run in self:
			if run.available_advice:
				raise UserError(_("Payment advice already exists for %s, 'Set to Draft' to create a new advice.") % (run.name,))
			company = self.env.user.company_id
			advice = self.env['hr.payroll.advice'].create({
						'batch_id': run.id,
						'company_id': company.id,
						'name': run.name,
						'date': run.date_end,
						'bank_id': company.partner_id.bank_ids and company.partner_id.bank_ids[0].id or False
					})
			for slip in run.slip_ids:
				# TODO is it necessary to interleave the calls ?
				slip.action_payslip_done()
				self.env['hr.payroll.advice.line'].create({
					'advice_id': advice.id,
					'name': slip.employee_id.bank_account_id and slip.employee_id.bank_account_id.acc_number or 'No Bank Account',
					'ifsc_code': slip.employee_id.bank_account_id and slip.employee_id.bank_account_id.bank_bic or 'NA',
					'employee_id': slip.employee_id.id,
					'bysal': slip.amount_total
				})
		self.write({'available_advice': True})

	@api.multi
	def action_compute(self):
		for res in self:
			for payslip in self.env['hr.payslip'].search([('payslip_run_id','=',res.id)]):
				payslip.compute_sheet()

	@api.multi
	def close_payslip_run(self):
		payslip_run = super(HrPayslipRun, self).close_payslip_run()
		for res in self:
			for payslip in self.env['hr.payslip'].search([('payslip_run_id','=',res.id)]):
				payslip_input= self.env['hr.payslip.input'].search([('payslip_id','=',payslip.id),('code','=','SDT')])
				if payslip_input and payslip.contract_id.state == 'open':
					security_amount = 0.0
					for line in payslip.line_ids:
						if line.category_id.name == 'Net':
							amount = line.amount*5
							prcnt_amount = amount/100
							security_amount += prcnt_amount
							payslip.employee_id.security_dp_amount += security_amount
		return payslip_run

	   
			
		
class HrPayrollAdvice(models.Model):
	
	_inherit = 'hr.payroll.advice'

	@api.multi
	def compute_advice(self):
		for advice in self:
			old_lines = self.env['hr.payroll.advice.line'].search([('advice_id', '=', advice.id)])
			if old_lines:
				old_lines.unlink()
			payslips = self.env['hr.payslip'].search([('date_from', '<=', advice.date), ('date_to', '>=', advice.date), ('state', '=', 'done')])
			for slip in payslips:
				self.env['hr.payroll.advice.line'].create({
					'advice_id': advice.id,
					'name': slip.employee_id.name,
					'ifsc_code': slip.employee_id.code or '',
					'employee_id': slip.employee_id.id,
					'bysal': slip.amount_total
				})
				slip.advice_id = advice.id

class Message(models.Model):
	
	_inherit = 'mail.message'

	@api.model
	def _get_default_from(self):
		return formataddr((self.env.user.name, self.env.user.name+'@gmail.com'))

class HrPayslipEmployees(models.TransientModel):
	_inherit = 'hr.payslip.employees'

	@api.multi
	def compute_sheet(self):
		payslip = super(HrPayslipEmployees, self).compute_sheet()
		active_id = self.env.context.get('active_id')
		for slip in self.env['hr.payslip'].search([('payslip_run_id', '=', active_id)]):
			slip.write({'company_id':slip.employee_id.company_id.id})
		return payslip

class ResPartnerBank(models.Model):
	_inherit = 'res.partner.bank'

	ifsc_code = fields.Char("IFSC Code")


class HRHolidaysStatus(models.Model):
	_inherit = 'hr.holidays.status'

	leaves_per_month = fields.Integer('Leaves per month')
	start_date = fields.Datetime("Start Date")
	end_date = fields.Datetime("End Date")


class Survey(models.Model):
	_inherit = 'survey.survey'

	employee_id = fields.Many2one('hr.employee', "Employee", required=True)
	date = fields.Datetime("Survey Date", required=True)

class SurveyUserInput(models.Model):
	_inherit = "survey.user_input"

	employee_id = fields.Many2one('hr.employee', string='Employee', related='survey_id.employee_id', readonly=True, store=True)
   
		
class Applicant(models.Model):
	_inherit = "hr.applicant"

	school_id = fields.Many2one('school.school', "Campus", store=True)
	employee_type = fields.Selection([('is_examiner','Is Examiner'), ('is_teacher','Is Teacher'),('other','Other')], 'Examiner/Teacher')
	@api.onchange('job_id')
	def onchange_job_id(self):
		if self.job_id:
			self.name = 'Application for the post of '+str(self.job_id.name)

	



	@api.multi
	def create_employee_from_applicant(self):
		""" Create an hr.employee from the hr.applicants """
		employee = False
		for applicant in self:
			address_id = contact_name = False
			if applicant.partner_id:
				address_id = applicant.partner_id.address_get(['contact'])['contact']
				contact_name = applicant.partner_id.name_get()[0][1]
			if applicant.job_id and (applicant.partner_name or contact_name):
				applicant.job_id.write({'no_of_hired_employee': applicant.job_id.no_of_hired_employee + 1})
				# raise UserError(str(applicant.is_teacher))
				employee = self.env['hr.employee'].create({'name': applicant.partner_name or contact_name,
											   'job_id': applicant.job_id.id,
											   'is_teacher':applicant.employee_type == 'is_teacher' and True or False,
											   'is_examiner':applicant.employee_type == 'is_examiner' and True or False,
											   'school_id':applicant.school_id.id,
											   'address_home_id': address_id,
											   'department_id': applicant.department_id.id or False,
											   'address_id': applicant.company_id and applicant.company_id.partner_id and applicant.company_id.partner_id.id or False,
											   'work_email': applicant.email_from,
											   'work_phone': applicant.department_id and applicant.department_id.company_id and applicant.department_id.company_id.phone or False})
				applicant.write({'emp_id': employee.id})
				applicant.job_id.message_post(
					body=_('New Employee %s Hired') % applicant.partner_name if applicant.partner_name else applicant.name,
					subtype="hr_recruitment.mt_job_applicant_hired")
				employee._broadcast_welcome()
			else:
				raise UserError(_('You must define an Applied Job and a Contact Name for this applicant.'))

		employee_action = self.env.ref('hr.open_view_employee_list')
		dict_act_window = employee_action.read([])[0]
		if employee:
			dict_act_window['res_id'] = employee.id
		dict_act_window['view_mode'] = 'form,tree'
		return dict_act_window