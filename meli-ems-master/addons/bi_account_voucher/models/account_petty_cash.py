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
from odoo.exceptions import UserError, ValidationError
import odoo.addons.decimal_precision as dp


#====================================================
#Class : AccountPettyCash
#Description :Used for petty cash management
#====================================================


class AccountPettyCash(models.Model):
	_name = "account.petty.cash"


	#====================================================
	#Class : AccountPettyCash
	#Method : _amount_all
	#Description :This function will calculate the total amount
	#====================================================

	@api.depends('vouchers.amount','opening_balance','amount_total')
	def _amount_all(self):
		amount_total = 0.0
		opening_balance = 0.0
		for payment in self:
			
			FndObj = self.env['account.petty.journal.cash'].search([('state','=','posted'),('custodian_id','=', payment.custodian_id.id),('close_balance','>', 0.0)])
			for line in FndObj:							
				opening_balance =  opening_balance + line.close_balance or line.fund_amount
				
			for line in payment.vouchers:
				amount_total+= line.amount
			closing_balance=(opening_balance-(amount_total))
			payment.update({'closing_balance':closing_balance,'amount_total': amount_total,'opening_balance':opening_balance})

		
	name = fields.Char(string='Sequence',copy=False, readonly=True, index=True, default=lambda self: _('New'))
	state = fields.Selection([('draft','Draft'),('verified','Verified'),('posted','Posted')], index=True, default='draft')
	company_id= fields.Many2one('res.company',"Company",default=lambda self: self.env['res.company']._company_default_get('account.petty.cash'))
	custodian_id = fields.Many2one('res.users',"Custodian",readonly=True, default=lambda self: self.env.user,states={'draft': [('readonly', False)]})
	journal_id = fields.Many2one('account.journal',"Journal",domain=[('type', 'in', ('bank', 'cash'))],readonly=True,states={'draft': [('readonly', False)]})                     
	vouchers = fields.One2many('account.petty.order.line','line_id',"Vouchers",readonly=True,states={'draft': [('readonly', False)]})
	journal_ref = fields.Many2one('account.move', string='Journal Entry',readonly=True, index=True, ondelete='restrict', copy=False,
		help = "Link to the automatically generated Journal Items.")
	payment_date = fields.Date(string='Payment Date', default=fields.Date.context_today, required=True,readonly=True,states={'draft': [('readonly', False)]})
	currency_id = fields.Many2one('res.currency', string='Currency',default=lambda self: self.env.user.company_id.currency_id)
	closing_balance = fields.Monetary(string='Closing Balance',store=True,compute='_amount_all',digits_compute=dp.get_precision('Product Price'))
	fund_id = fields.Many2one('account.petty.journal.cash')
	opening_balance = fields.Monetary(string='Opening Balance',store=True, compute='_amount_all',digits_compute=dp.get_precision('Product Price'))
	amount_total = fields.Monetary(string='Total',store=True, readonly=True, compute='_amount_all',digits_compute=dp.get_precision('Product Price'))
	school_id = fields.Many2one('school.school', 'Campus')

	@api.model
	def create(self, vals):
		if vals.get('name', _('New')) == _('New'):
			vals['name'] = self.env['ir.sequence'].next_by_code('account.petty.cash') or _('New')			
		result = super(AccountPettyCash, self).create(vals)	


		return result	

	
	#======================================================================
	#Class : AccountPettyCash
	#Method :create
	#Description :This function used to create,post the journal entry values
	# 			  and update the close balance
	#======================================================================

	
	@api.multi
	def button_post(self):
		aml_dict = {}
		total=0.0
		aml_obj = self.env['account.move.line'].with_context(check_move_validity=False)
		for payment in self:
			dst_move = self.env['account.move'].create({
														'name': self.name,
														'date': self.payment_date,
														'ref':'accounts',
														'company_id': self.company_id.id,
														'journal_id':self.journal_id.id,
														'school_id':self.school_id.id,
														})
			for line in self.vouchers:
				i=1
				aml_dict={
						'name':'Payment',
						'account_id': line.account_id.id,
						'currency_id': payment.currency_id.id,	            
						'journal_id': payment.journal_id.id,
						'debit':line.amount,
						'credit':0.0,
						'move_id':dst_move.id,
					}
				total = total + line.amount
				aml_obj.create(aml_dict)
			if total> 0:
				aml_dict.update({
					'name': 'Payment',
					'account_id': payment.journal_id.default_debit_account_id.id,
					'currency_id': payment.currency_id.id,	            
					'journal_id': payment.journal_id.id,
					'credit':total,
					'debit':0.0,
					'move_id':dst_move.id})            
				aml_obj.create(aml_dict)
			dst_move.post()
			self.write({'state':'posted','journal_ref':dst_move.id})

		
	@api.multi
	def button_verify(self):
		self.write({'state':'verified'})
		if (self.opening_balance <= 0.0):
			raise UserError(_('Not sufficient balance!!'))
		if (self.opening_balance < self.amount_total):
			raise UserError(_('Total amount is greater than your petty cash balance'))

		

		for payment in self:
			FndObj = self.env['account.petty.journal.cash'].search([('custodian_id','=', self.custodian_id.id),('close_balance','>', 0.0)])
			total = payment.amount_total
			for line in FndObj:
				bal = line.close_balance				
				if ((line.close_balance - total) > 0.0):
					fnd_new = line.write({
						'payment_ids': [(4, payment.id, None)],
						'close_balance':  line.close_balance - total,
							})
						
					break
				elif ((line.close_balance - total) <= 0.0):
					fnd_new = line.write({
						'payment_ids': [(4, payment.id, None)],
						'close_balance':  0.0,
							})
					total = total - bal
				
			
	
	#======================================================================
	#Class : AccountPettyCash
	#Method :onchange_custodian
	#Description :This function used to update the fund amount and opening balance
	#======================================================================

	

	@api.onchange('custodian_id')
	def onchange_custodian(self):
		FndObj = self.env['account.petty.journal.cash'].search([('custodian_id','=', self.custodian_id.id),('close_balance','>', 0.0)])
		opening_balance = 0.0
		if not FndObj:
			raise UserError(_('Not sufficient balance!!!!!!!!!!!'))

		for line in FndObj:
			self.amount= line.fund_amount
			self.journal_id= line.journal_id
			opening_balance =  opening_balance + (line.close_balance or line.fund_amount)
		self.opening_balance =	opening_balance 
		 

#====================================================
#Class : AccountPettyLine
#Description :Used for notebook creation
#====================================================

class AccountPettyOrderLine(models.Model):
	_name = "account.petty.order.line"


	line_id = fields.Many2one('account.petty.cash',"num")
	account_id = fields.Many2one('account.account',"Account",required=True,domain=[('user_type_id.name', '=', ('Expenses'))])
	description = fields.Char("Description",required=True)
	amount = fields.Float(string='Amount',required=True)
	partner_id = fields.Many2one('res.partner',"Partner")
	closing_balance = fields.Monetary(string='Closing Balance',store=True,digits_compute=dp.get_precision('Product Price'))
	currency_id = fields.Many2one('res.currency', related='line_id.currency_id', store=True, related_sudo=False)
	
	
	




	







