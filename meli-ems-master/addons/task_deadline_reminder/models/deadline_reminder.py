# -*- coding: utf-8 -*-

import datetime
from datetime import datetime
from odoo import SUPERUSER_ID
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError,UserError


class DeadLineReminder(models.Model):
    _inherit = "project.task"

    task_reminder = fields.Boolean("Reminder")

    @api.model
    def _cron_deadline_reminder(self):
        su_id = self.env['res.partner'].browse(SUPERUSER_ID)
        for task in self.env['project.task'].search([('date_deadline', '!=', None),
                                                     ('task_reminder', '=', True), ('user_id', '!=', None)]):
            reminder_date = datetime.strptime(task.date_deadline, '%Y-%m-%d').date()
            today = datetime.now().date()
            if reminder_date == today and task:
                template_id = self.env['ir.model.data'].get_object_reference(
                                                      'task_deadline_reminder',
                                                      'email_template_edi_deadline_reminder')[1]
                if template_id:
                    email_template_obj = self.env['mail.template'].browse(template_id)
                    values = email_template_obj.generate_email(task.id, fields=None)
                    values['email_from'] = su_id.email
                    values['email_to'] = task.user_id.email
                    values['res_id'] = False
                    mail_mail_obj = self.env['mail.mail']
                    msg_id = mail_mail_obj.create(values)
                    if msg_id:
                        msg_id.send()
        return True

class StudentStudent(models.Model):
    _inherit = "student.student"

    task_reminder = fields.Boolean("Reminder")

    @api.model
    def _cron_deadline_reminder_new(self):
        su_id = self.env['res.partner'].browse(SUPERUSER_ID)
        
        for task in self.env['student.student'].search([('task_reminder', '=', True),('availability', '!=', None)
                                                      ]):
            reminder_date = datetime.strptime(task.standard_id.start_date, '%Y-%m-%d').date()
            today = datetime.now().date()
            # if reminder_date == today and task:
            #     template_id = self.env['ir.model.data'].get_object_reference(
            #                                           'task_deadline_reminder',
            #                                           'email_template_edi_deadline_reminder')[1]
            #     if template_id:
            #         email_template_obj = self.env['mail.template'].browse(template_id)
            #         values = email_template_obj.generate_email(task.id, fields=None)
            #         values['email_from'] = su_id.email
            #         values['email_to'] = task.user_id.email
            #         values['res_id'] = False
            #         mail_mail_obj = self.env['mail.mail']
            #         msg_id = mail_mail_obj.create(values)
            #         if msg_id:
            #             msg_id.send()
        return True
    @api.multi
    def approve_state(self):
        self._cron_deadline_reminder_new()