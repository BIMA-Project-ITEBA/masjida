# -*- coding: utf-8 -*-

from odoo import models, fields, api

class Preacher(models.Model):
    _name = 'preacher.preacher'
    _description = 'Preacher Master Data Model'
    _rec_name = "display_name"

    
    code = fields.Char(string='code')
    name = fields.Char(string='Preacher Name', required=True)
    image = fields.Image(string='Profile Photo', max_width=1024, max_height=1024)
    phone = fields.Char(string='Phone Number')
    email = fields.Char(string='Email')
    bio = fields.Html(string='Biography')
    education = fields.Char(string='Education')
    date_of_birth = fields.Date(string='Date of birth')
    # FIELD DIPERBARUI: Dari Char menjadi Many2one
    specialization_id = fields.Many2one('preacher.specialization', string='Specialization')
    
    # FIELD BARU: Relasi ke Area
    area_id = fields.Many2one('area.area', string='Area')
    
    # Relation to the frontend user (portal user) for login purposes
    user_id = fields.Many2one('res.users', string='User Account', ondelete='cascade', copy=False,
                              help="The user account linked to this preacher for app login.")
    
    # Relation to view all schedules for this preacher
    schedule_ids = fields.One2many('sermon.schedule', 'preacher_id', string='My Sermon Schedules')
    
    # Relation to view all content created by this preacher
    content_ids = fields.One2many('sermon.content', 'preacher_id', string='My Content')
    
    # Relation to view all proposals sent by this preacher
    proposal_ids = fields.One2many('sermon.proposal', 'preacher_id', string='Sent Sermon Proposals')
    gender = fields.Selection([
        ('male', 'Laki-laki'),                 # Created by mosque admin
        ('female', 'Perempuan'),   # Invitation sent to preacher
    ], string='Gender', default='male')
    period = fields.Float(string="period of preaching(year)")

    state = fields.Selection([
        ('draft', 'Draft'),                 # Created by mosque admin
        ('proses', 'Proses'),   # Invitation sent to preacher
        ('confirmed', 'Confirmed'),         # Accepted by preacher
        ('rejected', 'Rejected'),           # Rejected by preacher              # The event has passed
        ('cancelled', 'Cancelled')          # Cancelled by either party
    ], string='Status', default='draft', readonly=True, copy=False)

    display_name = fields.Char(compute="_compute_display_name", store=True)

    @api.depends('name', 'code', 'area_id.name')
    def _compute_display_name(self):
        for preacher in self:
            name = f"[{preacher.code or 'N/A'}] {preacher.name or 'N/A'}"
            if preacher.area_id.name:
                name += f" ({preacher.area_id.name})"
            preacher.display_name = name

    @api.model
    def create(self, vals):
        """
        [DIUBAH]: Menggunakan logika Komposisi yang disederhanakan dan 
        memastikan user_id tidak bersifat unik.
        """
        
        user = None
        if vals.get('email'):
            # 1. Cari user yang sudah ada (tidak perlu cek user_id di vals karena ini Composition)
            user = self.env['res.users'].sudo().search([('login', '=', vals['email'])], limit=1)
            
            # 2. Jika user tidak ada, buat user Portal baru.
            if not user:
                portal_group_id = self.env.ref('base.group_portal').id
                user_vals = {
                    'name': vals.get('name'),
                    'login': vals.get('email'),
                    'email': vals.get('email'),
                    'groups_id': [(6, 0, [portal_group_id])] # Hanya grup Portal
                }
                user = self.env['res.users'].sudo().create(user_vals)
                
            # 3. Tautkan user ke record ini
            vals['user_id'] = user.id

        # 4. Buat record preacher
        preacher = super(Preacher, self).create(vals)
        return preacher
