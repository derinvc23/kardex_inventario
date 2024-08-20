# -*- coding: utf-8 -*-
from odoo import tools
from odoo import api, fields, models


class DetalleVentas(models.Model):
    _name = "detalle.ventas"
    _description = "Detalle Ventas"
    _auto = False
    journal_id = fields.Many2one('account.journal', string=u"Diario", readonly=True)
    trans = fields.Char(string=u"Transacción", readonly=True)
    number = fields.Char(string=u"N° DOC.", readonly=True)
    clie = fields.Char(string=u"Cliente", readonly=True)
    nombre = fields.Char(string=u'Nombre', readonly=True)
    nit = fields.Char(string=u"N.I.T.", readonly=True)
    amount_total = fields.Float(string=u"Bruto", readonly=True)
    amount_discount = fields.Float(string=u"Descuento", readonly=True)
    neto = fields.Float(string=u"Neto", readonly=True)
    amount_total_bs = fields.Float(string=u"Bruto Bs.", readonly=True)
    amount_discount_bs = fields.Float(string=u"Descuento Bs.", readonly=True)
    neto_bs = fields.Float(string=u"Neto Bs.", readonly=True)
    estado = fields.Char(string=u'Estado')
    date_invoice = fields.Date(string='Fecha')
    warehouse_id = fields.Many2one('stock.warehouse', string='Sucursal')

    @api.model
    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
        if self._name == 'detalle.ventas' and not domain:
            self.env.cr.execute("REFRESH MATERIALIZED VIEW detalle_ventas;")
        return super(DetalleVentas, self).search_read(domain=domain, fields=fields, offset=offset, limit=limit,
                                                      order=order)

    @api.model_cr
    def init(self):
        curr_bob = self.env['res.currency'].search([('name', '=', 'BOB')])
        rate = curr_bob.rate
        self.env.cr.execute("""
                DROP MATERIALIZED VIEW IF EXISTS detalle_ventas;
                CREATE MATERIALIZED VIEW detalle_ventas as (
                select ai.id,
                       ai.journal_id,
                       so.name                                       as trans,
                       ai.date_invoice,
                       ai.number,
                       rp.id                                         as clie,
                       rp.name                                       as nombre,
                       ai.nit,
                       ai.amount_total,
                       ai.amount_discount,
                       (ai.amount_total - ai.amount_discount)        as neto,
                       ai.amount_total * """+str(rate)+"""                        as amount_total_bs,
                       ai.amount_discount * """+str(rate)+"""                     as amount_discount_bs,
                       (ai.amount_total - ai.amount_discount) * * """+str(rate)+"""  as neto_bs,
                       so.warehouse_id,
                       CASE WHEN ai.state = 'cancel' THEN
                        'Cancelado'
                       WHEN ai.state = 'open' THEN
                        'Abierto'
                       WHEN ai.state = 'paid' THEN
                        'Pagado'
                       WHEN ai.state = 'draft' THEN
                        'Borrador'
                       ELSE
                        'Pro-forma'
                       END as estado
                from account_invoice ai
                         inner join res_partner rp on rp.id = ai.partner_id
                         left join sale_order so on so.name = ai.origin
                where ai.type in ('out_invoice', 'out_refund')
                order by ai.date_invoice desc
                )""")
