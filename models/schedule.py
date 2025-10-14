# -*- coding: utf-8 -*-

from odoo import models, fields, api

class SermonSchedule(models.Model):
    _name = 'sermon.schedule'
    _description = 'Sermon Schedule at a Mosque by a Preacher'
    _rec_name = 'topic'

    mosque_id = fields.Many2one('mosque.mosque', string='Mosque', required=True, ondelete='cascade')
    preacher_id = fields.Many2one('preacher.preacher', string='Preacher', required=True, ondelete='cascade')
    
    topic = fields.Char(string='Sermon Topic/Theme', required=True)
    description = fields.Text(string='Brief Description')
    start_time = fields.Datetime(string='Start Time', required=True)
    end_time = fields.Datetime(string='End Time')
    
    state = fields.Selection([
        ('draft', 'Draft'),                 # Created by mosque admin
        ('sent', 'Pending Confirmation'),   # Invitation sent to preacher
        ('confirmed', 'Confirmed'),         # Accepted by preacher
        ('rejected', 'Rejected'),           # Rejected by preacher
        ('done', 'Done'),                   # The event has passed
        ('cancelled', 'Cancelled')          # Cancelled by either party
    ], string='Status', default='draft', readonly=True, copy=False)

    def action_send_invitation(self):
        """Function called by the mosque admin to send the invitation."""
        for rec in self:
            # Logic to send notifications/emails to the preacher can be added here
            rec.state = 'sent'
            
    def action_confirm(self):
        """Function called by the preacher to accept the invitation."""
        self.ensure_one()
        # Validation: Ensure the user clicking is the correct preacher
        if self.env.user != self.preacher_id.user_id:
            raise models.UserError('You are not authorized to accept this invitation.')
        self.state = 'confirmed'
        
    def action_reject(self):
        """Function called by the preacher to reject the invitation."""
        self.ensure_one()
        self.state = 'rejected'

    def action_cancel(self):
        """Function to cancel a confirmed schedule."""
        self.state = 'cancelled'

    @api.model
    def _check_schedule_done(self):
        """Scheduler function to automatically set the state to 'Done'."""
        schedules = self.search([('state', '=', 'confirmed'), ('end_time', '<', fields.Datetime.now())])
        schedules.write({'state': 'done'})
