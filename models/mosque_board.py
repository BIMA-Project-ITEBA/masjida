# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.tools import email_re

class MosqueBoard(models.Model):
    """
    Model ini menggunakan komposisi (Composition) murni:
    MosqueBoard adalah model mandiri yang memiliki relasi Many2one ke res.users (user_id).
    Semua logika pembuatan user ditangani secara manual di metode create.
    """
    _name = 'mosque.board'
    _description = 'Mosque Board Member (Staf Masjid/Admin)'
    
    # --- Field dikembalikan ke model ini ---
    name = fields.Char(string='Name', required=True)
    
    position = fields.Selection([
        ('chairman', 'Chairman'),
        ('secretary', 'Secretary'),
        ('treasurer', 'Treasurer'),
        ('member', 'Member'),
    ], string='Position', required=True, default='member')
    
    phone = fields.Char(string='Phone Number')
    
    # Email field DIBUTUHKAN untuk logic create user.
    # Namun, karena ini bukan Delegation, kita tidak perlu membuatnya 'required' 
    # di sini agar tidak memicu duplikasi constraint login res.users. 
    # Kita andalkan logika create untuk validasi.
    email = fields.Char(string='Email (for login)') 

    # Relasi ke masjid yang diurus
    mosque_id = fields.Many2one('mosque.mosque', string='Mosque', required=True, ondelete='cascade')
    
    # Relasi ke akun user Odoo untuk login
    user_id = fields.Many2one('res.users', string='User Account', ondelete='restrict', index=True,
                              help="The user account linked to this board member. Automatically created/linked by Odoo.")

    _sql_constraints = [
        # Batasan SQL: satu akun pengguna hanya boleh memiliki satu posisi di MASJID tertentu.
        ('user_mosque_uniq', 'unique(user_id, mosque_id)', 'A user can only have one position at a given mosque!'),
        # Tambahkan constraint untuk email, karena email tidak lagi otomatis dilindungi oleh unique(login) res.users di lapisan ini.
        ('email_mosque_uniq', 'unique(email, mosque_id)', 'This email is already registered for this mosque!'),
    ]

    @api.constrains('email')
    def _check_email_format(self):
        for record in self:
            if record.email and not email_re.match(record.email):
                raise ValidationError(_("Invalid email format."))

    @api.model_create_multi
    def create(self, vals_list):
        """
        Melakukan Komposisi Manual: Membuat atau menautkan record res.users,
        lalu menautkannya kembali ke record mosque.board.
        """
        admin_group = self.env.ref('masjida.group_mosque_admin', raise_if_not_found=False)
        user_group = self.env.ref('base.group_user', raise_if_not_found=False) # Internal User
        portal_group = self.env.ref('base.group_portal', raise_if_not_found=False) # Portal/Mobile App

        if not admin_group or not user_group or not portal_group:
            raise ValidationError(_("One or more required user groups (Admin, Internal, Portal) not found."))
        
        # Proses setiap vals
        for vals in vals_list:
            if not vals.get('user_id') and vals.get('email'):
                user_vals = {
                    'name': vals.get('name'),
                    'login': vals.get('email'),
                    'email': vals.get('email'),
                    # Catatan: Password TIDAK diatur di sini. Odoo akan meminta Admin Odoo untuk mengaturnya 
                    # atau pengguna baru harus menggunakan fitur reset password.
                }

                # Cari user yang sudah ada
                user = self.env['res.users'].sudo().search([('login', '=', vals['email'])], limit=1)

                if not user:
                    # Buat user baru jika tidak ada
                    user = self.env['res.users'].sudo().create(user_vals)

                # Tambahkan grup yang diperlukan
                # Tambahkan grup yang diperlukan (TANPA portal)
                groups_to_add = []
                if not user.has_group('masjida.group_mosque_admin'):
                    groups_to_add.append(admin_group.id)
                if not user.has_group('base.group_user'):
                    groups_to_add.append(user_group.id)  # Internal User

                if groups_to_add:
                    user.write({'groups_id': [(4, gid) for gid in groups_to_add]})
                    
                vals['user_id'] = user.id
            
        # Panggil super().create() untuk membuat record mosque.board
        return super().create(vals_list)

    def write(self, vals):
        """
        Override write untuk memperbarui record res.users terkait jika 
        nama atau email diubah.
        """
        if any(f in vals for f in ['name', 'email']) and self.user_id:
            for record in self:
                user_vals = {}
                if 'name' in vals and record.user_id.name != vals['name']:
                    user_vals['name'] = vals['name']
                if 'email' in vals and record.user_id.login != vals['email']:
                    # Update login dan email res.users
                    user_vals['login'] = vals['email']
                    user_vals['email'] = vals['email']
                
                if user_vals:
                    record.user_id.sudo().write(user_vals)
                    
        return super().write(vals)

    def unlink(self):
        """
        Override unlink untuk menghapus record res.users terkait, 
        jika tidak digunakan oleh record lain (misalnya preacher.preacher).
        """
        users_to_unlink = self.mapped('user_id')
        res = super().unlink()
        
        # Hanya hapus user jika tidak ada record mosque.board lain 
        # (atau record preacher.preacher) yang menggunakannya.
        for user in users_to_unlink:
            # Cari apakah user ini masih ditautkan ke record MosqueBoard lain
            if not self.env['mosque.board'].search_count([('user_id', '=', user.id)]):
                # Opsional: Cek juga apakah user ini masih ditautkan ke record Preacher
                if not self.env['preacher.preacher'].search_count([('user_id', '=', user.id)]):
                    user.unlink()
        return res