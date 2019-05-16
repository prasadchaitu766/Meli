# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

# import time
import re
import calendar
from datetime import datetime
from odoo import models, fields, api
from odoo.tools.translate import _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, \
	DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import except_orm
from odoo.exceptions import ValidationError,UserError
from dateutil.relativedelta import relativedelta
import json
import string

import base64
import cStringIO
import qrcode

from lxml import etree
# added import statement in try-except because when server runs on
# windows operating system issue arise because this library is not in Windows.
try:
	from odoo.tools import image_colorize, image_resize_image_big
except:
	image_colorize = False
	image_resize_image_big = False

EM = (r"[_a-z0-9-]+(\.[_a-z0-9-]+)*@[a-z0-9-]+(\.[a-z0-9-]+)*(\.[a-z]{2,4})$")


def emailvalidation(email):

	if email:
		EMAIL_REGEX = re.compile(EM)
		if not EMAIL_REGEX.match(email):
			raise ValidationError(_('''This seems not to be valid email.
			Please enter email in correct format!'''))
		else:
			return True


class AcademicYear(models.Model):
	''' Defines an academic year '''
	_name = "academic.year"
	_description = "Academic Year"
	_order = "sequence"

	sequence = fields.Integer('Sequence', required=True,
							  help="Sequence order you want to see this year.")
	name = fields.Char('Name', required=True, help='Name of academic year')
	code = fields.Char('Code', required=True, help='Code of academic year')
	date_start = fields.Date('Start Date', required=True,
							 help='Starting date of academic year')
	date_stop = fields.Date('End Date', required=True,
							help='Ending of academic year')
	month_ids = fields.One2many('academic.month', 'year_id', 'Months',
								help="related Academic months")
	grade_id = fields.Many2one('grade.master', "Grade")
	current = fields.Boolean('Current', help="Set Active Current Year")
	description = fields.Text('Description')

	@api.model
	def next_year(self, sequence):
		'''This method assign sequence to years'''
		year_id = self.search([('sequence', '>', sequence)], order='id',
							  limit=1)
		if year_id:
			return year_id.id
		return False

	@api.multi
	def name_get(self):
		'''Method to display name and code'''
		return [(rec.id, ' [' + rec.code + ']' + rec.name) for rec in self]

	@api.multi
	def generate_academicmonth(self):
		interval = 1
		month_obj = self.env['academic.month']
		for data in self:
			ds = datetime.strptime(data.date_start, '%Y-%m-%d')
			while ds.strftime('%Y-%m-%d') < data.date_stop:
				de = ds + relativedelta(months=interval, days=-1)
				if de.strftime('%Y-%m-%d') > data.date_stop:
					de = datetime.strptime(data.date_stop, '%Y-%m-%d')
				month_obj.create({
					'name': ds.strftime('%B'),
					'code': ds.strftime('%m/%Y'),
					'date_start': ds.strftime('%Y-%m-%d'),
					'date_stop': de.strftime('%Y-%m-%d'),
					'year_id': data.id,
				})
				ds = ds + relativedelta(months=interval)
		return True

	@api.constrains('date_start', 'date_stop')
	def _check_academic_year(self):
		'''Method to check start date should be greater than end date
		   also check that dates are not overlapped with existing academic
		   year'''
		new_start_date = datetime.strptime(self.date_start, '%Y-%m-%d')
		new_stop_date = datetime.strptime(self.date_stop, '%Y-%m-%d')
		delta = new_stop_date - new_start_date
		if delta.days > 365 and not calendar.isleap(new_start_date.year):
			raise ValidationError(_('''Error! The duration of the academic year
									  is invalid.'''))
		if (self.date_stop and self.date_start and
				self.date_stop < self.date_start):
			raise ValidationError(_('''The start date of the academic year'
									  should be less than end date.'''))
		# for old_ac in self.search([('id', 'not in', self.ids)]):
			# Check start date should be less than stop date
			# if (old_ac.date_start <= self.date_start <= old_ac.date_stop or
			# 		old_ac.date_start <= self.date_stop <= old_ac.date_stop):
			# 	raise ValidationError(_('''Error! You cannot define overlapping
			# 							  academic years.'''))
		return True

	@api.constrains('current')
	def check_current_year(self):
		check_year = self.search([('current', '=', True)])
		# if len(check_year.ids) >= 2:
		# 	raise ValidationError(_('''Error! You cannot set two current
		# 	year active!'''))


class AcademicMonth(models.Model):
	''' Defining a month of an academic year '''
	_name = "academic.month"
	_description = "Academic Month"
	_order = "date_start"

	name = fields.Char('Name', required=True, help='Name of Academic month')
	code = fields.Char('Code', required=True, help='Code of Academic month')
	date_start = fields.Date('Start of Period', required=True,
							 help='Starting of academic month')
	date_stop = fields.Date('End of Period', required=True,
							help='Ending of academic month')
	year_id = fields.Many2one('academic.year', 'Academic Year', required=True,
							  help="Related academic year ")
	description = fields.Text('Description')

	_sql_constraints = [
		('month_unique', 'unique(date_start, date_stop, year_id)',
		 'Academic Month should be unique!'),
	]

	@api.constrains('date_start', 'date_stop')
	def _check_duration(self):
		'''Method to check duration of date'''
		if (self.date_stop and self.date_start and
				self.date_stop < self.date_start):
			raise ValidationError(_(''' End of Period date should be greater
									than Start of Peroid Date!'''))

	@api.constrains('year_id', 'date_start', 'date_stop')
	def _check_year_limit(self):
		'''Method to check year limit'''
		if self.year_id and self.date_start and self.date_stop:
			if (self.year_id.date_stop < self.date_stop or
					self.year_id.date_stop < self.date_start or
					self.year_id.date_start > self.date_start or
					self.year_id.date_start > self.date_stop):
				raise ValidationError(_('''Invalid Months ! Some months overlap
									or the date period is not in the scope
									of the academic year!'''))

	# @api.constrains('date_start', 'date_stop')
	# def check_months(self):
	# 	for old_month in self.search([('id', 'not in', self.ids)]):
	# 		# Check start date should be less than stop date
	# 		if old_month.date_start <= \
	# 				self.date_start <= old_month.date_stop \
	# 				or old_month.date_start <= \
	# 				self.date_stop <= old_month.date_stop:
	# 				raise ValidationError(_('''Error! You cannot define
	# 				overlapping months!'''))


