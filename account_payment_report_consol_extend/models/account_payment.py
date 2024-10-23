# Copyright 2019 Open Source Integrators
# <https://www.opensourceintegrators.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, models, fields, _
from odoo.exceptions import UserError, ValidationError
import time 
import logging
_logger = logging.getLogger(__name__)


class AccountAccountLines(models.Model):
    _inherit = "account.account_lines"
    _name = "account.account_lines"

    # move_id           = fields.Many2one('account.move', string='Póliza', readonly=True)

    payment_reference = fields.Char('Referencia del Pago', size=256, related="move_id.payment_reference")
