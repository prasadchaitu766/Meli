import time
import math
import pymssql

from odoo.osv import expression
from odoo.tools.float_utils import float_round as round
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import UserError, ValidationError
from odoo import api, fields, models, _
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
###############################################################################################################
# 										 MAIN CONNECTOR CLASS
###############################################################################################################
class connector(models.Model):
	_name = 'bi.connector.sqlserver'
	_rec_name = 'name'

	name = fields.Char(string='Connection name', required=True)
	db_name = fields.Char(string='Database Name', required=True)
	db_ip = fields.Char(string='Database IP', required=True)
	db_user = fields.Char(string='User', required=True)
	password = fields.Char(string='Pasword', required=True, password=True)
	db_port = fields.Char(string='Database port', required=True)
	last_server_pull_date = fields.Date(string="Last Server Pull Date")
	last_update_date = fields.Date(string="Last Update Date")
	last_update_id = fields.Integer(string="Last Update ID",readonly=True)

	def connect(self):
		conn = False		
		connector = self.env['bi.connector.sqlserver'].search([])
		conn = pymssql.connect(host=connector.db_ip, user=connector.db_user, password=connector.password, database=connector.db_name)		
		return conn

	def disconnect(self, conn):
		conn.close()

	
	@api.multi
	def selectView(self, cursor, view_name):
		cursor.execute('SELECT * FROM ' + view_name)
		return cursor
#################################################################################################################		
#function to get attendance data from database


	@api.multi
	def show_attendance(self):
		conn = self.env['bi.connector.sqlserver'].connect()
		cursor = conn.cursor(as_dict=True)
		details = self.env['bi.connector.sqlserver'].search([])
		for det in details:
			sql = '''SELECT att.AttendanceLogId,emp.EmployeeCode,emp.EmployeeName,att.AttendanceDate,emp.Team,
			att.InTime,att.OutTime,att.Duration,att.Status,att.PunchRecords,emp.UserType FROM Employees emp, AttendanceLogs att 
			where emp.EmployeeId=att.EmployeeId and emp.EmployeeName not like 'del_%' 
			and AttendanceDate>'''+"'"+det.last_server_pull_date+"'"+'''  and AttendanceDate<'''+"'"+fields.Date.context_today(self)+"'"+''' order by att.AttendanceLogId,att.AttendanceDate'''
			cursor.execute(sql)
			last_pull_date = False
			for result in cursor:				
				vals={'emp_code':str(result['EmployeeCode']),
					  'emp_name':result['EmployeeName'],
					  'att_date':result['AttendanceDate'],
					  'att_intime':result['InTime'] and result['InTime'] or False,
					  'att_outtime':result['OutTime'] and result['OutTime'] or False,
					  'att_dur':result['Duration'] and result['Duration'] or False,
					  'att_status':result['Status'].strip(),
					  'att_logid':result['AttendanceLogId'],
					  'att_punch':result['PunchRecords'],
					  'emp_team':result['Team'],
					  'user_type':result['UserType']
					  }
				last_pull_date = result['AttendanceDate']
				s=self.env['bi.attendance.sqlserver'].search([('emp_code', '=', str(result['EmployeeCode'])),('att_date', '=', result['AttendanceDate'])])
				if s:
					continue
				self.env['bi.attendance.sqlserver'].create(vals)
			if last_pull_date:
				det.write({'last_server_pull_date':last_pull_date})
		
		return cursor

