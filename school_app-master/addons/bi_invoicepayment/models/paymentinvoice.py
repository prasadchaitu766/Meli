# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
from odoo.tools.safe_eval import safe_eval
from odoo import api, fields, models, tools, SUPERUSER_ID
from odoo.tools.translate import _
from odoo.tools import email_re, email_split
from odoo.exceptions import UserError, AccessError                            
from odoo.exceptions import ValidationError


class BiInvoicePayment(models.Model):

	_name = "bi.invoice.payment"


	@api.depends('payment_line_ids.amount')
	def _amount_all(self):
		amount_total = 0.0
		for payment in self:
			for line in payment.payment_line_ids:
				amount_total+= line.amountpaid
			payment.update({'amount_total': amount_total,})
			
	state = fields.Selection([('draft', 'Unposted'), ('posted', 'Posted')], index='true', default='draft')
	name = fields.Char(string='Payment Number', copy=False, readonly=True, index=True, default=lambda self: _('New') )
	partner_id = fields.Many2one('res.partner', "Customer",  readonly=True,  states={'draft': [('readonly', False)]})
	date = fields.Date("Payment Date", default=fields.Date.context_today, readonly=True,  states={'draft': [('readonly', False)]})
	journal_id = fields.Many2one('account.journal', string='Journal',  domain=[('type', 'in', ('bank', 'cash'))], readonly=True, states={'draft': [('readonly', False)]})
	voucher_type = fields.Selection([('inbound','Receipt'),('outbound','Payment')], "Type")
	payment_line_ids = fields.One2many('bi.invoice.payment.line', 'payment_id', 'Payment', readonly=True,  states={'draft': [('readonly', False)]})
	company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env['res.company']._company_default_get('bi.invoice.payment') ,readonly=True, states={'draft': [('readonly', False)]})
	currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.user.company_id.currency_id)
	amount_total = fields.Monetary(string='Total', store=True, readonly=True, compute='_amount_all', track_visibility='always')
	journal_ref_id = fields.Many2one('account.move', string='Journal Entry', readonly=True, index=True, ondelete='restrict', copy=False,
		help="Link to the automatically generated Journal Items.")
	select_deduction = fields.Selection([('yes','Yes'),('no','No')],string="Deduction",readonly=True, states={'draft': [('readonly', False)]})
	bank_type = fields.Selection([('cheque','Cheque'),('ntfs','NTFS'),('cash','Cash'),('others','Others')],string="Payment Type",readonly=True, states={'draft': [('readonly', False)]})
	payment_line_id = fields.One2many('bi.account.multi.payment.line','account_payment_id','Payment',readonly=True, states={'draft': [('readonly', False)]})
	account_id = fields.Many2one('account.payment', "Payment")
	cheque_no = fields.Char("Cheque Number")
	Cheque_date = fields.Date("Cheque Date")
	bank_branch = fields.Char("Bank Branch")
	cheque_deposit_date = fields.Date("Cheque Deposit Date")
	cheque_clearing_date = fields.Date("Cheque Clearing Date")
	school_id = fields.Many2one('school.school', 'Campus')
	
	@api.onchange('partner_id')
	def onchange_partner_id(self):
		invoices = []
		details = {}
		if self.voucher_type == 'inbound':
			invoice = self.env['account.invoice'].search([('partner_id','=', self.partner_id.id),('state','=','open'),('type','=','out_invoice')])
		elif self.voucher_type == 'outbound':
			invoice = self.env['account.invoice'].search([('partner_id','=', self.partner_id.id),('state','=','open'),('type','=','in_invoice')])
		else:
			invoice = self.env['account.invoice'].search([('partner_id','=', self.partner_id.id),('state','=','open')])
		for inv in invoice:
			details = {
			'invoice_id': inv.id,
			'invoice_no' : inv.number,
			'invoice_date' : inv.date_invoice,
			'invoice_duedate' : inv.date_due,
			'amount' : inv.amount_total,
			'balance' : inv.residual,
			'amountpaid' : inv.residual,
			}
			invoices.append(details)
		self.payment_line_ids = invoices

	@api.model
	def create(self, vals):
		if vals.get('name', _('New')) == _('New'):
			if vals.get('voucher_type','') == 'inbound':
				vals['name'] = self.env['ir.sequence'].next_by_code('account.payment.customer.invoice') or _('New')
			else:
				vals['name'] = self.env['ir.sequence'].next_by_code('account.payment.supplier.invoice') or _('New')
		result = super(BiInvoicePayment, self).create(vals)
		return result

	@api.multi
	def write(self, vals):
		for res in self:
			if res.journal_ref_id:
				if vals.get('cheque_clearing_date',False):
					res.journal_ref_id.write({'date':vals['cheque_clearing_date']})
		result = super(BiInvoicePayment, self).write(vals)
		return result
	
	@api.onchange('journal_id')
	def _onchange_journal_id(self):
		if self.journal_id:
			self.currency_id = self.journal_id.currency_id.id or self.journal_id.company_id.currency_id.id

	@api.multi
	def post(self):
		aml_dict = {}
		apl_dict = {}
		payment_id = []
		total=0.0   
		total_amount_currency=0.0   
		aml_obj = self.env['account.move.line'].with_context(check_move_validity=False)
		for payment in self:
			if self.bank_type == 'cheque' and self.cheque_clearing_date:
				dst_move = self.env['account.move'].create({
															# 'name': self.name,
															'date': self.cheque_clearing_date ,
															'ref':self.name,
															'company_id': self.company_id.id,
															'journal_id':self.journal_id.id,
															'school_id':self.school_id.id,
															})
			else:
				dst_move = self.env['account.move'].create({
															# 'name': self.name,
															'date': self.date ,
															'ref':self.name,
															'company_id': self.company_id.id,
															'journal_id':self.journal_id.id,
															'school_id':self.school_id.id,
															})	
			company_currency = payment.journal_id.company_id.currency_id.id
			current_currency = payment.currency_id.id or company_currency
			for line in self.payment_line_ids:
				apl_obj = self.env['account.payment']
				
				ast_move = self.env['account.payment'].create({
					'communication': self.name,
					'journal_id': self.journal_id.id,
					'currency_id': payment.currency_id.id,
					'partner_id': self.partner_id.id,
					'payment_method_id' : 1,
					'payment_date': self.date,
					'payment_difference_handling':'open',
					'company_id': self.company_id.id,
					'state':'posted',
					'move_name': 'test',
					'partner_type': payment.voucher_type in 'outbound' and 'customer' or 'supplier',
					'name': self.name,
					'amount': line.amountpaid,
					'payment_type':  payment.voucher_type,
					'invoice_ids':[(4, line.invoice_id.id, None)],
					})
				payment_id.append(ast_move.id)
				i=1
				invoice_currency = line.invoice_id.currency_id
				amount = line.amountpaid * (payment.voucher_type in ('outbound') and 1 or -1)
				debit, credit, amount_currency, currency_id = aml_obj.with_context(date=self.date).compute_amount_fields(amount, self.currency_id, self.company_id.currency_id, invoice_currency)
				
				
				aml_dict.update({
						'name': payment.name,
						'account_id': line.invoice_id.account_id.id,              
						'journal_id': payment.journal_id.id,
						'credit':credit,
						'debit': debit,
						'move_id':dst_move.id,'payment_id':ast_move.id,
						'partner_id': self.partner_id.id,
						'credit_cash_basis':line.amountpaid,
						'balance_cash_basis':line.amountpaid,
						'reconciled':True,
						'amount_currency': amount_currency and amount_currency or  0.0,
						'currency_id': currency_id and currency_id or False,
						}) 
				recvd = aml_obj.create(aml_dict)
				total = total + (debit or credit)
				total_amount_currency = total_amount_currency + abs(amount_currency and amount_currency or  0.0)
				line.invoice_id.register_payment(recvd)
			if total> 0:
				for line in self.payment_line_id:
						if line.amount_total>0.0:
							amount = line.amount_total * (payment.voucher_type in ('inbound') and 1 or -1)
							debit, credit, amount_currency, currency_id = aml_obj.with_context(date=self.date).compute_amount_fields(amount, self.currency_id, self.company_id.currency_id, invoice_currency)
				
							aml_dict={
												'name':payment.name,
												'account_id':line.account_id.id,											           
												'journal_id':payment.journal_id.id,
												'debit':debit,
												'credit':credit,
												'move_id':dst_move.id,
												'amount_currency':amount_currency and amount_currency or 0.0,
												'currency_id':currency_id,

											}

							total = total - (debit or credit)
							total_amount_currency = total_amount_currency - abs(amount_currency and amount_currency or  0.0)
							aml_obj.create(aml_dict)
				if (payment.voucher_type in 'inbound'):
					amount_total = total 
					total_amount_currency=total_amount_currency
				else:
					amount_total = total*-1
					total_amount_currency = total_amount_currency*-1
				aml_dict={
							'name': payment.name,
							'account_id':payment.journal_id.default_debit_account_id.id,               
							'journal_id':payment.journal_id.id,
							'debit':payment.voucher_type in 'inbound' and total or 0.0,
							'credit':payment.voucher_type in 'outbound' and total or 0.0,
							'move_id':dst_move.id,
							'payment_id':ast_move.id,
							'partner_id':self.partner_id.id,
							'debit_cash_basis':total,
							'balance_cash_basis':total*-1,
							'reconciled':False,
							'amount_currency':total_amount_currency and total_amount_currency or 0.0,
							'currency_id':currency_id or False,
						}
				recvd = aml_obj.create(aml_dict)

			dst_move.post()	
			for ast_payment in self.env['account.payment'].browse(payment_id):
				ast_payment.write({'move_name': dst_move.name})
			self.write({'state':'posted', 'journal_ref_id':dst_move.id})
	
	@api.multi
	def button_cancel(self):
		self.write({'state':'draft'})

	
	@api.multi
	def unlink(self):
		for payment in self:
			if payment.state == "posted":
				raise UserError(_("You cannot delete a posted payment."))
		super(BiInvoicePayment, self).unlink()


