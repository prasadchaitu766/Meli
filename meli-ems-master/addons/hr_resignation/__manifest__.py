# -*- coding: utf-8 -*-
###################################################################################
#    A part of Open HRMS Project <https://www.openhrms.com>
#
#    Bassam Infotech LLP
#    Copyright (C) 2018-TODAY Bassam Infotech LLP(<https://www.bassaminfotech.com>).
#    Author: Niyas Raphy(<https://www.bassaminfotech.com>)
#
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
    'name': 'Open HRMS Resignation',
    'version': '10.0.1.1.0',
    'summary': 'Handle the resignation process of the employee',
    'author': 'Bassam Infotech LLP',
    'company': 'Bassam Infotech LLP',
    'website': 'https://www.openhrms.com',
    'depends': ['hr_employee_updation', 'mail','bi_hr'],
    'category': 'Human Resources',
    'maintainer': 'Bassam Infotech LLP',
    'demo': [],
    'data': [
        'views/resignation_view.xml',
        'views/approved_resignation.xml',
        'views/resignation_sequence.xml',
        'security/security.xml',
        'security/ir.model.access.csv',
        'report/hr_resignation_report.xml',
        'report/hr_resignation_report_view.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
}

