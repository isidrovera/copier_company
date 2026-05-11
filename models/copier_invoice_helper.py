# -*- coding: utf-8 -*-

import logging
from odoo import models

_logger = logging.getLogger(__name__)


class CopierInvoiceHelper(models.AbstractModel):
    _name = 'copier.invoice.helper'
    _description = 'Helper de Facturación Copier'

    def _apply_detraccion_if_needed(
        self,
        invoice,
        aplicar=True,
        monto_minimo=700.00,
        operation_type='1001'
    ):
        if not invoice:
            return False

        if not aplicar:
            return False

        invoice._compute_amount()

        amount_total = invoice.amount_total or 0.0

        _logger.info(
            '[DETRACCION] Evaluando factura ID %s | Total: %s | Mínimo: %s',
            invoice.id,
            amount_total,
            monto_minimo
        )

        if amount_total >= monto_minimo:
            if 'l10n_pe_edi_operation_type' in invoice._fields:
                invoice.write({
                    'l10n_pe_edi_operation_type': operation_type or '1001'
                })
                _logger.info(
                    '[DETRACCION] Aplicada operación %s a factura ID %s',
                    operation_type,
                    invoice.id
                )
                return True

            _logger.warning(
                '[DETRACCION] El campo l10n_pe_edi_operation_type no existe en account.move.'
            )

        return False