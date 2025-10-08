# -*- coding: utf-8 -*-

from odoo import models, fields

class ResUsers(models.Model):
    _inherit = 'res.users'

    # The inverse relation from mosque.mosque
    # This field is created automatically by the Many2many definition in the mosque.mosque model.
    # It doesn't need to be defined again, but it's good to be aware of its existence.
    # mosque_ids = fields.Many2many('mosque.mosque', 'mosque_res_users_rel', 'user_id', 'mosque_id', string='Managed Mosques')