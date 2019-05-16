# -*- coding: utf-8 -*-
#################################################################################
# Author      : Acespritech Solutions Pvt. Ltd. (<www.acespritech.com>)
# Copyright(c): 2012-Present Acespritech Solutions Pvt. Ltd.
# All Rights Reserved.
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
# Please see LICENSE file.
#################################################################################
from odoo import models, fields, api, _
import re
from openerp.exceptions import UserError


# class bi_pos_kitchen_order(models.Model):
# 	_name = "bi.pos.kitchen.order"
# 	_rec_name = 'order_id'

# 	session_name =  fields.Char(string='Session Id')
# 	order_id =  fields.Char(string='Order Id')
# 	order_line =  fields.Char(string='Order Line')
# 	order_line_ids = fields.One2many('bi.pos.kitchen.order.line', 'order_id', string='Order Lines', copy=True,)
# 	currency =  fields.Char(string='currency')
# 	payment_line = fields.Char(string ='Payment Line')
# 	session_id = fields.Many2one('pos.config',String="Pos Config")
# 	ac_token = fields.Boolean(default=False)
# 	floor_id = fields.Many2one('restaurant.floor',String="Floor")
# 	table_id = fields.Many2one('restaurant.table',String="Table")
# 	order_date = fields.Datetime(string='Order Date',default=fields.Datetime.now)
# 	state = fields.Selection([
# 			('New', 'New'),
# 			('Changed', 'Changed'),
# 			('Ready', 'Ready'),
# 			('Deliverd', 'Deliverd'),
# 			('Canceled', 'Canceled'),
# 			],default='New')
# 	delivery_boy = fields.Many2one('res.users',String="Delivery Boy")
# 	count=fields.Integer('Ready',compute='_compute_ready_items',store=True)
# 	total_count=fields.Integer('Total Items',compute='_compute_ready_items',store=True)


# 	@api.depends('order_line_ids.count')
# 	def _compute_ready_items(self):
# 		ready=0
# 		for rec in self:
# 			total_order=0
# 			for data in rec.order_line_ids:
# 				total_order=total_order+1
# 				rec.total_count=total_order
# 				if data.count:
# 					ready=ready+1
# 					rec.count = ready

# 	@api.model
# 	def create_pos_data(self, order_line, order_id, session_id, currency, ac_session,paymentLines, table_id, floor_id):
# 		if session_id:
# 			session_exist_id = self.env['bi.pos.kitchen.order'].sudo().search([['order_id', '=', order_id]])
# 			if session_exist_id:
# 				session_exist_id.write({'order_line': order_line,
# 									   'session_name': session_id,
# 									   'currency': currency,
# 									   'session_id': ac_session,
# 									   'payment_line': paymentLines,
# 									   'order_id':order_id,
# 									   'table_id':table_id,
# 									   'floor_id':floor_id,
# 									   'state':'Changed'
# 										})
# 				session_exist_id.order_line_ids.unlink()
# 				for line in order_line:
# 					self.env['bi.pos.kitchen.order.line'].create({'product_id':line[0],
# 																	'qty':line[3],
# 																	'order_id':session_exist_id.id,
# 																	})
# 			else:
# 				order_id=self.env['bi.pos.kitchen.order'].create({'order_line': order_line,
# 													   'session_name': session_id,
# 													   'currency': currency,
# 													   'session_id': ac_session,
# 													   'payment_line': paymentLines,
# 													   'order_id':order_id,
# 													   'table_id':table_id,
# 													   'floor_id':floor_id,
# 													   'state':'New'
# 													   })
# 				for line in order_line:
# 					self.env['bi.pos.kitchen.order.line'].create({'product_id':line[0],
# 																	'qty':line[3],
# 																	'order_id':order_id.id,
# 																	})

# 		return True

# 	@api.model
# 	def delete_pos_data(self, session_id):
# 		if session_id:
# 			session_exist_id = self.env['bi.pos.kitchen.order'].search([['session_name', '=', session_id]])
# 			if session_exist_id:
# 				session_exist_id.unlink()
# 		return True



# class pos_config(models.Model):
# 	_inherit = 'pos.config'
# 	kitchen_text = fields.Char(string="Promotional Message")
# 	kitchen_marque_color = fields.Char(string="Promotional Message color")
# 	kitchen_marque_bg_color = fields.Char(string="Promotional Background color")
# 	kitchen_marque_font_size = fields.Integer(string="Promotional Font size",default=1)
# 	kitchen_mute_video_sound = fields.Boolean(string="Mute Video sound")
# 	kitchen_ac_width = fields.Char(string="Width")
# 	kitchen_ac_height = fields.Char(string="Height")
# 	kitchen_delay = fields.Float(String="Kitchen Delay in Minutes")

class bi_notification_msg(models.Model):
	_name = 'bi.notification.msg'

	msg = fields.Boolean(String="MSG", default=False)
	create_note= fields.Integer(String="Id")

	@api.model
	def check_status(self):
		msg_id = self.search([('create_note','=',self._uid)])
		if msg_id:
			if msg_id.msg:
				msg_id.msg = False
				return True
			else:
				return False
		else:
			self.create({'msg':True,'create_note':self._uid})
			return True
		
# class bi_pos_kitchen_order_line(models.Model):
# 	_name = "bi.pos.kitchen.order.line"


# 	order_id = fields.Many2one('bi.pos.kitchen.order',String="order")

# 	product_id = fields.Many2one('product.product', string='Product')
# 	qty = fields.Float('Quantity', default=1)
# 	count=fields.Boolean('Ready')

