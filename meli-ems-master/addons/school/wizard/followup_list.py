# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api
from odoo.exceptions import ValidationError,UserError


class FollowupReason(models.TransientModel):
    _name = "followup.reason"

    followup_id = fields.Many2one('student.followup',"Reason")
    

    @api.multi
    def save_followup(self):
        self.env['student.student'
                 ].browse(self._context.get('active_id')
                          ).write({'followup_id':self.followup_id.name,'state':'followup'})
        return True

class StudentFollowup(models.Model):
    _name = 'student.followup'
    _description = 'Student.Followup'


    name = fields.Char(string='Reason',required=True)

    