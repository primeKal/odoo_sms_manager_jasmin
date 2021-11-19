import threading
from datetime import datetime
import requests
from odoo import fields, models, api, registry, sql_db
from threading import Thread
from odoo.exceptions import UserError

import smpplib.gsm
import smpplib.client
import smpplib.consts
import smpplib
import logging
import sys

import base64

# Campign based sms marketing, Here we can create campign of 3 different types and then we will
# Parse them to a rest api call and send them to jasmin and jasmin will replay back with a batch id
# We will use that id in our http callback method to match which callback is for which campign
# You can also schedule sms campigns for a later time in which an automated task will check them and
# send them if the time is up
class ListSms(models.Model):
    _name = "list.sms"
    _description = "Model for received sms messages"
    _order = "create_date desc"

    name = fields.Char(string="Subject")
    content = fields.Char(string="Content", required=True, size=150)
    type = fields.Selection([
        ('list', 'Contacts'),
        ('number', 'Numbers'),
        ('mail', 'Contact List')], "Campaign Type", default='list')

    # we will need this contact field, the type is list of contacts else its none
    contacts = fields.Many2many("res.partner", string="Recipents")

    # we will need this mail field, the type is mail else its none
    # It is used to locate the mailing list we want to specify
    mail = fields.Many2one("mail.sms", string="Mailing List")

    # we will need these 3 fields, if the type is number  else its none
    # It is used to send sms messages from the starting number to a range we specifiy
    # eg if starting number is 251911000000 and increment is 100
    # it will send to all numbers from 251911000000 to 251911000100
    start = fields.Char(string="Starting Number")
    increment = fields.Integer(string="Range of Nmbers")
    final = fields.Char(String="Last Number")

    #Jasmin Respone, to be used in callback
    batchid = fields.Char(string="Jasmin Id")

    url = fields.Many2one("gateway.sms", string="Gateway Used", required=True)
    color = fields.Integer(compute='_getColor', store=True)
    status = fields.Selection([
        ('d', 'Draft'),
        ('s', 'Scheduled'),
        ('st', 'Sent'),
        ('dl', 'Delivered')
    ], "Status", group_expand='_expand_status')
    now = fields.Boolean("Send Now", default=True)
    send_time = fields.Datetime("Schedule")

    #Total messages in queue of jasmin
    count = fields.Integer("Count", default=0)

    # Total messages acknowledged by call back
    delivered = fields.Integer("Count", default=0)

    # I dont know wat this is
    def _expand_status(self, status, domain, order):
        return [key for key, val in type(self).status.selection]

    # Method used to set color based on status
    @api.depends('status')
    def _getColor(self):
        if self.status == 'd':
            self.color = 5
        elif self.status == 's':
            self.color = 2
        elif self.status == 'st':
            self.color = 10
        elif self.status == 'dl':
            self.color = 15

    # Over ride the create method to send the campign if send now is true
    # Will call 3 different methods depending on the type of campaign, also set the sending time
    @api.model
    def create(self, vals):
        if vals['type'] == 'number' and vals['now'] == True:
            vals = self.prepare_number_type(vals)
            vals['send_time'] = datetime.now()
        elif vals['type'] == 'list' and vals['now'] == True:
            vals = self.prepare_list_type(vals)
            vals['send_time'] = datetime.now()
        elif vals['type'] == 'mail' and vals['now'] == True:
            vals = self.prepare_mail_type(vals)
            vals['send_time'] = datetime.now()

        # if no send now is false and send time is not set make it a draft and save it
        elif vals['now'] == False and vals['send_time'] == False:
            vals['status'] = 'd'
        # if send now is false and send time is set, check the time tat it its after
        # the current time, if true save it with a status of scheduled
        elif vals['now'] == False and vals['send_time']:
            vals['status'] = 's'
            schedule = vals['send_time']
            date = datetime.strptime(schedule, "%Y-%m-%d %H:%M:%S")
            if date < datetime.now():
                raise UserError("please Schedule For The Future")
        rec = super(ListSms, self).create(vals)
        return rec

    # We also over ride the write function to check unwanted edits of campaigns
    # case 1- set send time for draft
    # case 2- remove send time from a scheduled campaign
    # case 3- editing send now boolean

    def write(self, values):
        if 'send_time' in values and self.status == 'd' and values['send_time']:
            schedule = values['send_time']
            date = datetime.strptime(schedule, "%Y-%m-%d %H:%M:%S")
            if date < datetime.now():
                raise UserError("please Schedule For The Future")
            values['status'] = 's'
        elif 'send_time' in values and values['send_time'] == False:
            self.status == 'd'
        elif 'now' in values and self.status == 's':
            raise UserError("Please Press The send Now Button If You want to send now")
        elif 'now' in values and self.status == 'd':
            raise UserError("Please Press The send Now Button If You want to send now")
        # elif self.status == 'st':
        #     raise UserError("You can not alter a sent SMS")
        return super(ListSms, self).write(values)

    # prepare the numbers and find the final number of the number type campaign
    def prepare_number_type(self, vals):
        # check it has more than 3 numbers
        try:
            head = vals['start'][0:3]
        except:
            raise UserError("Please Input the correct starting time")
        # get the final number and save it in vals
        if (head == '251'):
            strr = vals['start'][3:]
            try:
                intt = int(strr)
                final = intt + vals['increment']
                final = str(final)
                final = "+251" + final
                vals['final'] = final
            except:
                raise UserError("Please Insert a valid Starting Phone Number")
            # call send batch method to parse and send it, it return jasmins response
            # which is a dictionary with batchid and count
            id = self.send_batch(vals)
            repo = eval(id.text)
            # save them in vals and set the status as sent
            vals['batchid'] = repo['data']['batchId']
            vals['count'] = repo['data']['messageCount']
            vals['status'] = 'st'
        else:
            raise UserError("Please Use 251 for the starting number")
        # return te vals to be saved in database
        return vals

    def prepare_mail_type(self, vals):
        numList = []
        mailing_ibj = self.env['mail.sms'].browse(vals['mail'])
        for contact in mailing_ibj.contacts:
            if (contact.mobile == False):
                try:
                    num = contact.phone
                    numList.append(num)
                except:
                    raise UserError(
                        "Please Use an integer in the phone value(omit the + sign) and Start the Campaign Process again")
            else:
                num = contact.mobile
                numList.append(num)

        url = self.env['gateway.sms'].browse(vals['url'])
        print(url)
        re = send_same_message_to_many(url.username, url.pwd, url.code, vals['content'], numList,url.url)
        response = eval(re.text)
        vals['batchid'] = response['data']['batchId']
        vals['count'] = response['data']['messageCount']
        vals['status'] = 'st'
        return vals

        pass

    # fetch all numbers from the databse and pass them to the sending method
    # since this method is called from 2 places check the contacts foreign key
    def prepare_list_type(self, vals):
        numList = []
        print("lets fetch all contacts")
        if len(vals['contacts'][0]) > 1:
            contacts = vals['contacts'][0][2]
        else:
            cont = []
            contacts = vals['contacts']
            for contact in contacts:
                cont.append(contact.id)
            contacts = cont

        for val in contacts:
            recipent = self.env['res.partner'].browse(val)
            if (recipent.mobile == False):
                try:
                    num = recipent.phone
                    numList.append(num)
                except:
                    raise UserError(
                        "Please Use an integer in the phone value(omit the + sign) and Start the Campaign Process again")
            else:
                num = recipent.mobile
                numList.append(num)
        url = self.env['gateway.sms'].browse(vals['url'])
        print(url)
        re = send_same_message_to_many(url.username, url.pwd, url.code, vals['content'], numList,url.url)
        response = eval(re.text)
        vals['batchid'] = response['data']['batchId']
        vals['count'] = response['data']['messageCount']
        vals['status'] = 'st'
        return vals
        pass

    # this method is called by prepare number type
    # it gets the start and last number and the adds all the numbers in between
    # to a list and passes them to a sending method
    # also fetchs the gateway model from its id in vals
    # returns jasmins response
    def send_batch(self, vals):
        print(vals)
        print(self.url.pwd)
        numlist = []
        strr = vals['start'][3:]
        intt = int(strr)
        final = intt + vals['increment']
        while intt != final:
            my = str(intt)
            my = "+251" + my
            numlist.append(my)
            intt = intt + 1
        print(numlist)
        url = self.env['gateway.sms'].browse(vals['url'])
        print(url)
        re = send_same_message_to_many(url.username, url.pwd, url.code, vals['content'], numlist,url.url)
        return re

    # method to convert self(campaign object) to a vals dictionary
    # because create method only accepts dictionary
    def convert_self_to_dict(self, record):
        val = {'type': record.type,
               'start': record.start,
               'mail': record.mail.id,
               'contacts': record.contacts,
               'increment': record.increment,
               'url': record.url.id,
               'content': record.content
               }
        return val

    # Method to be called with an automated scheduled action
    # this will execute every 5 or 10 minutes to see check and execute campaigns
    def scheduled_sender(self):
        campaign_obj = self.env['list.sms'].search([('status', '=', 's')])
        for record in campaign_obj:
            if record.send_time and record.send_time < datetime.now():
                values = self.convert_self_to_dict(record)
                if values['type'] == 'number':
                    values = self.prepare_number_type(values)
                elif values['type'] == 'list':
                    values = self.prepare_list_type(values)
                elif values['type'] == 'mail':
                    values = self.prepare_mail_type(values)
                record.batchid = values['batchid']
                record.count = values['count']
                record.status = values['status']

    # Method to be called with the send now button on campaign forms of status scheduled and draft
    # This simple calls the previous methods to send the message
    def send_message(self):
        values = {'type': self.type,
                  'start': self.start,
                  'mail': self.mail.id,
                  'contacts': self.contacts,
                  'increment': self.increment,
                  'url': self.url.id,
                  'content': self.content
                  }
        if values['type'] == 'number':
            values = self.prepare_number_type(values)
        elif values['type'] == 'list':
            values = self.prepare_list_type(values)
        elif values['type'] == 'mail':
            values = self.prepare_mail_type(values)
        self.batchid = values['batchid']
        self.count = values['count']
        self.status = values['status']
        self.send_time = datetime.now()

