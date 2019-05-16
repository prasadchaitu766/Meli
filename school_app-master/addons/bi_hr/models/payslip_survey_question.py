# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

#
# Please note that these reports are not multi-currency !!!
#

from odoo import api, fields, models, tools


class gst_report(models.Model):
	_name = "question.report"
	_description = "Question Report"
	_rec_name = 'employee_id'
	_auto = False
	
	employee_id = fields.Many2one('hr.employee', "Employee")
	survey_date = fields.Date("Survey Date")
	question = fields.Char("Questions")
	score = fields.Float("Score")
	
	@api.model_cr
	def init(self):

		tools.drop_view_if_exists(self._cr, 'question_report')
		self._cr.execute("""

		CREATE OR REPLACE VIEW question_report AS (
		SELECT 
			    row_number() over (ORDER BY sul.id) AS id,
				sui.employee_id AS employee_id,
				sui.create_date AS survey_date,
				sq.question AS question,
				(sul.value_text)::numeric AS score
		FROM 
		        survey_user_input_line sul
        INNER JOIN survey_question sq ON (sul.question_id=sq.id)
        INNER JOIN survey_user_input sui ON (sui.id=sul.user_input_id)
        group by sul.id,sui.employee_id,sq.question,sul.value_text,sui.create_date
					 )""")