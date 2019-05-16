# -*- coding: utf-8 -*-
import datetime
from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import UserError,ValidationError
date_format = "%Y-%m-%d"


class HrResignation(models.Model):
	_name = 'hr.resignation'
	_inherit = 'mail.thread'
	_rec_name = 'employee_id'

	def _get_employee_id(self):
		# assigning the related employee of the logged in user
		employee_rec = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
		return employee_rec.id

	name = fields.Char(string='Order Reference', required=True, copy=False, readonly=True, index=True,
					   default=lambda self: _('New'))
	employee_id = fields.Many2one('hr.employee', string="Employee", default=_get_employee_id,
								  help='Name of the employee for whom the request is creating')
	department_id = fields.Many2one('hr.department', string="Department", related='employee_id.department_id',
									help='Department of the employee')
	joined_date = fields.Date(string="Join Date", required=True, related='employee_id.date_of_join',
							  help='Joining date of the employee')
	expected_revealing_date = fields.Date(string="Revealing Date", required=True,
										  help='Date on which he is revealing from the company')
	resign_confirm_date = fields.Date(string="Resign confirm date", help='Date on which the request is confirmed')
	approved_revealing_date = fields.Date(string="Approved Date", help='The date approved for the revealing')
	reason = fields.Text(string="Reason", help='Specify reason for leaving the company')
	notice_period = fields.Char(string="Notice Period", compute='_notice_period')
	state = fields.Selection([('draft', 'Draft'), ('confirm', 'Confirm'), ('approved', 'Approved'), ('cancel', 'Cancel'),('rejected','Rejected')],
							 string='Status', default='draft')
	resignation_ids = fields.One2many("hr.resignation.line",'resignation_id',"Clearance Stock")

	@api.model
	def create(self, vals):
		# assigning the sequence for the record
		if vals.get('name', _('New')) == _('New'):
			vals['name'] = self.env['ir.sequence'].next_by_code('hr.resignation') or _('New')
		res = super(HrResignation, self).create(vals)
		return res
		due_check_mail_notification = self.env['ir.model.data'].sudo().get_object('hr_resignation', 'resignation_mail_due_check')
		if due_check_mail_notification:    
			create_and_send_email = self.env['mail.mail'].create(due_check_mail_notification).send()
		return True
		
	@api.constrains('employee_id')
	def check_employee(self):
		# Checking whether the user is creating resignation request of his/her own
		for rec in self:
			if not self.env.user.has_group('hr.group_hr_user'):
				if rec.employee_id.user_id.id and rec.employee_id.user_id.id != self.env.uid:
					raise ValidationError(_('You cannot create request for other employees'))

	@api.onchange('employee_id')
	@api.depends('employee_id')
	def check_request_existence(self):
		# Check whether any resignation request already exists
		for rec in self:
			if rec.employee_id:
				resignation_request = self.env['hr.resignation'].search([('employee_id', '=', rec.employee_id.id),
																		 ('state', 'in', ['confirm', 'approved'])])
				# if resignation_request:
				# 	raise ValidationError(_('There is a resignation request in confirmed or'
				# 							' approved state for this employee'))

	@api.multi
	def _notice_period(self):
		# calculating the notice period for the employee
		for rec in self:
			if rec.approved_revealing_date and rec.resign_confirm_date:
				approved_date = datetime.strptime(rec.approved_revealing_date, date_format)
				confirmed_date = datetime.strptime(rec.resign_confirm_date, date_format)
				notice_period = approved_date - confirmed_date
				rec.notice_period = notice_period.days

	@api.constrains('joined_date', 'expected_revealing_date')
	def _check_dates(self):
		# validating the entered dates
		for rec in self:
			resignation_request = self.env['hr.resignation'].search([('employee_id', '=', rec.employee_id.id),
																	 ('state', 'in', ['confirm', 'approved'])])
			# if resignation_request:
			# 	raise ValidationError(_('There is a resignation request in confirmed or'
			# 							' approved state for this employee'))
			if rec.joined_date >= rec.expected_revealing_date:
				raise ValidationError(_('Revealing date must be anterior to joining date'))
			
	@api.multi
	def confirm_resignation(self):
		for rec in self:
			rec.state = 'confirm'
			rec.resign_confirm_date = datetime.now()
			data = {}
			data_line = []
			clearance = self.env['account.asset.asset'].search([('employee_id','=',rec.employee_id.id),('state','=','open'),('active','=',True)])
			for res in clearance:
				data = self.env['hr.resignation.line'].create({
					'serial_no': res.serial_no,
					'name': res.id,
					'category_id':res.category_id.id,
					'resignation_id':rec.id,

				})
				data_line.append(data.id)
		self.send_mail_template()

	@api.multi
	def send_mail_template(self):
		# Find the e-mail template
		template = self.env.ref('hr_resignation.resignation_request_mail')
		# You can also find the e-mail template like this:
		# template = self.env['ir.model.data'].get_object('mail_template_demo', 'example_email_template')
 
		# Send out the e-mail template to the user
		self.env['mail.template'].browse(template.id).send_mail(self.id)
	
	@api.multi
	def cancel_resignation(self):
		for rec in self:
			rec.state = 'cancel'

	@api.multi
	def reject_resignation(self):
		for rec in self:
			rec.state = 'rejected'

	@api.multi
	def approve_resignation(self):
		for rec in self:
			if not rec.approved_revealing_date:
				raise ValidationError(_('Enter Approved Revealing Date'))
			if rec.approved_revealing_date and rec.resign_confirm_date:
				if rec.approved_revealing_date <= rec.resign_confirm_date:
					raise ValidationError(_('Approved revealing date must be anterior to confirmed date'))
				rec.employee_id.state ='resign'
				rec.employee_id.resign_date = rec.expected_revealing_date
				assign = {}
				for obj in self.resignation_ids:
					obj.name.write({'employee_id': obj.employee_assign.id})	
					obj.name.onchange_product_id()		
				rec.state = 'approved'


class HrResignationLine(models.Model):
	_name = 'hr.resignation.line'

	category_id = fields.Many2one('account.asset.category', string='Category', required=True)
	resignation_id = fields.Many2one('hr.resignation',"Resignation")
	serial_no = fields.Char(string="Serial No", required=True)
	name = fields.Many2one('account.asset.asset',string='Asset Name', required=True)
	employee_assign = fields.Many2one('hr.employee', string="Assign to Employee",required=True, domain=[('state', '=', 'draft')])
