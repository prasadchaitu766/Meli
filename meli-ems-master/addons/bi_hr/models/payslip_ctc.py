# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


import time
from datetime import datetime, timedelta
from dateutil import relativedelta
import babel
from email.utils import formataddr
from odoo.osv import expression
from odoo.exceptions import UserError, ValidationError
from odoo import api, fields, models, tools, SUPERUSER_ID
from odoo.tools.translate import _

class BiPayslipCtc(models.Model):
	_name = 'bi.ctc'
	_rec_name = "employee_id"

	# @api.depends('line_ids.ctc')
	# def _amount_all(self):
	# 	amount_total = 0.0
	# 	for payment in self:
	# 		for line in payment.line_ids:
	# 			amount_total+= line.ctc
	# 		payment.update({'sum_ctc': amount_total,})

	date_from = fields.Date(string="Date From")
	date_to = fields.Date(string="Date To")
	employee_id = fields.Many2one('hr.employee', string="Employee")
	line_ids = fields.One2many('bi.ctc.line', 'line_id', "Line")
	school_id = fields.Many2one('school.school',string="Campus")
	# sum_ctc = fields.Monetary(string='Total CTC', store=True, readonly=True, compute='_amount_all', track_visibility='always')
	# currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.user.company_id.currency_id)

	@api.multi
	def show_ctc(self):
		ledger = self.env['bi.ctc.line']
		for slip in self:
			ledger.search([('line_id', '=',slip.id)]).unlink()	
			amount_basic = amount_sdt = amount_td = amount_td1 = amount_td2 = amount_ctc = amount_td3 = amount_td4 = 0.0
			for emp in self.env['hr.payslip'].search([('date_from','>=',slip.date_from),('date_to','<=',slip.date_to),('employee_id','=',slip.employee_id.id),('state','=','done')]):			
				for line in self.env['hr.payslip.line'].search([('slip_id','=',emp.id),('employee_id','=',emp.employee_id.id)]):					
					if line.code == 'BASIC':														
						amount_basic = line.amount	
					elif line.code == 'SDT':					
						amount_sdt = line.amount	
					elif line.code == 'TD1':
						amount_td1 = line.amount
					elif line.code == 'TD2':
						amount_td2 = line.amount
					elif line.code == 'TD3':
						amount_td3 = line.amount
					elif line.code == 'TD4':
						amount_td4 = line.amount
					amount_td = amount_td1 + amount_td2 + amount_td3 + amount_td4
					amount_ctc = emp.amount_total - (amount_sdt + amount_td1 + amount_td2 + amount_td3 + amount_td4) 							
				vals = {
						'line_id':slip.id,
						'name':emp.name,
						'net': emp.amount_total,
						'epf': amount_sdt,
						'esi': amount_td,
						'ctc': amount_ctc, 
					   }
				rec=ledger.create(vals)

	@api.multi
	def unlink(self):
		return super(BiPayslipCtc, self).unlink()

	@api.onchange('employee_id')
	def _onchange_employee(self):		
		if self.employee_id:			
			self.school_id= self.employee_id.school_id.id
			

class BiPayslipCtcLine(models.Model):
	_name = 'bi.ctc.line'

	line_id = fields.Many2one('bi.ctc', "Ctc Line")
	name = fields.Char("Payslip Name")
	net = fields.Float("Net Pay")
	epf = fields.Float("Security Deposit")
	esi = fields.Float("Tax Deduction")
	ctc = fields.Float("CTC")

	@api.multi
	def unlink(self):
		return super(BiPayslipCtcLine, self).unlink()