# Parse any data that is to be sent to jasmins rest api
# and encode the username and password with base64 as the jasmin
# documentation
def send_same_message_to_many(uname, pwd, fr, message, numlist,url):
    stringg = str(uname + ':' + pwd)
    stringg = stringg.encode("utf-8")
    auth = base64.b64encode(stringg)
    print(auth)
    auth = "Basic ".encode('utf-8') + auth
    # auth = "Basic cmVraWs6cmVraWs="
    auth = str(auth)
    fr = str(fr)
    message = str(message)
    # auth = "Basic " + str(auth)
    print(auth)
    # message = message.encode('utf-8')
    print(":Starting")
    if url[0] == "h" :
        print("This is HTTP type so cut it")
        print(url)
        temp = url[7:15]
        temp_url = "http://" + temp + ":8080/secure/sendbatch"
        print(temp_url)
        raise UserError(temp_url)
    else :
        urll=url
        temp_url = "http://" + urll + ":8080/secure/sendbatch"
        print(temp_url)
        raise UserError(temp_url)
    # url = 'http://127.0.0.1:8080/secure/sendbatch'
    # header = {'Authorization': 'Basic aGVsbG86aGVsbG8='}
    header = {'Authorization': auth}
    print(header)
    # prepare the payload and then add the neccessary numbers in the list
    payload = {
        # "globals": {
        #     "from": "Brand2",
        #     "dlr-level": 3,
        #     "dlr": "yes",
        #     "dlr-url": "http://127.0.0.1:8069/dlr"
        # },
        "batch_config": {
            "callback_url": "http://127.0.0.1:8069/restcallback",
            "errback_url": "http://127.0.0.1:8069/restcallback"
        },
        "messages": [
            {
                "to": [

                ],
                "from": fr
            }
        ]
    }
    for num in numlist:
        if num is False:
            continue
        if num[0] == "+":
            num = num[1:]
        payload.get("messages")[0].get("to").append(num)
    payload.get("messages")[0].__setitem__("content", message)
    print("payload is " + str(payload))
    try:
        response = requests.post(temp_url, headers=header, json=payload)
        print(response.status_code)
        print(response.text)
        st_code = response.status_code
        # if st_code != 200:
        #     raise UserError(
        #         str(response.status_code) + " code :" + "An Error Ocuured please check your configuration settings")
        return response
    except Exception as e:
        print(e)
        print(e.__str__())
        raise UserError("Error Occured please check the server")
