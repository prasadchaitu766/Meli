# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, Warning as UserError
import re

class TimeTable(models.Model):
	_description = 'Time Table'
	_name = 'time.table'
	_order = 'id desc'

	@api.multi
	@api.depends('timetable_ids')
	def _compute_user(self):
		'''Method to compute user'''
		for rec in self:
			rec.user_ids = [teacher.teacher_id.employee_id.user_id.id
							for teacher in rec.timetable_ids
							]
		return True

	@api.onchange('medium_id')
	def onchange_medium_id(self):
		if self.timetable_type=='regular' and self.medium_id:
			for line in self.timetable_ids:
				line.start_time = self.medium_id.hour_from
				line.end_time = self.medium_id.hour_to
				
   
	name = fields.Char('Description')
	school_id = fields.Many2one('school.school', 'Campus',required=True ,store=True)
	standard_id = fields.Many2one('school.standard', 'Class',
								  required=True,
								  help="Select Standard")
	medium_id = fields.Many2one('standard.medium', 'Shift',
								  required=True,
								  help="Select Standard")
	semester_id = fields.Many2one('standard.semester', 'Semester')
	division_id = fields.Many2one('standard.division', 'Room Number')
	year_id = fields.Many2one('academic.year', 'Year',
							  help="select academic year")
	timetable_ids = fields.One2many('time.table.line', 'table_id', 'TimeTable')
	timetable_type = fields.Selection([('regular', 'Regular')],
									  'Time Table Type', default="regular",
									  inivisible=True)
	user_ids = fields.Many2many('res.users', string="Users",
								compute="_compute_user", store=True)
	class_room_id = fields.Many2one('class.room', 'Room Number')
	state = fields.Selection([
		('draft', 'New'),
		('finish', 'Finished'),
	], string='Status', track_visibility='onchange', help='Status of the contract', default='draft')

	@api.multi
	@api.constrains('timetable_ids')
	def _check_lecture(self):
		'''Method to check same lecture is not assigned on same day'''
		if self.timetable_type == 'regular':
			domain = [('table_id', 'in', self.ids)]
			line_ids = self.env['time.table.line'].search(domain)
			for rec in line_ids:
				records = [rec_check.id for rec_check in line_ids
						   if (rec.week_day == rec_check.week_day and
							   rec.start_time == rec_check.start_time and
							   rec.end_time == rec_check.end_time and
							   rec.teacher_id.id == rec.teacher_id.id)]
							   # rec.table_id.standard_id.id == rec.table_id.standard_id.id)]

				if len(records) > 1:
					raise ValidationError(_('''You cannot set lecture at same
											time %s  at same day %s for teacher
											%s..!''') % (rec.start_time,
														 rec.week_day,
														 rec.teacher_id.name))
				# Checks if time is greater than 24 hours than raise error
				if rec.start_time > 24:
					raise ValidationError(_('''Start Time should be less than
											24 hours!'''))
				if rec.end_time > 24:
					raise ValidationError(_('''End Time should be less than
											24 hours!'''))

				timetable_rec = self.env['time.table'].search([('id', '!=',
														rec.table_id.id)])

				if timetable_rec:
					for data in timetable_rec:
						for record in data.timetable_ids:
							# raise UserError(str(record.standard_id))
							if (data.timetable_type == 'regular' and
									rec.table_id.timetable_type == 'regular' and
									rec.teacher_id == record.teacher_id and
									rec.week_day == record.week_day and
									rec.start_time == record.start_time and
									rec.standard_id == record.standard_id.id):
									raise ValidationError(_('''There is a lecture of
									Lecturer at same time!'''))
							if (data.timetable_type == 'regular' and
									rec.table_id.timetable_type == 'regular' and
									rec.class_room_id == record.class_room_id and
									rec.teacher_id == record.teacher_id and
									rec.start_time == record.start_time):
									raise ValidationError(_("The room is occupied."))
			return True


class TimeTableLine(models.Model):
	_description = 'Time Table Line'
	_name = 'time.table.line'
	_rec_name = 'table_id'

	
	teacher_id = fields.Many2one('school.teacher', 'Faculty Name',
								 help="Select Teacher")
	subject_id = fields.Many2one('subject.subject', 'Subject Name',
								 help="Select Subject")
	table_id = fields.Many2one('time.table', 'TimeTable')

	start_time = fields.Float('Start Time', 
							  help="Time according to timeformat of 24 hours")
	end_time = fields.Float('End Time', 
							help="Time according to timeformat of 24 hours")
	week_day = fields.Selection([('monday', 'Monday'),
								 ('tuesday', 'Tuesday'),
								 ('wednesday', 'Wednesday'),
								 ('thursday', 'Thursday'),
								 ('friday', 'Friday'),
								 ('saturday', 'Saturday'),
								 ('sunday', 'Sunday')], "Week day",)
	class_room_id = fields.Many2one('class.room', 'Room Number')
	school_id = fields.Many2one('school.school', 'Campus',related='table_id.school_id')
	medium_id = fields.Many2one('standard.medium', 'Shift', related='table_id.medium_id')
	standard_id = fields.Many2one('school.standard', 'Class',related='table_id.standard_id')

	time_start = fields.Char("Start Time")
	time_end = fields.Char("End Time")

	@api.onchange('start_time','end_time')
	def _onchange_time(self):
		time_from = ''
		time_to = ''
		if self.start_time:
			time_from = '{0:02.0f}:{1:02.0f}'.format(*divmod(self.hour_from * 60, 60))
			self.time_start = time_from		
		if self.end_time:	
			time_to = '{0:02.0f}:{1:02.0f}'.format(*divmod(self.hour_to * 60, 60))
			self.time_end = time_to

	@api.onchange('time_start', 'time_end')
	def _onchange_time(self):
		time_from = ''
		time_to = ''
		if self.time_start:
			t_f = self._convert_time(self.time_start)
			time_from = re.findall('\d+', t_f)
			if len(time_from) != 2:
				self.start_time = float(time_from[0])
			else:
				hours = int(time_from[0])
				minutes = int(time_from[1])
				self.start_time = float(hours) + float(float(minutes)/60)
		if self.time_end:
			t_h = self._convert_time(self.time_end)
			time_to = re.findall('\d+', t_h)
			if len(time_to) != 2:
				self.end_time = float(time_to)
			else:
				hours = int(time_to[0])
				minutes = int(time_to[1])
				self.end_time = float(hours) + float(float(minutes) / 60)

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
			

	

class SubjectSubject(models.Model):
	_inherit = "subject.subject"

	@api.model
	def _search(self, args, offset=0, limit=None, order=None, count=False,
				access_rights_uid=None):
		'''Override method to get subject related to teacher'''
		teacher_id = self._context.get('teacher_id')
		if teacher_id:
			for teacher_data in self.env['school.teacher'].browse(teacher_id):
				args.append(('teacher_ids', 'in', [teacher_data.id]))
		return super(SubjectSubject, self)._search(
			args=args, offset=offset, limit=limit, order=order, count=count,
			access_rights_uid=access_rights_uid)
