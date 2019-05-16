# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.
import time
from datetime import date, datetime, timedelta
from odoo import models, fields, api, _
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError,Warning as UserError
import babel

class StudentStudent(models.Model):
	_inherit = 'student.student'
	_description = 'Student Information'

	exam_results_ids = fields.One2many('exam.result', 'student_id',
									   'Exam History', readonly=True)

	@api.model
	def _search(self, args, offset=0, limit=None, order=None, count=False,
				access_rights_uid=None):
		'''Override method to get exam of student selected'''
		if self._context.get('exam'):
			exam_obj = self.env['exam.exam']
			exam_data = exam_obj.browse(self._context['exam'])
			std_ids = [std_id.id for std_id in exam_data.standard_id]
			args.append(('standard_id', 'in', std_ids))
		return super(StudentStudent, self)._search(
			args=args, offset=offset, limit=limit, order=order, count=count,
			access_rights_uid=access_rights_uid)


class ExtendedTimeTable(models.Model):
	_inherit = 'time.table'

	@api.multi
	def unlink(self):
		exam = self.env['exam.exam']
		schedule_line = self.env['exam.schedule.line']
		for rec in self:
			exam_search = exam.search([('state', '=', 'running')])
			for data in exam_search:
				schedule_line_search = schedule_line.search([('exam_id', '=',
															  data.id),
															 ('timetable_id',
															  '=', rec.id)])
				if schedule_line_search:
					raise ValidationError(_('''You cannot delete schedule of
					exam which is in running!'''))
		return super(ExtendedTimeTable, self).unlink()

	timetable_type = fields.Selection(selection_add=[('exam', 'Exam')],
									  string='Time Table Type', required=True,
									  inivisible=False)
	exam_timetable_line_ids = fields.One2many('time.table.line', 'table_id',
											  'TimeTable')
	exam_id = fields.Many2one('exam.exam', 'Exam')
	

	@api.multi
	@api.constrains('exam_timetable_line_ids')
	def _check_exam(self):
		'''Method to check same exam is not assigned on same day'''
		if self.timetable_type == 'exam':
			if not self.exam_timetable_line_ids:
				raise ValidationError(_(''' Please Enter Exam Timetable!'''))
			domain = [('table_id', 'in', self.ids)]
			line_ids = self.env['time.table.line'].search(domain)
			for rec in line_ids:
				records = [rec_check.id for rec_check in line_ids
						   if (rec.day_of_week == rec_check.day_of_week and
							   rec.start_time == rec_check.start_time and
							   rec.end_time == rec_check.end_time and
							   rec.teacher_id.id == rec.teacher_id.id and
							   rec.exm_date == rec.exm_date)]
				# if len(records) > 1:
				#     raise ValidationError(_('''You cannot set exam at same
				#                             time %s  at same day %s in same date %s for
				#                             teacher %s!''') %
				#                            (rec.start_time, rec.day_of_week,rec.exm_date,
				#                             rec.teacher_id.name))


