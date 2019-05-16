# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

import time
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, Warning as UserError
from datetime import datetime
import odoo.addons.decimal_precision as dp
from odoo.tools import float_is_zero, float_compare
from odoo.tools.misc import formatLang

import logging
MAP_INVOICE_TYPE_PARTNER_TYPE = {
	'out_invoice': 'customer',
	'out_refund': 'customer',
	'in_invoice': 'supplier',
	'in_refund': 'supplier',
}

class StudentFeesRegister(models.Model):
	'''Student fees Register'''
	_name = 'student.fees.register'
	_description = 'Student fees Register'

	@api.multi
	@api.depends('line_ids')
	def _compute_total_amount(self):
		'''Method to compute total amount'''
		for rec in self:
			total_amt = 0.0
			for line in rec.line_ids:
				total_amt += line.total
			rec.total_amount = total_amt

	name = fields.Char('Name', required=True, help="Enter Name")
	date = fields.Date('Date', required=True,
					   help="Date of register",
					   default=lambda * a: time.strftime('%Y-%m-%d'))
	number = fields.Char('Number', readonly=True,
						 default=lambda self: _('New'))
	line_ids = fields.One2many('student.payslip', 'register_id',
							   'PaySlips')
	total_amount = fields.Float("Total",
								compute="_compute_total_amount",
								)
	state = fields.Selection([('draft', 'Draft'), ('confirm', 'Confirm')],
							 'State', readonly=True, default='draft')
	journal_id = fields.Many2one('account.journal', 'Journal',
								 help="Select Journal",
								 required=False)
	company_id = fields.Many2one('res.company', 'Company', required=True,
								 change_default=True, readonly=True,
								 default=lambda obj_c: obj_c.env['res.users'].
								 browse([obj_c._uid])[0].company_id)
	fees_structure = fields.Many2one('student.fees.structure',
									 'Fees Structure')
	standard_id = fields.Many2one('standard.standard', 'Program')
	

	@api.multi
	def fees_register_draft(self):
		'''Changes the state to draft'''
		self.write({'state': 'draft'})

	@api.multi
	def fees_register_confirm(self):
		'''Method to confirm payslip'''
		stud_obj = self.env['student.student']
		slip_obj = self.env['student.payslip']
		school_std_obj = self.env['school.standard']
		for rec in self:
			if not rec.journal_id:
				raise ValidationError(_('Kindly, Select Account Journal'))
			if not rec.fees_structure:
				raise ValidationError(_('Kindly, Select Fees Structure'))
			school_std = school_std_obj.search([('standard_id', '=',
												 rec.standard_id.id)])
			student_ids = stud_obj.search([('standard_id', 'in',
											school_std.ids),
										   ('state', '=', 'done')])
			for stu in student_ids:
				old_slips = slip_obj.search([('student_id', '=', stu.id),
											 ('date', '=', rec.date)])
				# Check if payslip exist of student
				if old_slips:
					raise UserError(_('There is already a Payslip exist for\
										   student: %s\
										   for same date.!') % stu.name)
				else:
					rec.number = self.env['ir.sequence'].\
						next_by_code('student.fees.register') or _('New')
					res = {'student_id': stu.id,
						   'register_id': rec.id,
						   'name': rec.name,
						   'date': rec.date,
						   'company_id': rec.company_id.id,
						   'currency_id':
						   rec.company_id.currency_id.id or False,
						   'journal_id': rec.journal_id.id,
						   'fees_structure_id': rec.fees_structure.id or False}
					slip_id = slip_obj.create(res)
					slip_id.onchange_student()
			# Calculate the amount
			amount = 0
			for data in rec.line_ids:
				amount += data.total
			rec.write({'total_amount': amount,
					   'state': 'confirm'})
		return True


