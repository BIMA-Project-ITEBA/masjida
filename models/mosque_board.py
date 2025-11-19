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
        Menciptakan atau menautkan akun res.users, memastikan pengguna baru
        secara otomatis menjadi Internal User dan Admin Masjid.
        """
        admin_group = self.env.ref('masjida.group_mosque_admin', raise_if_not_found=False)
        if not admin_group:
            raise ValidationError(_("Group 'Sermon App / Mosque Admin' not found."))

        user = None
        if vals.get('user_id'):
            user = self.env['res.users'].browse(vals['user_id'])
        elif vals.get('email'):
            # 1. Cari user berdasarkan email/login
            user = self.env['res.users'].sudo().search([('login', '=', vals['email'])], limit=1)
            
            # 2. Jika tidak ada, buat user baru
            if not user:
                # Tentukan grup dasar: Internal User dan Portal
                # Internal User (base.group_user) yang membuat akun dapat login ke backend Odoo.
                internal_user_group_id = self.env.ref('base.group_user').id
                portal_group_id = self.env.ref('base.group_portal').id
                
                # Cek apakah user sudah ada di preacher.py, jika iya, user sudah termasuk base.group_portal
                
                user = self.env['res.users'].sudo().create({
                    'name': vals.get('name'),
                    'login': vals.get('email'),
                    'email': vals.get('email'),
                    'groups_id': [(6, 0, [
                        internal_user_group_id, # <-- PERUBAHAN UTAMA: Menambahkan Internal User
                        portal_group_id, 
                    ])]
                })
            
            # 3. Tautkan user ke record yang sedang dibuat
            vals['user_id'] = user.id

        # 4. Buat record board_member
        board_member = super(MosqueBoard, self).create(vals)

        # 5. Tambahkan user ke grup Mosque Admin jika belum ada
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