class StandardMedium(models.Model):
	''' Defining a medium(ENGLISH, HINDI, GUJARATI) related to standard'''
	_name = "standard.medium"
	_description = "Standard Medium"
	_order = "sequence"


	sequence = fields.Char('Sequence',copy=False, index=True,default=lambda self: _('New'))
	name = fields.Char('Name', required=True)
	code = fields.Char('Code', required=True)
	description = fields.Text('Description')
	hour_from = fields.Float('Time From')
	hour_to = fields.Float('Time To')

	# @api.depends('hour_from','hour_to')
	# def _time_time(self):

	# 	time_from = ''
	# 	time_to = ''
	# 	for val in self:
			# time_from = '{0:02.0f}:{1:02.0f}'.format(*divmod(val.hour_from * 60, 60))
			# time_to = '{0:02.0f}:{1:02.0f}'.format(*divmod(val.hour_to * 60, 60))

	# 		val.write({'from_hour':int(time_from),
	# 				   'to_hour':int(time_to),})

	from_hour = fields.Char("Time From")
	to_hour = fields.Char("Time To")

	@api.onchange('hour_from','hour_to')
	def _onchange_time(self):
		time_from = ''
		time_to = ''
		if self.hour_from:
			time_from = '{0:02.0f}:{1:02.0f}'.format(*divmod(self.hour_from * 60, 60))
			self.from_hour = time_from		
		if self.hour_to:	
			time_to = '{0:02.0f}:{1:02.0f}'.format(*divmod(self.hour_to * 60, 60))
			self.to_hour = time_to

	@api.onchange('from_hour', 'to_hour')
	def _onchange_time(self):
		time_from = ''
		time_to = ''
		if self.from_hour:
			t_f = self._convert_time(self.from_hour)
			time_from = re.findall('\d+', t_f)
			if len(time_from) != 2:
				self.hour_from = float(time_from[0])
			else:
				hours = int(time_from[0])
				minutes = int(time_from[1])
				self.hour_from = float(hours) + float(float(minutes)/60)
		if self.to_hour:
			t_h = self._convert_time(self.to_hour)
			time_to = re.findall('\d+', t_h)
			if len(time_to) != 2:
				self.hour_to = float(time_to)
			else:
				hours = int(time_to[0])
				minutes = int(time_to[1])
				self.hour_to = float(hours) + float(float(minutes) / 60)

	def _convert_time(self,var):
		if var[-2:] == "AM" and var[:2] == "12":
			time = "00" + var[2:-2]
		elif var[-2:] == "AM":
			time = var[:-2]
		elif var[-2:] == "PM" and var[:2] == "12":
			time = var[:-2]
		else:
			time = str(int(var[:1]) + 12) + var[1:4] if var[:2].find(':') != -1 else str(int(var[:2]) + 12) + var[2:8]
		return time	
			
	@api.model
	def create(self, vals):
		if vals.get('sequence', _('New')) == _('New'):
			vals['sequence'] = self.env['ir.sequence'].next_by_code('student.medium') or _('New')			
		result = super(StandardMedium, self).create(vals)	

		return result

		
	
class StandardDivision(models.Model):
	''' Defining a division(A, B, C) related to standard'''
	_name = "standard.division"
	_description = "Standard Division"
	_order = "sequence"

		
	sequence = fields.Char('Sequence',copy=False, index=True,default=lambda self: _('New'))
	name = fields.Char('Name', required=True)
	code = fields.Char('Code', required=True)
	description = fields.Text('Description')
	

	@api.model
	def create(self, vals):
		if vals.get('sequence', _('New')) == _('New'):
			vals['sequence'] = self.env['ir.sequence'].next_by_code('student.division') or _('New')
		result = super(StandardDivision, self).create(vals)
		return result


class StandardSemester(models.Model):
	''' Defining a division(A, B, C) related to standard'''
	_name = "standard.semester"
	_description = "Standard Semester"
	_order = "sequence"

	sequence = fields.Integer('Sequence')
	name = fields.Char('Name', required=True)
	code = fields.Char('Code', required=True)
	description = fields.Text('Description')
	standard_id = fields.Many2one('standard.standard',"Program")

	@api.model
	def create(self, vals):
		if vals.get('sequence', _('New')) == _('New'):
			seq = self.env['standard.semester'].search([('standard_id', '=', vals.get('standard_id'))],count=True)
			vals['sequence'] = seq+1
		result = super(StandardSemester, self).create(vals)
		return result
	

class StandardStandard(models.Model):
	''' Defining Standard Information '''
	_name = 'standard.standard'
	_description = 'Standard Information'
	_order = "sequence"


	sequence = fields.Char('Sequence',copy=False, index=True,default=lambda self: _('New'))
	name = fields.Char('Name', required=True)
	code = fields.Char('Code', required=True)
	semester_ids = fields.One2many('standard.semester', 'standard_id',
								  'Course Level')
	description = fields.Text('Description')

	@api.model
	def create(self, vals):
		if vals.get('sequence', _('New')) == _('New'):
			vals['sequence'] = self.env['ir.sequence'].next_by_code('student.standard') or _('New')
		result = super(StandardStandard, self).create(vals)
		return result
	@api.model
	def next_standard(self, sequence):
		'''This method check sequence of standard'''
		stand_ids = self.search([('sequence', '>', sequence)], order='id',
								limit=1)
		if stand_ids:
			return stand_ids.id
		return False


