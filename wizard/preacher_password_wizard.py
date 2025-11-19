# masjida/wizard/preacher_password_wizard.py
# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError

class PreacherPasswordWizard(models.TransientModel):
    _name = 'preacher.password.wizard'
    _description = 'Reset Password for Selected Preachers'

    new_password = fields.Char(
        string='New Password',
        required=True,
        help="Masukkan password baru yang akan diterapkan ke semua Pendakwah yang dipilih."
    )
    
    preacher_ids = fields.Many2many(
        'preacher.preacher', 
        string='Selected Preachers'
    )

    def set_new_password(self):
        """
        Mengatur password baru untuk semua user yang terhubung dengan Pendakwah yang dipilih.
        """
        if not self.new_password:
            raise UserError("Password baru wajib diisi.")

        for preacher in self.preacher_ids:
            if not preacher.user_id:
                # Menghindari error jika preacher belum memiliki user_id
                continue
            
            # Akses superuser (sudo) untuk memastikan hak akses dalam mengubah password
            preacher.user_id.sudo().write({'password': self.new_password})
        
        return {'type': 'ir.actions.act_window_close'}