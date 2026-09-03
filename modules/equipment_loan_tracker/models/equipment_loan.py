from odoo import models, fields, api
from odoo.exceptions import ValidationError


class EquipmentLoan(models.Model):
    _name = 'equipment.loan'
    _description = 'Equipment Loan'
    _order = 'loan_date desc, id desc'

    name = fields.Char(
        string='Nomor Peminjaman',
        required=True,
        readonly=True,
        copy=False,
        default='New'
    )

    borrower_id = fields.Many2one(
        'res.partner',
        string='Peminjam',
        required=True,
        ondelete='restrict'
    )

    type = fields.Selection(
        selection=[
            ('internal', 'Internal Staff'),
            ('external', 'Eksternal'),
        ],
        string='Tipe',
    )

    loan_line_ids = fields.One2many(
        'equipment.loan.line',
        'loan_id',
        string='Daftar Alat'
    )

    borrower_email = fields.Char(
        string='Email',
        related='borrower_id.email',
        readonly=True
    )

    borrower_phone = fields.Char(
        string='Phone',
        related='borrower_id.phone',
        readonly=True
    )

    loan_duration = fields.Integer(
        string='Durasi Peminjaman (Hari)',
        compute='_compute_loan_duration'
    )

    loan_date = fields.Date(
        string='Tanggal Peminjaman',
        required=True,
        default=fields.Date.context_today
    )

    due_date = fields.Date(
        string='Tanggal Jatuh Tempo',
        required=True
    )

    return_date = fields.Date(
        string='Tanggal Pengembalian'
    )

    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('ongoing', 'Ongoing'),
            ('returned', 'Returned'),
            ('late', 'Late'),
            ('lost', 'Lost'),
        ],
        string='Status',
        default='draft',
        required=True
    )

    line_notes = fields.Text(
        string='Catatan'
    )

    equipment_names = fields.Char(
        string='Daftar Alat',
        compute='_compute_equipment_names'
    )

    outgoing_picking_id = fields.Many2one(
        'stock.picking',
        string='Picking Keluar',
        readonly=True,
        copy=False
    )

    return_picking_id = fields.Many2one(
        'stock.picking',
        string='Picking Kembali',
        readonly=True,
        copy=False
    )

    penalty_invoice_id = fields.Many2one(
        'account.move',
        string='Invoice Denda',
        readonly=True,
        copy=False
    )

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'equipment.loan'
                ) or 'New'

        return super().create(vals_list)

    @api.constrains('loan_date', 'due_date')
    def _check_due_date(self):
        for record in self:
            if record.loan_date and record.due_date:
                if record.due_date < record.loan_date:
                    raise ValidationError(
                        'Tanggal jatuh tempo tidak boleh lebih awal '
                        'dari tanggal peminjaman.'
                    )

    @api.constrains('return_date', 'loan_date')
    def _check_return_date(self):
        for record in self:
            if record.return_date and record.loan_date:
                if record.return_date < record.loan_date:
                    raise ValidationError(
                        'Tanggal pengembalian tidak boleh lebih awal '
                        'dari tanggal peminjaman.'
                    )

    @api.constrains('loan_line_ids', 'state')
    def _check_double_booking(self):
        for record in self:
            if record.state not in ('ongoing', 'late'):
                continue

            for line in record.loan_line_ids:
                existing_lines = self.env['equipment.loan.line'].search([
                    ('id', '!=', line.id),
                    ('equipment_id', '=', line.equipment_id.id),
                    ('loan_id.state', 'in', ('ongoing', 'late')),
                ], limit=1)

                if existing_lines:
                    raise ValidationError(
                        f'Alat "{line.equipment_id.name}" sedang dipinjam '
                        'dan tidak dapat dipinjam kembali.'
                    )

    def _get_loan_location(self):
        return self.env.ref('equipment_loan_tracker.stock_location_loan')

    def _get_source_location(self):
        return self.env.ref('stock.stock_location_stock')

    def action_confirm(self):
        for record in self:

            if not record.loan_line_ids:
                raise ValidationError(
                    'Minimal harus ada satu alat yang dipinjam.'
                )

            if record.due_date < record.loan_date:
                raise ValidationError(
                    'Tanggal jatuh tempo tidak boleh lebih awal '
                    'dari tanggal peminjaman.'
                )

            source_location = record._get_source_location()
            loan_location = record._get_loan_location()

            for line in record.loan_line_ids:
                qty_available = line.equipment_id.with_context(
                    location=source_location.id
                ).qty_available

                if qty_available < 1:
                    raise ValidationError(
                        f'Alat "{line.equipment_id.name}" tidak tersedia '
                        'di lokasi stok dan tidak dapat dipinjam.'
                    )

            picking_type = self.env.ref(
                'equipment_loan_tracker.stock_picking_type_loan_out'
            )

            picking = self.env['stock.picking'].create({
                'picking_type_id': picking_type.id,
                'location_id': source_location.id,
                'location_dest_id': loan_location.id,
                'partner_id': record.borrower_id.id,
                'origin': record.name,
                'move_ids': [
                    (0, 0, {
                        'name': line.equipment_id.name,
                        'product_id': line.equipment_id.id,
                        'product_uom_qty': 1.0,
                        'product_uom': line.equipment_id.uom_id.id,
                        'location_id': source_location.id,
                        'location_dest_id': loan_location.id,
                    })
                    for line in record.loan_line_ids
                ],
            })

            picking.action_confirm()
            picking.action_assign()

            for move in picking.move_ids:
                move.quantity = move.product_uom_qty
                move.picked = True

            picking.button_validate()

            record.write({
                'state': 'ongoing',
                'outgoing_picking_id': picking.id,
            })

    def action_return(self):
        for record in self:

            if record.state not in ('ongoing', 'late'):
                raise ValidationError(
                    'Hanya peminjaman yang sedang berlangsung '
                    'atau terlambat yang dapat dikembalikan.'
                )

            source_location = record._get_source_location()
            loan_location = record._get_loan_location()

            picking_type = self.env.ref(
                'equipment_loan_tracker.stock_picking_type_loan_return'
            )

            picking = self.env['stock.picking'].create({
                'picking_type_id': picking_type.id,
                'location_id': loan_location.id,
                'location_dest_id': source_location.id,
                'partner_id': record.borrower_id.id,
                'origin': record.name,
                'move_ids': [
                    (0, 0, {
                        'name': line.equipment_id.name,
                        'product_id': line.equipment_id.id,
                        'product_uom_qty': 1.0,
                        'product_uom': line.equipment_id.uom_id.id,
                        'location_id': loan_location.id,
                        'location_dest_id': source_location.id,
                    })
                    for line in record.loan_line_ids
                ],
            })

            picking.action_confirm()
            picking.action_assign()

            for move in picking.move_ids:
                move.quantity = move.product_uom_qty
                move.picked = True

            picking.button_validate()

            today = fields.Date.context_today(self)

            if today > record.due_date:
                new_state = 'late'
                note = (
                    'Peminjaman dikembalikan setelah '
                    'tanggal jatuh tempo.'
                )
            else:
                new_state = 'returned'
                note = False

            record.write({
                'state': new_state,
                'return_date': today,
                'return_picking_id': picking.id,
                'line_notes': note,
            })

    def action_lost(self):
        for record in self:

            if record.state not in ('ongoing', 'late'):
                raise ValidationError(
                    'Hanya peminjaman yang sedang berlangsung '
                    'atau terlambat yang dapat dinyatakan hilang.'
                )

            lost_lines = record.loan_line_ids.filtered('is_lost')

            if not lost_lines:
                raise ValidationError(
                    'Tandai minimal satu alat sebagai "Hilang" '
                    'sebelum menandai peminjaman ini hilang.'
                )

            invoice_line_vals = []
            for line in lost_lines:
                penalty = line.equipment_id.loan_penalty_amount
                invoice_line_vals.append((0, 0, {
                    'product_id': line.equipment_id.id,
                    'quantity': 1,
                    'price_unit': penalty,
                    'name': f'Denda kehilangan alat: {line.equipment_id.name}',
                }))

            invoice = self.env['account.move'].create({
                'move_type': 'out_invoice',
                'partner_id': record.borrower_id.id,
                'invoice_origin': record.name,
                'invoice_line_ids': invoice_line_vals,
            })

            invoice.action_post()

            record.write({
                'state': 'lost',
                'penalty_invoice_id': invoice.id,
            })

    @api.model
    def _cron_check_overdue(self):
        today = fields.Date.context_today(self)

        loans = self.search([
            ('state', '=', 'ongoing'),
            ('due_date', '<', today),
        ])

        if loans:
            loans.write({
                'state': 'late',
                'line_notes': 'kamu sudah terlambat'
            })

    @api.depends('loan_date', 'return_date')
    def _compute_loan_duration(self):
        today = fields.Date.context_today(self)

        for record in self:
            if not record.loan_date:
                record.loan_duration = 0
                continue

            end_date = record.return_date or today
            duration = (end_date - record.loan_date).days

            record.loan_duration = max(duration, 0)

    @api.depends('loan_line_ids.equipment_id')
    def _compute_equipment_names(self):
        for record in self:
            record.equipment_names = ', '.join(
                record.loan_line_ids.mapped('equipment_id.name')
            )


class EquipmentLoanLine(models.Model):
    _name = 'equipment.loan.line'
    _description = 'Equipment Loan Line'

    loan_id = fields.Many2one(
        'equipment.loan',
        string='Peminjaman',
        required=True,
        ondelete='cascade'
    )

    equipment_id = fields.Many2one(
        'product.product',
        string='Alat',
        required=True,
        ondelete='restrict'
    )

    is_lost = fields.Boolean(
        string='Hilang',
        default=False
    )