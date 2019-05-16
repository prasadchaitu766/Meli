import mimetypes


from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools.mimetypes import guess_mimetype


class UploadDoc(models.Model):
	_inherit = "ir.attachment"


	doc_name = fields.Many2one('ir.selectitem', string="Document Name")


	@api.onchange('doc_name')
	def get_attach_name(self):
		active_ids = self.env.context.get('active_ids')		
		applicant_name = self.env['hr.applicant'].search([])
		if self.doc_name.name != False:
			for applicants in applicant_name:
				if active_ids[0] == applicants.id:
					self.name = applicants.partner_name+"_"+self.doc_name.name

	@api.constrains('mimetype')
	def onchnage_name_action(self):
		if self.doc_name.name != False:
			if self.type == "binary":
				if self.doc_name.name == "Two pictures (passport size)":
					if self.mimetype != "image/jpeg":
						raise UserError('Allowed Format jpeg')

				if self.doc_name.name != "Two pictures (passport size)":
					if self.mimetype != "application/pdf":
						raise UserError('Allowed Format Pdf')

			if self.type == "url":
				if self.url == False:
					raise UserError('Add Document url')
		else:
			pass

		

class UploadFileSelection(models.Model):
	_name = "ir.selectitem"


	name = fields.Char(string="Document Name")


