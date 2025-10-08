# -*- coding: utf-8 -*-

from odoo import models, fields

class SermonContent(models.Model):
    _name = 'sermon.content'
    _description = 'Sermon Content (Text, Photo, Video)'

    name = fields.Char(string='Content Title', required=True)
    preacher_id = fields.Many2one('preacher.preacher', string='By', required=True, ondelete='cascade')
    
    content_type = fields.Selection([
        ('text', 'Article/Text'),
        ('image', 'Photo'),
        ('video', 'Video')
    ], string='Content Type', required=True, default='text')
    
    content_text = fields.Html(string='Article Content')
    image_content = fields.Image(string='Upload Photo')
    video_url = fields.Char(string='Video URL', help="URL from platforms like YouTube, Vimeo, etc.")
    
    publish_date = fields.Datetime(string='Publish Date', default=fields.Datetime.now)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('published', 'Published')
    ], string='Status', default='draft')

    def action_publish(self):
        """Publish the content to make it visible to public users."""
        self.write({'state': 'published', 'publish_date': fields.Datetime.now()})

    def action_unpublish(self):
        """Unpublish the content, returning it to draft state."""
        self.write({'state': 'draft'})