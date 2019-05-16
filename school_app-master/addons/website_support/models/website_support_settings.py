# -*- coding: utf-8 -*-
import logging
_logger = logging.getLogger(__name__)
import requests
from openerp.http import request
import odoo

from openerp import api, fields, models

class WebsiteSupportSettings(models.Model):

    _name = "website.support.settings"
    _inherit = 'res.config.settings'
            
    close_ticket_email_template_id = fields.Many2one('mail.template', domain="[('model_id','=','website.support.ticket')]", string="(OBSOLETE)Close Ticket Email Template")
    change_user_email_template_id = fields.Many2one('mail.template', domain="[('model_id','=','website.support.ticket')]", string="Change User Email Template")
    staff_reply_email_template_id = fields.Many2one('mail.template', domain="[('model_id','=','website.support.ticket.compose')]", string="Staff Reply Email Template")
    max_ticket_attachments = fields.Integer(string="Max Ticket Attachments")
    max_ticket_attachment_filesize = fields.Integer(string="Max Ticket Attachment Filesize (KB)")
    allow_user_signup = fields.Boolean(string="Allow User Signup")
    
    #-----Allow User Signup-----

    @api.multi
    def get_default_allow_user_signup(self, fields):
        return {'allow_user_signup': self.env['ir.values'].get_default('website.support.settings', 'allow_user_signup')}

    @api.multi
    def set_default_allow_user_signup(self):
        for record in self:
            self.env['ir.values'].set_default('website.support.settings', 'allow_user_signup', record.allow_user_signup)
    
    #-----Change User Email Template-----

    @api.multi
    def get_default_change_user_email_template_id(self, fields):
        return {'change_user_email_template_id': self.env['ir.values'].get_default('website.support.settings', 'change_user_email_template_id')}

    @api.multi
    def set_default_change_user_email_template_id(self):
        for record in self:
            self.env['ir.values'].set_default('website.support.settings', 'change_user_email_template_id', record.change_user_email_template_id.id)
    
    #-----Close Ticket Email Template-----

    @api.multi
    def get_default_close_ticket_email_template_id(self, fields):
        return {'close_ticket_email_template_id': self.env['ir.values'].get_default('website.support.settings', 'close_ticket_email_template_id')}

    @api.multi
    def set_default_close_ticket_email_template_id(self):
        for record in self:
            self.env['ir.values'].set_default('website.support.settings', 'close_ticket_email_template_id', record.close_ticket_email_template_id.id)
            
    #-----Staff Reply Email Template-----

    @api.multi
    def get_default_staff_reply_email_template_id(self, fields):
        return {'staff_reply_email_template_id': self.env['ir.values'].get_default('website.support.settings', 'staff_reply_email_template_id')}

    @api.multi
    def set_default_staff_reply_email_template_id(self):
        for record in self:
            self.env['ir.values'].set_default('website.support.settings', 'staff_reply_email_template_id', record.staff_reply_email_template_id.id)

    #-----Max Ticket Attachments-----

    @api.multi
    def get_default_max_ticket_attachments(self, fields):
        return {'max_ticket_attachments': self.env['ir.values'].get_default('website.support.settings', 'max_ticket_attachments')}

    @api.multi
    def set_default_max_ticket_attachments(self):
        for record in self:
            self.env['ir.values'].set_default('website.support.settings', 'max_ticket_attachments', record.max_ticket_attachments)

    #-----Max Ticket Attachment Filesize-----

    @api.multi
    def get_default_max_ticket_attachment_filesize(self, fields):
        return {'max_ticket_attachment_filesize': self.env['ir.values'].get_default('website.support.settings', 'max_ticket_attachment_filesize')}

    @api.multi
    def set_default_max_ticket_attachment_filesize(self):
        for record in self:
            self.env['ir.values'].set_default('website.support.settings', 'max_ticket_attachment_filesize', record.max_ticket_attachment_filesize)
