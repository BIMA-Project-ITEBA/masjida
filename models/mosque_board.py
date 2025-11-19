from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class MosqueBoard(models.Model):
    """
    Model ini mewarisi (inherit) dari res.users menggunakan Delegated Inheritance.
    Setiap record MosqueBoard adalah record res.users, memungkinkan akses backend 
    dan manajemen grup secara efisien.
    """
    _inherit = 'res.users'  # Mewarisi semua properti dan metode res.users
    _inherits = {'res.users': 'user_id'} # Delegasi field ke user_id
    
    _name = 'mosque.board'
    _description = 'Mosque Board Member (Staf Masjid/Admin)'
    
    # user_id adalah field wajib yang menautkan ke parent model (res.users).
    # Odoo akan membuat record res.users baru jika field ini tidak diisi saat 'create'.
    user_id = fields.Many2one(
        'res.users', 
        string='User Account (Delegated)', 
        required=True, 
        ondelete='cascade', # Jika Board Member dihapus, akun user juga dihapus
        auto_join=True,
        index=True
    )
    
    # Catatan: Field 'name', 'email', 'login' (dari res.users) sekarang diakses 
    # secara langsung (e.g., self.name, self.email).

    position = fields.Selection([
        ('chairman', 'Chairman'),
        ('secretary', 'Secretary'),
        ('treasurer', 'Treasurer'),
        ('member', 'Member'),
    ], string='Position', required=True, default='member')
    
    # phone field tetap ada untuk data spesifik board member
    phone = fields.Char(string='Phone Number')
    
    # Relasi ke masjid yang diurus
    mosque_id = fields.Many2one('mosque.mosque', string='Mosque', required=True, ondelete='cascade')

    _sql_constraints = [
        # Batasan SQL: satu akun pengguna hanya boleh memiliki satu posisi di MASJID tertentu.
        # Ini memungkinkan pengguna yang sama menjadi Board Member di beberapa masjid.
        ('user_mosque_uniq', 'unique(user_id, mosque_id)', 'A user can only have one position at a given mosque!'),
    ]

    @api.model_create_multi
    def create(self, vals_list):
        """
        Override create untuk memastikan hak akses (grup) yang benar diberikan.
        Delegated Inheritance secara otomatis membuat atau menautkan res.users.
        """
        # Mendapatkan referensi grup
        admin_group = self.env.ref('masjida.group_mosque_admin', raise_if_not_found=False)
        user_group = self.env.ref('base.group_user', raise_if_not_found=False) # Grup Internal User
        portal_group = self.env.ref('base.group_portal', raise_if_not_found=False) # Grup Portal/Mobile App

        if not admin_group or not user_group or not portal_group:
            raise ValidationError(_("One or more required user groups (Admin, Internal, Portal) not found."))
            
        # 1. Tambahkan grup ke vals. Odoo akan menggunakannya saat membuat res.users baru.
        for vals in vals_list:
            if not vals.get('user_id'): # Hanya berlaku jika Odoo akan membuat user baru
                vals.setdefault('groups_id', []).extend([
                    (4, admin_group.id),
                    (4, user_group.id), # Menjadikan Internal User (Akses Backend)
                    (4, portal_group.id) # Memastikan akses Mobile App (jika diperlukan)
                ])

        # 2. Panggil super().create() - ini yang memicu Delegation Inheritance
        board_members = super().create(vals_list)
        
        # 3. Validasi dan penambahan grup secara terpisah jika user sudah ada sebelumnya
        for member in board_members:
            user = member.user_id.sudo()
            
            # Pastikan user yang ditautkan memiliki grup yang diperlukan
            if not user.has_group('masjida.group_mosque_admin'):
                user.write({'groups_id': [(4, admin_group.id)]})
            
            if not user.has_group('base.group_user'):
                user.write({'groups_id': [(4, user_group.id)]})

        return board_members

    def write(self, vals):
        """
        Mempertahankan logika write yang ada (tetapi disederhanakan)
        untuk memastikan hak akses tetap konsisten jika ada perubahan
        pada record Board Member yang sudah ada.
        """
        res = super().write(vals)
        
        # Logika ini tidak lagi diperlukan karena penambahan grup dilakukan di create
        # dan Delegation Inheritance seharusnya mengelola pembaruan field user
        # namun, ini dapat digunakan sebagai pengamanan jika ada operasi write
        # yang menargetkan user_id atau jika ada modifikasi massal.
        if 'user_id' in vals:
            admin_group = self.env.ref('masjida.group_mosque_admin', raise_if_not_found=False)
            user_group = self.env.ref('base.group_user', raise_if_not_found=False)
            
            if admin_group and user_group:
                for member in self.filtered(lambda m: m.user_id):
                    user = member.user_id.sudo()
                    if not user.has_group('masjida.group_mosque_admin'):
                        user.write({'groups_id': [(4, admin_group.id)]})
                    if not user.has_group('base.group_user'):
                        user.write({'groups_id': [(4, user_group.id)]})
        return res