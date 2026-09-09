from odoo import http
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.exceptions import AccessError, MissingError, ValidationError
from odoo.http import request


class EquipmentLoanPortal(CustomerPortal):

    def _get_portal_my_home_counters(self):
        counters = super()._get_portal_my_home_counters()
        counters.append('loan_count')
        return counters

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        if 'loan_count' in counters:
            values['loan_count'] = request.env['equipment.loan'].search_count([])
        return values

    @http.route(
        ['/my/equipment-loans'],
        type='http',
        auth='user',
        website=True
    )
    def portal_my_loans(self, **kw):
        loans = request.env['equipment.loan'].search([])

        return request.render(
            'equipment_loan_tracker.portal_my_loans',
            {'loans': loans}
        )

    @http.route(
        ['/my/equipment-loans/<int:loan_id>'],
        type='http',
        auth='user',
        website=True
    )
    def portal_loan_detail(self, loan_id, access_token=None, **kw):
        try:
            loan_sudo = self._document_check_access(
                'equipment.loan', loan_id, access_token=access_token
            )
        except (AccessError, MissingError):
            return request.redirect('/my')

        return request.render(
            'equipment_loan_tracker.portal_loan_detail',
            {'loan': loan_sudo}
        )

    def _get_available_lots(self):
        source_location = request.env.ref('stock.stock_location_stock')

        lots = request.env['stock.lot'].search([])
        available = request.env['stock.lot']

        for lot in lots:
            qty = request.env['stock.quant']._get_available_quantity(
                lot.product_id,
                source_location,
                lot_id=lot,
                strict=True
            )
            if qty >= 1:
                available |= lot

        return available

    @http.route(
        ['/my/equipment-loans/new'],
        type='http',
        auth='user',
        website=True,
        methods=['GET']
    )
    def portal_new_loan_form(self, **kw):
        available_lots = self._get_available_lots()

        return request.render(
            'equipment_loan_tracker.portal_new_loan',
            {
                'available_lots': available_lots,
                'error': kw.get('error'),
            }
        )

    @http.route(
        ['/my/equipment-loans/new'],
        type='http',
        auth='user',
        website=True,
        methods=['POST'],
        csrf=True
    )
    def portal_new_loan_submit(self, **post):
        lot_ids = [int(i) for i in request.httprequest.form.getlist('lot_ids')]
        loan_date = post.get('loan_date')
        due_date = post.get('due_date')

        if not lot_ids:
            return request.redirect(
                '/my/equipment-loans/new?error=Pilih minimal satu alat.'
            )

        if not loan_date or not due_date:
            return request.redirect(
                '/my/equipment-loans/new?error=Tanggal wajib diisi.'
            )

        lots = request.env['stock.lot'].browse(lot_ids)

        try:
            loan = request.env['equipment.loan'].create({
                'borrower_id': request.env.user.partner_id.id,
                'loan_date': loan_date,
                'due_date': due_date,
                'loan_line_ids': [
                    (0, 0, {
                        'equipment_id': lot.product_id.id,
                        'lot_id': lot.id,
                    })
                    for lot in lots
                ],
            })
        except ValidationError as e:
            return request.redirect(
                f'/my/equipment-loans/new?error={e.args[0]}'
            )

        return request.redirect(f'/my/equipment-loans/{loan.id}')

    @http.route(
        ['/my/equipment-loans/<int:loan_id>/extend'],
        type='http',
        auth='user',
        website=True,
        methods=['GET']
    )
    def portal_extend_form(self, loan_id, access_token=None, **kw):
        try:
            loan_sudo = self._document_check_access(
                'equipment.loan', loan_id, access_token=access_token
            )
        except (AccessError, MissingError):
            return request.redirect('/my')

        if loan_sudo.state not in ('ongoing', 'late'):
            return request.redirect(f'/my/equipment-loans/{loan_id}')

        return request.render(
            'equipment_loan_tracker.portal_extend_request',
            {
                'loan': loan_sudo,
                'error': kw.get('error'),
            }
        )

    @http.route(
        ['/my/equipment-loans/<int:loan_id>/extend'],
        type='http',
        auth='user',
        website=True,
        methods=['POST'],
        csrf=True
    )
    def portal_extend_submit(self, loan_id, access_token=None, **post):
        try:
            loan_sudo = self._document_check_access(
                'equipment.loan', loan_id, access_token=access_token
            )
        except (AccessError, MissingError):
            return request.redirect('/my')

        requested_due_date = post.get('requested_due_date')
        reason = post.get('reason')

        if not requested_due_date:
            return request.redirect(
                f'/my/equipment-loans/{loan_id}/extend'
                '?error=Tanggal baru wajib diisi.'
            )

        try:
            request.env['equipment.loan.extension.request'].create({
                'loan_id': loan_sudo.id,
                'requested_due_date': requested_due_date,
                'reason': reason,
            })
        except ValidationError as e:
            return request.redirect(
                f'/my/equipment-loans/{loan_id}/extend?error={e.args[0]}'
            )

        return request.redirect(f'/my/equipment-loans/{loan_id}')