class SchoolStandard(models.Model):
	''' Defining a standard related to school '''
	_name = 'school.standard'
	_description = 'School Standards'
	_rec_name = "standard"

	@api.multi
	@api.depends('standard_id', 'school_id', 'division_id', 'medium_id','semester_id')
	def _compute_student(self):
		'''Compute student of done state'''
		student_obj = self.env['student.student']
		for rec in self:
			domain = [
					  ('standard_id', '=', rec.id),
					  ('school_id', '=', rec.school_id.id),
					  ('standard_id.division_id', '=', rec.division_id.id),
					  ('medium_id', '=', rec.medium_id.id),
					  ('semester_id','=',rec.semester_id.id),
					  ('state', '=', 'done')
					  ]
			rec.student_ids = student_obj.search(domain)
			qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=20, border=4)
			if rec.sequence:
				crnt_time = datetime.now().strftime("%Y-%m-%d %H:%M")	
				name = rec.sequence + '_ code.png'
				qr.add_data(str(rec.standard+crnt_time))
				qr.make(fit=True)
				# c= open("/home/bassam5/error.txt", "a")
				# c.write(str('student_qr'))
				# c.close()
				img = qr.make_image()
				buffer = cStringIO.StringIO()
				img.save(buffer, format="PNG")
				qrcode_img = base64.b64encode(buffer.getvalue())
				rec.qr_code=qrcode_img


	# @api.multi
	# @api.depends('sequence')	
	# def _generate_qr_code(self):
	# 	qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_L, box_size=20, border=4)
	# 	raise UserError(str("inside"))
	# 	if self.sequence:
	# 		crnt_time = datetime.now().strftime("%Y-%m-%d %H:%M")	
	# 		name = self.sequence + '_ code.png'
	# 		qr.add_data(self.sequence+str(crnt_time))
	# 		qr.make(fit=True)
	# 		img = qr.make_image()
	# 		buffer = cStringIO.StringIO()
	# 		img.save(buffer, format="PNG")
	# 		qrcode_img = base64.b64encode(buffer.getvalue())
	# 		raise UserError(str(qrcode_img))
	# 		self.qr_code=qrcode_img


	@api.multi
	@api.depends('standard_id', 'school_id')
	def _compute_student_class(self):
		'''Compute student of done state'''
		student_obj = self.env['student.history']
		for rec in self:
			domain = [('standard_id', '=', rec.id),
					  ]
			rec.history_ids = student_obj.search(domain)


	@api.onchange('standard_id', 'division_id')
	def onchange_combine(self):
		self.name = str(self.standard_id.name
						) + '-' + str(self.division_id.name)
	
	@api.multi
	@api.depends('subject_ids')
	def _compute_subject(self):
		'''Method to compute subjects'''
		for rec in self:
			rec.total_no_subjects = len(rec.subject_ids)

	@api.multi
	@api.depends('student_ids')
	def _compute_total_student(self):
		for rec in self:
			rec.total_students = len(rec.student_ids)

	@api.depends("capacity", "total_students")
	def _compute_remain_seats(self):
		for rec in self:
			rec.remaining_seats = rec.capacity - rec.total_students

	@api.model
	def create(self, vals):
		school_id=vals['school_id']
		semester_id = vals['semester_id']
		medium_id = vals['medium_id']
		# sequence_id = vals['sequence']
		school_code = self.env['school.school'].search([('id','=',school_id)])
		semester_code = self.env['standard.semester'].search([('id','=',semester_id)])
		medium_code = self.env['standard.medium'].search([('id','=',medium_id)])
		data = list(string.ascii_uppercase)
		if vals.get('sequence', _('New')) == _('New'):
			seq_obj = self.env['class.sequence']
			seq = seq_obj.search([('school_id', '=', vals.get('school_id'))])
			number=seq.number
			if not seq:
				order= 'A'	
				vals['sequence']= order
				seq_obj.create({
				'school_id' : vals.get('school_id'),
				'alphabet' : order,
				'number':'0',
				})
				
			else:
				order = chr(ord(seq.alphabet)+1)
				if order in data:
					order=order
				else:
					order='A'
					number=number+1	
				if number > 0:
					vals['sequence']= order+str(number)	
				else:
					vals['sequence']= order		
				seq.write({'alphabet' : order,
						   'number' : number})
			
		vals.update({
					'standard': school_code.code +'/'+ semester_code.code +'/'+ medium_code.code +'/'+ vals['sequence']
						 })
		self.check_student(school_code.id,semester_code.id,medium_code.id,vals['start_date'])

		return super(SchoolStandard, self).create(vals)

	@api.multi
	def check_student(self,school_id,semester_id,medium_id,date):
		domain = [('state', '=','followup'),('standard_id', '=',False),('semester_id', '=',semester_id),('school_id', '=',school_id),('medium_id', '=',medium_id)]
		students = self.env['student.student'].search(domain)

		for student in students:
			vals =	{
				'stu_id':student.id,
				'name' : 'Reminder(Class Opening)',
				'date' : fields.Date.today(),
				'description':'Your Class will be opened on ' + str(date)
			}
			self.env['student.reminder'].create(vals)

	
	
		
	sequence = fields.Char('Sequence')
	school_id = fields.Many2one('school.school', 'Campus', required=True)
	standard_id = fields.Many2one('standard.standard', 'Program',
								  required=True)
	division_id = fields.Many2one('standard.division', 'Room Number',
								  required=True)
	medium_id = fields.Many2one('standard.medium', 'Shift', required=True)
	subject_ids = fields.Many2many('subject.subject', 'subject_standards_rel',
								   'subject_id', 'standard_id', 'Subject')
	user_id = fields.Many2one('school.teacher', 'Class Teacher')
	student_ids = fields.One2many('student.student', 'standard_id',
								  'Student In Class',
								  compute='_compute_student', store=True
								  )
	history_ids = fields.One2many('student.history', 'standard_id',
								  'Student In Class',
								  compute='_compute_student_class', store=False
								  )
	color = fields.Integer('Color Index')
	cmp_id = fields.Many2one('res.company', 'Company Name',
							 related='school_id.company_id', store=True)
	syllabus_ids = fields.One2many('subject.syllabus', 'standard_id',
								   'Syllabus')
	total_no_subjects = fields.Integer('Total No of Subject',
									   compute="_compute_subject")
	name = fields.Char('Name')
	capacity = fields.Integer("Capacity")
	total_students = fields.Integer("Strength",compute="_compute_total_student",store=False)
	remaining_seats = fields.Integer("Available Seats",compute="_compute_remain_seats",store=False)
	class_room_id = fields.Many2one('class.room', 'Room Number')
	semester_id = fields.Many2one('standard.semester','Course Level')
	start_date = fields.Date("Start Date")
	end_date = fields.Date("End Date")
	standard =fields.Char("Class")
	state = fields.Selection([
		('draft', 'New'),
		('running', 'Running'),
		('close', 'Closed'),
	], string='Status', default='draft')
	tv_user_id = fields.Many2one('res.users', string='TV User')
	qr_code = fields.Binary('QR Code')


	@api.constrains('standard_id', 'division_id','medium_id','state')
	def check_standard_unique(self):
		standard_search = self.env['school.standard'
								   ].search([('standard_id', '=',
											  self.standard_id.id),
											 ('semester_id', '=',
											  self.semester_id.id),
											 ('division_id', '=',
											  self.division_id.id),('medium_id','=',self.medium_id.id),
											 ('school_id', '=',
											  self.school_id.id),
											 ('state','!=','close'),
											 ('id', 'not in', self.ids)])
		if standard_search:
			raise ValidationError(_('''Division and class should be unique!'''
									))
		return True	

	
	@api.multi
	def send_class_status_new(self):
		today = datetime.now()
		if self.state == "draft":
			date_from = '%-' + today.strftime('%m') + '-' + today.strftime('%d')
			for line in self.search([('start_date', 'like', date_from),('state','=','draft')]):
				# raise UserError(str(line))
				line.write({
					'state' : "running",
					})
			
		if self.state == "running":			
			date_end = today.strftime('%Y')+ '-' + today.strftime('%m') + '-' + today.strftime('%d')
			for res in self.search([('end_date', '<', date_end),('state','=','running')]):
				res.write({
					'state' : "close",
					})

	@api.multi
	def approve_state(self):
		self.send_class_status_new()					

	@api.constrains('capacity')
	def check_seats(self):
		if self.capacity <= 0:
			raise ValidationError(_('''Total seats should be greater than
				0!'''))

	@api.multi
	def unlink(self):
		for data in self:
			if data.id:
				raise UserError(_('You cannot delete this document.'))
		return super(SchoolStandard, self).unlink()		

	
