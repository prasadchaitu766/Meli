# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

import time
# import re
from datetime import date, datetime
from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.modules import get_module_resource
# from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import except_orm
from odoo.osv import expression
from odoo.exceptions import ValidationError,UserError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
# from dateutil.relativedelta import relativedelta
import base64
import cStringIO
# import qrcode
from .import school

# from lxml import etree
# added import statement in try-except because when server runs on
# windows operating system issue arise because this library is not in Windows.
try:
	from odoo.tools import image_colorize, image_resize_image_big
except:
	image_colorize = False
	image_resize_image_big = False


class StudentStudent(models.Model):
	''' Defining a student information '''
	_name = 'student.student'
	_table = "student_student"
	_description = 'Student Information'
	_order = "id desc"

	@api.multi
	@api.depends('date_of_birth')
	def _compute_student_age(self):
		'''Method to calculate student age'''
		current_dt = datetime.today()
		for rec in self:
			if rec.date_of_birth:
				start = datetime.strptime(rec.date_of_birth,
										  DEFAULT_SERVER_DATE_FORMAT)
				age_calc = ((current_dt - start).days / 365)
				# Age should be greater than 0
				if age_calc > 0.0:
					rec.age = age_calc

	@api.constrains('date_of_birth')
	def check_age(self):
		'''Method to check age should be greater than 5'''
		current_dt = datetime.today()
		if self.date_of_birth:
			start = datetime.strptime(self.date_of_birth,
									  DEFAULT_SERVER_DATE_FORMAT)
			age_calc = ((current_dt - start).days / 365)
			# Check if age less than 5 years
			if age_calc < 5:
				raise ValidationError(_('''Age of student should be greater
				than 5 years!'''))

	# @api.constrains('nid')
	# def check_nid(self):
	# 	'''Method to check age should be greater than 5'''
	# 	num = self.search([('nid','=',self.nid)])
	# 	raise UserError(str(self.nid))
	# 	nidnum = self.env['student.student'].search([('nid','=',self.nid)]).mapped('nid')
	# 	raise UserError(str(nidnum))

	# 	if self.nid == nidnum:
	# 		raise ValidationError(_('''xcvbhnm,'''))	
	# 	else:
	# 		raise UserError(str("sdfghjk"))				

	# @api.multi
	# @api.depends('student_code')	
	# def _generate_qr_code(self):
	# 	qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=20, border=4)
	# 	if self.student_code:
	# 		crnt_time = datetime.now().strftime("%Y-%m-%d %H:%M")	
	# 		name = self.student_code + '_ code.png'
	# 		qr.add_data(self.student_code+str(crnt_time))
	# 		qr.make(fit=True)
	# 		img = qr.make_image()
	# 		buffer = cStringIO.StringIO()
	# 		img.save(buffer, format="PNG")
	# 		qrcode_img = base64.b64encode(buffer.getvalue())
	# 		self.qr_code=qrcode_img
			# c= open("/home/bassam5/error.txt", "a")
			# c.write(str(qrcode_img+'------------'+self.student_code+'///////////'))
			# c.close()


	@api.model
	def create(self, vals):
		'''Method to create user when student is created'''
		ir_sequence = self.env['ir.sequence']
		student_app = ir_sequence.next_by_code('student.student')
		date_today=datetime.now().strftime("%d%m%Y")
		school_id=vals['school_id']
		school=self.env['school.school'].search([('id','=',school_id)])
		school_code=school.code
		student_obj=self.env['student.student']
		date=datetime.today().strftime("%Y-%m-%d")
		app_no=student_obj.search([('admission_date','=',date),('school_id','=',school_id)],count=True)
		if vals.get('pid', _('New')) == _('New'):
			vals['pid'] = school_code+'/'+str(date_today) + str('/') +str(app_no+1) or _('New')
		if vals.get('pid', False):
			vals['login'] = vals['pid']
			vals['password'] = vals['pid']
			vals['user_type'] ='student'
		else:
			raise except_orm(_('Error!'),
							 _('''PID not valid
								 so record will not be saved.'''))
		if vals.get('cmp_id', False):
			company_vals = {'company_ids': [(4, vals.get('cmp_id'))],
							'company_id': vals.get('cmp_id')}
			vals.update(company_vals)
		# if vals.get('email'):
		#     school.emailvalidation(vals.get('email'))
		res = super(StudentStudent, self).create(vals)
		# Assign group to student based on condition
		emp_grp = self.env.ref('base.group_user')
		if res.state == 'draft':
			admission_group = self.env.ref('school.group_is_admission')
			new_grp_list = [admission_group.id, emp_grp.id]
			res.user_id.write({'groups_id': [(6, 0, new_grp_list)]})
		elif res.state == 'done':
			done_student = self.env.ref('school.group_school_student')
			group_list = [done_student.id, emp_grp.id]
			res.user_id.write({'groups_id': [(6, 0, group_list)]})
		return res

	@api.multi
	def unlink(self):
		for data in self:
			if data.pid:
				raise UserError(_('You cannot delete this document.'))
		return super(StudentStudent, self).unlink()
	@api.model
	def _get_default_image(self, is_company, colorize=False):
		'''Method to get default Image'''
		# added in try-except because import statements are in try-except
		try:
			img_path = get_module_resource('base', 'static/src/img',
										   'avatar.png')
			with open(img_path, 'rb') as f:
				image = f.read()
			image = image_colorize(image)
			return image_resize_image_big(image.encode('base64'))
		except:
			return False

	@api.multi
	@api.depends('state')
	def _compute_teacher_user(self):
		for rec in self:
			if rec.state == 'done':
				teacher = self.env.user.has_group("school.group_school_teacher"
												  )
				if teacher:
					rec.teachr_user_grp = True

	@api.model
	def check_current_year(self):
		'''Method to get default value of logged in Student'''
		res = self.env['academic.year'].search([('current', '=',
												 True)])
		
	division = fields.Char('Room Number')
	start_class = fields.Text('Class Start On')

	@api.onchange('standard_id')
	def onchange_standard_id(self):
		if self.standard_id:
			self.division_id = self.standard_id.division_id 
			self.remaining_seats = self.standard_id.remaining_seats
			self.division = str(self.division_id.name) +' - ' + str(self.remaining_seats)
			self.start_class = str(self.standard_id.start_date)+ '  to  ' + str(self.standard_id.end_date)
			
	@api.multi
	@api.depends('state')
	def _generate_seat(self):
		for val in self:
			
			student_obj = self.env['school.standard'].search([('school_id','=',val.school_id.id),
							('standard_id','=',val.program_id.id),
							('medium_id','=',val.medium_id.id),
							('semester_id','=',val.semester_id.id),
							('state','!=','close')])
			for res in student_obj:
				if res.remaining_seats > 0:
					num = student_obj.search_count([('school_id','=',val.school_id.id),
								('standard_id','=',val.program_id.id),
								('medium_id','=',val.medium_id.id),
								('semester_id','=',val.semester_id.id),
								('state','!=','close')])
					val.availability = num
	
	def _warning_count(self):
		for order in self:
			warning_obj = self.env['student.warning'].search([('student_id','=',self.id)])
			self.warning_count = len(warning_obj)

	@api.multi
	@api.depends('state')
	def _generate_class(self):
		for val in self:
			student_obj = self.env['student.payslip'].search([('student_id','=',val.id),('semester_id','=',val.semester_id.id)])
			# for res in student_obj:
			if student_obj:
				val.is_class = True
			else:
				val.is_class = False	

	is_class = fields.Boolean(default=False,compute="_generate_class")			
	availability = fields.Integer("No of Classes",compute="_generate_seat")	
	warning_count = fields.Integer(compute="_warning_count", default=0)	
	line_ids = fields.One2many('student.transfer.line','line_id')
	user_id = fields.Many2one('res.users', 'User ID', ondelete="cascade",
							  required=True, delegate=True)
	student_name = fields.Char('Student Name', related='user_id.name',
							   store=True, readonly=True)
	pid = fields.Char('Application No', required=True,
					  default=lambda self: _('New'),
					  help='Personal IDentification Number')
	reg_code = fields.Char('Registration Code',
						   help='Student Registration Code')
	student_code = fields.Char('Student Code')
	contact_phone1 = fields.Char('Phone no.',)
	contact_mobile1 = fields.Char('Mobile no',)
	roll_no = fields.Integer('Roll No.')
	photo = fields.Binary('Photo', default=lambda self: self._get_default_image
						  (self._context.get('default_is_company',
											 False)))
	year = fields.Many2one('academic.year', 'Academic Year', readonly=True,
						   default=check_current_year)
	cast_id = fields.Many2one('student.cast', 'Religion/Caste')
	relation = fields.Many2one('student.relation.master', 'Relation')

	admission_date = fields.Date('Application Date', default=lambda self: fields.Date.today())
	admission_donedate = fields.Date('Admission Date')
	expired_date = fields.Date('Expired Date')
	middle = fields.Char('Middle Name',
						 states={'done': [('readonly', True)]})
	last = fields.Char('Last Name',
						 states={'done': [('readonly', True)]},required=True)
	
	gender = fields.Selection([('male', 'Male'), ('female', 'Female')],
							  'Gender', states={'done': [('readonly', True)]})
	date_of_birth = fields.Date('BirthDate',
								states={'done': [('readonly', True)]})
	mother_tongue = fields.Many2one('mother.toungue', "Mother Tongue")
	age = fields.Integer(compute='_compute_student_age', string='Age',
						 readonly=True)
	maritual_status = fields.Selection([('unmarried', 'Unmarried'),
										('married', 'Married')],
									   'Marital Status',
									   states={'done': [('readonly', True)]})
	reference_ids = fields.One2many('student.reference', 'reference_id',
									'References',
									states={'done': [('readonly', True)]})
	previous_school_ids = fields.One2many('student.previous.school',
										  'previous_school_id',
										  'Previous Campus Detail',
										  states={'done': [('readonly',
															True)]})
	designation = fields.Char('Designation')
	remark = fields.Text('Remark', states={'done': [('readonly', True)]})
	school_id = fields.Many2one('school.school', 'Campus',
								states={'done': [('readonly', True)]})
	state = fields.Selection([('draft', 'Draft'),
							  ('invoiced','Invoiced'),
							  ('done', 'Done'),
							  ('movesemester','Move Course Level'),
							  ('repeat','Repeat'),
							  ('terminate', 'Terminate'),
							  ('cancel', 'Cancel'),
							  ('alumni', 'Alumni'),
							  ('followup', 'Follow Up')],
							 'State', readonly=True, default="draft")
	history_ids = fields.One2many('student.history', 'student_id', 'History')
	certificate_ids = fields.One2many('student.certificate', 'student_id',
									  'Certificate')
	student_discipline_line = fields.One2many('student.descipline',
											  'student_id', 'Descipline')
	document = fields.One2many('student.document', 'doc_id', 'Documents')
	description = fields.One2many('student.description', 'des_id',
								  'Description')
	student_id = fields.Many2one('student.student', 'Name')
	contact_phone = fields.Char('Phone No', related='student_id.phone',
								readonly=True)
	contact_mobile = fields.Char('Mobile No', related='student_id.mobile',
								 readonly=True)
	contact_email = fields.Char('Email', related='student_id.email',
								readonly=True)
	contact_website = fields.Char('WebSite', related='student_id.website',
								  readonly=True)
	# award_list = fields.One2many('student.award', 'award_list_id',
	#                              'Award List')
	student_status = fields.Selection('Status', related='student_id.state',
									  help="Shows Status Of Student",
									  readonly=True)
	stu_name = fields.Char('First Name', related='user_id.name',
						   readonly=True)
	Acadamic_year = fields.Char('Academic Year', related='year.name',
								help='Academic Year', readonly=True)
	division_id = fields.Many2one('standard.division', 'Class Room',states={'alumni': [('readonly', True)]})
	medium_id = fields.Many2one('standard.medium', 'Shift',states={'alumni': [('readonly', True)]})
	cmp_id = fields.Many2one('res.company', 'Company Name',
							 related='school_id.company_id', store=True)
	standard_id = fields.Many2one('school.standard', 'Class',states={'alumni': [('readonly', True)]})
	parent_id = fields.Char("Father Name")
	grandparent_id = fields.Char("Grand Father Name")  
	terminate_reason = fields.Text('Reason')
	active = fields.Boolean(default=True)
	teachr_user_grp = fields.Boolean("Teacher Group",
									 compute="_compute_teacher_user",
									 )
	followup_id = fields.Text('Reason',store=True)
	nid = fields.Char('NID/Tazkira Number')

	semester_id = fields.Many2one('standard.semester',"Course Level",store=True,states={'alumni': [('readonly', True)]})

	occupation = fields.Char("Occupation")


	city=fields.Char('Campus Name')
	street=fields.Char('Street')
	zip=fields.Char('District')
	street2=fields.Char('Street2')
	state_id = fields.Many2one("res.country.state", string='State', ondelete='restrict')
	country_id = fields.Many2one('res.country', string='Country', ondelete='restrict',default=lambda self: self.env['res.country'].browse([(3)]))
	currency_id = fields.Many2one('res.currency', string='Currency',default=lambda self: self.env.user.company_id.currency_id,readonly=True)
	company_id = fields.Many2one('res.company', string='Company',default=lambda self: self.env.user.company_id)

	same_address = fields.Boolean(string="Click here if both the addresses are same")

	permanent_city=fields.Char('Campus Name',store=True)
	permanent_street=fields.Char('Street',store=True)
	permanent_zip=fields.Char('District',store=True)
	permanent_street2=fields.Char('Street2',store=True)
	permanent_state_id = fields.Many2one("res.country.state", string='State', ondelete='restrict',store=True)
	permanent_country_id = fields.Many2one('res.country', string='Country', ondelete='restrict',store=True,default=lambda self: self.env['res.country'].browse([(3)]))
	program_id = fields .Many2one('standard.standard',"Program")
	remaining_seats = fields.Integer("Available Seats")
	app_no = fields.Char('Application No', required=True,
					  default=lambda self: _('New'),
					  help='Application Number')
	# att_device = fields .Many2one('zkteco.machine',"Select Device")


	percentage = fields.Float("Attendance(%)")
	percentage_id = fields.Many2one('exam.schedule.line','Percentage')
	eligible = fields.Boolean('Eligible')
	qr_code = fields.Binary('QR Code')
	admission_user_id = fields.Many2one('res.users', 'Admission Taken by',default=lambda self: self.env.user)
	class_added_by = fields.Many2one('res.users','Class Added By')

	_sql_constraints = [
		('nid_unique', 'unique(nid)',
		 'Nid/Tazkira number should be unique!'),
	]	

	@api.onchange('same_address')
	def _same_address(self):
		if self.same_address == True:
			# raise UserError(str(self.same_address))
			self.permanent_city = self.city
			self.permanent_street = self.street
			self.permanent_zip = self.zip
			self.permanent_street2 = self.street2
			self.permanent_state_id = self.state_id
			self.permanent_country_id = self.country_id

   

	@api.model
	def name_search(self,name, args=None, operator='ilike', limit=100):
		args = args or []
		domain = []
		if name:
			domain = ['|', ('student_name', '=ilike', name + '%'), ('student_code', operator, name)]
			if operator in expression.NEGATIVE_TERM_OPERATORS:
				domain = ['&', '!'] + domain[1:]
		jobs = self.search(domain + args, limit=limit)
		return jobs.name_get()

	@api.multi
	@api.depends('student_name','student_code')
	def name_get(self):
		result = []
		for job in self:
			if job.student_code:
				name = str(job.student_code) + ' - ' + str(job.student_name)
			else:
				name = str(job.student_name)
			result.append((job.id, name))
		return result
		

	@api.multi
	def set_to_draft(self):
		'''Method to change state to draft'''
		self.write({'state': 'draft'})

	@api.multi
	def set_alumni(self):
		'''Method to change state to alumni'''
		self.write({'state': 'alumni'})

	@api.multi
	def set_done(self):
		'''Method to change state to done'''
		self.write({'state': 'done'})

	@api.multi
	def admission_draft(self):
		'''Set the state to draft'''
		self.write({'state': 'draft'})

	@api.multi
	def set_terminate(self):
		self.write({'state': 'terminate'})

	@api.multi
	def cancel_admission(self):
		self.write({'state': 'cancel'})

	@api.multi
	def set_reset(self):
		if self.env['school.standard'].search([('id','=',self.standard_id.id),('state','=','running')]):
			self.write({'state': 'done'})

		if self.env['school.standard'].search([('id','=',self.standard_id.id),('state','=','close')]):	
			self.write({'state': 'draft'})	
		
	@api.multi
	def admission_done(self):
		'''Method to confirm admission'''
		school_standard_obj = self.env['school.standard']
		ir_sequence = self.env['ir.sequence']
		student_group = self.env.ref('school.group_school_student')
		emp_group = self.env.ref('base.group_user')
		for rec in self:
			if not rec.standard_id:
				raise ValidationError(_('''Please select class!'''))
			if rec.standard_id.remaining_seats <= 0:
				raise ValidationError(_('Seats of class %s are full'
										) % rec.standard_id.standard_id.name)
			domain = [('school_id', '=', rec.school_id.id)]
			if not rec.student_code:
				fees = self.env['student.payslip'].search([('student_id','=',rec.id),('state','=','paid')])
				fees.write({
						'program_id':rec.program_id.id,
						'standard_id':rec.standard_id.id,
					})
				reg_code = ir_sequence.next_by_code('student.registration')
				registation_code = (str(rec.school_id.state_id.name) + str('/') +
									str(rec.school_id.city) + str('/') +
									str(rec.school_id.name) + str('/') +
									str(reg_code))
				stu_code = ir_sequence.next_by_code('student.code')
				student_code = ('MELI'+'/'+str(rec.school_id.code) + str('/')+str(stu_code))
				pass_obj = self.env['website.support.ticket'].search([('id','=',rec.ticket_number.id)])
				if rec.ticket_number:
					rec.user_id.write({'login':student_code,'password':pass_obj.pwd})
				else:
					rec.user_id.write({'login':student_code,'password':student_code})	
				admission = datetime.now()
				dateyear = admission.year
				date = admission.replace(year=dateyear+1)
				rec.admission_donedate = admission
				rec.expired_date = date
			else:
				student_code=rec.student_code
				registation_code=rec.reg_code
				admission = rec.admission_donedate

			# Checks the standard if not defined raise error
			if not school_standard_obj.search(domain):
				raise except_orm(_('Warning'),
								 _('''The standard is not defined in
									 school'''))
			# Assign group to student
			rec.user_id.write({'groups_id': [(6, 0, [emp_group.id,
													 student_group.id])]})
			# Assign roll no to student
			number = 1
			domain_1 =  [('school_id', '=', rec.school_id.id),('standard_id', '=', rec.standard_id.id)]
			for rec_std in rec.search(domain_1):
				rec_std.roll_no = number
				number += 1
			# Assign registration code to student
			class_added_by = self.env.user.id
			rec.write({'state': 'done',
					   # 'admission_date': time.strftime('%Y-%m-%d'),
					   'student_code': student_code,
					   'reg_code': registation_code,
					   'class_added_by':class_added_by,
					   
					 })
		return True


	# @api.multi
	# def Move_semester_done(self):
	# 	if not self.standard_id:
	# 		raise ValidationError(_('''Please select class!'''))
	# 	self.write({'state': 'done'})
	# 	return True

	# @api.multi
	# def repeat_done(self):
	# 	self.write({'state': 'done'})
	# 	return True

class StudentTransferLine(models.Model):
	_name = 'student.transfer.line'
	_description = 'Transfer History'
	_rec_name = "stud_name"

	line_id = fields.Many2one('student.student')
	transfer_date = fields.Datetime("Transfer Date")
	stud_name = fields.Many2one('student.student',"Name", store=True)
	from_campus_id = fields.Char("From Campus", store=True)
	to_campus_id = fields.Many2one('school.school', "To Campus", store=True)
	reason_id = fields.Text("Reason", store=True)
	previous_standard_id = fields.Char("Program",store=True)
	previous_semester_id = fields.Char("Semester",store=True)
	previous_medium_id = fields.Char("Shift",store=True)


