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



class StudentStudent(models.Model):
	''' Defining a student information '''
	_inherit = 'student.student'

	ticket_number = fields.Many2one('website.support.ticket',string="Enq. Number")

	@api.onchange('ticket_number')
	def _ticket_number(self):
		if self.ticket_number:
			# raise UserError(str(self.same_address))
			self.name = self.ticket_number.first_name
			self.last = self.ticket_number.last_name
			self.school_id = self.ticket_number.school_id.id
			self.program_id = self.ticket_number.program_id.id
			self.nid = self.ticket_number.nid
			self.email = self.ticket_number.email
			self.parent_id = self.ticket_number.parent_id
			self.grandparent_id = self.ticket_number.grandparent_id
			self.gender = self.ticket_number.gender
			self.age = self.ticket_number.age
			self.date_of_birth = self.ticket_number.date_of_birth
			self.maritual_status = self.ticket_number.maritual_status
			self.occupation = self.ticket_number.occupation
			self.mobile = self.ticket_number.mobile
			self.pwd = self.ticket_number.pwd
			
	@api.model
	def create(self, vals):
		res = super(StudentStudent, self).create(vals)
		if res.ticket_number:
			res.ticket_number.button_admit()
		return res