class StudentPayslipLine(models.Model):
	'''Student PaySlip Line'''
	_name = 'student.payslip.line'
	_description = 'Student PaySlip Line'



	@api.depends('discount', 'amount')
	def _compute_amount(self):
		"""
		Compute the amounts of the SO line.
		"""
		for line in self:
			price = line.amount * (1 - (line.discount or 0.0) / 100.0)
			# taxes = line.tax_id.compute_all(price, line.currency_id, partner=False)
			line.update({
				# 'price_tax': taxes['total_included'] - taxes['total_excluded'],
				# 'price_total': taxes['total_included'],
				'price_subtotal': price,
			})


	name = fields.Char('Name', required=True)
	code = fields.Char('Code', required=True)
	fee_type = fields.Selection([('tuitionfee','Tuition Fee'),
							('book', 'Book'),
							('idcard', 'Id Card'),
							('exam', 'Exam'),
							('latexam', 'Late Exam'),
							('repeat', 'Repeat'),
							('other', 'Other')],
							'Fees Type', required=True)

	type = fields.Selection([('month', 'Monthly'),
							 ('year', 'Yearly'),
							 ('range', 'Range')],
							'Duration', required=True)
	amount = fields.Float('Amount', digits=(16, 2))
	discount = fields.Float(string='Discount (%)', digits=dp.get_precision('Discount'), default=0.0)
	price_subtotal = fields.Monetary(string='Subtotal',
		store=True, readonly=True, compute='_compute_amount')
	currency_id = fields.Many2one('res.currency', string='Currency',default=lambda self: self.env.user.company_id.currency_id)
	# price_tax = fields.Monetary(compute='_compute_amount', string='Taxes', readonly=True, store=True)
	# price_total = fields.Monetary(compute='_compute_amount', string='Total', readonly=True, store=True)
	line_ids = fields.One2many('student.payslip.line.line', 'slipline_id',
							   'Calculations')
	slip_id = fields.Many2one('student.payslip', 'Pay Slip')
	description = fields.Text('Description')
	company_id = fields.Many2one('res.company', 'Company',
								 change_default=True,
								 default=lambda obj_c: obj_c.env['res.users'].
								 browse([obj_c._uid])[0].company_id)
	currency_id = fields.Many2one('res.currency',
								  'Currency')
	currency_symbol = fields.Char(related="currency_id.symbol",
								  string='Symbol')
	account_id = fields.Many2one('account.account', "Account")
	product_id = fields.Many2one('product.product',string="Product")
	qty = fields.Float("Quantity")

	@api.onchange('company_id')
	def set_currency_onchange(self):
		for rec in self:
			rec.currency_id = rec.company_id.currency_id.id


class StudentFeesStructureLine(models.Model):
	'''Student Fees Structure Line'''
	_name = 'student.fees.structure.line'
	_description = 'Student Fees Structure Line'
	_order = 'sequence'

	name = fields.Char('Name', required=True)
	code = fields.Char('Code', required=True)
	type = fields.Selection([('month', 'Monthly'),
							 ('year', 'Yearly'),
							 ('range', 'Range')],
							'Duration', required=True)
	amount = fields.Float('Amount', digits=(16, 2))
	sequence = fields.Char('Sequence',copy=False, index=True,default=lambda self: _('New'))
	line_ids = fields.One2many('student.payslip.line.line', 'slipline1_id',
							   'Calculations')
	account_id = fields.Many2one('account.account', string="Account")
	company_id = fields.Many2one('res.company', 'Company',
								 change_default=True,
								 default=lambda obj_c: obj_c.env['res.users'].
								 browse([obj_c._uid])[0].company_id)
	currency_id = fields.Many2one('res.currency', 'Currency')
	currency_symbol = fields.Char(related="currency_id.symbol",
								  string='Symbol')
	product_id = fields.Many2one('product.product',string="Product")
	qty = fields.Float("Quantity", default=1.0)
	fee_type = fields.Selection([('tuitionfee','Tuition Fee'),
							('book', 'Book'),
							('idcard', 'Id Card'),
							('exam', 'Exam'),
							('latexam', 'Late Exam'),
							('repeat', 'Repeat'),
							('other', 'Other')],
							'Fees Type', required=True)

	@api.model
	def create(self, vals):
		if vals.get('sequence', _('New')) == _('New'):
			vals['sequence'] = self.env['ir.sequence'].next_by_code('student.fees') or _('New')			
		result = super(StudentFeesStructureLine, self).create(vals)	


		return result	

	@api.onchange('company_id')
	def set_currency_company(self):
		for rec in self:
			rec.currency_id = rec.company_id.currency_id.id


class StudentFeesStructure(models.Model):
	'''Fees structure'''
	_name = 'student.fees.structure'
	_description = 'Student Fees Structure'

	name = fields.Char('Name', required=True)
	code = fields.Char('Code', required=True)
	line_ids = fields.Many2many('student.fees.structure.line',
								'fees_structure_payslip_rel',
								'fees_id', 'slip_id', 'Fees Structure')
	semester_id = fields.Many2one('standard.semester', string="Semester", required=True)
	sem_type = fields.Selection([('normal', 'Normal'),('repeat', 'Repeat'),('exam', 'Exam'),('lateexam', 'Late Exam')], "Type", required=True, default='normal')

	_sql_constraints = [('code_uniq', 'unique(code)',
						 '''The code of the Fees Structure must
						 be unique !''')]