class ExtendedTimeTableLine(models.Model):
	_inherit = 'time.table.line'

	exm_date = fields.Date('Exam Date')
	day_of_week = fields.Char('Week Day')
	class_room_id = fields.Many2one('class.room', 'Classroom')

	@api.multi
	@api.onchange('exm_date')
	def onchange_date_day(self):
		'''Method to get weekday from date'''
		for rec in self:
			if rec.exm_date:
				week_day = datetime.strptime(rec.exm_date, "%Y-%m-%d")
				rec.day_of_week = week_day.strftime("%A").title()

	@api.multi
	def _check_date(self):
		'''Method to check constraint of start date and end date'''
		for line in self:
			if line.exm_date:
				dt = datetime.strptime(line.exm_date, "%Y-%m-%d")
				if line.week_day != dt.strftime("%A").lower():
					return False
				elif dt.__str__() < datetime.strptime(date.today().__str__(),
													  "%Y-%m-%d").__str__():
					raise ValidationError(_('''Invalid Date Error !
						Either you have selected wrong day
									   for the date or you have selected\
									   invalid date!'''))
		return True

	@api.constrains('teacher_id')
	def check_supervisior_exam(self):
			for rec in self:
				if (rec.table_id.timetable_type == 'exam' and
						not rec.teacher_id):
						raise ValidationError(_('''PLease Enter Supervisior!
						'''))

	@api.constrains('start_time', 'end_time')
	def check_time(self):
		for rec in self:
			if rec.start_time >= rec.end_time:
				raise ValidationError(_('''Start time should be less than end
				time!'''))

	@api.constrains('teacher_id', 'class_room_id')
	def check_teacher_room(self):
		timetable_rec = self.env['time.table'].search([('id', '!=',
														self.table_id.id)])
		if timetable_rec:
			for data in timetable_rec:
				for record in data.timetable_ids:
					if (data.timetable_type == 'exam' and
							self.table_id.timetable_type == 'exam' and
							self.class_room_id == record.class_room_id and
							self.exm_date == record.exm_date and
							self.day_of_week == record.day_of_week and
							self.start_time == record.start_time):
							raise ValidationError(_("The room is occupied!."))

	@api.constrains('subject_id', 'class_room_id')
	def check_exam_date(self):
		for rec in self.table_id.exam_timetable_line_ids:
			record = self.table_id
			if rec.id not in self.ids:
				if (record.timetable_type == 'exam' and
						self.exm_date == rec.exm_date and
						self.start_time == rec.start_time):
					raise ValidationError(_('''There is already Exam at
						same Date and Time!'''))
				if (record.timetable_type == 'exam' and
						self.table_id.timetable_type == 'exam' and
						self.subject_id == rec.subject_id):
						raise ValidationError(_('''%s Subject Exam Already
						Taken''') % (self.subject_id.name))
				if (record.timetable_type == 'exam' and
						self.table_id.timetable_type == 'exam' and
						self.exm_date == rec.exm_date and
						self.class_room_id == rec.class_room_id and
						self.start_time == rec.start_time):
					raise ValidationError(_('''%s is occupied by '%s' for %s
					class!''') % (self.class_room_id.name, record.name,
								  record.standard_id.standard_id.name))


class ExamExam(models.Model):
	_name = 'exam.exam'
	_description = 'Exam Information'
	_order = 'id desc'

	# @api.constrains('start_date', 'end_date')
	# def check_date_exam(self):
	# 	'''Method to check constraint of exam start date and end date'''
	# 	for rec in self:
	# 		if rec.end_date < rec.start_date:
	# 			raise ValidationError(_('''Exam end date should be
	# 							  greater than start date!'''))
	# 		for line in rec.exam_schedule_ids:
	# 			if line.timetable_id:
	# 				for tt in line.timetable_id.exam_timetable_line_ids:
	# 					if not rec.start_date <= tt.exm_date <= rec.end_date:
	# 						raise ValidationError(_('Invalid Exam Schedule\
	# 						\n\nExam Dates must be in between Start\
	# 						date and End date !'))

	@api.constrains('active')
	def check_active(self):
		'''if exam results is not in done state then raise an
		validation Warning'''
		result_obj = self.env['exam.result']
		if not self.active:
			for result in result_obj.search([('s_exam_ids', '=', self.id)]):
				if result.state != 'done':
					raise ValidationError(_('Kindly,mark as done %s\
					examination results!') % (self.name))

	@api.model
	def create(self, vals):
		if vals.get('exam_code', _('New')) == _('New'):
			vals['exam_code'] = self.env['ir.sequence'].next_by_code('exam.exam') or _('New')
		result = super(ExamExam, self).create(vals)
		return result				

	active = fields.Boolean('Active', default="True")
	name = fields.Char("Exam Name",
					   help="Name of Exam")
	exam_code = fields.Char('Exam Code', required=True, readonly=True,
							help="Code of exam",copy=False, index=True,default=lambda self: _('New'))
	standard_id = fields.Many2one('school.standard',
									'Classes')
	start_date = fields.Date("Exam Start Date",
							 help="Exam will start from this date")
	end_date = fields.Date("Exam End date", help="Exam will end at this date")
