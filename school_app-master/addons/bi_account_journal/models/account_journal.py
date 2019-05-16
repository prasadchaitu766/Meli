from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import amount_to_text_en, float_round
import odoo.addons.decimal_precision as dp
#==================================================
# Class : BiAccountReceipt
# Description : Account Receipt Details
#==================================================
class BiAccountReceipt(models.Model):
	_name = "bi.account.receipt"
	_description = "Account Receipt Details"

	@api.depends('receipt_ids.price_total')
	def _compute_total(self):
		for receipt in self:
			amount_untaxed = amount_tax = 0.0
			for line in receipt.receipt_ids:
				amount_untaxed += line.price_subtotal
				# FORWARDPORT UP TO 10.0
				if receipt.company_id.tax_calculation_rounding_method == 'round_globally':
					taxes = line.tax_id.compute_all(line.amount, line.currency_id, 1, product=False, partner=False)
					amount_tax += sum(t.get('amount', 0.0) for t in taxes.get('taxes', []))
				else:
					amount_tax += line.price_tax
			receipt.update({
				'subtotal': receipt.currency_id.round(amount_untaxed),
				'amount_tax': receipt.currency_id.round(amount_tax),
				'total': amount_untaxed + amount_tax,
			})

	
	name = fields.Char(string="Sequence No", required=True, Index= True, default=lambda self:('New'), readonly=True, states={'draft': [('readonly',False)]})
	receipt_date = fields.Date(string="Receipt Date", default=fields.Date.context_today, required=True, readonly=True, states={'draft': [('readonly',False)]})
	customer = fields.Many2one('res.partner', string = "Customer", readonly=True, states={'draft': [('readonly',False)]})
	journal_id =  fields.Many2one('account.journal',string="Journal ID", required=True, readonly=True, states={'draft': [('readonly',False)]}, domain=[('type', 'in', ('bank', 'cash'))])  
	account_id = fields.Many2one('account.account',string="Account ID" , required=True, readonly=True, states={'draft': [('readonly',False)]})
	narration = fields.Text(string="Narration")
	receipt_ids =  fields.One2many('bi.account.receipt.line','receipt_id',string="Accounts",readonly=True, states={'draft': [('readonly', False)]})
	user_id = fields.Many2one('res.users',string='Username',default=lambda self: self.env.user)
	move_id = fields.Many2one('account.move', string='Journal Entry',readonly=True, index=True, ondelete='restrict', copy=False,
		help = "Link to the automatically generated Journal Items.")
	state = fields.Selection([
		('draft', 'Draft'),
		('post', 'Posted'),
		('cancel', 'Cancelled'),
		], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', default='draft')
	company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env['res.company']._company_default_get('sale.order'), states={'post': [('readonly',True)]})
	total = fields.Monetary(compute='_compute_total', string='Total', readonly=True, store=True)
	currency_id = fields.Many2one('res.currency', string='Currency',default=lambda self: self.env.user.company_id.currency_id,readonly=True, states={'draft': [('readonly', False)]})
	amount_tax = fields.Monetary(string='Amount Tax',store=True, readonly=True, compute='_compute_total',digits_compute=dp.get_precision('Product Price'))
	subtotal = fields.Monetary(string='Sub Total',store=True, readonly=True, compute='_compute_total',digits_compute=dp.get_precision('Product Price'))
	bank_type = fields.Selection([('cheque','Cheque'),('ntfs','NTFS'),('cash','Cash'),('others','Others')],string="Payment Type",readonly=True, states={'draft': [('readonly', False)]})
	cheque_no = fields.Char("Cheque Number")
	Cheque_date = fields.Date("Cheque Date")
	school_id = fields.Many2one('school.school', 'Campus')

	
	@api.onchange('journal_id')
	def onchange_journal_id(self):
		if self.journal_id:
			self.account_id = self.journal_id.default_debit_account_id

	
	
	# @api.model
	# def create(self, vals):
	# 	if vals.get('name', _('New')) == _('New'):
	# 		if 'company_id' in vals:
	# 			vals['name'] = self.env['ir.sequence'].with_context(force_company=vals['company_id']).next_by_code('bi.account.receipt') or _('New')
	# 		else:
	# 			vals['name'] = self.env['ir.sequence'].next_by_code('bi.account.receipt') or _('New')

				
	# 	result = super(BiAccountReceipt, self).create(vals)
	# 	return result

	
	@api.multi
	def button_post(self):
		aml_dict = {}
		total=0.0
		aml_obj = self.env['account.move.line'].with_context(check_move_validity=False)
		for receipt in self:
			dst_move = self.env['account.move'].create({
														
														'date': receipt.receipt_date,
														'ref':'Receipt',
														'company_id': receipt.company_id.id,
														'journal_id':receipt.journal_id.id,
														'school_id':receipt.school_id.id,
														})
			company_currency = receipt.company_id.currency_id
			for line in receipt.receipt_ids:				
				debit, credit, amount_currency, currency_id = aml_obj.with_context(date=self.receipt_date).compute_amount_fields(line.price_subtotal, self.currency_id, self.company_id.currency_id, company_currency)
				i=1
				
				aml_dict={
						'name':(receipt.cheque_no and '-'+str(receipt.cheque_no) or '')+'-'+(line.name and str(line.name) or ''),
						'account_id': line.account_id.id,
						'currency_id': currency_id and currency_id or False,	            
						'journal_id': receipt.journal_id.id,
						'debit':0.0,
						'analytic_account_id':line.analytic_account_id and line.analytic_account_id.id or False,
						'credit':debit,#line.price_subtotal,
						'partner_id':receipt.customer.id,
						'move_id':dst_move.id,
						'amount_currency': amount_currency and amount_currency*-1 or  0.0,
					}
				total = total + line.price_subtotal
				aml_obj.create(aml_dict)
				if line.tax_id:
					for tax in line.tax_id.compute_all(line.amount, line.currency_id, 1)['taxes']:
						debit, credit, amount_currency, currency_id = aml_obj.with_context(date=self.receipt_date).compute_amount_fields(tax['amount'], self.currency_id, self.company_id.currency_id, company_currency)
						aml_dict={
						'name':_('Tax') + ' ' + tax['name'],
						'account_id': tax['account_id'],
						'debit': ((debit < 0) and -debit) or 0.0,
						'credit': ((debit > 0) and debit) or 0.0,
						'move_id':dst_move.id,
						'analytic_account_id': tax['analytic'] and line.analytic_account_id.id or False,
						'amount_currency': debit > 0 and amount_currency*-1 or  amount_currency,
						'currency_id': currency_id and currency_id or False,
						}
						aml_obj.create(aml_dict)
						total = total +tax['amount']

			if total> 0:
				debit, credit, amount_currency, currency_id = aml_obj.with_context(date=self.receipt_date).compute_amount_fields(total, self.currency_id, self.company_id.currency_id, company_currency)
				
				aml_dict.update({
					'name': (receipt.cheque_no and '-'+str(receipt.cheque_no) or '')+'-'+(line.name and str(line.name) or ''),
					'account_id': receipt.journal_id.default_debit_account_id.id,
					'currency_id': currency_id and currency_id or False,          
					'journal_id': receipt.journal_id.id,
					'credit':0.0,
					'debit':debit,#total,
					'analytic_account_id':False,
					'partner_id':receipt.customer.id,
					'move_id':dst_move.id,
					'amount_currency': amount_currency and amount_currency or  0.0,
					})            
				aml_obj.create(aml_dict)
			dst_move.post()
			receipt.write({'state':'post','move_id':dst_move.id,'name':dst_move.name})

	@api.multi
	def button_cancel(self):
		if self.move_id:
			self.move_id.button_cancel()
			move_id = self.move_id	
			self.write({'state': 'cancel','move_id' : False})
			move_id.unlink()


	@api.multi
	def button_draft(self):		
		self.write({'state': 'draft'})
		


	@api.multi
	def unlink(self):
		for order in self:
			if order.state not in ('draft'):
				raise UserError(_('You can not delete receipt voucher'))
		return super(BiAccountReceipt, self).unlink()



	@api.multi
	def get_check_amount_in_words(self, amount):
		# TODO: merge, refactor and complete the amount_to_text and amount_to_text_en classes
		check_amount_in_words = amount_to_text_en.amount_to_text(amount, lang='en', currency='')
		check_amount_in_words = check_amount_in_words.replace('Cents', ' Only') # Ugh
		check_amount_in_words = check_amount_in_words.replace('Cent', ' Only') 
		decimals = amount % 1
		# if decimals >= 10**-2:
		# 	check_amount_in_words += _(' and %s/100') % str(int(round(float_round(decimals*100, precision_rounding=1))))
		return check_amount_in_words

	@api.onchange('account_id')
	def OnchangeAccount(self):
		for x in self:
			x.tax_id = self.account_id.tax_ids
				
