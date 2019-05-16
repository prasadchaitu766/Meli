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
    'name': "Lifeline for Task",
    'summary': """Lifeline Progressbar for Tasks (100% -> 0%)""",
    'description': """Calculates the time remaining based on live time & deadline.""",
    'author': 'Bassam Infotech LLP',
    'website': "https://www.bassaminfotech.com",
    'company': 'Bassam Infotech LLP',
    'category': 'Project',
    'version': '10.0.2.0.0',
    'depends': ['base', 'project'],
    'data': [
        'security/ir.model.access.csv',
        'views/task_lifeline_view.xml',
        'views/progress_bar_view.xml',
        'views/progress_bar_settings.xml',
    ],
    'images': ['static/description/banner.jpg'],
    'installable': True,
    'auto_install': False,
}