#    exam_timetable_ids = fields.One2many('', 'exam_id',
#                                         'Exam Schedule')
	state = fields.Selection([('generate', 'Generate'),
							  ('draft', 'Draft'),
							  ('running', 'Running'),
							  ('finished', 'Finished'),
							  ('cancelled', 'Cancelled')], 'State',
							 readonly=True, default='generate')
	grade_system = fields.Many2one('grade.master', "Grade System",
								   help="Select Grade System")
	academic_year = fields.Many2one('academic.year', 'Academic Year',
									help="Select Academic Year")
	exam_schedule_ids = fields.One2many('exam.schedule.line', 'exam_id',
										'Exam Schedule')
	school_id = fields.Many2one('school.school', 'Campus',required = True) 



	@api.multi
	def generate_exam(self):
		data = {}
		data_line = []
		self.exam_schedule_ids.unlink()
		timetable = self.env['time.table'].search([('timetable_ids.exm_date','>=',self.start_date),('timetable_ids.exm_date','<=',self.end_date),('state','=','draft')])
		for rec in timetable:
			# raise UserError(str(rec))
			data = self.env['exam.schedule.line'].create({
				'standard_id': rec.standard_id.id,
				'timetable_id': rec.id,
				'exam_id': self.id,
			})
			
			data_line.append(data.id)

		for percentages in self.env['exam.schedule.line'].search([('exam_id','=',self.id)]):
			student_obj = self.env['student.student'].search([('standard_id','=',percentages.standard_id.id)])
			for rec in student_obj:
				exam_obj=self.env['exam.percentage']
				data1=self.env['daily.attendance'].search_count([('standard_id','=',percentages.standard_id.id)])
				data = self.env['daily.attendance.line'].search_count([('is_present','=',True),('standard_id.standard_id','=',percentages.standard_id.id),('stud_id','=',rec.id)])
				if data1!= 0:
					percentage = (float(data) / float(data1))* 100
					eligible_data = ''	
					if percentage >= 75.00:
						eligible_data = True
					else:
						eligible_data = False
					exam_percentage = exam_obj.search([('exam_percentage_id','=',percentages.id),('student_id','=',rec.id)])
					exam_percentage.unlink()
					exam = exam_obj.create({
								'roll_no':rec.roll_no,
								'student_id':rec.id,
								'attendance_percentage':percentage,
								'exam_percentage_id':percentages.id,
								'eligible':eligible_data,
								})		
					rec.write({'percentage':percentage,
							   'eligible':eligible_data
						})	
				else:
					data = 0
					percentage = 0.0
					eligible_data = ''	
					if percentage >= 75.00:
						eligible_data = True
					else:
						eligible_data = False
					exam_percentage = exam_obj.search([('exam_percentage_id','=',percentages.id),('student_id','=',rec.id)])
					exam_percentage.unlink()
					exam = exam_obj.create({
								'roll_no':rec.roll_no,
								'student_id':rec.id,
								'attendance_percentage':percentage,
								'exam_percentage_id':percentages.id,
								'eligible':eligible_data,
								})		
					rec.write({'percentage':percentage,
							   'eligible':eligible_data
						})	

		self.write({'state': 'draft'})
	@api.multi
	def unlink(self):
		for order in self:
			if order.state not in ('draft'):
				raise UserError(_('You can delete exam details only in draft state '))
		return super(ExamExam, self).unlink()

	@api.multi
	def set_to_draft(self):
		'''Method to set state to draft'''
		self.write({'state': 'draft'})

	@api.multi
	def set_running(self):
		'''Method to set state to running'''
		for rec in self:
			# if not rec.standard_id:
			# 	raise ValidationError(_('Please Select Program!'))
			if rec.exam_schedule_ids:
				rec.state = 'running'
			else:
				raise ValidationError(_('You must add one Exam Schedule!'))
		return True

	@api.multi
	def set_finish(self):
		'''Method to set state to finish'''

		for res in self:
			for line in res.exam_schedule_ids:
				line.timetable_id.write({'state':'finish'})
		self.write({'state': 'finished'})

	@api.multi
	def set_cancel(self):
		'''Method to set state to cancel'''
		self.write({'state': 'cancelled'})

	@api.multi
	def _validate_date(self):
		'''Method to check start date should be less than end date'''
		for exm in self:
			if exm.start_date > exm.end_date:
				return False
		return True

	@api.multi
	def generate_result(self):
		'''Method to generate result'''
		result_obj = self.env['exam.result']
		student_obj = self.env['student.student']
		attend_obj = self.env['daily.attendance.line']
		result_list = []
		for rec in self:
			for exam_schedule in rec.exam_schedule_ids:
				domain = [('standard_id', '=', exam_schedule.standard_id.id),
						  ('state', '=', 'done'),
						  ('school_id', '=',
						   exam_schedule.standard_id.school_id.id),
						  ('eligible','=',True)]
				
				students = student_obj.search(domain)
				for student in students:
					domain = [('standard_id', '=',
							   student.standard_id.id),
							  ('student_id', '=', student.id),
							  ('s_exam_ids', '=', rec.id)]

					result_exists = result_obj.search(domain)
					if result_exists:
						[result_list.append(res.id) for res in result_exists]
					else:
						rs_dict = {'s_exam_ids': rec.id,
								   'student_id': student.id,
								   'standard_id': student.standard_id.id,
								   'roll_no_id': student.roll_no,
								   'grade_system': rec.grade_system.id,
								   }
						exam_line = []
						timetable = exam_schedule.sudo().timetable_id
						for line in timetable.sudo().timetable_ids:
							attendance = attend_obj.search([('stud_id','=',student.id),('standard_id.date','=',line.exm_date)])
							if attendance.is_present==True:
								min_mrks = line.subject_id.minimum_marks
								max_mrks = line.subject_id.maximum_marks
								sub_vals = {'subject_id': line.subject_id.id,
											'minimum_marks': min_mrks,
											'maximum_marks': max_mrks,
											'exam_date':line.exm_date,
											'attendance':True}
										
								exam_line.append((0, 0, sub_vals))
							else:
								min_mrks = line.subject_id.minimum_marks
								max_mrks = line.subject_id.maximum_marks
								sub_vals = {'subject_id': line.subject_id.id,
											'minimum_marks': min_mrks,
											'maximum_marks': max_mrks,
											'exam_date':line.exm_date,
											'attendance':False}
									
								exam_line.append((0, 0, sub_vals))	
						rs_dict.update({'result_ids': exam_line})
						result = result_obj.create(rs_dict)
						result_list.append(result.id)
		return {'name': _('Result Info'),
				'view_type': 'form',
				'view_mode': 'tree,form',
				'res_model': 'exam.result',
				'type': 'ir.actions.act_window',
				'domain': [('id', 'in', result_list)]}


