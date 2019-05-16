# -*- coding: utf-8 -*-
###################################################################################
#    Bassam Infotech LLP
#    Copyright (C) 2018-TODAY Bassam Infotech LLP (<https://www.bassaminfotech.com>).#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###################################################################################

{
    'name': "Task Deadline Reminder",
    'version': "10.0.1.0.0",
    'author': 'Bassam Infotech LLP',
    'company': 'Bassam Infotech LLP',
    'website': 'https://www.bassaminfotech.com',
    'summary': '''Automatically Send Mail To Responsible User if Deadline Of Task is Today''',
    'description': '''Automatically Send Mail To Responsible User if Deadline Of Task is Today''',
    'category': "Project",
    'depends': ['project','school'],
    'license': 'AGPL-3',
    'data': [
            'views/deadline_reminder_view.xml',
            'views/deadline_reminder_cron.xml',
            'data/deadline_reminder_action_data.xml'
             ],
    'demo': [],
    'images': ['static/description/banner.jpg'],
    'installable': True,
    'auto_install': False
}