#==================================================
# Class : BiAccountReceiptLine
# Description : Account Receipt Line
#==================================================
class BiAccountReceiptLine(models.Model):

	_name = "bi.account.receipt.line"
	_description = "Account Receipt Line"

	@api.depends('amount', 'tax_id')
	def _compute_amount(self):
		for line in self:
			taxes = line.tax_id.compute_all(line.amount, line.currency_id,1, product=False, partner=False)
			line.update({
				'price_tax': taxes['total_included'] - taxes['total_excluded'],
				'price_total': taxes['total_included'],
				'price_subtotal': taxes['total_excluded'],
			})
	
	receipt_id = fields.Many2one('bi.account.receipt',string="Receipt")
	tax_id = fields.Many2many('account.tax', string='Taxes', domain=['|', ('active', '=', False), ('active', '=', True)])
	account_id = fields.Many2one('account.account', domain=[] , string="Account ID", required=True)
	analytic_account_id = fields.Many2one('account.analytic.account',"Analytic Account")
	name = fields.Char(string="Description", required=True)
	amount = fields.Float(string="Amount", required=True)
	currency_id = fields.Many2one('res.currency', related='receipt_id.currency_id', store=True, related_sudo=False)
	price_subtotal = fields.Monetary(compute='_compute_amount', string='Subtotal', store=True)
	price_total = fields.Monetary(compute='_compute_amount', string='Total', store=True)
	price_tax = fields.Monetary(compute='_compute_amount', string='Tax', store=True)

