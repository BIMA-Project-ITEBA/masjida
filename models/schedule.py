# -*- coding: utf-8 -*-

from odoo import models, fields, api
import urllib.parse

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
        self.state = 'confirmed'
        
    def action_reject(self):
        """Function called by the preacher to reject the invitation."""
        self.ensure_one()
        self.state = 'rejected'

    def action_cancel(self):
        """Function to cancel a confirmed schedule."""
        self.state = 'cancelled'

    def action_open_whatsapp_invitation(self):
        """
        Menghasilkan URL WhatsApp untuk mengirim undangan awal kepada Pendakwah.
        """
        self.ensure_one()
        
        preacher = self.preacher_id
        mosque = self.mosque_id
        
        # 1. Validasi dan Pembersihan Nomor Telepon
        if not preacher.phone:
            raise models.UserError("Nomor telepon Pendakwah belum diisi pada profilnya.")

        # Bersihkan nomor dari spasi/strip dan pastikan format internasional (62...)
        phone_number = ''.join(filter(str.isdigit, preacher.phone))
        if phone_number.startswith('0'):
            phone_number = '62' + phone_number[1:]
        elif not phone_number.startswith('62') and len(phone_number) > 5:
             # Asumsi, jika tidak diawali 0 atau 62, tambahkan 62 (ini perlu disesuaikan dengan standar Anda)
             phone_number = '62' + phone_number

        # 2. Penentuan Panggilan Hormat (Honorific)
        honorific = 'Ustaz'
        if preacher.gender == 'female':
            honorific = 'Ustazah'
        elif preacher.gender != 'male':
            # Jika gender tidak terdefinisi/tidak jelas
            honorific = 'Ustaz/Ustazah'

        # 3. Format Tanggal & Waktu
        # Mengambil objek datetime yang sudah disesuaikan dengan timezone pengguna Odoo
        start_dt = fields.Datetime.context_timestamp(self, self.start_time)
        end_dt = fields.context_timestamp(self, self.end_time) if self.end_time else None
        
        # Menggunakan strftime, dengan asumsi locale Odoo sudah dikonfigurasi untuk Indonesia
        # Jika locale belum diatur, perlu penanganan manual (lihat catatan di bawah)
        # Format: Senin, 19 November 2025
        formatted_date = start_dt.strftime("%A, %d %B %Y")
        
        formatted_time_start = start_dt.strftime("%H:%M")
        formatted_time_end = end_dt.strftime("%H:%M") if end_dt else 'Selesai'

        # 4. Susun Pesan (menggunakan f-string untuk keterbacaan)
        message = f"""assalamualaikum {honorific} {preacher.name},
Semoga {honorific} selalu dalam keadaan sehat wal 'afiat.
saya pengurus Masjid {mosque.name} dengan hormat menawarkan untuk mengisi kegiatan di masjid kami. :

Tema/Topik yang Diusulkan: {self.topic}
Waktu yang Diajukan: {formatted_date}
Pukul: {formatted_time_start} - {formatted_time_end} WIB

Jika {honorific} berminat dan memiliki pertanyaan, mohon berikan balasan pada pesan ini.
"""
        
        # 5. URL Encode Pesan
        encoded_message = urllib.parse.quote(message)
        
        # 6. Buat Link WhatsApp
        whatsapp_url = f"https://wa.me/{phone_number}?text={encoded_message}"
        
        # 7. Kembalikan action untuk membuka link di browser baru
        return {
            'type': 'ir.actions.act_url',
            'url': whatsapp_url,
            'target': 'new', 
        }

    @api.model
    def _check_schedule_done(self):
        """Scheduler function to automatically set the state to 'Done'."""
        schedules = self.search([('state', '=', 'confirmed'), ('end_time', '<', fields.Datetime.now())])
        schedules.write({'state': 'done'})