class StudentPayslip(models.Model):
	_name = 'student.payslip'
	_description = 'Student PaySlip'
	_rec_name = 'number'
	_order = "date desc"

	@api.multi
	def _compute_invoice(self):
		'''Method to compute number invoice'''
		inv_obj = self.env['account.invoice']
		for rec in self:
			rec.invoice_count = inv_obj.search_count([('student_payslip_id',
													   '=', rec.id)])
		return True
	@api.multi
	def _get_default_journal(self):
		return self.env['account.journal'].search([('code', '=', 'SLIP')], limit=1).id

	@api.depends('line_ids.price_subtotal')
	def _amount_total_all(self):
		for order in self:
			total = 0.0
			for line in order.line_ids:
				total += line.price_subtotal
			order.update({
				'total': total,
			})	
	

	fees_structure_id = fields.Many2one('student.fees.structure',
										'Fees Structure',
										states={'paid': [('readonly', True)]}, store=True)
	program_id = fields.Many2one('standard.standard', 'Program')
	standard_id = fields.Many2one('school.standard', 'Class')
	division_id = fields.Many2one('standard.division', 'Class Room')
	medium_id = fields.Many2one('standard.medium', 'Shift')
	register_id = fields.Many2one('student.fees.register', 'Register')
	name = fields.Char('Course Level')
	number = fields.Char('Slip Number', readonly=True,
						 default=lambda self: _('New'))
	student_id = fields.Many2one('student.student', 'Student', required=True)
	date = fields.Date('Date', readonly=True,
					   help="Current Date of payslip",
					   default=lambda * a: time.strftime('%Y-%m-%d'))
	line_ids = fields.One2many('student.payslip.line', 'slip_id',
							   'PaySlip Line',readonly=True,states={'draft': [('readonly',False)]})
	total = fields.Monetary("Total", store=True, readonly=True, compute='_amount_total_all', track_visibility='always',
							help="Total Amount")
	state = fields.Selection([('draft', 'Draft'),('submit_discount','Concession Requested'),('discount_state','Concession Approved'), ('confirm', 'Confirmed'),
							  ('pending', 'Pending'), ('paid', 'Paid')],
							 'State', readonly=True, default='draft')
	journal_id = fields.Many2one('account.journal', 'Journal', required=False,default=_get_default_journal)
	invoice_count = fields.Integer(string="# of Invoices",
								   compute="_compute_invoice")
	paid_amount = fields.Monetary('Paid Amount', help="Amount Paid")
	due_amount = fields.Monetary('Due Amount', help="Amount Remaining")
	currency_id = fields.Many2one('res.currency', string='Currency',default=lambda self: self.env.user.company_id.currency_id)
	currency_symbol = fields.Char(related='currency_id.symbol',
								  string='Symbol')
	move_id = fields.Many2one('account.move', 'Journal Entry', readonly=True,
							  ondelete='restrict',
							  help='Link to the automatically'
							  'generated Journal Items.')
	payment_date = fields.Date('Payment Date', readonly=True,
							   states={'draft': [('readonly', False)]},
							   help='Keep empty to use the current date')
	type = fields.Selection([('out_invoice', 'Customer Invoice'),
							 ('in_invoice', 'Supplier Invoice'),
							 ('out_refund', 'Customer Refund'),
							 ('in_refund', 'Supplier Refund'),
							 ], 'Type', required=True,
							change_default=True, default='out_invoice')
	company_id = fields.Many2one('res.company', 'Company', required=True,
								 change_default=True, readonly=True,
								 default=lambda obj_c: obj_c.env['res.users'].
								 browse([obj_c._uid])[0].company_id)
	school_id = fields.Many2one('school.school', 'Campus')
	semester_id = fields.Many2one('standard.semester','Course Level') 
	discount_approval = fields.Boolean('Discount Approved')
	collected_by = fields.Many2one('res.users', 'Collected By',default=lambda self: self.env.user)

	concession_reason = fields.Text('Reason',store=True)
	pid = fields.Char('Application No', related='student_id.pid', store=True)
	parent_id = fields.Char('Father Name', related='student_id.parent_id', store=True)
	refund_amount = fields.Float("Refund Amount",required=False)


	@api.onchange('fees_structure_id')
	def onchange_fees_structure_id(self):
		if self.fees_structure_id:
			line_ids=[]
			for quotation_line in self.fees_structure_id.line_ids:
				vals ={}
				vals['name'] = quotation_line.name
				vals['fee_type'] = quotation_line.fee_type
				vals['code'] = quotation_line.code
				vals['product_id'] = quotation_line.product_id
				vals['qty'] = quotation_line.qty
				vals['type'] = quotation_line.type
				vals['amount'] = quotation_line.amount
				vals['account_id'] = quotation_line.account_id.id
				line_ids.append((0, 0, vals))
			if line_ids:
				self.line_ids = [(5)]
				self.line_ids = line_ids
		   
		
			
	@api.onchange('student_id')
	def onchange_student(self):
		'''Method to get standard , division , medium of student selected'''

		if self.student_id:
			self.program_id = self.student_id.program_id.id
			self.school_id = self.student_id.school_id.id
			self.standard_id = self.student_id.standard_id.id
			self.name = self.student_id.semester_id.name
			self.semester_id = self.student_id.semester_id.id
			fees_structure = self.env['student.fees.structure'].search([('semester_id','=',self.student_id.semester_id.id),('name','=',self.name)], limit=1)
			self.fees_structure_id = fees_structure

			

	@api.multi
	def unlink(self):
		for rec in self:
			if rec.state != 'draft':
				raise UserError(_('''You can delete record in unconfirm state
				only!'''))
		return super(StudentPayslip, self).unlink()

	@api.multi
	@api.onchange('journal_id')
	def onchange_journal_id(self):
		'''Method to get currency from journal'''
		for rec in self:
			currency_id = rec.journal_id and rec.journal_id.currency_id and\
				rec.journal_id.currency_id.id\
				or rec.journal_id.company_id.currency_id.id
			rec.currency_id = currency_id

	@api.model
	def create(self, vals):
		if vals.get('student_id'):
			student = self.env['student.student'].browse(vals.get('student_id'))
			structure_id = self.env['student.fees.structure'].search([('semester_id','=',student.semester_id.id),('name','=',vals['name'])],limit=1)
			vals.update({'standard_id': student.standard_id.id,
						 'division_id': student.standard_id.division_id.id,
						 'medium_id': student.medium_id.id,
						 'school_id': student.school_id.id,
						 'fees_structure_id': structure_id.id})

		return super(StudentPayslip, self).create(vals)

	@api.multi
	def write(self, vals):
		if vals.get('student_id'):
			student = self.env['student.student'].browse(vals.get('student_id'))
			vals.update({'standard_id': student.standard_id.id,
						 'division_id': student.standard_id.division_id.id,
						 'medium_id': student.medium_id.id})
		return super(StudentPayslip, self).write(vals)

	@api.multi
	def copy(self, default=None):
		if default is None:
			default = {}
		default.update({'state': 'draft',
						'number': False,
						'move_id': False,
						'line_ids': []})
		return super(StudentPayslip, self).copy(default)

	@api.multi
	def payslip_draft(self):
		'''Change state to draft'''
		self.write({'state': 'draft'})
		return True

	@api.multi
	def payslip_paid(self):
		'''Change state to paid'''
		self.write({'state': 'paid'})
		return True

	@api.multi
	def submit_concession(self):
		for main in self:
			# for obj in main.line_ids:
			if any(obj.discount > 0.00 for obj in main.line_ids ):
				break
			else:
				raise ValidationError(_('Sorry , To request fee concession need to add discount.'))

		self.write({'state':'submit_discount'})
		return {
			'name': _('Concession Reason'),
			'view_type': 'form',
			"view_mode": 'form',
			'res_model': 'concession.reason',
			'type': 'ir.actions.act_window',
			'target': 'new',
		}

	@api.multi
	def reject_discount(self):
		for discount_reject in self:
			for discount_line in discount_reject.line_ids:
				if discount_line.discount:
					discount_line.discount = 0.00
		self.write({'state':'draft'})
		return True
	@api.model
	def _default_get_gateway1(self):
		if self._context is None:
			self._context = {}
		sms_obj = self.env['sms.smsclient']
		gateway_ids = sms_obj.search([], limit=1)
		return gateway_ids and gateway_ids[0] or False	

	@api.multi
	def discount_confirm(self):
		for file in self:
			for line in file.line_ids:
				if line.discount > 0.00:
					file.discount_approval = True

			client_obj = self.env['sms.smsclient'].search([],limit=1)
			student_obj = self.env['student.student'].search([('id','=',self.student_id.id)])
			active_ids = self.env.context.get('active_ids', [])
			client_queueobj = self.env['partner.sms.send']
			
			data={
				'gateway': client_obj.id,
				'mobile_to': student_obj.mobile,
				'text': "Your concession is approved",
				'validity': client_obj.validity, 
				'classes': client_obj.classes, 
				'deferred': client_obj.deferred, 
				'priorirty': client_obj.priority, 
				'coding': client_obj.coding, 
				'tag': client_obj.tag, 
				'nostop': client_obj.nostop,
			}
			
			if not client_obj:
				raise UserError(_('You can only select one partner'))
			else:
				client_obj.send_msg_2(data)
		self.write({'state':'discount_state'})
		return True
	gateway = fields.Many2one('sms.smsclient', 'SMS Gateway', required=True,default = _default_get_gateway1)

	@api.multi
	def payslip_confirm(self):
		'''Method to confirm payslip'''
		for rec in self:
			if not rec.journal_id:
				raise ValidationError(_('Kindly, Select Account Journal!'))
			if not rec.fees_structure_id:
				raise ValidationError(_('Kindly, Select Fees Structure!'))
			for lines in rec.line_ids:
				if lines.discount > 0.00 and rec.discount_approval == False:
					raise ValidationError(_('Discount Invoices Need an Extra Approval , Click on Apply Concession button !'))
			# lines = []
			# for data in rec.fees_structure_id.line_ids or []:
			# 	line_vals = {'slip_id': rec.id,
			# 				 'name': data.name,
			# 				 'code': data.code,
			# 				 'type': data.type,
			# 				 'account_id': data.account_id.id,
			# 				 'amount': data.amount,
			# 				 'currency_id': data.currency_id.id or False,
			# 				 'currency_symbol': data.currency_symbol or False}
			# 	lines.append((0, 0, line_vals))
			# rec.write({'line_ids': lines})
			# Compute amount
			amount = 0
			for data in rec.line_ids:
				amount += data.price_subtotal
			rec.register_id.write({'total_amount': rec.total})
			rec.write({'total': amount,
					   'state': 'confirm',
					   'due_amount': amount,
					   'currency_id': rec.company_id.currency_id.id or False
					   })
		return True

	@api.multi
	def invoice_view(self):
		'''View number of invoice of student'''
		invoice_obj = self.env['account.invoice']
		for rec in self:
			invoices = invoice_obj.search([('student_payslip_id', '=',
											rec.id)])
			action = rec.env.ref('account.action_invoice_tree1').read()[0]
			if len(invoices) > 1:
				action['domain'] = [('id', 'in', invoices.ids)]
			elif len(invoices) == 1:
				action['views'] = [(rec.env.ref('account.invoice_form').id,
									'form')]
				action['res_id'] = invoices.ids[0]
			else:
				action = {'type': 'ir.actions.act_window_close'}
		return action

	@api.multi
	def action_move_create(self):
		cur_obj = self.env['res.currency']
		move_obj = self.env['account.move']
		move_line_obj = self.env['account.move.line']
		for fees in self:
			if not fees.journal_id.sequence_id:
				raise UserError(_('Please define sequence on'
								  'the journal related to this'
								  'invoice.'))
			if fees.move_id:
				continue
			ctx = self._context.copy()
			ctx.update({'lang': fees.student_id.lang})
			if not fees.payment_date:
				self.write([fees.id], {'payment_date': time.strftime
						   ('%Y-%m-%d')})
			company_currency = fees.company_id.currency_id.id
			diff_currency_p = fees.currency_id.id != company_currency
			current_currency = fees.currency_id and fees.currency_id.id\
				or company_currency
			account_id = False
			comapny_ac_id = False
			if fees.type in ('in_invoice', 'out_refund'):
				account_id = fees.student_id.property_account_payable.id
				cmpy_id = fees.company_id.partner_id
				comapny_ac_id = cmpy_id.property_account_receivable.id
			elif fees.type in ('out_invoice', 'in_refund'):
				account_id = fees.student_id.property_account_receivable.id
				cmp_id = fees.company_id.partner_id
				comapny_ac_id = cmp_id.property_account_payable.id
			if fees.journal_id.centralisation:
				raise UserError(_('You cannot create an invoice on a'
								  'centralized'
								  'journal. UnCheck the centralized'
								  'counterpart'
								  'box in the related journal from the'
								  'configuration menu.'))
			move = {'ref': fees.name,
					'journal_id': fees.journal_id.id,
					'date': fees.payment_date or time.strftime('%Y-%m-%d')}
			ctx.update({'company_id': fees.company_id.id})
			move_id = move_obj.create(move)
			context_multi_currency = self._context.copy()
			context_multi_currency.update({'date': time.strftime('%Y-%m-%d')})
			debit = 0.0
			credit = 0.0
			if fees.type in ('in_invoice', 'out_refund'):
				credit = cur_obj.compute(self._cr, self._uid,
										 fees.currency_id.id, company_currency,
										 fees.total,
										 context=context_multi_currency)
			elif fees.type in ('out_invoice', 'in_refund'):
				debit = cur_obj.compute(self._cr, self._uid,
										fees.currency_id.id, company_currency,
										fees.total,
										context=context_multi_currency)
			if debit < 0:
				credit = -debit
				debit = 0.0
			if credit < 0:
				debit = -credit
				credit = 0.0
			sign = debit - credit < 0 and -1 or 1
			cr_id = diff_currency_p and current_currency or False
			am_cr = diff_currency_p and sign * fees.total or 0.0
			date = fees.payment_date or time.strftime('%Y-%m-%d')
			move_line = {'name': fees.name or '/',
						 'move_id': move_id,
						 'debit': debit,
						 'credit': credit,
						 'account_id': account_id,
						 'journal_id': fees.journal_id.id,
						 'parent_id': fees.student_id.parent_id.id,
						 'currency_id': cr_id,
						 'amount_currency': am_cr,
						 'date': date}
			move_line_obj.create(move_line)
			cr_id = diff_currency_p and current_currency or False
			move_line = {'name': fees.name or '/',
						 'move_id': move_id,
						 'debit': credit,
						 'credit': debit,
						 'account_id': comapny_ac_id,
						 'journal_id': fees.journal_id.id,
						 'parent_id': fees.student_id.parent_id.id,
						 'currency_id': cr_id,
						 'amount_currency': am_cr,
						 'date': date}
			move_line_obj.create(move_line)
			fees.write({'move_id': move_id})
			move_obj.post([move_id])
		return True

	@api.multi
	def student_pay_fees(self):
		'''Generate invoice of student fee'''
		for rec in self:
			if rec.number == 'New':
				rec.number = self.env['ir.sequence'
									  ].next_by_code('student.payslip'
													 ) or _('New')
			rec.write({'state': 'pending'})
			partner = rec.student_id and rec.student_id.partner_id
			vals = {'partner_id': partner.id,
					'date_invoice': rec.date,
					'account_id': partner.property_account_receivable_id.id,
					'journal_id': rec.journal_id.id,
					'slip_ref': rec.number,
					'student_payslip_id': rec.id,
					'school_id':rec.school_id.id,
					'type': 'out_invoice'}
			invoice_line = []
			for line in rec.line_ids:
				acc_id = ''
				if line.account_id.id:
					acc_id = line.account_id.id
				else:
					# check type of invoice
					if rec.type in ('out_invoice', 'in_refund'):
						acc_id = rec.journal_id.default_credit_account_id.id
					else:
						acc_id = rec.journal_id.default_debit_account_id.id
				invoice_line_vals = {'name': line.name,
									 'account_id': acc_id,
									 'quantity': line.qty,
									 'price_unit': line.amount,
									 'discount': line.discount,
									 'uom_id': line.product_id.uom_id.id,
									 'product_id': line.product_id.id,
									 'price_subtotal': line.price_subtotal}
				invoice_line.append((0, 0, invoice_line_vals))
			vals.update({'invoice_line_ids': invoice_line})
			# creates invoice
			account_invoice_id = self.env['account.invoice'].create(vals)
			invoice_obj = self.env.ref('account.invoice_form')
			return {'name': _("Pay Fees"),
					'view_mode': 'form',
					'view_type': 'form',
					'res_model': 'account.invoice',
					'view_id': invoice_obj.id,
					'type': 'ir.actions.act_window',
					'nodestroy': True,
					'target': 'current',
					'res_id': account_invoice_id.id,
					'context': {}}