#==================================================
# Class : BiAccountPayment
# Description : Account Payment Details
#==================================================
class BiAccountPayment(models.Model):
	_name = "bi.account.payment"
	_description = "Account Payment Details"

	@api.depends('payment_ids.price_total')
	def _compute_total(self):
		for payment in self:
			amount_untaxed = amount_tax = 0.0
			for line in payment.payment_ids:
				amount_untaxed += line.price_subtotal
				# FORWARDPORT UP TO 10.0
				if payment.company_id.tax_calculation_rounding_method == 'round_globally':
					taxes = line.tax_id.compute_all(line.amount, line.currency_id, 1, product=False, partner=False)
					amount_tax += sum(t.get('amount', 0.0) for t in taxes.get('taxes', []))
				else:
					amount_tax += line.price_tax
			payment.update({
				'subtotal': payment.currency_id.round(amount_untaxed),
				'amount_tax': payment.currency_id.round(amount_tax),
				'total': amount_untaxed + amount_tax,
			})


	name = fields.Char(string="Sequence No", required=True, Index= True, default=lambda self:('New'), readonly=True, states={'draft': [('readonly',False)]})
	payment_date = fields.Date(string="Payment Date", default=fields.Date.context_today, required=True, readonly=True, states={'draft': [('readonly',False)]})
	customer = fields.Many2one('res.partner', string = "Customer", readonly=True, states={'draft': [('readonly',False)]})
	journal_id =  fields.Many2one('account.journal',string="Journal ID", required=True, readonly=True, states={'draft': [('readonly',False)]}, domain=[('type', 'in', ('bank', 'cash'))])  
	account_id =  fields.Many2one('account.account', string="Account ID", required=True, readonly=True, states={'draft': [('readonly',False)]})
	narration = fields.Text(string="Narration")
	user_id = fields.Many2one('res.users',string='Username',default=lambda self: self.env.user)
	payment_ids =  fields.One2many('bi.account.voucher.payment.line','receipt_id',string="Accounts",readonly=True, states={'draft': [('readonly', False)]})
	# currency_id = fields.Many2one('res.currency', string='Currency',default=lambda self: self.env.user.company_id.currency_id)
	move_id = fields.Many2one('account.move', string='Journal Entry',readonly=True, index=True, ondelete='restrict', copy=False,
		help = "Link to the automatically generated Journal Items.")	
	company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env['res.company']._company_default_get('sale.order'), states={'post': [('readonly',True)]})
	state = fields.Selection([
		('draft', 'Draft'),
		('post', 'Posted'),
		('cancel', 'Cancelled'),
		], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', default='draft')
	total = fields.Monetary(compute='_compute_total', string='Total', readonly=True, store=True)
	currency_id = fields.Many2one('res.currency', string='Currency',default=lambda self: self.env.user.company_id.currency_id,readonly=True, states={'draft': [('readonly', False)]})
	amount_tax = fields.Monetary(string='Amount Tax',store=True, readonly=True, compute='_compute_total',digits_compute=dp.get_precision('Product Price'))
	subtotal = fields.Monetary(string='Sub Total',store=True, readonly=True, compute='_compute_total',digits_compute=dp.get_precision('Product Price'))
	bank_type = fields.Selection([('cheque','Cheque'),('ntfs','NTFS'),('cash','Cash'),('others','Others')],string="Payment Type", states={'draft': [('readonly', False)]})
	cheque_no = fields.Char("Cheque Number")
	Cheque_date = fields.Date("Cheque Date")
	school_id = fields.Many2one('school.school', 'Campus')


	
	# @api.onchange('journal_id')
	# def _onchange_journal_id(self):
	# 	if self.journal_id:
	# 		self.account_id = self.journal_id.account_id

	@api.onchange('journal_id')
	def onchange_journal_id(self):
		if self.journal_id:
			self.account_id = self.journal_id.default_credit_account_id
		
	@api.multi
	def button_cancel(self):
		if self.move_id:
			self.move_id.button_cancel()
			move_id = self.move_id	
			self.write({'state': 'cancel','move_id' : False})
			move_id.unlink()


	@api.multi
	def button_draft(self):		
		self.write({'state': 'draft'})

	# @api.model
	# def create(self, vals):
	# 	if vals.get('name', _('New')) == _('New'):
	# 		if 'company_id' in vals:
	# 			vals['name'] = self.env['ir.sequence'].with_context(force_company=vals['company_id']).next_by_code('bi.account.payment') or _('New')
	# 		else:
	# 			vals['name'] = self.env['ir.sequence'].next_by_code('bi.account.payment') or _('New')

				
	# 	result = super(BiAccountPayment, self).create(vals)
	# 	return result

	@api.multi
	def button_post(self):
		aml_dict = {}
		total=0.0
		aml_obj = self.env['account.move.line'].with_context(check_move_validity=False)
		for payment in self:
			dst_move = self.env['account.move'].create({
														# 'name': payment.name,
														'date': payment.payment_date,
														'ref':'Payment',
														'company_id': payment.company_id.id,
														'journal_id':payment.journal_id.id,
														'school_id':payment.school_id.id,
														})
			company_currency = payment.company_id.currency_id
			for line in payment.payment_ids:
				debit, credit, amount_currency, currency_id = aml_obj.with_context(date=self.payment_date).compute_amount_fields(line.price_subtotal, self.currency_id, self.company_id.currency_id, company_currency)
				i=1
				aml_dict={
						'name':(payment.cheque_no and 'CH.No:'+str(payment.cheque_no) or '')+'-'+(line.name and '-'+str(line.name) or ''),
						'account_id': line.account_id.id,
						'currency_id': currency_id and currency_id or False,
						'journal_id': payment.journal_id.id,
						'debit':debit,
						'analytic_account_id':line.analytic_account_id and line.analytic_account_id.id or False,
						'credit':0.0,
						'partner_id':payment.customer.id,
						'move_id':dst_move.id,
						'move_id':dst_move.id,
						'amount_currency': amount_currency and amount_currency or  0.0,
					}
				total = total + line.price_subtotal
				aml_obj.create(aml_dict)
				if line.tax_id:
					for tax in line.tax_id.compute_all(line.amount, line.currency_id, 1)['taxes']:
						debit, credit, amount_currency, currency_id = aml_obj.with_context(date=self.payment_date).compute_amount_fields(tax['amount'], self.currency_id, self.company_id.currency_id, company_currency)
						aml_dict={
						'name':_('Tax') + ' ' + tax['name'],
						'account_id': tax['account_id'],
						'debit': ((debit > 0) and debit) or 0.0,
						'credit': ((debit < 0) and -debit) or 0.0,
						'move_id':dst_move.id,
						'analytic_account_id': tax['analytic'] and line.analytic_account_id.id or False,
						'move_id':dst_move.id,
						'amount_currency':  debit < 0 and amount_currency*-1 or  amount_currency,
						'currency_id': currency_id and currency_id or False,
						}
						aml_obj.create(aml_dict)
						total = total +tax['amount']
			if total> 0:
				debit, credit, amount_currency, currency_id = aml_obj.with_context(date=self.payment_date).compute_amount_fields(total, self.currency_id, self.company_id.currency_id, company_currency)
				aml_dict.update({
					'name':(payment.cheque_no and 'CH.No:'+str(payment.cheque_no) or '')+'-'+(line.name and '-'+str(line.name) or ''),
					'account_id': payment.journal_id.default_debit_account_id.id,
					'currency_id': currency_id and currency_id or False,
					'journal_id': payment.journal_id.id,
					'credit':debit,
					'debit':0.0,
					'analytic_account_id':False,
					'partner_id':payment.customer.id,
					'move_id':dst_move.id,
					'amount_currency': amount_currency and amount_currency*-1 or  0.0,
					})            
				aml_obj.create(aml_dict)
			dst_move.post()
			payment.write({'state':'post','move_id':dst_move.id,'name':dst_move.name})


	@api.multi
	def unlink(self):
		for order in self:
			if order.state not in ('draft'):
				raise UserError(_('You can not delete payment voucher'))
		return super(BiAccountPayment, self).unlink()


	

	@api.multi
	def get_check_amount_in_words(self, amount):
		# TODO: merge, refactor and complete the amount_to_text and amount_to_text_en classes
		check_amount_in_words = amount_to_text_en.amount_to_text(amount, lang='en', currency='')
		check_amount_in_words = check_amount_in_words.replace('Cents', ' Only') # Ugh
		check_amount_in_words = check_amount_in_words.replace('Cent', ' Only') 
		decimals = amount % 1
		# if decimals >= 10**-2:
		# 	check_amount_in_words += _(' and %s/100') % str(int(round(float_round(decimals*100, precision_rounding=1))))
		return check_amount_in_words	

	@api.onchange('account_id')
	def OnchangeAccount(self):
		for x in self:
			x.tax_id = self.account_id.tax_ids
	
#==================================================
# Class : BiAccountPaymentLine
# Description : Account Payment Line
#==================================================
class BiAccountVoucherPaymentLine(models.Model):
	_name = "bi.account.voucher.payment.line"
	_description = "Account Payment Line"

	@api.depends('amount', 'tax_id')
	def _compute_amount(self):
		for line in self:
			taxes = line.tax_id.compute_all(line.amount, line.currency_id,1, product=False, partner=False)
			line.update({
				'price_tax': taxes['total_included'] - taxes['total_excluded'],
				'price_total': taxes['total_included'],
				'price_subtotal': taxes['total_excluded'],
			})

	receipt_id = fields.Many2one('bi.account.payment', string="Receipt")
	analytic_account_id = fields.Many2one('account.analytic.account',"Analytic Account")
	tax_id = fields.Many2many('account.tax', string='Taxes', domain=['|', ('active', '=', False), ('active', '=', True)])
	account_id = fields.Many2one('account.account', domain=[], string="Account ID", required=True)
	name = fields.Char(string="Description", required=True)
	amount = fields.Float(string="Amount", required=True)
	currency_id = fields.Many2one('res.currency', related='receipt_id.currency_id', store=True, related_sudo=False)
	price_subtotal = fields.Monetary(compute='_compute_amount', string='Subtotal', store=True)
	price_total = fields.Monetary(compute='_compute_amount', string='Total', store=True)
	price_tax = fields.Monetary(compute='_compute_amount', string='Tax', store=True)

