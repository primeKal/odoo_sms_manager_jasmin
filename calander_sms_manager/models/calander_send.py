from odoo import fields, models, api
from odoo.exceptions import UserError

import smpplib
import smpplib.gsm
import smpplib.client
import smpplib.consts
import logging

import sys

_logger = logging.getLogger(__name__)


# class SmsContentFilter(models.Model):
#     _name = "calander.sms_manager"
#     _description = "To filter out received sms messages based on content"
#     _order = "create_date desc"
#
#     message = fields.Char(string="Filter", required=True)

class Calander_Sms(models.TransientModel):
    _name = "send.sms.calander"
    _description = "A Wizard for sending sms messages to calander event"

    def _default_to(self):
        active = self._context.get('active_id')
        print(active)
        event = self.env["calendar.event"].browse(active)
        attendees = event.attendee_ids
        return attendees
    to = fields.Many2many("calendar.attendee",string="To", default=_default_to, required=True)
    message = fields.Text(string="Message", required=True)
    gateway = fields.Many2one("gateway.sms", string="Gateway", required=True)


    def send_message_attendees(self):
        message = self.message
        gateway = self.gateway
        to = self.to
        send = self.env['send.sms']
        for child in to:
            partner=child.partner_id
            # partner = self.env['res.partner']
            # partner = partner_obj.browse(partner_id)
            if (partner.mobile == False):
                too = partner.phone
            else:
                too = partner.mobile
            # to = child.mobile
            if gateway.type == 'http':
                send.send_with_http(gateway, gateway.username, gateway.pwd, message, too, gateway.code)
            else:
                half_url = gateway.url.split(':')
                send.send_with_smpp(gateway, gateway.username, gateway.pwd, message, too, gateway.code)

        return {'type': 'ir.actions.act_window_close'}

