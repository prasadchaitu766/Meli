from datetime import datetime, timedelta, date
from odoo import api, fields, models, tools, SUPERUSER_ID, _
from odoo.exceptions import UserError, AccessError
from ast import literal_eval

class MaterialRequest(models.Model):
	_name = "material.request"
	_description = "Internal Material Request"
	_order = "id desc"
	@api.multi
	def _get_default_picking_type(self):
		
		return self.env['stock.picking.type'].search([('name', '=', 'Internal Transfers')], limit=1).id

	def _get_employee_id(self):
		# assigning the related employee of the logged in user
		employee_rec = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
		return employee_rec.id
	

	name = fields.Char(
		'Sequence', default='/',
		copy=False,  index=True)
	reference = fields.Char(string="Reference")
	state = fields.Selection([
		('draft', 'Draft'),('cancel', 'Cancelled'),
		('waiting','Waiting For Approval'),
		('approved','Approved'),
		('received','Received'),
		('done', 'Done')], string='Status', index= True, default='draft',
		store=True, help=" * Draft: not confirmed yet and will not be scheduled until confirmed\n"
			 " * Cancelled: has been cancelled, can't be confirmed anymore")
	location_id = fields.Many2one('stock.location', "Source Location Zone")
	location_dest_id = fields.Many2one('stock.location', "Destination Location Zone")
	transfer_date = fields.Date(string="Scheduled Date", required=True, default=fields.Datetime.now)
	warehouse_id = fields.Many2one('stock.warehouse', string="Warehouse",select=True, required=False)
	material_line_ids = fields.One2many('material.request.line','material_id',string="Material Request Line")
	picking_type_id = fields.Many2one('stock.picking.type', string="Stock Picking Type", default=_get_default_picking_type)
	transfer_reference = fields.Many2one('stock.picking',string="Transfer Reference",readonly=True)
	school_id = fields.Many2one('school.school',string="Campus")
	requester = fields.Many2one('hr.employee', "Requester",default=_get_employee_id)
	note = fields.Text(string="Reason")
	issued_by = fields.Many2one('res.users', "Issued by")

	# requester_id = fields.Many2one('stock.picking', string="Requester")



	@api.model
	def create(self, vals):
		if vals.get('name', _('New')) == _('New'):
			if 'company_id' in vals:
				vals['name'] = self.env['ir.sequence'].with_context(force_company=vals['company_id']).next_by_code('material.request.new') or _('New')
			else:
				vals['name'] = self.env['ir.sequence'].next_by_code('material.request.new') or _('New')	
				
		result = super(MaterialRequest, self).create(vals)
		return result

	def do_confirm(self):
		self.send_mail_template()
		self.write({'state':'waiting'})


	@api.multi
	def send_mail_template(self):
		# Find the e-mail template
		template = self.env.ref('bi_material_request_form.material_request_mail')
		# You can also find the e-mail template like this:
		# template = self.env['ir.model.data'].get_object('mail_template_demo', 'example_email_template')
 
		# Send out the e-mail template to the user
		self.env['mail.template'].browse(template.id).send_mail(self.id)

	 
	
	def done_receive(self):
		self.write({'state':'received'})	

	def approve_product(self):
		for vals in self:
			type_obj = self.env['stock.picking.type']
			picking_type_id = type_obj.search([('name', '=', 'Internal Transfers'),('default_location_src_id','=',vals.location_id.id)], limit=1)
			pick = {
					'origin': vals.name,
					'school_id': vals.school_id.id,
					# 'requester_id': vals.school_id.id,
					'delivery_slip_id': vals.id,
					'picking_type_id': picking_type_id.id,
					'location_id': vals.location_id.id,
					'location_dest_id': vals.location_dest_id.id,
					'min_date': vals.transfer_date,
				}
		picking = self.env['stock.picking'].create(pick)
		for line in self.material_line_ids:
			move = {
				'name': vals.name,
				'product_id': line.product_id.id,
				'product_uom_qty': line.quantity if line.quantity<line.product_id.qty_available else line.product_id.qty_available,
				'product_uom': line.unit_of_measure.id,
				'location_id': vals.location_id.id,
				'location_dest_id': vals.location_dest_id.id,
				'picking_id': picking.id,
				}
			self.env['stock.move'].create(move)
		# for pack in picking.move_lines:
		# 	operation = {
		# 				'product_id': pack.product_id.id,
		# 				'qty_done': pack.product_uom_qty,
		# 				'product_qty': pack.product_uom_qty,
		# 				'location_id': pack.location_id.id,
		# 				'location_dest_id': pack.location_dest_id.id,
		# 				'product_uom_id': pack.product_uom.id,
		# 				'picking_id': picking.id,
		# 	}
		# 	self.env['stock.pack.operation'].create(operation)
		picking.action_assign()
		self.transfer_reference = picking.id

	@api.onchange('requester')
	def onchange_requester(self):
		if self.requester:
			self.school_id = self.requester.school_id

	def do_approve(self):
		self.write({'state':'approved'})


	def done_transfer(self):

		for line in self.material_line_ids:
			if line.product_id.qty_available <= 0:
				raise UserError(_("Material %s is not available")%line.product_id.name)

		if not self.location_id:
			raise UserError(_("Please select source location"))
		elif not self.location_dest_id:
			raise UserError(_("Please select destination location"))
		self.approve_product()
		transfer = self.env['stock.immediate.transfer'].create({'pick_id': self.transfer_reference.id})
		transfer.process()
		self.write({'state': 'done','issued_by': self.env.user.id})
		asset_obj=self.env['account.asset.asset']
		for line in self.material_line_ids:
			if line.asset_id:
				asset=asset_obj.search([('id','=',line.asset_id.id)])
				asset.write({'custodian':line.material_id.requester.user_id.id,'employee_id':line.material_id.requester.id,'school_id':line.material_id.requester.school_id.id})
class MaterialRequestLine(models.Model):
	_name = 'material.request.line'

	product_id = fields.Many2one('product.product','Product')
	quantity = fields.Float(string="Quantity", default=1.0)
	unit_of_measure = fields.Many2one('product.uom',string="Unit Of Measure")
	product_cost = fields.Float(string="Cost")
	product_unit_price = fields.Float(string="Unit Price")
	material_id = fields.Many2one('material.request',string="Material Request")
	asset_id = fields.Many2one('account.asset.asset',string="Asset")
	state = fields.Selection([
		('draft', 'Draft'),('cancel', 'Cancelled'),
		('waiting','Waiting For Approval'),
		('approved','Approved'),
		('received','Received'),
		('done', 'Done')], string='Status', index= True, default='draft', related='material_id.state',
		store=True, help=" * Draft: not confirmed yet and will not be scheduled until confirmed\n"
			 " * Cancelled: has been cancelled, can't be confirmed anymore")

	@api.onchange('product_id')
	def onchange_product_id(self):
		for vals in self:
			if vals.product_id:
				vals.unit_of_measure = vals.product_id.uom_id
				vals.product_cost = vals.product_id.standard_price
				vals.product_unit_price = vals.product_id.list_price 

class Picking(models.Model):
	_inherit = "stock.picking"

	delivery_slip_id = fields.Many2one('material.request',string="Delivery Payslip")