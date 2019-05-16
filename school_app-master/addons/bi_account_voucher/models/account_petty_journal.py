# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
from odoo import api, fields, models
from odoo import tools, _
from odoo.exceptions import ValidationError
from odoo.modules.module import get_module_resource
import time
from datetime import datetime
from dateutil.relativedelta import relativedelta
import odoo.addons.decimal_precision as dp


#====================================================
#Class : AccountPettyCashJournal
#Description :Used for petty cash fund creation
#====================================================



class AccountPettyCashJournal(models.Model):
	_name = "account.petty.journal.cash"


	custodian_id = fields.Many2one('res.users',"Custodian",required=True,readonly=True,states={'draft': [('readonly', False)]})
	state = fields.Selection([('draft','Draft'),('posted','Posted')], index=True, default='draft')
	journal_id = fields.Many2one('account.journal',"Journal",required=True,readonly=True,domain=[('type', 'in', ('bank', 'cash'))],states={'draft': [('readonly', False)]})
	date = fields.Date("Date",required=True,default=fields.Date.context_today,index=True,readonly=True,states={'draft': [('readonly', False)]})
	account_id = fields.Many2one('account.account',"Account", required=True,readonly=True,states={'draft': [('readonly', False)]})
	currency_id = fields.Many2one('res.currency',string="Currency")
	fund_amount = fields.Float("Fund Amount",required=True,readonly=True,states={'draft': [('readonly', False)]},digits_compute=dp.get_precision('Product Price'))
	close_balance = fields.Float(string='Closing Balance',readonly=True,digits_compute=dp.get_precision('Product Price'))
	company_id = fields.Many2one('res.company',"Company",default=lambda self: self.env['res.company']._company_default_get('account.petty.journal.cash'))
	journal_ref = fields.Many2one('account.move', string='Journal Entry',readonly=True, index=True, ondelete='restrict', copy=False,
		help = "Link to the automatically generated Journal Items.")
	payment_ids = fields.Many2many('account.petty.cash', 'bi_account_cash_payment_rel', 'cash_id', 'config_id', string="Payments", copy=False, readonly=True)
	school_id = fields.Many2one('school.school', 'Campus')

	
	#====================================================
	#Class : AccountPettyCashJournal
	#Method :initialize_fund
	#Description :This function will post the created fund journal entry
	#====================================================

	@api.multi
	def initialize_fund(self):
		

		aml_dict = {}
		total=0.0
		aml_obj = self.env['account.move.line'].with_context(check_move_validity=False)
		for payment in self:
			dst_move = self.env['account.move'].create({
														'name':'Petty Cash mangement',
														'date': payment.date,
														'ref':' Petty accounts',
														'company_id': payment.company_id.id,
														'journal_id':payment.journal_id.id,
														'school_id':payment.school_id.id,
														})
			
	
			aml_dict={
						'name':'Petty Cash mangement',
						'account_id': payment.account_id.id,
						'currency_id': payment.currency_id.id,	            
						'journal_id': payment.journal_id.id,
						'debit':payment.fund_amount,
						'credit':0.0,
						'move_id':dst_move.id,
					}
			total = total + payment.fund_amount
			aml_obj.create(aml_dict)
			if total> 0:
				aml_dict.update({
					'name': 'Petty Cash mangement',
					'account_id': payment.journal_id.default_credit_account_id.id,
					'currency_id': payment.currency_id.id,	            
					'journal_id': payment.journal_id.id,
					'credit':total,
					'debit':0.0,
					'move_id':dst_move.id})            
				aml_obj.create(aml_dict)
			dst_move.post()
			self.write({'state':'posted','close_balance':self.fund_amount,'journal_ref':dst_move.id})
			FndObj = self.env['account.petty.cash'].search([('custodian_id','=', self.custodian_id.id),('state','=', 'draft')])
			for line in FndObj:
				line.write({'opening_balance':line.opening_balance +self.fund_amount})


