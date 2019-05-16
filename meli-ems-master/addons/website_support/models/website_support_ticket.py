# -*- coding: utf-8 -*-
from openerp import api, fields, models
from openerp import tools
from HTMLParser import HTMLParser
from random import randint
from datetime import date, datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
from odoo import SUPERUSER_ID
import logging
from odoo.exceptions import UserError
_logger = logging.getLogger(__name__)

class MLStripper(HTMLParser):
    def __init__(self):
        self.reset()
        self.fed = []
    def handle_data(self, d):
        self.fed.append(d)
    def get_data(self):
        return ''.join(self.fed)
        
class WebsiteSupportTicket(models.Model):

    _name = "website.support.ticket"
    _description = "Website Support Ticket"
    _rec_name = "ticket_number_display"
    _inherit = ['mail.thread','ir.needaction_mixin']
    _order = "id desc"

    @api.model
    def _read_group_state(self, states, domain, order):
        """ Read group customization in order to display all the states in the
            kanban view, even if they are empty
        """
        
        staff_replied_state = self.env['ir.model.data'].get_object('website_support', 'website_ticket_state_staff_replied')
        customer_replied_state = self.env['ir.model.data'].get_object('website_support', 'website_ticket_state_customer_replied')
        customer_admitted = self.env['ir.model.data'].get_object('website_support', 'website_ticket_state_approval_admitted')
        # staff_closed = self.env['ir.model.data'].get_object('website_support', 'website_ticket_state_staff_closed')
        
        exclude_states = [staff_replied_state.id, customer_replied_state.id, customer_admitted.id]
        
        #state_ids = states._search([('id','not in',exclude_states)], order=order, access_rights_uid=SUPERUSER_ID)
        state_ids = states._search([], order=order, access_rights_uid=SUPERUSER_ID)
        
        return states.browse(state_ids)
        
    def _default_state(self):
        return self.env['ir.model.data'].get_object('website_support', 'website_ticket_state_open')

    def _default_priority_id(self):
        default_priority = self.env['website.support.ticket.priority'].search([('sequence','=','1')])
        return default_priority[0]

    # def _default_approval_id(self):
    #     return self.env['ir.model.data'].get_object('website_support', 'no_approval_required')
    
    # approval_id = fields.Many2one('website.support.ticket.approval', default=_default_approval_id, string="Approval")
    create_user_id = fields.Many2one('res.users', "Create User")
    priority_id = fields.Many2one('website.support.ticket.priority', default=_default_priority_id, string="Priority")
    partner_id = fields.Many2one('res.partner', string="Partner")
    user_id = fields.Many2one('res.users', string="Assigned User")
    first_name = fields.Char(string="First Name")
    last_name = fields.Char(string="Last Name")
    email = fields.Char(string="Email")
    support_email = fields.Char(string="Support Email")
    description = fields.Text(string="Description")
    state = fields.Many2one('website.support.ticket.states', default=_default_state, group_expand='_read_group_state', string="State")
    state_id = fields.Selection([
        ('new', 'New'),
        ('reply', 'Reply'),
        ('reject', 'Rejected'),
        ('admit', 'Admitted'),
        ('cancel', 'Cancelled'),
        ], string='Status', readonly=True, copy=False, index=True, track_visibility='onchange', default='new')
    conversation_history = fields.One2many('website.support.ticket.message', 'ticket_id', string="Conversation History")
    attachment = fields.Binary(string="Attachments")
    attachment_filename = fields.Char(string="Attachment Filename")
    attachment_ids = fields.One2many('ir.attachment', 'res_id', domain=[('res_model', '=', 'website.support.ticket')], string="Media Attachments")
    unattended = fields.Boolean(string="Unattended", compute="_compute_unattend", store="True", help="In 'Open' state or 'Customer Replied' state taken into consideration name changes")
    portal_access_key = fields.Char(string="Portal Access Key")
    ticket_number = fields.Integer(string="Ticket Number")
    ticket_number_display = fields.Char(string="Ticket Number Display", compute="_compute_ticket_number_display")
    ticket_color = fields.Char(related="priority_id.color", string="Ticket Color")
    company_id = fields.Many2one('res.company', string="Company", default=lambda self: self.env['res.company']._company_default_get('website.support.ticket') )
    support_rating = fields.Integer(string="Support Rating")
    support_comment = fields.Text(string="Support Comment")
    close_comment = fields.Text(string="Close Comment")
    close_time = fields.Datetime(string="Close Time")
    close_date = fields.Date(string="Close Date")
    closed_by_id = fields.Many2one('res.users', string="Closed By")
    time_to_close = fields.Integer(string="Time to close (seconds)")
    extra_field_ids = fields.One2many('website.support.ticket.field', 'wst_id', string="Extra Details")
    approve_url = fields.Char(compute="_compute_approve_url", string="Approve URL")
    disapprove_url = fields.Char(compute="_compute_disapprove_url", string="Disapprove URL")
    school_id = fields.Many2one('school.school', "Campus", store=True)
    date_of_birth = fields.Date('Birth Date')
    age = fields.Integer( compute='_compute_student_age',string='Age',readonly=True)
    maritual_status = fields.Selection([('unmarried', 'Unmarried'),
                                        ('married', 'Married')],
                                       'Marital Status')
    parent_id = fields.Char("Parent Name")
    grandparent_id = fields.Char("Grand Father Name")
    nid = fields.Char('NID/Tazkira Number')
    occupation = fields.Char("Occupation",readonly=True)
    program_id = fields .Many2one('standard.standard',"Course")
    gender = fields.Selection([('male', 'Male'), ('female', 'Female')],'Gender')
    mobile = fields.Char(string="Mobile")
    pwd = fields.Char(string="Password")

    @api.multi
    def button_reject(self):
        for rec in self:
            state = self.env['website.support.ticket.states'].search([('name','=','Cancelled')])
            rec.write({'state_id': 'cancel',
                        'state': state.id
                        })


    @api.multi
    def button_admit(self):
        admit_state = self.env['ir.model.data'].sudo().get_object('website_support', 'website_ticket_state_approval_admitted')        
        
        #We record state change manually since it would spam the chatter if every 'Staff Replied' and 'Customer Replied' gets recorded
        # message = "<ul class=\"o_mail_thread_message_tracking\">\n<li>State:<span> " + self.state.name + " </span><b>-></b> " + admit_state.name + " </span></li></ul>"
        # self.message_post(body=message, subject="Student Admitted")

        # self.close_comment = self.message
        # self.closed_by_id = self.env.user.id
        # admit_state_mail_template = self.env['ir.model.data'].get_object('website_support', 'website_ticket_state_approval_admitted').mail_template_id
        # if admit_state_mail_template == False:
        #     admit_state_mail_template = self.env['ir.model.data'].sudo().get_object('website_support', 'support_ticket_admitted').mail_template_id
        #     f = open("/home/administrator/err.txt","a+")
        #     f.write(str(admit_state_mail_template)+"\n============================================\n")
        #     f.close()
        #     admit_state_mail_template.send_mail(self.id, True)
        # else:
        #     admit_state_mail_template.send_mail(self.id, True)

        self.write({'state_id': 'admit',
                    'state': admit_state.id
            })

        # ticket_open_email_template = self.env['ir.model.data'].get_object('website_support', 'website_ticket_state_open').mail_template_id
        # if ticket_open_email_template == False:
        #     ticket_open_email_template = self.env['ir.model.data'].sudo().get_object('website_support', 'support_ticket_new')
        #     ticket_open_email_template.send_mail(new_id.id, True)
        # else:
        #     ticket_open_email_template.send_mail(new_id.id, True)

    @api.multi
    @api.depends('date_of_birth')
    def _compute_student_age(self):
        '''Method to calculate student age'''
        current_dt = datetime.today()
        for rec in self:
            if rec.date_of_birth:
                start = datetime.strptime(rec.date_of_birth,
                                          DEFAULT_SERVER_DATE_FORMAT)
                age_calc = ((current_dt - start).days / 365)
                # Age should be greater than 0
                if age_calc > 0.0:
                    rec.age = age_calc

    @api.one
    def _compute_approve_url(self):
        self.approve_url = "/support/approve/" + str(self.id)

    @api.one
    def _compute_disapprove_url(self):
        self.disapprove_url = "/support/disapprove/" + str(self.id)
        
    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        self.first_name = self.partner_id.name
        self.email = self.partner_id.email
    
    def message_new(self, msg, custom_values=None):
        """ Create new support ticket upon receiving new email"""

        defaults = {'support_email': msg.get('to'), 'subject': msg.get('subject')}

        #Extract the name from the from email if you can        
        if "<" in msg.get('from') and ">" in msg.get('from'):
            start = msg.get('from').rindex( "<" ) + 1
            end = msg.get('from').rindex( ">", start )
            from_email = msg.get('from')[start:end]
            from_name = msg.get('from').split("<")[0].strip()
            defaults['first_name'] = from_name
        else:
            from_email = msg.get('from')

        defaults['email'] = from_email
        
        #Try to find the partner using the from email
        search_partner = self.env['res.partner'].sudo().search([('email','=', from_email)])
        if len(search_partner) > 0:
            defaults['partner_id'] = search_partner[0].id
            defaults['first_name'] = search_partner[0].name

        defaults['description'] = tools.html_sanitize(msg.get('body'))
        
        portal_access_key = randint(1000000000,2000000000)
        defaults['portal_access_key'] = portal_access_key

        
        return super(WebsiteSupportTicket, self).message_new(msg, custom_values=defaults)

    def message_update(self, msg_dict, update_vals=None):
        """ Override to update the support ticket according to the email. """

        body_short = tools.html_sanitize(msg_dict['body'])
        #body_short = tools.html_email_clean(msg_dict['body'], shorten=True, remove=True)
                
        #s = MLStripper()
        #s.feed(body_short)
        #body_short = s.get_data()
                
        #Add to message history field for back compatablity
        self.conversation_history.create({'ticket_id': self.id, 'by': 'customer', 'content': body_short })

        #If the to email address is to the customer then it must be a staff member...
        if msg_dict.get('to') == self.email:
            change_state = self.env['ir.model.data'].get_object('website_support','website_ticket_state_staff_replied')        
        else:
            change_state = self.env['ir.model.data'].get_object('website_support','website_ticket_state_customer_replied')
        
        self.state = change_state.id

        return super(WebsiteSupportTicket, self).message_update(msg_dict, update_vals=update_vals)

    @api.one
    @api.depends('ticket_number')
    def _compute_ticket_number_display(self):
        if self.ticket_number:
            self.ticket_number_display = str(self.school_id.code)+'/'+str(datetime.today().strftime('%d%m%Y')) + "/" + str(self.ticket_number) 
        else:
            self.ticket_number_display = str(self.school_id.code)+'/'+str(datetime.today().strftime('%d%m%Y'))+str(self.id)
            
    @api.depends('state')
    def _compute_unattend(self):
        staff_replied = self.env['ir.model.data'].get_object('website_support', 'website_ticket_state_staff_replied')
        customer_admitted = self.env['ir.model.data'].get_object('website_support', 'website_ticket_state_approval_admitted')
        customer_cancel = self.env['ir.model.data'].get_object('website_support', 'website_ticket_state_cancel')
        # customer_admitted = self.env['ir.model.data'].get_object('website_support', 'website_ticket_state_customer_replied')

        #If not closed or replied to then consider all other states to be attended to
        if self.state != staff_replied and self.state != customer_admitted and self.state != customer_cancel:
            self.unattended = True


    @api.model
    def _needaction_domain_get(self):
        open_state = self.env['ir.model.data'].get_object('website_support', 'website_ticket_state_open')
        custom_replied_state = self.env['ir.model.data'].get_object('website_support', 'website_ticket_state_customer_replied')
        return ['|',('state', '=', open_state.id ), ('state', '=', custom_replied_state.id)]

    @api.model
    def create(self, vals):
        new_id = super(WebsiteSupportTicket, self).create(vals)
        new_id.ticket_number = new_id.company_id.next_support_ticket_number

        #Add one to the next ticket number
        new_id.company_id.next_support_ticket_number += 1

        #Auto create contact if one with that email does not exist
        setting_auto_create_contact = self.env['ir.values'].get_default('website.support.settings', 'auto_create_contact')
        
        if setting_auto_create_contact and 'email' in vals:
            if self.env['res.partner'].search_count([('email','=',vals['email'])]) == 0:
                if 'first_name' in vals:
                    new_contact = self.env['res.partner'].create({'name':vals['first_name'], 'email': vals['email'], 'company_type': 'person'})
                else:
                    new_contact = self.env['res.partner'].create({'name':vals['email'], 'email': vals['email'], 'company_type': 'person'})
                    
                new_id.partner_id = new_contact.id
                    
        #(BACK COMPATABILITY) Fail safe if no template is selected, future versions will allow disabling email by removing template
        ticket_open_email_template = self.env['ir.model.data'].get_object('website_support', 'website_ticket_state_open').mail_template_id
        if ticket_open_email_template == False:
            ticket_open_email_template = self.env['ir.model.data'].sudo().get_object('website_support', 'support_ticket_new')
            ticket_open_email_template.send_mail(new_id.id, True)
        else:
            ticket_open_email_template.send_mail(new_id.id, True)

        #Send an email out to everyone in the category
        support_ticket_menu = self.env['ir.model.data'].sudo().get_object('website_support', 'website_support_ticket_menu')
        support_ticket_action = self.env['ir.model.data'].sudo().get_object('website_support', 'website_support_ticket_action')
        
            
        return new_id
        
    @api.multi
    def write(self, values, context=None):

        update_rec = super(WebsiteSupportTicket, self).write(values)

        if 'state' in values:
            if self.state.mail_template_id:
                self.state.mail_template_id.send_mail(self.id, True)

        if 'user_id' in values:
            setting_change_user_email_template_id = self.env['ir.values'].get_default('website.support.settings', 'change_user_email_template_id')
        
            if setting_change_user_email_template_id:
                email_template = self.env['mail.template'].browse(setting_change_user_email_template_id)
            else:
                #Default email template
                email_template = self.env['ir.model.data'].get_object('website_support','support_ticket_user_change')

            email_values = email_template.generate_email([self.id])[self.id]
            email_values['model'] = "website.support.ticket"
            email_values['res_id'] = self.id
            assigned_user = self.env['res.users'].browse( int(values['user_id']) )
            email_values['email_to'] = assigned_user.partner_id.email
            email_values['body_html'] = email_values['body_html'].replace("_user_name_", assigned_user.name)
            email_values['body'] = email_values['body'].replace("_user_name_", assigned_user.name)
            send_mail = self.env['mail.mail'].create(email_values)
            send_mail.send()

        
        return update_rec