class ExamScheduleLine(models.Model):
	_name = 'exam.schedule.line'
			
	standard_id = fields.Many2one('school.standard', 'Class',
								  help="Select Class")
	timetable_id = fields.Many2one('time.table', 'Exam Schedule')
	exam_id = fields.Many2one('exam.exam', 'Exam')
	percentage_ids = fields.One2many('exam.percentage','exam_percentage_id',
			  string='Participant Program')
	student_id = fields.Many2one('student.student', 'Student')


class ExamPercentage(models.Model):
	_name = 'exam.percentage'

	roll_no = fields.Integer('Roll No.')
	student_id = fields.Many2one('student.student', 'Student')
	attendance_percentage = fields.Float("Attendance(%)")
	exam_percentage_id = fields.Many2one('exam.schedule.line','percentage')
	eligible = fields.Boolean('Eligible')
class AdditionalExam(models.Model):
	_name = 'additional.exam'
	_description = 'additional Exam Information'

	@api.multi
	def _compute_color_name(self):
		for rec in self:
			rec.color_name = rec.subject_id.id

	name = fields.Char("Additional Exam Name", required=True,
					   help="Name of Exam")
	addtional_exam_code = fields.Char('Exam Code', required=True,
									  help="Exam Code",
									  readonly=True,
									  default=lambda obj:
									  obj.env['ir.sequence'].
									  next_by_code('additional.exam'))
	standard_id = fields.Many2one("school.standard", "Class")
	semester_id = fields.Many2one("standard.semester", "Book")
	subject_id = fields.Many2one("subject.subject", "Subject Name")
	exam_date = fields.Date("Exam Date")
	maximum_marks = fields.Integer("Maximum Mark",
								   help="Minimum Marks of exam")
	minimum_marks = fields.Integer("Minimum Mark",
								   help="Maximum Marks of Exam")
	weightage = fields.Char("WEIGHTAGE")
	create_date = fields.Date("Created Date", help="Exam Created Date")
	write_date = fields.Date("Updated date", help="Exam Updated Date")
	color_name = fields.Integer("Color index of creator",
								compute='_compute_color_name', store=False)

	@api.constrains('maximum_marks', 'minimum_marks')
	def check_marks(self):
		if self.minimum_marks > self.maximum_marks:
			raise ValidationError(_('''Configure Maximum marks greater than
			minimum marks!'''))

	@api.model
	def create(self, vals):
		curr_dt = datetime.now()
		new_dt = datetime.strftime(curr_dt, '%m/%d/%Y')
		vals.update({'create_date': new_dt})
		return super(AdditionalExam, self).create(vals)

	@api.multi
	def write(self, vals):
		curr_dt = datetime.now()
		new_dt = datetime.strftime(curr_dt, '%m/%d/%Y')
		vals.update({'write_date': new_dt})
		return super(AdditionalExam, self).write(vals)