class StudentPayslipLineLine(models.Model):
	'''Function Line'''
	_name = 'student.payslip.line.line'
	_description = 'Function Line'
	_order = 'sequence'

	slipline_id = fields.Many2one('student.payslip.line', 'Slip Line')
	slipline1_id = fields.Many2one('student.fees.structure.line', 'Slip Line')
	sequence = fields.Integer('Sequence')
	from_month = fields.Many2one('academic.month', 'From Month')
	to_month = fields.Many2one('academic.month', 'To Month')


class AccountInvoice(models.Model):
	_inherit = "account.invoice"

	slip_ref = fields.Char('Fees Slip Reference',
						   help="Payslip Reference")
	student_payslip_id = fields.Many2one('student.payslip',
										 string="Student Payslip")


	@api.model
	def _prepare_refund(self, invoice, date_invoice=None, date=None, description=None, journal_id=None):
		value=super(AccountInvoice,self)._prepare_refund(invoice, date_invoice=None, date=None, description=None, journal_id=None)
		value['student_payslip_id']=invoice.student_payslip_id.id
		return value

	@api.multi
	def _get_payment_info_qweb(self):
		
		info = []
		if self.payment_move_line_ids:
			
			currency_id = self.currency_id
			for payment in self.payment_move_line_ids:
				payment_currency_id = False
				if self.type in ('out_invoice', 'in_refund'):
					amount = sum([p.amount for p in payment.matched_debit_ids if p.debit_move_id in self.move_id.line_ids])
					amount_currency = sum([p.amount_currency for p in payment.matched_debit_ids if p.debit_move_id in self.move_id.line_ids])
					if payment.matched_debit_ids:
						payment_currency_id = all([p.currency_id == payment.matched_debit_ids[0].currency_id for p in payment.matched_debit_ids]) and payment.matched_debit_ids[0].currency_id or False
				elif self.type in ('in_invoice', 'out_refund'):
					amount = sum([p.amount for p in payment.matched_credit_ids if p.credit_move_id in self.move_id.line_ids])
					amount_currency = sum([p.amount_currency for p in payment.matched_credit_ids if p.credit_move_id in self.move_id.line_ids])
					if payment.matched_credit_ids:
						payment_currency_id = all([p.currency_id == payment.matched_credit_ids[0].currency_id for p in payment.matched_credit_ids]) and payment.matched_credit_ids[0].currency_id or False
				# get the payment value in invoice currency
				if payment_currency_id and payment_currency_id == self.currency_id:
					amount_to_show = amount_currency
				else:
					amount_to_show = payment.company_id.currency_id.with_context(date=payment.date).compute(amount, self.currency_id)
				if float_is_zero(amount_to_show, precision_rounding=self.currency_id.rounding):
					continue
				payment_ref = payment.move_id.name
				if payment.move_id.ref:
					payment_ref += ' (' + payment.move_id.ref + ')'
				info.append({
					'name': payment.name,
					'journal_name': payment.journal_id.name,
					'amount': amount_to_show,
					'currency': currency_id.symbol,
					'digits': [69, currency_id.decimal_places],
					'position': currency_id.position,
					'date': payment.date,
					'payment_id': payment.id,
					'move_id': payment.move_id.id,
					'ref': payment_ref,
				})
		return info
	
	@api.multi
	def action_invoice_sent1(self):
		""" Open a window to compose an email, with the edi invoice template
			message loaded by default
		"""
		self.ensure_one()
		template = self.env.ref('school_fees.email_template_edi_invoice1', False)
		compose_form = self.env.ref('mail.email_compose_message_wizard_form', False)
		ctx = dict(
			default_model='account.invoice',
			default_res_id=self.id,
			default_use_template=bool(template),
			default_template_id=template and template.id or False,
			default_composition_mode='comment',
			mark_invoice_as_sent=True,
			custom_layout="school_fees.mail_template_data_notification_email_account_invoice1"
		)
		return {
			'name': _('Compose Email'),
			'type': 'ir.actions.act_window',
			'view_type': 'form',
			'view_mode': 'form',
			'res_model': 'mail.compose.message',
			'views': [(compose_form.id, 'form')],
			'view_id': compose_form.id,
			'target': 'new',
			'context': ctx,
		}


	
