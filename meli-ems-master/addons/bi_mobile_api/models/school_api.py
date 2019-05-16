# -*- coding: utf-8 -*-
#################################################################################
# Author      : Acespritech Solutions Pvt. Ltd. (<www.acespritech.com>)
# Copyright(c): 2012-Present Acespritech Solutions Pvt. Ltd.
# All Rights Reserved.
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
# Please see LICENSE file.
#################################################################################
from odoo import models, fields, api, _
import re
from openerp.exceptions import UserError
import json
from datetime import date, datetime,timedelta
from passlib.context import CryptContext
import logging
_logger = logging.getLogger(__name__)

class SchoolApi(models.Model):
	_name = 'school.api'

	@api.model
	def get_campus_info(self):
		school_obj=self.env['school.school']
		school_data = school_obj.search([])
		data=[]
		for school in school_data:
			vals={
			'campus_id' : school.id,
			'campus_code' : school.code,
			'campus_name' : school.name,
			}
			data.append(vals)
		res=json.dumps({'data':data})
		return [res]

	#2.Login API
	@api.model
	def get_student_info(self,mobile,password):
		_logger.warning('The password got from mobile app (%s) The mobile number (%s)',password,mobile)
		data=[]
		student_obj=self.env['student.student']
		user_obj=self.env['res.users']	
		student_data = student_obj.search([('mobile','=',mobile)])
		users=user_obj.search([('login','=',mobile)])
		if student_data:
			for student in student_data:
				password_crypt=student.user_id.password_crypt
				x=CryptContext(['pbkdf2_sha512']).verify(password, password_crypt)
				_logger.warning('X value (%s)',x)		
				if x == True:
					if student.student_code:
						vals={
						'student_id' : student.id,
						'student_code' : student.student_code,
						'student_name' : student.name,
						'school_id' : student.school_id.id,
						'standard_id' : student.standard_id.id,
						'status':'registered user',
						}
					else:
						vals={
						'student_id' : student.id,
						'application_no' : student.pid,
						'student_name' : student.name,
						'school_id' : student.school_id.id,
						'standard_id' : student.standard_id.id,
						'status':'applied user',
						}
					data.append(vals)
		elif users:
			for user in users:
				passd= user.password_crypt
				x=CryptContext(['pbkdf2_sha512']).verify(password, passd)		

				if x:
					student=student_obj.search([('user_id','=',user.id)])
					if student.student_code:
						vals={
						'student_id' : student.id,
						'student_code' : student.student_code,
						'student_name' : student.name,
						'school_id' : student.school_id.id,
						'standard_id' : student.standard_id.id,
						'status':'registered user',
						}
					else:
						vals={
						'student_id' : student.id,
						'application_no' : student.pid,
						'student_name' : student.name,
						'school_id' : student.school_id.id,
						'standard_id' : student.standard_id.id,
						'status':'applied user',
						}
					data.append(vals)
		if not data:
			enquiry=self.env['website.support.ticket'].search([('mobile','=',mobile),('pwd','=',password)])
			for student in enquiry:
				vals={
					'enquiry_no' : student.ticket_number,
					'name' : student.first_name,
					'last_name' : student.last_name,
					'school_id' : student.school_id.id,
					'course' : student.program_id.id,
					'status':'new user',
					}
				data.append(vals)
		res=json.dumps({'data':data})
		return [res]


	#1.Register API
	@api.model
	def create_new_registration(self,first_name,last_name,program_id,school_id,email,nid,parent_id,date_of_birth,gender,grandparent_id,maritual_status,mobile,pwd):
		ticket_obj=self.env['website.support.ticket']
		vals={
		'first_name':first_name,
		'last_name':last_name,
		'program_id':program_id,
		'school_id':school_id,
		'email':email,
		'nid':nid,
		'parent_id':parent_id,
		'date_of_birth':date_of_birth,
		'gender':gender,
		'grandparent_id':grandparent_id,
		'maritual_status':maritual_status,
		'mobile':mobile,
		'pwd':pwd,
		}
		res=ticket_obj.create(vals)
		return True

	#4.Courses API
	@api.model
	def get_course_info(self):
		course_obj=self.env['standard.standard']
		course_data = course_obj.search([])
		data=[]
		for course in course_data:
			vals={
			'course_id' : course.id,
			'code' : course.code,
			'name' : course.name,
			'description' : course.description,
			}
			data.append(vals)
		res=json.dumps({'data':data})
		return [res]

	#7.View attendance API
	@api.model
	def view_attendance(self,student_id,start_date,end_date):
		attendance_obj=self.env['daily.attendance.line']
		attendance_data = attendance_obj.search([('stud_id','=',student_id),('standard_id.date','>=',start_date),('standard_id.date','<=',end_date)])
		data=[]
		for attendance in attendance_data:

			att_data = self.env['time.table'].search([('school_id','=',attendance.standard_id.school_id.id),('standard_id','=',attendance.standard_id.standard_id.id),('timetable_type','=','regular')],limit=1)
			a_date=datetime.strptime(attendance.standard_id.date,'%Y-%m-%d')
			current_day=a_date.weekday()
			if current_day == 0:
				domain = [
					  ('table_id', '=', att_data.id),
					  ('week_day', '=', 'monday'),
				  ]
			elif current_day == 1:
				domain = [
					  ('table_id', '=', att_data.id),
					  ('week_day', '=', 'tuesday'),
				  ]
			elif current_day == 2:
				domain = [
					('table_id', '=', att_data.id),
					('week_day', '=', 'wednesday'),
				  ]
			elif current_day == 3:
				domain = [
					  ('table_id', '=', att_data.id),
					  ('week_day', '=', 'thursday'),
				  ]
			elif current_day == 4:
				domain = [
					  ('table_id', '=', att_data.id),
					  ('week_day', '=', 'friday'),
				  ]
			elif current_day == 5:
				domain = [
					  ('table_id', '=', att_data.id),
					  ('week_day', '=', 'saturday'),
				  ]
			else:
				domain = [
					  ('table_id', '=', att_data.id),
					  ('week_day', '=', 'sunday'),
				  ]
			time_table_line_id=self.env['time.table.line'].search(domain,limit=1)
			vals={
			'status' : attendance.is_present,
			'date' : attendance.standard_id.date,
			'class' : attendance.standard_id.standard_id.id,
			'campus' : attendance.standard_id.school_id.name,
			'time_from':attendance.standard_id.standard_id.medium_id.hour_from,
			'time_to':attendance.standard_id.standard_id.medium_id.hour_to,
			'subject_name':time_table_line_id.subject_id.name,
			}
			data.append(vals)
		res=json.dumps({'data':data})
		return [res]

	#8.View Timetable API
	@api.model
	def view_timetable(self,student_id):
		student_id = self.env['student.student'].search([('id','=',student_id)])
		timetable_obj=self.env['time.table']
		timetable = timetable_obj.search([('standard_id','=',student_id.standard_id.id),('school_id','=',student_id.school_id.id)],limit=1)
		line_obj=self.env['time.table.line']
		timetable_line=line_obj.search([('table_id','=',timetable.id)])
		data=[]
		for line in timetable_line:
			vals={
			'day' : line.week_day,
			'start_time' : line.start_time,
			'end_time' : line.end_time,
			'subject_id' : line.subject_id.id,
			'teacher_id' : line.teacher_id.id,
			'subject_name' : line.subject_id.name,
			'teacher_name' : line.teacher_id.name,
			}
			data.append(vals)
		res=json.dumps({'data':data})
		return [res]

	#9.Student Reminders API
	@api.model
	def student_reminders(self,student_id):
		reminder_obj=self.env['student.reminder']
		current_dt = date.today()
		current_month=current_dt.month
		start_date=current_dt.replace(day=1)
		start_date=datetime.strftime(start_date, "%Y-%m-%d 00:00")
		end_date_1=current_dt.replace(month=current_month+1,day=1)
		end_date=end_date_1-timedelta(days=1)
		end_date=datetime.strftime(end_date, "%Y-%m-%d 23:59")
		reminder_data = reminder_obj.search([('stu_id','=',student_id),('date','<=',end_date),('date','>=',start_date)])
		reminder_data = reminder_obj.search([('stu_id','=',student_id)])
		data=[]
		for line in reminder_data:
			vals={
			'date' : line.date,
			'title' : line.name,
			'description' : line.description,
			}
			data.append(vals)
		res=json.dumps({'data':data})
		return [res]


	#9.Student Warning API
	@api.model
	def student_warning(self,student_id):
		warning_obj=self.env['student.warning']
		warning_data = warning_obj.search([('student_id','=',student_id)])
		data=[]
		for line in warning_data:
			vals={
			'date' : line.date,
			'warning_message' : line.name,
			}
			data.append(vals)
		res=json.dumps({'data':data})
		raise UserError(str(res))
		return [res]

	#10.Fees paid API
	@api.model
	def student_fee(self,student_id):
		fee_obj=self.env['student.payslip']
		student_fee = fee_obj.search([('student_id','=',student_id)])
		data=[]
		for fee in student_fee:
			vals={
			'course_id' : fee.student_id.program_id.id,
			'course_name' : fee.student_id.program_id.name,
			'amount' : fee.total,
			'status' : fee.state,
			'date' : fee.date,
			}
			data.append(vals)
		res=json.dumps({'data':data})
		return [res]

	#16. Leave request API
	@api.model
	def leave_request(self,name,student_id,reason,end_date,start_date):
		stud_obj=self.env['student.student']
		student_id=stud_obj.search([('id','=',student_id)])
		leave_obj=self.env['studentleave.request']
		if student_id:
			vals={
			'name' :'name',
			'reason' :reason,
			'student_id' :student_id.id,
			'start_date':start_date,
			'end_date':end_date,
			'type':'remove'
			}
			res=leave_obj.create(vals)
			return True


	#17.Leave List API
	@api.model
	def leave_list(self,student_id):
		leave_obj=self.env['studentleave.request']
		leave_list=leave_obj.search([('student_id','=',student_id)])
		data=[]
		for leave in leave_list:
			vals={
				'from_date':leave.start_date,
				'to_date':leave.end_date,
				'status':leave.state,
				'reason':leave.reason,
							}
			data.append(vals)
		res=json.dumps({'data':data})
		return [res]

	#18.Transfer request API
	@api.model
	def transfer_request(self,student_id,reason,to_campus,class_id,shift_id,from_campus):
		stud_obj=self.env['student.student']
		student_id=stud_obj.search([('id','=',student_id)])
		transfer_obj=self.env['student.transfer']
		if student_id:
			vals={
			'reason' :reason,
			'student_name' :student_id.id,
			'school_id':to_campus,
			'standard_id':class_id,
			'medium_id':shift_id,
			'from_campus':student_id.school_id.id,
			}
			res=transfer_obj.create(vals)
			return True

	#19. View Transfer request  API

	@api.model
	def view_transfer_details(self,student_id):
		transfer_obj=self.env['student.transfer']
		transfer_list=transfer_obj.search([('student_name','=',student_id)])
		data=[]
		for line in transfer_list:
			vals={
				'from_campus':line.from_campus.id,
				'from_campus_name':line.from_campus.name,
				'to_campus':line.school_id.id,
				'to_campus_name':line.school_id.name,
				'status':line.state,
				'date':line.date,
							}
			rows = ",".join(str(vals[x]) for x in vals)				
			_logger.warning('The data from mobile app (%s)',rows)				
							
			data.append(vals)
		res=json.dumps({'data':data})
		return [res]

	# 20.   API

	@api.model
	def register_attendance(self,student_id,status,date):
		student_obj = self.env['student.student']
		student_id = student_obj.search([('student_code','=',student_id)])
		standard_id = student_id.standard_id
		attendance_obj = self.env['daily.attendance']
		attendance =attendance_obj.search([('standard_id','=',standard_id.id),('date','=',date)])
		if not attendance and status == True:
			vals={
				'standard_id':standard_id.id,
				'date':date,
				'school_id':standard_id.school_id.id,
				}
			res=attendance_obj.create(vals)
			if res:
				student_list = []
				stud_ids = student_obj.search([('standard_id', '=',standard_id.id),('state', '=', 'done')])
				for stud in stud_ids:
					student_list.append({'roll_no': stud.roll_no,
										 'photo':stud.photo,
										 'stud_id': stud.id,
										 'is_absent': True,})
			res.student_ids = student_list
		if status == True:
			attendance =attendance_obj.search([('standard_id','=',standard_id.id),('date','=',date)],limit=1)
			attendance_line=self.env['daily.attendance.line'].search([('standard_id','=',attendance.id),('stud_id','=',student_id.id)])
			attendance_line.write({'is_present': True,'is_absent':False})
		return True



	#.class API
	@api.model
	def get_class_info(self):
		class_obj=self.env['school.standard']
		class_data = class_obj.search([('state','in',('running','new'))])
		datas=[]
		for data in class_data:
			vals={
			'class_name':data.standard,
			'course_id' : data.standard_id.id,
			'campus' : data.school_id.id,
			'course_level' : data.semester_id.id,
			'shift' : data.medium_id.id,
			'room_no' : data.division_id.id,
			'start_date' : data.start_date,
			'end_date' : data.start_date,

			}
			datas.append(vals)
		res=json.dumps({'data':datas})
		return [res]

	@api.model
	def view_exam_timetable(self,student_id,start_date,end_date):
		student_id = self.env['student.student'].search([('id','=',student_id)])
		timetable_obj=self.env['time.table']
		timetable = timetable_obj.search([('standard_id','=',student_id.standard_id.id),('school_id','=',student_id.school_id.id),('timetable_type','=','exam'),('state','=','draft')],limit=1)
		line_obj=self.env['time.table.line']
		timetable_line=line_obj.search([('table_id','=',timetable.id),('exm_date','>=',start_date),('exm_date','<=',end_date)])
		data=[]
		for line in timetable_line:
			vals={
			'date':line.exm_date,
			'day' : line.day_of_week,
			'start_time' : line.start_time,
			'end_time' : line.end_time,
			'subject_id' : line.subject_id.id,
			'teacher_id' : line.teacher_id.id,
			'subject_name' : line.subject_id.name,
			'teacher_name' : line.teacher_id.name,
			}
			data.append(vals)
		res=json.dumps({'data':data})
		return [res]

	#.shift API
	@api.model
	def get_shift_info(self):
		shift_data=self.env['standard.medium'].search([])
		datas=[]
		for data in shift_data:
			vals={
			'shift_id' : data.id,
			'name' : data.name,
			'code' : data.code,
			'hour_from' : data.hour_from,
			'hour_to' : data.hour_to,
			'description' : data.description,
			}
			datas.append(vals)
		res=json.dumps({'data':datas})
		return [res]

	#Reset Password
	@api.model
	def reset_password(self,student_id,old_password,new_password,confirm_password):
		data=[]
		if new_password == confirm_password:
			student_id = self.env['student.student'].browse(student_id)
			password_crypt=student_id.user_id.password_crypt
			x=CryptContext(['pbkdf2_sha512']).verify(old_password, password_crypt)	
			if x:
				student_id.user_id.write({'password':new_password})
		return True

	@api.model
	def get_exam_result(self,student_id):
		datas=[]
		exam_id=self.env['exam.result'].search([('student_id','=',student_id)])
		for exam in exam_id:
			exam_result_id=self.env['exam.subject'].search([('exam_id','=',exam.id)])
			for data in exam_result_id:
				vals={
				'standard' : data.exam_id.standard_id.name,
				'exam_date' : data.exam_date,
				'subject_id' : data.subject_id.name,
				'obtained_mark' : data.obtain_marks,
				'result' : data.exam_id.result,
				}
				datas.append(vals)
		res=json.dumps({'data':datas})
		return [res]


# class SchoolSchool(models.Model):
# 	_inherit = 'school.school'

# 	@api.multi
# 	def write(self, vals):
# 		timetable_obj=self.env['school.api']
# 		student_id=1 #id
# 		# student_id=1
# 		# start_date='2018-08-1' #date
# 		# end_date='2018-09-25'
# 		# no='589589'
# 		# password='11'
# 		# xx=timetable_obj.get_student_info(no,password)
# 		timetable_obj.view_transfer_details(self)
# 		return super(SchoolSchool,self).write(vals)