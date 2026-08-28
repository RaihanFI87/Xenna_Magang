from odoo import fields, models


class KategoriBuku(models.Model):
    _name = 'kategori.buku'
    _description = 'Kategori Buku'

    name = fields.Char(string='Nama Kategori', required=True)
    keterangan = fields.Text(string='Keterangan')
