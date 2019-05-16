# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models, fields, _
from odoo.exceptions import UserError, ValidationError

class WizardBiPayslip(models.TransientModel):
	_name = 'bi.payslip.rep'

	# start_date = fields.Date('From Date',default=fields.Datetime.now(), required=True)
	# end_date = fields.Date('To Date',default=fields.Datetime.now(),required=True)
	batch_ids = fields.Many2many('hr.payslip.run', 'bi_hr_payslip_run_rel', 'run_id', 'config_id', string="Batches", copy=False, readonly=False)
	
	@api.multi
	def print_Excel_report(self, vals):
		active_ids = self.env.context.get('active_ids', [])
		#raise UserError((str(self._context)))
		# for data in self:
		# 	data.write({'batch_ids':[(6,0,active_ids)],})		
		datas = {
			 'ids': active_ids,
			 'model': 'hr.payslip.run',
			 'form': self.read()[0]
		}
		return self.env["report"].get_action(self, 'account.bi.payslip.new.xlsx', data=datas)


