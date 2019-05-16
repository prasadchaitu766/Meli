# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class HrRecruitmentInherit(models.Model):
	_inherit = "hr.recruitment.stage"


	interviewer_name = fields.Many2one('hr.employee', string="Interviewer Name")
	interviewer_designation = fields.Char(string="Interviewer Designation")



	@api.onchange('interviewer_name')
	def get_interviewer_designation(self):
		if self.interviewer_name.name == False:
			self.interviewer_designation = False
		else:
			self.interviewer_designation = self.interviewer_name.job_id.name
			