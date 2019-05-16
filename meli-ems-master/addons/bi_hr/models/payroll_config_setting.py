# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class HrPayrollConfigSettings(models.TransientModel):
    _inherit = 'hr.payroll.config.settings' 

    designation_id = fields.Many2one('hr.job', string='Designation')
    

    @api.multi
    def set_designation_id_defaults(self):
        return self.env['ir.values'].sudo().set_default(
            'hr.payroll.config.settings', 'designation_id', self.designation_id.id)

    
    