class ExamResult(models.Model):
	_name = 'exam.result'
	_inherit = ["mail.thread", "ir.needaction_mixin"]
	_rec_name = 'roll_no_id'
	_description = 'exam result Information'

	@api.multi
	@api.depends('result_ids', 'result_ids.obtain_marks',
				 'result_ids.marks_reeval')
	def _compute_total(self):
		'''Method to compute total'''
		for rec in self:
			total = 0.0
			if rec.result_ids:
				for line in rec.result_ids:
					obtain_marks = line.obtain_marks
					if line.state == "re-evaluation":
						obtain_marks = line.marks_reeval
					total += obtain_marks
			rec.total = total

	@api.multi
	@api.depends('total')
	def _compute_per(self):
		'''Method to compute percentage'''
		total = 0.0
		obtained_total = 0.0
		obtain_marks = 0.0
		per = 0.0
		for result in self:
			for sub_line in result.result_ids:
				if sub_line.state == "re-evaluation":
					obtain_marks = sub_line.marks_reeval
				else:
					obtain_marks = sub_line.obtain_marks
				total += sub_line.maximum_marks or 0
				obtained_total += obtain_marks
			if total > 1.0:
				per = (obtained_total / total) * 100
				if result.grade_system:
					for grade_id in result.grade_system.grade_ids:
						if per >= grade_id.from_mark and\
								per <= grade_id.to_mark:

							result.grade = grade_id.grade or ''
			result.percentage = per



	@api.multi
	@api.depends('result_ids.grade_line_id')
	def _compute_result(self):
		'''Method to compute result'''
		for rec in self:
			flag = False
			if rec.percentage == 0.0:
				rec.result = 'Fail'
			else:
				rec.result = 'Fail' if 'Fail' in rec.mapped('result_ids').mapped('result') else 'Pass'

				
						
	@api.model
	def create(self, vals):
		if vals.get('student_id'):
			student = self.env['student.student'].browse(vals.get('student_id'
																  ))
			vals.update({'roll_no_id': student.roll_no,
						 'standard_id': student.standard_id.id
						 })
		return super(ExamResult, self).create(vals)

	@api.multi
	def write(self, vals):
		if vals.get('student_id'):
			student = self.env['student.student'].browse(vals.get('student_id'
																  ))
			vals.update({'roll_no_id': student.roll_no,
						 'standard_id': student.standard_id.id
						 })
		return super(ExamResult, self).write(vals)

	@api.multi
	def unlink(self):
		for rec in self:
			if rec.state != 'draft':
				raise ValidationError(_('''You can delete record in unconfirm
				state only!.'''))
		return super(ExamResult, self).unlink()

	@api.onchange('student_id')
	def onchange_student(self):
		'''Method to get standard and roll no of student selected'''
		if self.student_id:
			self.standard_id = self.student_id.standard_id.id
			self.roll_no_id = self.student_id.roll_no

	@api.depends('student_id')
	def depends_parent(self):
		'''Method to get standard and roll no of student selected'''
		for stud in self:
			if stud.student_id:
				stud.parent_id = stud.student_id.parent_id

	s_exam_ids = fields.Many2one("exam.exam", "Examination", required=True,
								 help="Select Exam")
	student_id = fields.Many2one("student.student", "Student Name",
								 required=True,
								 help="Select Student")
	parent_id = fields.Char("Parent Name", compute="depends_parent")
	roll_no_id = fields.Integer(string="Roll No",
								readonly=True)
	pid = fields.Char(related='student_id.pid', string="Student ID",
					  readonly=True)
	standard_id = fields.Many2one("school.standard", "Class",
								  help="Select Class")
	result_ids = fields.One2many("exam.subject", "exam_id", "Exam Subjects")
	total = fields.Float(compute='_compute_total', string='Obtain Total',
						 store=True, help="Total of marks")
	# grade_total = fields.Char("Grade", compute='_compute_grade_total')
	percentage = fields.Float("Percentage", compute="_compute_per",
							  store=True,
							  help="Percentage Obtained")
	result = fields.Char(compute='_compute_result', string='Result',
						   store=True,help="Result Obtained")
	grade = fields.Char("Grade", compute="_compute_per",
						store=True, help="Grade Obtained")
	state = fields.Selection([('draft', 'Draft'),
							  ('confirm', 'Confirm'),
							  ('re-evaluation', 'Re-Evaluation'),
							  ('re-evaluation_confirm',
							   'Re-Evaluation Confirm'),
							  ('done', 'Done')],
							 'State', readonly=True,
							 track_visibility='onchange',
							 default='draft')
	color = fields.Integer('Color')
	division = fields.Many2one('student.student')
	grade_system = fields.Many2one('grade.master', "Grade System",
								   help="Grade System selected", required=True)
	message_ids = fields.One2many('mail.message', 'res_id', 'Messages',
								  domain=lambda self: [('model', '=',
														self._name)],
								  auto_join=True)
	message_follower_ids = fields.One2many('mail.followers', 'res_id',
										   'Followers',
										   domain=lambda self: [('res_model',
																 '=',
																 self._name
																 )])

	@api.multi
	def result_confirm(self):
		'''Method to confirm result'''
		for rec in self:
			for line in rec.result_ids:
				if line.maximum_marks == 0:
					# Check subject marks not greater than maximum marks
					raise ValidationError(_('Kindly add maximum\
							marks of subject "%s".') % (line.subject_id.name))
				elif line.minimum_marks == 0:
					raise ValidationError(_('Kindly add minimum\
						marks of subject "%s".') % (line.subject_id.name))
				elif ((line.maximum_marks == 0 or line.minimum_marks == 0) and
					  line.obtain_marks):
					raise ValidationError(_('Kindly add marks\
						details of subject "%s"!') % (line.subject_id.name))
				# elif line.obtain_marks ==0:
				# 	raise ValidationError(_('Please Enter your marks'))	
			vals = {'grade': rec.grade,
					'percentage': rec.percentage,
					'state': 'confirm'
					}
			rec.write(vals)
		return True

	@api.multi
	def re_evaluation_confirm(self):
		'''Method to change state to re_evaluation_confirm'''
		self.write({'state': 're-evaluation_confirm'})

	@api.multi
	def result_re_evaluation(self):
		'''Method to set state to re-evaluation'''
		if self.result == 'Pass':
			raise ValidationError(_('You are already Pass the examination'))
		
		for rec in self:
			for line in rec.result_ids:
				line.marks_reeval = line.obtain_marks
			rec.state = 're-evaluation'
		return True

	@api.multi
	def set_done(self):
		'''Method to obtain history of student'''
		history_obj = self.env['student.history']
		standard_obj = self.env["standard.semester"]
		school_stand_obj = self.env["standard.standard"]
		student_obj = self.env['student.student']
		for rec in self:
			vals = {'student_id': rec.student_id.id,
					'standard_id': rec.standard_id.id,
					'start_date': rec.standard_id.start_date,
					'end_date': rec.standard_id.end_date,
					'roll_no':rec.student_id.roll_no,
					'percentage': rec.percentage,
					'result': rec.result,
					'school_id':rec.student_id.school_id.id}

			history = history_obj.search([('student_id', '=',
										   rec.student_id.id),
										  ('standard_id', '=',
										   rec.standard_id.id),
										   ])

			if history:
				history_obj.write(vals)
			elif not history:
				history_obj.create(vals)
			rec.write({'state': 'done'})
			if rec.result =='Pass':

				std_seq = rec.student_id.semester_id.sequence
				std_prog = rec.student_id.semester_id.standard_id
				result = self.env['standard.semester'].search([('sequence','=',int(std_seq) + 1),('standard_id','=',std_prog.id)])
				result1= int(result)
				rec.student_id.write({'semester_id':result1,
									  'standard_id':'',
									  'division':'',
									 'state':'movesemester'})
				
			else:
				rec.student_id.write({'standard_id':'',
									'division':'',
									'state':'repeat'})
				
		return True


