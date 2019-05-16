# -*- coding: utf-8 -*-
##############################################################################
#
#    Bassam Infotech LLP.
#    Copyright (C) 2017-TODAY Bassam Infotech LLP(<https://www.bassaminfotech.com>).
#    Author: Redouane ADADI(<https://www.bassaminfotech.com>)
#    you can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    It is forbidden to publish, distribute, sublicense, or sell copies
#    of the Software or modified copies of the Software.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{
    'name': 'Employee Information Excel Report',
    'version': '1.1',
    'summary': 'Employee Information Excel Report',
    'description': 'Employee Information Excel Report',
    'category': 'Human Resources',
    'author': 'Bassam Infotech LLP',
    'website': 'http://www.bassaminfotech.com',
    'company': 'Odoo Developers',
    'depends': ['base', 'hr', 'report_xlsx', 'school'],
    'data': ['wizard/employee_info_excel_report.xml'],
    'images': ['static/description/main.png'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}