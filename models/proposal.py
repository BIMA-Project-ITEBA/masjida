# -*- coding: utf-8 -*-

from odoo import models, fields, api

class SermonProposal(models.Model):
    _name = 'sermon.proposal'
    _description = 'Sermon Schedule Proposal from Preacher to Mosque'

    preacher_id = fields.Many2one('preacher.preacher', string='Preacher', required=True,
                                 default=lambda self: self.env['preacher.preacher'].search([('user_id', '=', self.env.uid)], limit=1))
    mosque_id = fields.Many2one('mosque.mosque', string='Target Mosque', required=True, domain="[('admin_ids', '!=', False)]")
    
    proposed_topic = fields.Char(string='Proposed Topic', required=True)
    proposed_start_time = fields.Datetime(string='Proposed Time', required=True)
    notes = fields.Text(string='Notes for Mosque Admin')
    
    state = fields.Selection([
        ('draft', 'Draft'),          # Newly created by the preacher
        ('submitted', 'Submitted'),  # Submitted to the mosque admin
        ('approved', 'Approved'),    # Approved by the mosque admin
        ('rejected', 'Rejected')     # Rejected by the mosque admin
    ], string='Status', default='draft', readonly=True)

    def action_submit(self):
        """Function to send the proposal to the mosque admin."""
        self.state = 'submitted'
        # Notification logic for the mosque admin can be added here

    def action_approve(self):
        """Function for the mosque admin to approve and create a new schedule."""
        self.ensure_one()
        # Validation: Ensure the user is an admin of the related mosque
        # if self.env.user not in self.mosque_id.admin_ids:
        #     raise models.UserError('Only this mosque\'s admin can approve the proposal.')
        is_board_member = self.env['mosque.board'].search_count([('mosque_id', '=', self.mosque_id.id),('user_id', '=', self.env.uid)])
        if not is_board_member:
            raise models.UserError('Only a board member of this mosque can approve the proposal.')
        # Sisa kode di bawahnya biarkan sama
        self.env['sermon.schedule'].create({
            # ...
        })
        self.state = 'approved'
            
        # Create a new record in sermon.schedule
        self.env['sermon.schedule'].create({
            'mosque_id': self.mosque_id.id,
            'preacher_id': self.preacher_id.id,
            'topic': self.proposed_topic,
            'start_time': self.proposed_start_time,
            'state': 'confirmed' # The status is immediately set to confirmed
        })
        self.state = 'approved'

    def action_reject(self):
        """Function for the mosque admin to reject the proposal."""
        self.ensure_one()
        if self.env.user not in self.mosque_id.admin_ids:
            raise models.UserError('Only this mosque\'s admin can reject the proposal.')
        self.state = 'rejected'