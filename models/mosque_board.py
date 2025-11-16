# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

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
    # Email sekarang akan menjadi 'required' karena akan digunakan sebagai login
    email = fields.Char(string='Email (for login)', required=True)

    # Relasi ke masjid yang diurus
    mosque_id = fields.Many2one('mosque.mosque', string='Mosque', required=True, ondelete='cascade')
    
    # Relasi ke akun user Odoo untuk login
    # Kita hapus 'required=True' agar bisa diisi otomatis oleh logic 'create'
    user_id = fields.Many2one('res.users', string='User Account', ondelete='restrict',
                              help="The user account. Will be automatically created or linked based on the Email if left empty.")

    _sql_constraints = [
        ('user_mosque_uniq', 'unique(user_id, mosque_id)', 'A user can only have one position at a given mosque!'),
        ('email_mosque_uniq', 'unique(email, mosque_id)', 'This email is already registered for this mosque!')
    ]

    @api.model
    def create(self, vals):
        """
        Override create method.
        1. Check if user_id is provided.
        2. If not, check if a user exists with the provided email.
        3. If not, create a new user.
        4. Add the user to the 'Mosque Admin' group.
        5. Link the user to the board member.
        """
        admin_group = self.env.ref('masjida.group_mosque_admin', raise_if_not_found=False)
        if not admin_group:
            raise ValidationError(_("Group 'Sermon App / Mosque Admin' not found."))

        user = None
        if vals.get('user_id'):
            user = self.env['res.users'].browse(vals['user_id'])
        elif vals.get('email'):
            # Cari user berdasarkan email/login
            user = self.env['res.users'].sudo().search([('login', '=', vals['email'])], limit=1)
            if not user:
                # Jika tidak ada, buat user baru
                user = self.env['res.users'].sudo().create({
                    'name': vals.get('name'),
                    'login': vals.get('email'),
                    'email': vals.get('email'),
                    # Tambahkan ke grup Portal dan Internal User (grup dasar untuk login backend)
                    'groups_id': [(6, 0, [
                        self.env.ref('base.group_portal').id,
                        self.env.ref('base.group_user').id
                    ])]
                })
            vals['user_id'] = user.id

        # Buat record board_member
        board_member = super(MosqueBoard, self).create(vals)

        # Tambahkan user ke grup Mosque Admin jika belum ada
        if user and not user.has_group('masjida.group_mosque_admin'):
            user.sudo().write({'groups_id': [(4, admin_group.id)]})
            
        return board_member

    def write(self, vals):
        """
        Override write method to ensure group consistency if the user is changed.
        """
        # Panggil write asli
        res = super(MosqueBoard, self).write(vals)
        
        # Jika user_id diubah, pastikan user baru memiliki grup admin
        if 'user_id' in vals:
            admin_group = self.env.ref('masjida.group_mosque_admin', raise_if_not_found=False)
            if admin_group:
                for member in self.filtered(lambda m: m.user_id):
                    if not member.user_id.has_group('masjida.group_mosque_admin'):
                        member.user_id.sudo().write({'groups_id': [(4, admin_group.id)]})
        return res