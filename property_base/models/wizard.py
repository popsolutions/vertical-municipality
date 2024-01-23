# Copyright 2021 - TODAY, Marcel Savegnago <marcel.savegnago@gmail.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models, api
import logging

logger = logging.getLogger(__name__)

class PropertyInvoiceWizard(models.TransientModel):

    _name = 'property.invoice.wizard'
    _description = 'Property Invoice Wizard'

    def process_batch_invoices(self):
        # 1. Criar Faturas em Lote - Processamento mensal que cria todas as faturas

        logger.info('## process_batch_invoices - Criar Faturas em Lote - Processamento mensal que cria todas as faturas')

        """
        Basicamente será chamado a rotina /riviera/vertical-municipality/property_base/models/invoice.py.process_property_invoice
          para os modelos:

          -property_tax.product_property_tax                             - CTM - Contribuiao mensal
          -property_ga_maintenance.property_ga_maintenance               - Manutenção de área verde
          -property_water_consumption.product_property_water_consumption - Agua e esgoto
          -property_water_catchment.product_property_water_catchment     - Taxa de captação
        """

        self.env['account.invoice']._cron_process_municipality_services()
        self.env.cr.commit()

        logger.info('## [CONCLUÍDO] process_batch_invoices - Criar Faturas em Lote - Processamento mensal que cria todas as faturas')


class property_invoice_wizard_processar_faturas_acumuladas(models.TransientModel):
    _name = 'property.invoice.wizard.processar_faturas_acumuladas'
    _description = 'Processar Faturas Acumuladas'
    def button_processar_faturas_acumuladas(self):
        # 2. Processar os boletos atrasados (acumulados) nas novas faturas geradas para o ano/mês de processamento(vw_property_settings_monthly_last.year_month)
        logger.info('## button_processar_faturas_acumuladas - Processar os boletos atrasados (acumulados) nas novas faturas geradas')
        self.env['account.invoice'].invoice_accumulated__all_monthly_last()
        self.env.cr.commit()
        logger.info('## [CONCLUÍDO] button_processar_faturas_acumuladas - Processar os boletos atrasados (acumulados) nas novas faturas geradas')

class PropertyWaterConsumptionWizardOldInvoicesFees(models.TransientModel):
    _name = 'property.water.consumption.wizard.old.invoices.fees'
    _description = 'Process fees on Old Invoices'
    def process_old_invoices_fees(self):
        self.env['account.invoice'].process_old_invoices_fees()