class ClassSequence(models.Model):
	''' Defining School Information '''
	_name = 'class.sequence'

	alphabet = fields.Char("Alphabet")
	number = fields.Integer("Number")
	school_id = fields.Many2one('school.school', string='Company')
	
class SchoolSchool(models.Model):
	''' Defining School Information '''
	_name = 'school.school'
	# _inherits = {'res.company': 'company_id'}
	_description = 'School Information'
	_rec_name = "name"
	_order = "id desc"

	

	@api.model
	def _lang_get(self):
		'''Method to get language'''
		languages = self.env['res.lang'].search([])
		return [(language.code, language.name) for language in languages]

	company_id = fields.Many2one('res.company', 'Company',
								 ondelete="cascade",
								 required=True)
	com_name = fields.Char('Campus Name')
	code = fields.Char('Code', required=True)
	standards = fields.One2many('school.standard', 'school_id',
								'Class')
	lang = fields.Selection(_lang_get, 'Language',
							help='''If the selected language is loaded in the
								system, all documents related to this partner
								will be printed in this language.
								If not, it will be English.''')
	member_ids = fields.One2many('campus.members', 'member_id',
								'Members')
	name = fields.Char('Campus Name')
	
	city=fields.Char('Campus Name')
	street=fields.Char('Street')
	zip=fields.Char('District')
	street2=fields.Char('Street2')
	state_id = fields.Many2one("res.country.state", string='State', ondelete='restrict')
	country_id = fields.Many2one('res.country', string='Country', ondelete='restrict',default=lambda self: self.env['res.country'].browse([(3)]))
	currency_id = fields.Many2one('res.currency', string='Currency',default=lambda self: self.env.user.company_id.currency_id,readonly=True)
	company_id = fields.Many2one('res.company', string='Company',default=lambda self: self.env.user.company_id)
	tv_user_id = fields.Many2one('res.users', string='TV User')
	partner_id = fields.Many2one('res.partner', 'Partner')

	@api.model
	def create(self, vals):
		result = super(SchoolSchool, self).create(vals)
		partner_obj=self.env['res.partner']
		partner_data = {'name':result.name,
						'company_id':result.company_id.id,
						'street':result.street,
						'city':result.city,
						'display_name':result.name,
						'zip':result.zip,
						'country_id':result.country_id.id,
						'street2':result.street2,
						'type':'contact'}
		partner_id=partner_obj.create(partner_data)

		result.partner_id=partner_id.id
		return result


class CampusMembers(models.Model):
	''' Defining School Information '''
	_name = 'campus.members'

	user_id = fields.Many2one('res.users', 'Members',ondelete="cascade",required=True)
	member_id = fields.Many2one('school.school', 'Members')
	
	
class SubjectSubject(models.Model):
	'''Defining a subject '''
	_name = "subject.subject"
	_description = "Subjects"
	_order = "id desc"

	name = fields.Char('Name', required=True)
	code = fields.Char('Code', required=True)
	maximum_marks = fields.Integer("Maximum marks")
	minimum_marks = fields.Integer("Minimum marks")
	weightage = fields.Integer("WeightAge")
	teacher_ids = fields.Many2many('school.teacher', 'subject_teacher_rel',
								   'subject_id', 'teacher_id', 'Teachers')
#    standard_ids = fields.Many2many('standard.standard',
#                                    'subject_standards_rel',
#                                    'standard_id', 'subject_id', 'Standards')
	# standard_ids = fields.Many2many('standard.standard',
	# 								string='Programs')
	standard_id = fields.Many2one('standard.standard', 'Program')
	is_practical = fields.Boolean('Is Practical',
								  help='Check this if subject is practical.')
	elective_id = fields.Many2one('subject.elective')
	student_ids = fields.Many2many('student.student',
								   'elective_subject_student_rel',
								   'subject_id', 'student_id', 'Students')
	grade_system = fields.Many2one('grade.master', "Grade System")

class SubjectSyllabus(models.Model):
	'''Defining a  syllabus'''
	_name = "subject.syllabus"
	_description = "Syllabus"
	_rec_name = "subject_id"

	standard_id = fields.Many2one('standard.standard', 'Program')
	subject_id = fields.Many2one('subject.subject', 'Subject')
	syllabus_doc = fields.Binary("Syllabus Doc",
								 help="Attach syllabus related to Subject")


class SubjectElective(models.Model):
	''' Defining Subject Elective '''
	_name = 'subject.elective'

	name = fields.Char("Name")
	subject_ids = fields.One2many('subject.subject', 'elective_id',
								  'Elective Subjects')


class MotherTongue(models.Model):
	_name = 'mother.toungue'
	_description = "Mother Toungue"

	name = fields.Char("Mother Tongue")