#################################################################################################################		
#function to generate 


	@api.multi
	def generate_attendance(self):
		
		details = self.env['bi.connector.sqlserver'].search([])
		for conn in details:
			last_update_date = False
			last_update_id = False 
			for attendance  in self.env['bi.attendance.sqlserver'].search(['|',('att_status','ilike','Present'),('att_status','=','Absent'),('att_date','>',conn.last_update_date)]):
				employee = self.env['hr.employee'].search([('code','=',attendance.emp_code),('user_id.user_type','=','staff')])
				if not employee:
					student_obj = self.env['student.student']
					student_id = student_obj.search([('student_code','=',attendance.emp_code)])
					if not student_id:
						continue
					att_intime = datetime.strptime(attendance.att_intime, "%Y-%m-%d %H:%M:%S")
					att_outtime = datetime.strptime(attendance.att_outtime, "%Y-%m-%d %H:%M:%S")
					inyear = att_intime.year
					outyear = att_outtime.year				
					if inyear > 1900:
						att_intime -= timedelta(minutes = 330)
					else:
						att_intime = datetime.strptime(attendance.att_date+' 00:00:00', "%Y-%m-%d %H:%M:%S")
						att_intime -= timedelta(minutes = 330)				
					if outyear > 1900:
						att_outtime -= timedelta(minutes = 330)
					else:
						att_outtime = datetime.strptime(attendance.att_date+' 00:00:00', "%Y-%m-%d %H:%M:%S")
						att_outtime -= timedelta(minutes = 330)
					att_intime = att_intime.strftime("%Y-%m-%d %H:%M:%S")
					att_outtime = att_outtime.strftime("%Y-%m-%d %H:%M:%S")
					status = (attendance.att_status.strip()).replace(u'\xc2\xbd', u'1/2')
					status = (attendance.att_status.strip()).replace(u'\xbd', u'1/2')
					standard_id = student_id.standard_id
					attendance_obj = self.env['daily.attendance']
					attendances =attendance_obj.search([('standard_id','=',standard_id.id),('date','=',attendance.att_date)])
					if not attendances and attendance.att_status =='Present':
						val={
							'standard_id':standard_id.id,
							'date':attendance.att_date,
							'school_id':standard_id.school_id.id,
							}
						res=attendance_obj.create(val)
						if res:
							student_list = []
							stud_ids = student_obj.search([('standard_id', '=',standard_id.id),('state', '=', 'done')])
							for stud in stud_ids:
								student_list.append({'roll_no': stud.roll_no,
													 'stud_id': stud.id,
													 'check_in':att_intime,
													 'check_out':att_outtime ,
													 'is_absent': True,})
						res.student_ids = student_list

					if attendance.att_status =='Present':
						attendances =attendance_obj.search([('standard_id','=',standard_id.id),('date','=',attendance.att_date)],limit=1)
						attendance_line=self.env['daily.attendance.line'].search([('standard_id','=',attendances.id),('stud_id','=',student_id.id)])
						fff=attendance_line.write({'is_present': True,'is_absent':False})

					
				else:
					att_intime = datetime.strptime(attendance.att_intime, "%Y-%m-%d %H:%M:%S")
					att_outtime = datetime.strptime(attendance.att_outtime, "%Y-%m-%d %H:%M:%S")
					inyear = att_intime.year
					outyear = att_outtime.year				
					if inyear > 1900:
						att_intime -= timedelta(minutes = 330)
					else:
						att_intime = datetime.strptime(attendance.att_date+' 00:00:00', "%Y-%m-%d %H:%M:%S")
						att_intime -= timedelta(minutes = 330)				
					if outyear > 1900:
						att_outtime -= timedelta(minutes = 330)
					else:
						att_outtime = datetime.strptime(attendance.att_date+' 00:00:00', "%Y-%m-%d %H:%M:%S")
						att_outtime -= timedelta(minutes = 330)
					att_intime = att_intime.strftime("%Y-%m-%d %H:%M:%S")
					att_outtime = att_outtime.strftime("%Y-%m-%d %H:%M:%S")
					status = (attendance.att_status.strip()).replace(u'\xc2\xbd', u'1/2')
					status = (attendance.att_status.strip()).replace(u'\xbd', u'1/2')
					vals = {'employee_id':employee.id,
							'check_in':att_intime,
							'check_out':att_outtime ,
							'att_punch':attendance.att_punch,
							'att_status':status,
							'att_date': attendance.att_date,
							'att_dur': attendance.att_dur,
							'user_type': attendance.user_type
							}
					s=self.env['hr.attendance'].search([('employee_id', '=', employee.id),('att_date', '=', attendance.att_date)])
					if s:
						continue
					ss=self.env['hr.attendance'].create(vals)
				last_update_date = attendance.att_date
				last_update_id = attendance.att_logid 
			
			if last_update_date and last_update_id:
				conn.write({'last_update_date':last_update_date,'last_update_id':last_update_id})
	
	@api.multi
	def generate_all(self):
		self.show_attendance()
		self.generate_attendance()
		
	@api.multi
	def unlink(self):
		for order in self:
			raise UserError(_('Permission Denied'))
		return super(connector, self).unlink()	



###############################################################################################################
#
###############################################################################################################
class bi_attendance(models.Model):
	_name = 'bi.attendance.sqlserver'
	_rec_name = 'emp_code'
	_order = 'att_date'

	emp_code = fields.Char(string='Employee Code', required=True)
	emp_name = fields.Char(string='Employee Name', required=True)
	att_date = fields.Date(string='Attendance Date', required=True)
	att_intime = fields.Datetime(string='InTime', required=False)
	att_outtime = fields.Datetime(string='OutTime', required=False)
	att_dur = fields.Char(string='Duration', required=False)
	att_status = fields.Char(string='Status', required=True)
	att_logid = fields.Integer(string='Log ID', required=True)
	att_punch = fields.Char(string='Punch Details', size=500, required=False)
	emp_team = fields.Char(string='Team')
	user_type = fields.Char(string='User Type')
	@api.multi
	def unlink(self):
		for order in self:
			raise UserError(_('Permission Denied'))
		return super(bi_attendance, self).unlink()

################################################################################################################
#                     			 INHERIT HR.EMPLOYEE CLASS
################################################################################################################		


class HrEmployee(models.Model):
	_inherit = 'hr.employee'

	code = fields.Char(string="Code")


################################################################################################################
#								INHERIT HR.ATTENDANCE CLASS
################################################################################################################


class HrAttendance(models.Model):
	
	_inherit = "hr.attendance"

	att_punch = fields.Char(string='Punch Details', size=500, required=False, readonly=True)
	att_status = fields.Selection([('1/2Present', '1/2Present'),
									('Present', 'Present'),
									('WeeklyOff  1/2Present','WeeklyOff  1/2Present'),
									('WeeklyOff Present','WeeklyOff Present'),
									('Holiday  1/2Present','Holiday  1/2Present'),
									('Holiday Present','Holiday Present'),
									('Absent','Absent'),
									('Present  On OD','Present  On OD'),
									('WeeklyOff Present  On OD','WeeklyOff Present  On OD')
									],string='Status')
	att_date = fields.Date(string='Attendance Date',default = datetime.today())
	att_dur = fields.Float(string='Duration')
	company_id = fields.Many2one('res.company', related='employee_id.company_id',store=True)
	user_type = fields.Char(string='User Type')

	# @api.one 
	# @api.depends('check_in','check_out')
	# def _total_minutes(self):
	# 	difference=float()
	# 	if self.check_in and self.check_out:
	# 		check_in = fields.Datetime.from_string(self.check_in)
	# 		check_out = fields.Datetime.from_string(self.check_out)
	# 		difference = relativedelta(check_out, check_in)
	# 		days = difference.days
	# 		hours = difference.hours
	# 		minutes = difference.minutes
	# 		seconds = 0
	# 	self.update({
	# 				'att_dur': difference
	# 				   })
	  


	
###############################################################################################################	