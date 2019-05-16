# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

import time
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, Warning as UserError
from datetime import datetime


class SchoolWarning(models.Model):
	''' Defining a Teacher information '''
	_name = 'student.warning'
	_description = 'Warning Message'
	_order = "date desc"

	student_id = fields.Many2one('student.student','Student Name')
	name = fields.Text("Warning Message", required=True)
	state = fields.Selection([('draft', 'Draft'), ('confirm', 'Confirm')],
							 'State', readonly=True, default='draft')
	date = fields.Date('Date', required=True,
					   help="Date of Warning",
					   default=lambda * a: time.strftime('%Y-%m-%d'))
	roll_no = fields.Char(string="Roll Number")
	standard_id = fields.Many2one('school.standard', string="Class")


	@api.onchange('student_id')
	def onchange_student(self):
		'''Method to get standard and roll no of student selected'''
		if self.student_id:
			self.standard_id = self.student_id.standard_id.id
			self.roll_no = self.student_id.roll_no

	@api.multi
	def warning_confirm(self):
		'''Method to change state to done'''
		self.write({'state': 'confirm'})


	@api.multi
	def unlink(self):
		for rec in self:
			if rec.state !='draft':
				raise ValidationError(_('''You can delete the entry only in draft state !'''))
		return super(SchoolWarning, self).unlink()

