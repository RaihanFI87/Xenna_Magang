from odoo import fields, models, api


class DataBuku(models.Model):
    _name = 'data.buku'
    _description = 'Description'

    name = fields.Char(string='Nama Buku')
    tahun_terbit = fields.Datetime(string='Tahun Terbit', required=True)
    penulis = fields.Char(string='Penulis')
    penerbit = fields.Char(string='Penerbit')
    jumlah_halaman = fields.Integer(string='Jumlah Halaman')
    kategori_id = fields.Many2one('kategori.buku', string='Kategori')
    jumlah_buku = fields.Integer(string='Jumlah Buku', default=1)
    jumlah_tersedia = fields.Integer(string='Jumlah Tersedia',default=1)

    @api.constrains('jumlah_buku', 'jumlah_tersedia')
    def _check_jumlah_buku(self):
        for record in self:
            if record.jumlah_buku < 0:
                raise ValidationError(
                    'Jumlah buku tidak boleh kurang dari 0.'
                )
            if record.jumlah_tersedia < 0:
                raise ValidationError(
                    'Jumlah buku tersedia tidak boleh kurang dari 0.'
                )
            if record.jumlah_tersedia > record.jumlah_buku:
                raise ValidationError(
                    'Jumlah tersedia tidak boleh lebih besar '
                    'dari jumlah buku.'
                )