# class WebsiteSupportTicketApproval(models.Model):

#     _name = "website.support.ticket.approval"

#     wst_id = fields.Many2one('website.support.ticket', string="Support Ticket")
#     name = fields.Char(string="Name", translate=True)

class WebsiteSupportTicketField(models.Model):

    _name = "website.support.ticket.field"

    wst_id = fields.Many2one('website.support.ticket', string="Support Ticket")
    name = fields.Char(string="Label")
    value = fields.Char(string="Value")
    
class WebsiteSupportTicketMessage(models.Model):

    _name = "website.support.ticket.message"
    
    ticket_id = fields.Many2one('website.support.ticket', string='Ticket ID')
    by = fields.Selection([('staff','Staff'), ('customer','Customer')], string="By")
    content = fields.Html(string="Content")
   
    
class WebsiteSupportTicketStates(models.Model):

    _name = "website.support.ticket.states"
    
    name = fields.Char(required=True, translate=True, string='State Name')
    mail_template_id = fields.Many2one('mail.template', domain="[('model_id','=','website.support.ticket')]", string="Mail Template")

class WebsiteSupportTicketPriority(models.Model):

    _name = "website.support.ticket.priority"
    _order = "sequence asc"

    sequence = fields.Integer(string="Sequence")
    name = fields.Char(required=True, translate=True, string="Priority Name")
    color = fields.Char(string="Color")
    
    @api.model
    def create(self, values):
        sequence=self.env['ir.sequence'].next_by_code('website.support.ticket.priority')
        values['sequence']=sequence
        return super(WebsiteSupportTicketPriority, self).create(values)
        

