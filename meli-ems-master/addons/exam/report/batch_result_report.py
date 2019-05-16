# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

from odoo import models, api
from odoo.exceptions import UserError


class BatchExamReport(models.AbstractModel):
	_name = 'report.exam.exam_result_batch'

	@api.multi
	def pass_student(self, standard_id):
		'''Method to determine students who pass the exam'''
		# exam = self.env['exam.exam'].search([('standard_id', '=',
											  # standard_id.id),
		# 									 # ('academic_year', '=', year.id),
											 # ('state', '=', 'finished')])
		exam_obj = self.env['exam.result'].search([('standard_id', '=',standard_id.id)])
		for rec in exam_obj:
			# exam_result = rec.search([('s_exam_ids', '=', rec.id),
			# 							   ('state', '!=', 'draft')])
			exam_result_pass = rec.search([('standard_id', '=',standard_id.id),('result', '=', 'Pass'),('state', '!=', 'draft')])
			exam_result_fail = rec.search([('standard_id', '=',standard_id.id),('result', '=', 'Fail'),('state', '!=', 'draft')])
			student_appear = len(exam_result_pass.ids) + len(exam_result_fail.ids)
			std_pass = ''
			if len(exam_result_pass.ids) > 0:
			# 	# Calculate percentage of students who pass the exams
				std_pass = ((100 * len(exam_result_pass.ids)) /
							(student_appear))
			return [{'student_appear': student_appear or 0.0,
					 'studnets': len(exam_result_pass.ids) or 0.0,
					 'pass_std': std_pass or 0.0,
					 'fail_student': len(exam_result_fail.ids) or 0.0}]

	@api.model
	def render_html(self, docids, data=None):
		self.model = self.env.context.get('active_model')
		docs = self.env[self.model].browse(self.env.context.get('active_ids',
																[]))
		docargs = {'doc_ids': docids,
				   'doc_model': self.model,
				   'docs': docs,
				   'pass_student_count': self.pass_student,
				   }
		render_model = "exam.exam_result_batch"
		return self.env['report'].render(render_model, docargs)
