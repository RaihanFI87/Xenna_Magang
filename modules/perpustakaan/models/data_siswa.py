from odoo import fields, models, api


class DataSiswa(models.Model):
    _name = 'data.siswa'
    _description = 'Data Siswa'

    name = fields.Char(string='Nama Siswa', required=True)
    umur = fields.Integer(string='Umur Siswa', required=True)
    nis = fields.Integer(string='Nis')
    kelas = fields.Selection([
        ('1', '1'),
        ('2', '2'),
        ('3', '3'),
    ])
    tanggal_lahir = fields.Date(string='Tanggal Lahir', required=True)
    tempat_lahir = fields.Char(string='Tempat Lahir', required=True)