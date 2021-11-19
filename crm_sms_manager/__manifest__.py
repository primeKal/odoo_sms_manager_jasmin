# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': 'CRM Sms Manager',
    'version': '13.1.1',
    'summary': 'Tool used to send and receive sms messages from jasmin server',
    'sequence': 15,
    'description': "Helps send bulk sms to jasmin's sms gateway. And receive sms in a stateful SMPP protocool",
    'category': 'Tools',
    'depends': [
        'web_notify',
        'crm'
    ],
    'data': [
        'views/wizz.xml'
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