class StudentAward(models.Model):
	_name = 'student.award'
	_description = "Student Awards"

	award_list_id = fields.Many2one('student.student', 'Student')
	name = fields.Char('Award Name')
	description = fields.Char('Description')


class AttendanceType(models.Model):
	_name = "attendance.type"
	_description = "School Type"

	name = fields.Char('Name', required=True)
	code = fields.Char('Code', required=True)


class StudentDocument(models.Model):
	_name = 'student.document'
	_rec_name = "doc_type"

	doc_id = fields.Many2one('student.student', 'Student')
	file_no = fields.Char('File No', readonly="1", default=lambda obj:
						  obj.env['ir.sequence'].
						  next_by_code('student.document'))
	submited_date = fields.Date('Submitted Date')
	doc_type = fields.Many2one('document.type', 'Document Type', required=True)
	file_name = fields.Char('File Name',)
	return_date = fields.Date('Return Date')
	new_datas = fields.Binary('Attachments')


class DocumentType(models.Model):
	''' Defining a Document Type(SSC,Leaving)'''
	_name = "document.type"
	_description = "Document Type"
	_rec_name = "doc_type"
	_order = "seq_no"

	seq_no = fields.Char('Sequence', readonly=True,
						 default=lambda self: _('New'))
	doc_type = fields.Char('Document Type', required=True)

	@api.model
	def create(self, vals):
		if vals.get('seq_no', _('New')) == _('New'):
			vals['seq_no'] = self.env['ir.sequence'
									  ].next_by_code('document.type'
													 ) or _('New')
		return super(DocumentType, self).create(vals)


class StudentDescription(models.Model):
	''' Defining a Student Description'''
	_name = 'student.description'

	des_id = fields.Many2one('student.student', 'Description')
	name = fields.Char('Name')
	description = fields.Char('Description')


class StudentDescipline(models.Model):
	_name = 'student.descipline'

	student_id = fields.Many2one('student.student', 'Student')
	teacher_id = fields.Many2one('school.teacher', 'Teacher')
	date = fields.Date('Date')
	class_id = fields.Many2one('standard.standard', 'Class')
	note = fields.Text('Note')
	action_taken = fields.Text('Action Taken')


class StudentHistory(models.Model):
	_name = "student.history"

	student_id = fields.Many2one('student.student', 'Student')
	start_date = fields.Date("Start Date")
	end_date = fields.Date("End Date")
	school_id = fields.Many2one('school.school', 'Campus', required=True)
	standard_id = fields.Many2one('school.standard', 'Class')
	percentage = fields.Float("Percentage", readonly=True)
	result = fields.Char('Result', readonly=True)
	roll_no= fields.Integer('Roll No')
	
class StudentCertificate(models.Model):
	_name = "student.certificate"

	student_id = fields.Many2one('student.student', 'Student')
	description = fields.Char('Description')
	certi = fields.Binary('Certificate', required=True)


class StudentReference(models.Model):
	''' Defining a student reference information '''
	_name = "student.reference"
	_description = "Student Reference"

	reference_id = fields.Many2one('student.student', 'Student')
	name = fields.Char('First Name', required=True)
	middle = fields.Char('Middle Name')
	last = fields.Char('Surname', required=True)
	designation = fields.Char('Designation', required=True)
	phone = fields.Char('Phone', required=True)
	gender = fields.Selection([('male', 'Male'), ('female', 'Female')],
							  'Gender')


class StudentPreviousSchool(models.Model):
	''' Defining a student previous school information '''
	_name = "student.previous.school"
	_description = "Student Previous School"

	previous_school_id = fields.Many2one('student.student', 'Student')
	name = fields.Char('Name', required=True)
	registration_no = fields.Char('Registration No.', required=True)
	admission_date = fields.Date('Admission Date')
	exit_date = fields.Date('Exit Date')
	course_id = fields.Many2one('standard.standard', 'Programs', required=True)
	add_sub = fields.One2many('academic.subject', 'add_sub_id', 'Add Subjects')

	@api.constrains('admission_date', 'exit_date')
	def check_date(self):
		curr_dt = datetime.now()
		new_dt = datetime.strftime(curr_dt,
								   DEFAULT_SERVER_DATE_FORMAT)
		if self.admission_date >= new_dt or self.exit_date >= new_dt:
			raise ValidationError(_('''Your admission date and exit date
			should be less than current date in previous school details!'''))
		if self.admission_date > self.exit_date:
			raise ValidationError(_(''' Admission date should be less than
			exit date in previous school!'''))


class AcademicSubject(models.Model):
	''' Defining a student previous school information '''
	_name = "academic.subject"
	_description = "Student Previous School"

	add_sub_id = fields.Many2one('student.previous.school', 'Add Subjects',
								 invisible=True)
	name = fields.Char('Name', required=True)
	maximum_marks = fields.Integer("Maximum marks")
	minimum_marks = fields.Integer("Minimum marks")


class StudentFamilyContact(models.Model):
	''' Defining a student emergency contact information '''
	_name = "student.family.contact"
	_description = "Student Family Contact"

	@api.multi
	@api.depends('relation', 'stu_name')
	def _compute_get_name(self):
		for rec in self:
			if rec.stu_name:
				rec.relative_name = rec.stu_name.name
			else:
				rec.relative_name = rec.name

	family_contact_id = fields.Many2one('student.student', 'Student')
	exsting_student = fields.Many2one('student.student',
									  'Student')
	rel_name = fields.Selection([('exist', 'Link to Existing Student'),
								 ('new', 'Create New Relative Name')],
								'Related Student', help="Select Name",
								required=True)
	user_id = fields.Many2one('res.users', 'User ID', ondelete="cascade")
	stu_name = fields.Many2one('student.student', 'Name',
							   help="Select Student From Existing List")
	name = fields.Char('Name')
	relation = fields.Many2one('student.relation.master', 'Relation',
							   required=True)
	phone = fields.Char('Phone', required=True)
	email = fields.Char('E-Mail')
	relative_name = fields.Char(compute='_compute_get_name', string='Name')


class StudentRelationMaster(models.Model):
	''' Student Relation Information '''
	_name = "student.relation.master"
	_description = "Student Relation Master"

	name = fields.Char('Name', required=True, help="Enter Relation name")
	seq_no = fields.Integer('Sequence')