class WebsiteSupportTicketCompose(models.Model):

    _name = "website.support.ticket.compose"

    ticket_id = fields.Many2one('website.support.ticket', string='Ticket ID')
    approval = fields.Boolean(string="Approval")
    partner_id = fields.Many2one('res.partner', string="Partner", readonly="True")
    email = fields.Char(string="Email", readonly="True")
    subject = fields.Char(string="Subject")
    body = fields.Text(string="Message Body")
    template_id = fields.Many2one('mail.template', string="Mail Template", domain="[('model_id','=','website.support.ticket'), ('built_in','=',False)]")
    planned_time = fields.Datetime(string="Planned Time")
    
    @api.onchange('template_id')
    def _onchange_template_id(self):
        if self.template_id:
            values = self.env['mail.compose.message'].generate_email_for_composer(self.template_id.id, [self.ticket_id.id])[self.ticket_id.id]                
            self.body = values['body']
            
    @api.one
    def send_reply(self):
        #Send email
        values = {}

        setting_staff_reply_email_template_id = self.env['ir.values'].get_default('website.support.settings', 'staff_reply_email_template_id')
        
        if setting_staff_reply_email_template_id:
            email_wrapper = self.env['mail.template'].browse(setting_staff_reply_email_template_id)
        else:
            #Defaults to staff reply template for back compatablity
            email_wrapper = self.env['ir.model.data'].get_object('website_support','support_ticket_reply_wrapper')

        values = email_wrapper.generate_email([self.id])[self.id]
        values['model'] = "website.support.ticket"
        values['res_id'] = self.ticket_id.id
        send_mail = self.env['mail.mail'].create(values)
        send_mail.send()
        
        #Add to message history field for back compatablity
        self.env['website.support.ticket.message'].create({'ticket_id': self.ticket_id.id, 'by': 'staff', 'content':self.body.replace("<p>","").replace("</p>","")})
        
        #Post in message history
        self.ticket_id.message_post(body=self.body, subject=self.subject, message_type='comment', subtype='mt_comment')
	
        if self.approval:
	    #Change the ticket state to awaiting approval
	    awaiting_approval_state = self.env['ir.model.data'].get_object('website_support','website_ticket_state_awaiting_approval')
	    self.ticket_id.state = awaiting_approval_state.id
	
	    #Also change the approval
	    awaiting_approval = self.env['ir.model.data'].get_object('website_support','awaiting_approval')
	    self.ticket_id.approval_id = awaiting_approval.id        
        else:
	    #Change the ticket state to staff replied        
	    staff_replied = self.env['ir.model.data'].get_object('website_support','website_ticket_state_staff_replied')
	    self.ticket_id.state = staff_replied.id
        self.ticket_id.write({'state_id': 'reply'})
