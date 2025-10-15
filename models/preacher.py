# -*- coding: utf-8 -*-

from odoo import models, fields, api

class Preacher(models.Model):
    _name = 'preacher.preacher'
    _description = 'Preacher Master Data Model'
    
    code = fields.Char(string='code', required=True)
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
    ], string='Gender', default='male', readonly=True, copy=False)
    period = fields.Float(string="period of preaching(year)")

    state = fields.Selection([
        ('draft', 'Draft'),                 # Created by mosque admin
        ('proses', 'Proses'),   # Invitation sent to preacher
        ('confirmed', 'Confirmed'),         # Accepted by preacher
        ('rejected', 'Rejected'),           # Rejected by preacher              # The event has passed
        ('cancelled', 'Cancelled')          # Cancelled by either party
    ], string='Status', default='draft', readonly=True, copy=False)

    @api.model
    def create(self, vals):
        """Automatically creates a portal user if one does not exist when a preacher profile is created."""
        preacher = super(Preacher, self).create(vals)
        if not preacher.user_id and preacher.email:
            # Create a new user and add them to the portal group
            user = self.env['res.users'].sudo().create({
                'name': preacher.name,
                'login': preacher.email,
                'email': preacher.email,
                'groups_id': [(6, 0, [self.env.ref('base.group_portal').id])]
            })
            preacher.user_id = user.id
        return preacher