class GradeMaster(models.Model):
	_name = 'grade.master'

	name = fields.Char('Grade', required=True)
	grade_ids = fields.One2many('grade.line', 'grade_id', 'Grade Name')


class GradeLine(models.Model):
	_name = 'grade.line'
	_rec_name = 'grade'

	from_mark = fields.Integer('From %', required=True,
							   help='The grade will starts from this marks.')
	to_mark = fields.Integer('To %', required=True,
							 help='The grade will ends to this marks.')
	grade = fields.Char('Grade', required=True, help="Grade")
	sequence = fields.Integer('Sequence', help="Sequence order of the grade.")
	fail = fields.Boolean('Fail', help='If fail field is set to True,\
								  it will allow you to set the grade as fail.')
	grade_id = fields.Many2one("grade.master", 'Grade')
	name = fields.Char('Name')


class StudentNews(models.Model):
	_name = 'student.news'
	_description = 'Student News'
	_rec_name = 'subject'
	_order = 'date asc'

	subject = fields.Char('Subject', required=True,
						  help='Subject of the news.')
	description = fields.Text('Description', help="Description")
	date = fields.Datetime('Expiry Date', help='Expiry date of the news.')
	user_ids = fields.Many2many('res.users', 'user_news_rel', 'id', 'user_ids',
								'User News',
								help='Name to whom this news is related.')
	color = fields.Integer('Color Index', default=0)

	@api.constrains("date")
	def checknews_dates(self):
		curr_dt = datetime.now()
		new_date = datetime.strftime(curr_dt, DEFAULT_SERVER_DATETIME_FORMAT)
		if self.date < new_date:
			raise ValidationError(_('''Configure expiry date greater than
			current date!'''))

	@api.multi
	def news_update(self):
		'''Method to send email to student for news update'''
		emp_obj = self.env['hr.employee']
		obj_mail_server = self.env['ir.mail_server']
		user = self.env['res.users'].browse(self._context.get('uid'))
		# Check if out going mail configured
		mail_server_ids = obj_mail_server.search([])
		if not mail_server_ids:
			raise except_orm(_('Mail Error'),
							 _('''No mail outgoing mail server
							   specified!'''))
		mail_server_record = mail_server_ids[0]
		email_list = []
		# Check email is defined in student
		for news in self:
			if news.user_ids and news.date:
				email_list = [news_user.email for news_user in news.user_ids
							  if news_user.email]
				if not email_list:
					raise except_orm(_('User Email Configuration!'),
									 _("Email not found in users !"))
			# Check email is defined in user created from employee
			else:
				for employee in emp_obj.search([]):
					if employee.work_email:
						email_list.append(employee.work_email)
					elif employee.user_id and employee.user_id.email:
						email_list.append(employee.user_id.email)
				if not email_list:
					raise except_orm(_('Email Configuration!'),
									 _("Email not defined!"))
			news_date = datetime.strptime(news.date,
										  DEFAULT_SERVER_DATETIME_FORMAT)
			# Add company name while sending email
			company = user.company_id.name or ''
			body = """Hi,<br/><br/>
					This is a news update from <b>%s</b> posted at %s<br/>
					<br/> %s <br/><br/>
					Thank you.""" % (company,
									 news_date.strftime('%d-%m-%Y %H:%M:%S'),
									 news.description or '')
			smtp_user = mail_server_record.smtp_user or False
			# Check if mail of outgoing server configured
			if not smtp_user:
				raise except_orm(_('Email Configuration '),
								 _("Kindly,Configure Outgoing Mail Server!"))
			notification = 'Notification for news update.'
			# Configure email
			message = obj_mail_server.build_email(email_from=smtp_user,
												  email_to=email_list,
												  subject=notification,
												  body=body,
												  body_alternative=body,
												  reply_to=smtp_user,
												  subtype='html')
			# Send Email configured above with help of send mail method
			obj_mail_server.send_email(message=message,
									   mail_server_id=mail_server_ids[0].id)
		return True


