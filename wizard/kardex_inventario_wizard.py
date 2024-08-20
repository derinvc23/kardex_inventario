# -*- coding: utf-8 -*-
import time
from odoo import models, fields, api, _, tools
from datetime import datetime


class KardexInventarioWizard(models.TransientModel):
    _name = "kardex.inventario.wizard"
    _description = "Kardex Inventario"

    product_ids = fields.Many2many('product.product', string='Productos', required=True)
    location_ids = fields.Many2many('stock.location', string=u'Ubicaciónes', required=True)
    date_from = fields.Date(string='Desde:', size=64, required=True, default=lambda *a: time.strftime('%Y-%m-%d'))
    date_to = fields.Date(string='Hasta', size=64, required=True, default=lambda *a: time.strftime('%Y-%m-%d'))
    company_id = fields.Many2one('res.company', string=u'Compañia',
                                 default=lambda self: self.env.user.company_id)


    @api.multi
    def open_table(self):
        context = self._context
        datas = {'ids': context.get('active_ids', [])}
        datas['model'] = 'kardex.inventario.wizard'
        datas['form'] = self.read()[0]
        for field in datas['form'].keys():
            if isinstance(datas['form'][field], tuple):
                datas['form'][field] = datas['form'][field][0]
        return {'type': 'ir.actions.report.xml',
                'report_name': 'kardex_inventario.kardex_xlsx.xlsx',
                'datas': datas,
                'name': 'Kardex Inventario'
                }
