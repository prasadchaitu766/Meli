# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api
from odoo.exceptions import ValidationError,UserError

class Location(models.Model):
	_inherit = "stock.location" 

	school_id = fields.Many2one('school.school', 'Campus', required=False)

class Picking(models.Model):
	_inherit = "stock.picking"

	school_id = fields.Many2one('school.school', 'Campus', required=False)

class StockWarehouse(models.Model):
	_inherit = "stock.warehouse"

	school_id = fields.Many2one('school.school',string="Campus")