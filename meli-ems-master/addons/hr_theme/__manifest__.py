# -*- coding: utf-8 -*-
###################################################################################
#    A part of Open HRMS Project <https://www.openhrms.com>
#
#    Bassam Infotech LLP
#    Copyright (C) 2018-TODAY Cybrosys Technologies (<https://www.Bassaminfotech.com>).
#    
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
    'name': 'Open HRMS Theme',
    'version': '10.0.1.1.0',
    'summary': """Curtain Raiser of Open HRMS.""",
    'description': """Open HRMS all set in new colour theme of blues and whites totaling to a new experience""",
    'category': 'Theme',
    'author': 'Bassam Infotech LLP',
    'company': 'Bassam Infotech LLP',
    'maintainer': 'Bassam Infotech LLP',
    'website': "https://www.bassaminfotech.com",
    'depends': ['web'],
    'data': [
        'views/open_hrms_theme.xml',
    ],
    'demo': [],
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