class ExamGradeLine(models.Model):
	_name = "exam.grade.line"
	_description = 'Exam Subject Information'
	_rec_name = 'standard_id'

	standard_id = fields.Many2one('standard.standard', 'Class')
	exam_id = fields.Many2one('exam.result', 'Result')
	grade = fields.Char('Grade')


class ExamSubject(models.Model):
	_name = "exam.subject"
	_description = 'Exam Subject Information'
	_rec_name = 'subject_id'

	@api.constrains('obtain_marks', 'minimum_marks', 'maximum_marks',
					'marks_reeval')
	def _validate_marks(self):
		'''Method to validate marks'''
		if self.obtain_marks > self.maximum_marks:
			raise ValidationError(_('''The obtained marks
			should not extend maximum marks!.'''))
		if self.minimum_marks > self.maximum_marks:
			raise ValidationError(_('''The minimum marks
			should not extend maximum marks!.'''))
		if(self.marks_reeval > self.maximum_marks):
			raise ValidationError(_('''The revaluation marks
			should not extend maximum marks!.'''))


	@api.multi
	@api.depends('obtain_marks','marks_reeval')
	def _compute_percen(self):

		'''Method to compute percentage'''
		maximum_marks = 0.0
		obtained_total = 0.0
		obtain_marks = 0.0
		per = 0.0
		rev=0.0
		for sub_line in self:
			maximum_marks = sub_line.maximum_marks
			if sub_line.state == "re-evaluation":
				obtain_marks = sub_line.marks_reeval
				if maximum_marks > 1.0:
					rev = (obtain_marks / maximum_marks) * 100
					sub_line.percentage_line = rev

			else:
				obtain_marks = sub_line.obtain_marks
				if maximum_marks > 1.0:
					per = (obtain_marks / maximum_marks) * 100
					sub_line.percentage_line = per
			

	@api.multi
	@api.depends('exam_id', 'percentage_line')
	def _compute_grade(self):
		'''Method to compute grade after re-evaluation'''
		for rec in self:
			grade_lines = rec.exam_id.grade_system.grade_ids
			if (rec.exam_id and rec.exam_id.student_id and grade_lines):
				for grade_id in grade_lines:
					if rec.percentage_line and rec.percentage_line <= 0.0:
						b_id = rec.percentage_line <= grade_id.to_mark
						if (rec.percentage_line >= grade_id.from_mark and b_id):
							rec.grade_line_id = grade_id
					if rec.percentage_line and rec.percentage_line >= 0.0:
						r_id = rec.percentage_line <= grade_id.to_mark
						if (rec.percentage_line >= grade_id.from_mark and r_id):
							rec.grade_line_id = grade_id
				
	
	@api.multi
	@api.depends('grade_line_id')
	def _compute_results(self):
		'''Method to compute result'''
		for rec in self:
			flag = False
			if rec.percentage_line == 0.0:
				rec.result = 'Fail'
			else:
				if not rec.grade_line_id.fail:
					rec.result = 'Pass'
				else:
					rec.result = 'Fail'			

	exam_id = fields.Many2one('exam.result', 'Result')
	state = fields.Selection([('draft', 'Draft'), ('confirm', 'Confirm'),
							  ('re-evaluation', 'Re-Evaluation'),
							  ('re-evaluation_confirm',
							   'Re-Evaluation Confirm')],
							 related='exam_id.state', string="State")
	subject_id = fields.Many2one("subject.subject", "Subject Name")
	obtain_marks = fields.Float("Obtain Marks", group_operator="avg")
	minimum_marks = fields.Float("Minimum Marks",
								 help="Minimum Marks of subject")
	maximum_marks = fields.Float("Maximum Marks",
								 help="Maximum Marks of subject")
	marks_reeval = fields.Float("Marks After Re-Test",
								help="Marks Obtain after Re-evaluation")
	grade_line_id = fields.Many2one('grade.line', "Grade", compute='_compute_grade',store=True)
	result = fields.Char(compute='_compute_results', string='Result',
						 store=True) 
	attendance = fields.Boolean("Attendance", default=False)
	exam_date = fields.Date("Exam Date")
	percentage_line = fields.Float("Percentage", compute="_compute_percen",
							  store=True,
							  help="Percentage Obtained")
	percentage_line1 = fields.Float("Percentage Reval", compute="_compute_percen",store=True,
							  help="Percentage Obtained")
