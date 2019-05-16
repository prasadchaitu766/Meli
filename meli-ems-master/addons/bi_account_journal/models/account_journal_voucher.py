from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools import amount_to_text_en, float_round
import odoo.addons.decimal_precision as dp
#==================================================
# Class : BiJournalVoucher
# Description : Account Receipt Details
#==================================================
class BiJournalVoucher(models.Model):
	_name = "bi.journal.voucher"
	_description = "Journal Voucher Details"

	@api.multi
	def _get_default_journal(self):
		return self.env['account.journal'].search([('type', '=', 'general')], limit=1).id

	
	name = fields.Char(string="Sequence No", required=True, Index= True, default=lambda self:('New'), readonly=True, states={'draft': [('readonly',False)]})
	receipt_date = fields.Date(string="Voucher Date", default=fields.Date.context_today, required=True, readonly=True, states={'draft': [('readonly',False)]})
	customer = fields.Many2one('res.partner', string = "Customer", readonly=True, states={'draft': [('readonly',False)]})
	journal_id =  fields.Many2one('account.journal',string="Journal ID", required=True, readonly=True, states={'draft': [('readonly',False)]}, default=_get_default_journal, domain=[('type', '=', 'general')])  
	account_id = fields.Many2one('account.account',string="Account ID", readonly=True, states={'draft': [('readonly',False)]})
	narration = fields.Text(string="Narration")
	receipt_ids =  fields.One2many('bi.journal.voucher.line','receipt_id',string="Accounts",readonly=True, states={'draft': [('readonly', False)]})	
	user_id = fields.Many2one('res.users',string='Username',default=lambda self: self.env.user)
	move_id = fields.Many2one('account.move', string='Journal Entry',readonly=True, index=True, ondelete='restrict', copy=False,
		help = "Link to the automatically generated Journal Items.")
	state = fields.Selection([
		('draft', 'Draft'),
		('post', 'Posted'),
		('cancel', 'Cancelled'),
		], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', default='draft')
	company_id = fields.Many2one('res.company', 'Company', default=lambda self: self.env['res.company']._company_default_get('sale.order'), states={'post': [('readonly',True)]})
	currency_id = fields.Many2one('res.currency', string='Currency',default=lambda self: self.env.user.company_id.currency_id,readonly=True, states={'draft': [('readonly', False)]})
	bank_type = fields.Selection([('cheque','Cheque'),('ntfs','NTFS'),('cash','Cash'),('others','Others')],string="Payment Type",readonly=True, states={'draft': [('readonly', False)]})
	cheque_no = fields.Char("Cheque Number")
	Cheque_date = fields.Date("Cheque Date")
	vendor_invoice = fields.Char(string="Vendor Invoice" , store=True)
	school_id = fields.Many2one('school.school', 'Campus')

	_sql_constraints = [
		  ('vendor_invoice', 'unique( vendor_invoice )', 'Vendor Invoice must be unique.')   ]

	
	@api.multi
	def button_post(self):
		aml_dict = {}
		total=0.0
		aml_obj = self.env['account.move.line'].with_context(check_move_validity=False)
		for receipt in self:
			dst_move = self.env['account.move'].create({
														
														'date': receipt.receipt_date,
														'ref':('Receipt'+' - '+str(receipt.vendor_invoice)),
														'company_id': receipt.company_id.id,
														'journal_id':receipt.journal_id.id,
														'school_id':receipt.school_id.id,
														})
			company_currency = receipt.company_id.currency_id
			for line in receipt.receipt_ids:
				if line.credit_amount>0:
					debit, credit, amount_currency, currency_id = aml_obj.with_context(date=self.receipt_date).compute_amount_fields(line.credit_amount, self.currency_id, self.company_id.currency_id, company_currency)
					i=1
					aml_dict={
							'name':(receipt.cheque_no and '-'+str(receipt.cheque_no) or '')+'-'+(line.name and str(line.name) or ''),
							'account_id': line.account_id.id,
							'currency_id': receipt.currency_id.id,	
							'currency_id': currency_id and currency_id or False,	                        
							'journal_id': receipt.journal_id.id,
							'debit':0.0,
							'analytic_account_id':line.analytic_account_id and line.analytic_account_id.id or False,
							'credit':debit,
							'partner_id':line.partner_id.id,
							'move_id':dst_move.id,
							'amount_currency': amount_currency and amount_currency*-1 or  0.0,
						}
					aml_obj.create(aml_dict)
				if 	line.debit_amount>0:
					debit, credit, amount_currency, currency_id = aml_obj.with_context(date=self.receipt_date).compute_amount_fields(line.debit_amount, self.currency_id, self.company_id.currency_id, company_currency)
					aml_dict.update({
						'name': (receipt.cheque_no and '-'+str(receipt.cheque_no) or '')+'-'+(line.name and str(line.name) or ''),
						'account_id': line.account_id.id,
						'currency_id': currency_id and currency_id or False,          
						'journal_id': receipt.journal_id.id,
						'credit':0.0,
						'debit':debit,
						'analytic_account_id':False,
						'partner_id':line.partner_id.id,
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
		return super(BiJournalVoucher, self).unlink()



	@api.multi
	def get_check_amount_in_words(self, amount):
		# TODO: merge, refactor and complete the amount_to_text and amount_to_text_en classes
		check_amount_in_words = amount_to_text_en.amount_to_text(amount, lang='en', currency='')
		check_amount_in_words = check_amount_in_words.replace('Cents', ' Only') # Ugh
		check_amount_in_words = check_amount_in_words.replace('Cent', ' Only') 
		decimals = amount % 1
		
		return check_amount_in_words

	@api.onchange('account_id')
	def OnchangeAccount(self):
		for x in self:
			x.tax_id = self.account_id.tax_ids
				
#==================================================
# Class : BiAccountReceiptLine
# Description : Account Receipt Line
#==================================================
class BiAccountVoucherLine(models.Model):

	_name = "bi.journal.voucher.line"
	_description = "Journal Voucher Line"

	receipt_id = fields.Many2one('bi.journal.voucher',string="Receipt")
	tax_id = fields.Many2many('account.tax', string='Taxes', domain=['|', ('active', '=', False), ('active', '=', True)])
	account_id = fields.Many2one('account.account', domain=[] , string="Account ID", required=True)
	analytic_account_id = fields.Many2one('account.analytic.account',"Analytic Account")
	name = fields.Char(string="Description", required=True)
	credit_amount = fields.Float(string="Credit Amount", required=False)
	debit_amount = fields.Float(string="Debit Amount", required=False)
	currency_id = fields.Many2one('res.currency', related='receipt_id.currency_id', store=True, related_sudo=False)
	partner_id = fields.Many2one('res.partner', string = "Partner Account")

	sql_constraints = [
		('credit_debit1', 'CHECK (credit_amount*debit_amount=0)', 'Wrong credit or debit value in accounting entry !'),
		('credit_debit2', 'CHECK (credit_amount+debit_amount>=0)', 'Wrong credit or debit value in accounting entry !'),
	]

	@api.onchange('partner_id')
	def _onchange_partner_id(self):
		if self.partner_id:
			if self.partner_id.customer == True:
				self.account_id = self.partner_id.property_account_receivable_id.id
			if self.partner_id.supplier ==True:
				self.account_id = self.partner_id.property_account_payable_id.id
