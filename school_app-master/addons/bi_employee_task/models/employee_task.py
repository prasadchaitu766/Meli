# -*- coding: utf-8 -*-
##############################################################################
#
#    This module uses OpenERP, Open Source Management Solution Framework.
#    Copyright (C) 2014-Today BrowseInfo (<http://www.browseinfo.in>)
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>
#
##############################################################################

from openerp import api, fields, models, _

class hr_employee(models.Model):
    _inherit = 'hr.employee'

    @api.multi
    @api.depends('user_id')
    def compute_tasks_count(self):
        usr_id = 0
        ir_model_data = self.env['ir.model.data']
        search_view_id = ir_model_data.get_object_reference('project', 'view_task_search_form')[1]
    	for each in self:
            if each.user_id:
                project_task_ids = self.env['project.task'].search([('user_id','=',each.user_id.id)])
                length_count = len(project_task_ids)
                each.task_count = length_count
                usr_id = each.user_id.id
            else:
    			pass
        return{
            'name':'Employee Task',
            'res_model':'project.task',
            'type':'ir.actions.act_window',
            'view_type':'list',
            'view_mode':'list,form,kanban,calendar,pivot,graph',
            'context':{'group_by':'stage_id'},
            'domain': [('user_id', '=', usr_id)],
            'search_view_id':search_view_id,
         }

    task_count = fields.Integer(compute=compute_tasks_count,string='Task Count',readonly=True)



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: