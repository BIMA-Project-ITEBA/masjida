# -*- coding: utf-8 -*-

from odoo import models, fields

class MosqueBoard(models.Model):
    _name = 'mosque.board'
    _description = 'Mosque Board Member'

    name = fields.Char(string='Name', required=True)
    position = fields.Selection([
        ('chairman', 'Chairman'),
        ('secretary', 'Secretary'),
        ('treasurer', 'Treasurer'),
        ('member', 'Member'),
    ], string='Position', required=True, default='member')
    
    phone = fields.Char(string='Phone Number')
    email = fields.Char(string='Email')

    # Relasi ke masjid yang diurus
    mosque_id = fields.Many2one('mosque.mosque', string='Mosque', required=True, ondelete='cascade')
    
    # Relasi ke akun user Odoo untuk login
    user_id = fields.Many2one('res.users', string='User Account', required=True,
                              help="The user account that will be used by this board member to log in.")

    _sql_constraints = [
        ('user_mosque_uniq', 'unique(user_id, mosque_id)', 'A user can only have one position at a given mosque!')
    ]