class BiInvoicePaymentLine(models.Model):
	_name = "bi.invoice.payment.line"

	invoice_id = fields.Many2one('account.invoice', "Invoice")
	payment_id =  fields.Many2one('bi.invoice.payment', "Invoice")
	invoice_no = fields.Char("Invoice Number")
	invoice_date = fields.Date("Invoice Date")
	invoice_duedate = fields.Date("Due Date")
	amount = fields.Float("Amount")
	balance = fields.Float("Balance")
	amountpaid = fields.Float("Amount to be Paid")
	company_id = fields.Many2one(related='payment_id.company_id', string='Company', store=True, readonly=True)



class BiAccountMultiPaymentLine(models.Model):
	_name = "bi.account.multi.payment.line"
	
	account_payment_id =  fields.Many2one('bi.invoice.payment', 'Payment')
	invoice_ids = fields.Many2one('account.invoice', string="Invoices", copy=False, readonly=True)
	account_id = fields.Many2one('account.account', "Account", store=True)
	description = fields.Char("Description", store=True)
	amount_total = fields.Monetary("Amount", store=True)
	percentage = fields.Monetary("Percentage", store=True)
	currency_id = fields.Many2one('res.currency', related='account_payment_id.currency_id', store=True, related_sudo=False)
	payment_amount = fields.Monetary(string='Payment amount', store=True)


	@api.onchange('account_id')
	def onchange_payment(self):
		self.payment_amount=self.account_payment_id.amount_total

	@api.onchange('percentage')
	def onchange_deduction(self):
		for line in self:
			total1=0.0
			total1=(line.payment_amount*line.percentage)/100.00
			line.update({'amount_total':total1})
			



	