class StudentTransfer(models.Model):
	_name = 'student.transfer'
	_description = 'Student Transfer'
	_rec_name = "student_name"
	_order = "id desc"

	date = fields.Date('Date',readonly=True, default=datetime.today())

	student_name = fields.Many2one('student.student',"Name", store=True,default=lambda self: self.env['student.student'].search([('user_id', '=', self.env.user.id)]))
	from_campus = fields.Many2one('school.school','Current Campus',compute='_compute_student_school', store=True)
	school_id = fields.Many2one('school.school', "To Campus")
	school_id_from = fields.Many2one('school.school', "Current Campus",store=True)

	reason = fields.Text("Reason")
	shift_id = fields.Many2one('standard.medium', 'Current Shift',compute='_compute_student_school', store=True)
	program_id = fields.Char('Current Program',compute='_compute_student_school', store=True)
	course_id = fields.Many2one('standard.semester','Current Course Level',compute='_compute_student_school', store=True)
	class_id = fields.Char('Current Class',compute='_compute_student_school',required=False, store=True)

	state = fields.Selection([('draft','New'),
		('in progress','In Progress'),
		('approve','Approved'),
		('rejected','Rejected')], index='true', default='draft')

	medium_id = fields.Many2one('standard.medium', 'Shift Needed')
	standard_id = fields.Many2one('school.standard', 'Class')
	semester_id = fields.Many2one('standard.semester',"Course Level",compute='_compute_student_school', store=True)
	program = fields.Many2one('standard.standard',"Program",compute='_compute_student_school', store=True)
	remaining_seats_transfer = fields.Char("Available Seats",default=None, compute='_compute_remain_seats_transfer',store=True)
	division = fields.Char('Room Number', compute='_compute_remain_seats_transfer',store=True)

	line_id = fields.Many2one('student.student')

	@api.multi
	def unlink(self):
		for rec in self:
			if rec.state !='draft':
				raise ValidationError(_('''You cannot delete this request!'''))
		return super(StudentTransfer, self).unlink()


	# @api.onchange('student_name')
	# def onchange_student(self):
	# 	self.from_campus = self.student_name.school_id.id
		
			
	@api.depends('student_name')
	def _compute_student_school(self):
		if self.student_name:
			self.from_campus = self.student_name.school_id.id
			self.school_id_from = self.student_name.school_id.id
			self.shift_id = self.student_name.medium_id.id
			self.program_id = self.student_name.program_id.name
			self.course_id = self.student_name.semester_id.id
			self.class_id = (str (self.student_name.school_id.code + 
				'/' + self.student_name.semester_id.code + 
				'/' + self.student_name.medium_id.code +
				'/' + self.student_name.standard_id.division_id.code))
			self.program = self.student_name.program_id.id
			self.semester_id = self.student_name.semester_id.id


	@api.depends("standard_id")
	def _compute_remain_seats_transfer(self):
		for rec in self:
			rec.remaining_seats_transfer = rec.standard_id.capacity - rec.standard_id.total_students
			rec.division = str(rec.standard_id.division_id.name) +'-' + str(rec.standard_id.remaining_seats)

	@api.multi
	def set_start(self):
		self.write({'state': 'in progress'})
		self.send_mail_template()

	@api.multi
	def send_mail_template(self):
		# Find the e-mail template
		template = self.env.ref('school.studenttransfer_request_mail')
		# You can also find the e-mail template like this:
		# template = self.env['ir.model.data'].get_object('mail_template_demo', 'example_email_template')
 
		# Send out the e-mail template to the user
		self.env['mail.template'].browse(template.id).send_mail(self.id)

	@api.multi
	def set_close(self):
		if self.school_id:
			self.student_name.school_id = self.school_id
		var = self.env['student.student'].search([('id','=',self.student_name.id)])
		var_list = []
		if var:
			ele = {
				'stud_name': self.student_name.id,
				'from_campus': self.from_campus,
				'to_campus_id': self.school_id.id,
				'transfer_date' : self.date,
				'reason_id': self.reason,
				'previous_standard_id': self.student_name.standard_id.name,
				'previous_semester_id': self.student_name.semester_id.name,
				'previous_medium_id': self.student_name.medium_id.name
					}
			var_list.append(ele)
		# raise UserError(str(ele))
		var.line_ids = var_list
		self.write({'state': 'approve'})
		self.student_name.standard_id = self.standard_id.id
		self.student_name.semester_id = self.semester_id.id
		self.student_name.medium_id = self.medium_id.id
		self.student_name.division_id = self.standard_id.division_id.id
		self.student_name.division = self.division
		self.student_name.roll_no = self.standard_id.total_students + 1

	@api.multi
	def set_reject(self):
		self.write({'state': 'rejected'})	

	@api.multi
	def set_to_reset(self):
		self.write({'state': 'draft'})

	@api.model
	def create(self, vals):
		transfer = super(StudentTransfer, self).create(vals)
		# raise UserError(_(str(transfer.remaining_seats_transfer)))
		if (str(transfer.remaining_seats_transfer)) == '0' :
			raise ValidationError('Sorry! Seats are fully occupied. We cannot accommodate you to the selected particular class. You can try an another class or try later. 😊')
		return transfer


class StudentWithdrawal(models.Model):
	_name = 'student.withdrawal'
	_description = 'Student Withdrawal'
	_rec_name = "student_name"
	_order = "withdrawal_date desc"

	withdrawal_date = fields.Date('Date')
	student_name = fields.Many2one('student.student',"Student Name",default=lambda self: self.env['student.student'].search([('user_id', '=', self.env.user.id)]))
	student_campus = fields.Char("Current Campus",compute='_compute_student_school', store=True)
	withdrawal_reason = fields.Text("Reason")

	student_code = fields.Char('Student Code',compute='_compute_student_school', store=True)

	state = fields.Selection([('draft','New'),
		('in progress','In Progress'),
		('alumni','Alumni'),
		('terminate','Terminated'),
		('rejected','Rejected')], index='true', default='draft')

	@api.multi
	def unlink(self):
		for rec in self:
			if rec.state !='draft':
				raise ValidationError(_('''You can delete the request only in draft state!'''))
		return super(StudentWithdrawal, self).unlink()


	

	@api.depends('student_name')
	def _compute_student_school(self):
		if self.student_name:
			self.student_campus = self.student_name.school_id.name
			self.student_code = self.student_name.student_code

	@api.multi
	def set_start(self):
		self.write({'state': 'in progress'})
		self.send_mail_template()

	@api.multi
	def send_mail_template(self):
		# Find the e-mail template
		template = self.env.ref('school.withdrawal_request_mail')
		# You can also find the e-mail template like this:
		# template = self.env['ir.model.data'].get_object('mail_template_demo', 'example_email_template')
 
		# Send out the e-mail template to the user
		self.env['mail.template'].browse(template.id).send_mail(self.id)

	@api.multi
	def set_close(self):
		self.student_name.set_alumni()
		self.write({'state': 'alumni'})

	@api.multi
	def set_terminate(self):
		self.student_name.set_terminate()
		self.write({'state': 'terminate'})

	@api.multi
	def set_reject(self):
		self.write({'state': 'rejected'})	

	@api.multi
	def set_to_reset(self):
		self.write({'state': 'draft'})

class TeacherTransfer(models.Model):
	_name = 'teacher.transfer'
	_description = 'Teacher Transfer'
	_rec_name = "teacher_id"
	_order = "date desc"

	date = fields.Date('Date')

	teacher_id = fields.Many2one('school.teacher', 'Teacher')
	from_campus = fields.Char("Current Campus",compute='_compute_teacher_transfer', store=True)
	school_id = fields.Many2one('school.school', "To Campus")
	reason = fields.Text("Reason")

	state = fields.Selection([('draft','New'),
		('in progress','In Progress'),
		('approve','Approved'),
		('rejected','Rejected')], index='true', default='draft')
	@api.multi
	def unlink(self):
		for rec in self:
			if rec.state =='in progress' or rec.state == 'approve' or rec.state =='rejected':
				raise ValidationError(_('''You cannot delete this request!'''))
		return super(TeacherTransfer, self).unlink()

	

	@api.depends('teacher_id')
	def _compute_teacher_transfer(self):
		if self.teacher_id:
			self.from_campus = self.teacher_id.school_id.name

	@api.multi
	def set_start(self):
		self.write({'state': 'in progress'})
		self.send_mail_template()

	@api.multi
	def send_mail_template(self):
		# Find the e-mail template
		template = self.env.ref('school.teacher_transfer_request_mail')
		# You can also find the e-mail template like this:
		# template = self.env['ir.model.data'].get_object('mail_template_demo', 'example_email_template')
 
		# Send out the e-mail template to the user
		self.env['mail.template'].browse(template.id).send_mail(self.id)

	@api.multi
	def set_close(self):
		if self.school_id:
			self.teacher_id.school_id = self.school_id
		teacher_var = self.env['school.teacher'].search([('id','=',self.teacher_id.id)])
		teacher_var_list = []
		if teacher_var:
			ele = {
				'teacher_name_id': self.teacher_id.id,
				'teacher_from_campus': self.from_campus,
				'teacher_school_id': self.school_id.id,
				'teacher_date' : self.date,
				'teacher_reason': self.reason,
					}
			teacher_var_list.append(ele)
		# raise UserError(str(ele))
		teacher_var.teacher_transfer_ids = teacher_var_list
		# variable.stud_name = self.student_name.id

		self.write({'state': 'approve'})

	@api.multi
	def set_reject(self):
		self.write({'state': 'rejected'})   

	@api.multi
	def set_to_reset(self):
		self.write({'state': 'draft'})