class AdditionalExamResult(models.Model):
	_name = 'additional.exam.result'
	_description = 'subject result Information'
	_rec_name = 'roll_no_id'

	@api.multi
	@api.depends('a_exam_id', 'obtain_marks')
	def _compute_student_result(self):
		'''Method to compute result of student'''
		for rec in self:
			if rec.a_exam_id and rec.a_exam_id:
				if rec.a_exam_id.minimum_marks < \
						rec.obtain_marks:
					rec.result = 'Pass'
				else:
					rec.result = 'Fail'

	@api.model
	def create(self, vals):
		'''Override create method to get roll no and standard'''
		student = self.env['student.student'].browse(vals.get('student_id'))
		vals.update({'roll_no_id': student.roll_no,
					 'standard_id': student.standard_id.id
					 })
		return super(AdditionalExamResult, self).create(vals)

	@api.multi
	def write(self, vals):
		'''Override write method to get roll no and standard'''
		student = self.env['student.student'].browse(vals.get('student_id'))
		vals.update({'roll_no_id': student.roll_no,
					 'standard_id': student.standard_id.id
					 })
		return super(AdditionalExamResult, self).write(vals)

	@api.onchange('student_id')
	def onchange_student(self):
		''' Method to get student roll no and standard by selecting student'''
		self.standard_id = self.student_id.standard_id.id
		self.roll_no_id = self.student_id.roll_no

	@api.constrains('obtain_marks')
	def _validate_obtain_marks(self):
		if self.obtain_marks > self.a_exam_id.subject_id.maximum_marks:
			raise ValidationError(_('''The obtained marks should not extend
									maximum marks!.'''))
		return True

	a_exam_id = fields.Many2one('additional.exam', 'Additional Examination',
								required=True,
								help="Select Additional Exam")
	student_id = fields.Many2one('student.student', 'Student Name',
								 required=True,
								 help="Select Student")
	roll_no_id = fields.Integer("Roll No",
								readonly=True)
	standard_id = fields.Many2one('school.standard',
								  "Class", readonly=True)
	obtain_marks = fields.Float('Obtain Marks', help="Marks obtain in exam")
	result = fields.Char(compute='_compute_student_result', string='Result',
						 help="Result Obtained", store=True)
