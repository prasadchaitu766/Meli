# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api
from datetime import datetime

class TerminateReason(models.TransientModel):
		_name = "terminate.reason"

		reason = fields.Text('Reason')
		date_terminate = fields.Date(string='Date',default=datetime.today())

		@api.multi
		def save_terminate(self):
				'''Method to terminate student and change state to terminate'''
				self.env['student.student'
								 ].browse(self._context.get('active_id')
													).write({'state': 'terminate',
																	 'terminate_reason': self.reason})
				return True