class AccountInvoiceRefund(models.TransientModel):
	"""Refunds invoice"""

	_inherit = "account.invoice.refund"
	_description = "Invoice Refund"

	date_invoice = fields.Date(string='Refund Date', default=fields.Date.context_today)
	# slip_ref1 = fields.Char('Fees Slip Reference',
	# 					   help="Payslip Reference")
	# student_payslip_id1 = fields.Many2one('student.payslip',
	# 									 string="Student Payslip")


class AccountPayment(models.Model):
	_inherit = "account.payment"

	 
	@api.multi
	def post(self):
		'''Method to change state to paid when state in invoice is paid'''
		res = super(AccountPayment, self).post()
		curr_date = datetime.now()
		refund_amount=0.0
		
		for rec in self:
			for invoice in rec.invoice_ids:
				vals = {'due_amount': invoice.residual}
				if invoice.student_payslip_id and invoice.state == 'paid':
					# Calculate paid amount and changes state to paid
					if invoice.type != 'out_refund':
						fees_payment = (invoice.student_payslip_id.paid_amount +
									rec.amount)
					else:
						fees_payment=(invoice.student_payslip_id.paid_amount +0)
						refund_amount=(invoice.student_payslip_id.refund_amount +rec.amount)
					vals = {'state': 'paid',
							'payment_date': curr_date,
							'move_id': invoice.move_id.id or False,
							'paid_amount': fees_payment,
							'due_amount': invoice.residual,
							'refund_amount': refund_amount,
							}
				if invoice.student_payslip_id and invoice.state == 'open':
					# Calculate paid amount and due amount and changes state
					# to pending
					# fees_payment = (invoice.student_payslip_id.paid_amount +
					# 				rec.amount)
					if invoice.type != 'out_refund':
						fees_payment = (invoice.student_payslip_id.paid_amount +
									rec.amount)
					else:
						fees_payment=(invoice.student_payslip_id.paid_amount +0)
						refund_amount=(invoice.student_payslip_id.refund_amount +rec.amount)
					vals = {'state': 'pending',
							'due_amount': invoice.residual,
							'paid_amount': fees_payment,
							'refund_amount': refund_amount,}
				invoice.student_payslip_id.write(vals)
				if invoice.student_payslip_id.student_id.state =="draft":
					invoice.student_payslip_id.student_id.write({'state':'invoiced'})
				elif invoice.student_payslip_id.student_id.state =="movesemester":
					invoice.student_payslip_id.student_id.write({'state':'invoiced'})
				elif invoice.student_payslip_id.student_id.state =="repeat":
					invoice.student_payslip_id.student_id.write({'state':'invoiced'})		
			
				client_obj = self.env['sms.smsclient'].search([],limit=1)
				student_obj = self.env['res.partner'].search([('id','=',rec.partner_id.id)])
				data={
					'gateway': client_obj.id,
					'mobile_to': student_obj.mobile,
					'text': "You have paid   " + str(rec.amount) +"  only, And your balance is  " + str(invoice.residual),
					'validity': client_obj.validity, 
					'classes': client_obj.classes, 
					'deferred': client_obj.deferred, 
					'priorirty': client_obj.priority, 
					'coding': client_obj.coding, 
					'tag': client_obj.tag, 
					'nostop': client_obj.nostop,
				}
				
				if not client_obj:
					raise UserError(_('You can only select one partner'))
				else:
					client_obj.send_msg_2(data)
		return res
	@api.multi
	def _get_default_journal(self):
		return self.env['account.journal'].search([('type', '=', 'cash')], limit=1).id	


	journal_id = fields.Many2one('account.journal', string='Payment Journal', required=True, domain=[('type', 'in', ('bank', 'cash'))],default=_get_default_journal)	
	communication = fields.Char(string='Description')
	school_id = fields.Many2one('school.school', 'Campus')

	
	@api.model
	def default_get(self, fields):
		rec = super(AccountPayment, self).default_get(fields)
		invoice_defaults = self.resolve_2many_commands('invoice_ids', rec.get('invoice_ids'))
		if invoice_defaults and len(invoice_defaults) == 1:
			invoice = invoice_defaults[0]
			rec['communication'] = invoice['reference'] or invoice['name'] or invoice['number']
			rec['currency_id'] = invoice['currency_id'][0]
			rec['payment_type'] = invoice['type'] in ('out_invoice', 'in_refund') and 'inbound' or 'outbound'
			rec['partner_type'] = MAP_INVOICE_TYPE_PARTNER_TYPE[invoice['type']]
			rec['partner_id'] = invoice['partner_id'][0]
			rec['amount'] = invoice['residual']
			rec['school_id'] = invoice['school_id']
		return rec



	def _get_move_vals(self, journal=None):
		""" Return dict to create the payment move
		"""
		journal = journal or self.journal_id
		if not journal.sequence_id:
			raise UserError(_('Configuration Error !'), _('The journal %s does not have a sequence, please specify one.') % journal.name)
		if not journal.sequence_id.active:
			raise UserError(_('Configuration Error !'), _('The sequence of journal %s is deactivated.') % journal.name)
		name = self.move_name or journal.with_context(ir_sequence_date=self.payment_date).sequence_id.next_by_id()
		return {
			'name': name,
			'date': self.payment_date,
			'ref': self.communication or '',
			'company_id': self.company_id.id,
			'journal_id': journal.id,
			'school_id': self.school_id.id,
		}
