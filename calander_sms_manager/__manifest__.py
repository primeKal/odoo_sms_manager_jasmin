# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'Calander Sms Manager',
    'version': '13.1.1',
    'summary': 'Tool used to send and receive sms messages from jasmin server to calander attendees',
    'sequence': 15,
    'description': "Helps send message",
    'category': 'Tools',
    'depends': [
        'web_notify',
        'sms_manager',

    ],
    'data': [
                'views/wiz.xml'
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
