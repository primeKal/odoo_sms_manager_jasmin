from odoo import fields, models, api, registry, sql_db


# Simple mailing list to be used over and over again to create a campign that uses a defined
# list of contacts
class MailList(models.Model):
    _name = "mail.sms"
    _description = "Model for a Group Of Recioents"
    _order = "create_date desc"

    # Simlpe name, its descriptions and a list of contacts that have mobile or
    # phone number set
    name = fields.Char("Name")
    descri = fields.Char("Info")
    contacts = fields.Many2many("res.partner", string="Recipents")
    total = fields.Integer("Total", compute="_getTotal", store=True)

    @api.depends('contacts')
    def _getTotal(self):
        i = 0
        for contact in self.contacts:
            i = i + 1
        self.count = i
