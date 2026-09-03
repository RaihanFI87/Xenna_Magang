from odoo import models, fields


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    loan_penalty_amount = fields.Float(
        string='Nominal Denda Kehilangan',
        help='Nominal denda dasar per unit apabila produk ini '
             'dinyatakan hilang saat dipinjam.'
    )