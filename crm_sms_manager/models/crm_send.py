import urllib

from odoo import fields, models, api
from odoo.exceptions import UserError

import smpplib
import smpplib.gsm
import smpplib.client
import smpplib.consts
import logging

import sys

_logger = logging.getLogger(__name__)


class Crm_Sms_Manager(models.TransientModel):
    _name = "send.sms.crm"
    _description = "A Wizard for sending sms messages to CRM"

    def _default_to(self):
        active = self._context.get('active_id')
        print(active)
        crm = self.env["crm.lead"].browse(active)
        number = crm.mobile
        if (number == False):
            number = crm.phone
        return number

    to = fields.Char(string="To", default=_default_to, required=True)
    message = fields.Char(string="Message", required=True, size=150)
    gateway = fields.Many2one("gateway.sms", string="Gateway", required=True)


    def send_message_crm(self):
        url = self.gateway
        msg = self.message
        dest = self.to
        un = self.gateway.username
        pwd = self.gateway.pwd
        fr = self.gateway.code
        gateway_type = self.gateway.type
        send = self.env['send.sms']
        if gateway_type == 'http':
            send.send_with_http(url, un, pwd, msg, dest, fr)
        else:
            send.send_with_smpp(url, un, pwd, msg, dest, fr)
        return {'type': 'ir.actions.act_window_close'}
