import mimetypes


from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools.mimetypes import guess_mimetype


class UploadDoc(models.Model):
	_inherit = "ir.attachment"


	doc_name = fields.Many2one('ir.selectitem', string="attachment Name")


	# @api.constrains('mimetype')
	# def onchnage_name_action(self):

	# 	if self.type == "binary":
	# 		print self.name.name,"@@@@@@@@@@@@@@@@"
	# 		if self.name.name == "Two pictures (passport size)":
	# 			if self.mimetype != "image/jpeg":
	# 				raise UserError('Allowed Format jpeg')

	# 		if self.name.name != "Two pictures (passport size)":
	# 			if self.mimetype != "application/pdf":
	# 				raise UserError('Allowed Format Pdf')

	# 	pass

		

class UploadFileSelection(models.Model):
	_name = "ir.selectitem"


	name = fields.Char(string="Document Name")

