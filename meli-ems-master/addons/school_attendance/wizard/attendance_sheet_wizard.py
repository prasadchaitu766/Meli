# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api
from odoo.exceptions import Warning as UserError
from datetime import datetime
import calendar
from datetime import datetime, timedelta



class MonthlyAttendanceSheet(models.TransientModel):
	'''For Monthly Attendance Sheet'''
	_name = "monthly.attendance.sheet"
	_description = "Monthly Attendance Sheet Wizard"

	standard_id = fields.Many2one('school.standard', 'Academic Class',
								  compute='_compute_standard_id')
	year_id = fields.Many2one('academic.year', 'Year')
	date_start = fields.Date('Start Date')
	date_stop = fields.Date('End Date')
	month_id = fields.Date('Month')
	is_running = fields.Boolean(string='Inactive')
	run_standard_id = fields.Many2one('school.standard','Academic Class')
	close_standard_id = fields.Many2one('school.standard','Academic Class')

	@api.onchange('standard_id')
	def onchange_standard_id(self):
		'''Method to get standard and roll no of student selected'''
		if self.standard_id:
			self.date_start = self.standard_id.start_date
			self.date_stop = self.standard_id.end_date

	# @api.onchange('run_standard_id')
	# def onchange_run_standard_id(self):		
	# 	if self.run_standard_id:
	# 		self.date_start = self.run_standard_id.start_date
	# 		self.date_stop = self.run_standard_id.end_date	

	# @api.onchange('close_standard_id')
	# def onchange_close_standard_id(self):			
	# 	if self.close_standard_id:
	# 		self.date_start = self.close_standard_id.start_date
	# 		self.date_stop = self.close_standard_id.end_date	
	
	@api.multi
	@api.depends('run_standard_id', 'close_standard_id')
	def _compute_standard_id(self):
		for rec in self:
			if self.run_standard_id:
				rec.standard_id =self.run_standard_id
			elif self.close_standard_id:	
				rec.standard_id = self.close_standard_id.id
		
	@api.multi
	def monthly_attendance_sheet_open_window(self):
		''' This method open new window with monthly attendance sheet
			@param self : Object Pointer
			@param cr : Database Cursor
			@param uid : Current Logged in User
			@param ids : Current Records
			@param context : standard Dictionary
			@return : record of monthly attendance sheet
		'''
		data = self.read([])[0]
		date_start=self.date_start
		date_stop=self.date_stop
		start_month = datetime.strptime(date_start, '%Y-%m-%d').month
		crnt_year = datetime.strptime(date_start, '%Y-%m-%d').year
		crnt_day = datetime.strptime(date_start, '%Y-%m-%d').day
		end_month = datetime.strptime(date_stop, '%Y-%m-%d').month
		crnt_year1 = datetime.strptime(date_stop, '%Y-%m-%d').year
		crnt_day1 = datetime.strptime(date_stop, '%Y-%m-%d').day
		crnt_date = datetime.strptime(date_start, '%Y-%m-%d')
		context = {'start_date': date_start,
				   'end_date': date_stop}
		# raise UserError(str(context))			   
		models_data = self.env['ir.model.data']
		# Get opportunity views
		dummy, form_view = models_data.\
			get_object_reference('school_attendance',
								 'view_attendance_sheet_form')
		dummy, tree_view = models_data.\
			get_object_reference('school_attendance',
								 'view_attendance_sheet_tree')
		return {'view_type': 'form',
				'view_mode': 'tree, form',
				'res_model': 'attendance.sheet',
				'view_id': False,
				'domain': [('standard_id', '=', data['standard_id'][0]),
						   ('month_id', '>=',start_month),
						   ('month_id', '<=',end_month)
						  ],
				'context': context,
				'views': [(tree_view or False, 'tree'),
						  (form_view or False, 'form')],
				'type': 'ir.actions.act_window'}