class StaffTransfer(models.Model):
	_name = 'staff.transfer'
	_rec_name = "staff_id"

	staff_id = fields.Many2one('hr.employee',string ="Employee Name")
	staff_job_id = fields.Many2one('hr.job', string='Designation',compute='_compute_staff_details', store=True)  
	staff_date = fields.Datetime('Date')
	current_company_id = fields.Many2one('school.school',"Current Campus",compute='_compute_staff_details', store=True)
	cmp_id = fields.Many2one('school.school', 'To Campus')
	staff_purpose = fields.Text("Purpose Of Transfer")
	staff_work_location = fields.Char('Work Location',compute='_compute_staff_details', store=True)

	state = fields.Selection([('draft','New'),
		('in progress','In Progress'),
		('approve','Approved'),
		('rejected','Rejected')], index='true', default='draft')
	

	@api.depends('staff_id')
	def _compute_staff_details(self):
		if self.staff_id:
			self.staff_work_location = self.staff_id.work_location
			self.staff_job_id = self.staff_id.job_id
			self.current_company_id = self.staff_id.school_id.id

	@api.multi
	def set_start(self):
		self.send_mail_template()
		self.write({'state': 'in progress'})
		
		
	
	@api.multi
	def send_mail_template(self):
		# Find the e-mail template
		template = self.env.ref('school.staff_transfer_request_mail')
		# You can also find the e-mail template like this:
		# template = self.env['ir.model.data'].get_object('mail_template_demo', 'example_email_template')
 
		# Send out the e-mail template to the user
		self.env['mail.template'].browse(template.id).send_mail(self.id)
	
	@api.multi
	def set_close(self):
		if self.cmp_id:
			self.staff_id.school_id = self.cmp_id
			self.staff_id.work_location = self.cmp_id.name
			self.staff_id.address_id = self.cmp_id.partner_id.id

		staff_var = self.env['hr.employee'].search([('id','=',self.staff_id.id)])
		staff_var_list = []
		if staff_var:
			ele = {
				'company_date': self.staff_date,
				'from_company': self.current_company_id.id,
				'to_company': self.cmp_id.id,
				'reason' : self.staff_purpose,
					}
			staff_var_list.append(ele)
		# raise UserError(str(ele))
		staff_var.employee_line_ids = staff_var_list
		# variable.stud_name = self.student_name.id

		self.write({'state': 'approve'})

	@api.multi
	def set_reject(self):
		self.write({'state': 'rejected'})	

	@api.multi
	def set_to_reset(self):
		self.write({'state': 'draft'})



class StudentReminder(models.Model):
	_name = 'student.reminder'

	@api.model
	def check_user(self):
		'''Method to get default value of logged in Student'''
		return self.env['student.student'].search([('user_id', '=',
													self._uid)]).id

	stu_id = fields.Many2one('student.student', 'Student Name', required=True,
							 default=check_user)
	name = fields.Char('Title')
	date = fields.Datetime('Date')
	description = fields.Text('Description')
	color = fields.Integer('Color Index', default=0)


class StudentCast(models.Model):
	_name = "student.cast"

	name = fields.Char("Name", required=True)


class ClassRoom(models.Model):
	_name = "class.room"

	name = fields.Char("Name")
	number = fields.Char("Room Number")


class Report(models.Model):
	_inherit = "report"

	@api.multi
	def render(self, template, values=None):
		if 'docs' in values:
			for data in values.get('docs'):
				if (values.get('doc_model') == 'student.student' and
						data.state == 'draft'):
						raise ValidationError(_('''You cannot print report for
					student in unconfirm state!'''))
		res = super(Report, self).render(template, values)
		return res

class HrEmployee(models.Model):
	_inherit = 'hr.employee'

	employee_line_ids = fields.One2many('staff.transfer.line','employee_line_id')

class StaffTransferLine(models.Model):
	_name = "staff.transfer.line"
	_description = 'Staff Transfer Line'

	employee_line_id = fields.Many2one('hr.employee')
	company_date = fields.Date("Date")
	from_company = fields.Many2one('school.school', 'From Branch')
	to_company = fields.Many2one('school.school','To Branch')
	reason = fields.Char("Transfer Reason")

class HrExpense(models.Model):
	_inherit = 'hr.expense'
	_description = "Expense"

	job_id = fields.Many2one('hr.job', string='Designation',compute='_compute_work_location_for_expense', store=True)
	school_id = fields.Many2one('school.school', "From Campus")
	to_school_id = fields.Many2one('school.school', "To Campus")
	work_location = fields.Char('Work Location',compute='_compute_work_location_for_expense', store=True)
	
	@api.depends('employee_id')
	def _compute_work_location_for_expense(self):
		if self.employee_id:
			self.work_location = self.employee_id.school_id.name
			self.job_id = self.employee_id.job_id


class HrExpenseSheet(models.Model):
	_inherit = "hr.expense.sheet"
	_description = "Expense"
	def _get_users_to_subscribe(self, employee=False):
		users = self.env['res.users']
		employee = employee or self.employee_id
		if employee.user_id:
			users |= employee.user_id
		if employee.parent_id:
			users |= employee.sudo().parent_id.user_id
		if employee.department_id and employee.department_id.manager_id and employee.parent_id != employee.department_id.manager_id:
			users |= employee.department_id.manager_id.user_id
		return users
