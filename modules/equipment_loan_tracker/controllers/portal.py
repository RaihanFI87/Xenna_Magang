from odoo import http
from odoo.addons.portal.controllers.portal import CustomerPortal
from odoo.exceptions import AccessError, MissingError
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