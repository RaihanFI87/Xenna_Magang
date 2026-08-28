
from odoo import api, fields, models
from odoo.exceptions import UserError


class PinjamBuku(models.Model):
    _name = 'pinjam.buku'
    _description = 'Description'

    name = fields.Char(
        string='Nomor Transaksi',
        default='-',
        readonly=True,
        copy=False
    )

    siswa = fields.Many2one(comodel_name='data.siswa', string='Siswa', required=True)
    buku = fields.Many2one(comodel_name='data.buku', required=True)
    tanggal_peminjaman = fields.Date(string='Tanggal Pinjaman', required=True)
    tanggal_pengembalian = fields.Date(string='Tanggal Pengambalian',  readonly=True)
    tanggal_jatuh_tempo = fields.Date(string='Tanggal Jatuh Tempo', required=True)
    jumlah_hari_terlambat = fields.Integer(
        string='Hari Terlambat',
        readonly=True,
        default=0
    )

    status = fields.Selection(
        [
            ("dipinjam", "Dipinjam"),
            ("dikembalikan", "Dikembalikan"),
            ("terlambat", "Terlambat")
        ],
        string='Status',
        default='dipinjam',
        required=True,
    )

    @api.model
    def create(self, vals):
        if vals.get('buku'):
            buku = self.env['data.buku'].browse(vals['buku'])
        if buku.jumlah_tersedia <= 0:
            raise UserError(
                'Buku yang dipilih sedang tidak tersedia.'
            )
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'pinjam.buku'
            ) or 'New'

        return super().create(vals)

    def action_pinjam(self):
        for record in self:
            if record.buku.jumlah_tersedia <= 0:
                raise UserError(
                    'Buku yang dipilih sedang tidak tersedia.'
                )
            record.buku.jumlah_tersedia -= 1
            record.status = 'dipinjam'

    def action_kembalikan(self):
        for record in self:
            if record.status == 'dikembalikan':
                raise UserError('Buku sudah dikembalikan.')
            tanggal_kembali = fields.Date.today()
            record.tanggal_pengembalian = tanggal_kembali
            if tanggal_kembali > record.tanggal_jatuh_tempo:
                record.jumlah_hari_terlambat = (
                        tanggal_kembali - record.tanggal_jatuh_tempo
                ).days
                record.total_denda = (
                        record.jumlah_hari_terlambat * record.denda_per_hari
                )
            else:
                record.jumlah_hari_terlambat = 0
                record.total_denda = 0
            record.status = 'dikembalikan'
            record.buku.jumlah_tersedia += 1

    @api.model
    def cek_peminjaman_terlambat(self):
        hari_ini = fields.Date.today()
        data_peminjaman = self.search([
            ('status', '=', 'dipinjam'),
            ('tanggal_jatuh_tempo', '<', hari_ini),
        ])
        for record in data_peminjaman:
            record.status = 'terlambat'

    denda_per_hari = fields.Integer(
        string='Denda Per Hari',
        default=1000
    )

    total_denda = fields.Integer(
        string='Total Denda',
        readonly=True,
        default=0
    )

