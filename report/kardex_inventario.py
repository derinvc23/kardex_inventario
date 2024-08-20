# -*- coding: utf-8 -*-

from openerp import models, fields, api, _, tools
import time


class KardexInventario(models.Model):
    _name = 'kardex.inventario'
    _description = "Kardex Inventario"
    _auto = False

    date = fields.Date(string='Fecha', readonly=True)
    product_id = fields.Many2one('product.product', string='Producto', readonly=True)
    picking = fields.Char(string='Albarán')
    origin = fields.Char(string='Doc. Origen')
    name_mov = fields.Char(string='Movimiento')
    origen = fields.Char(string='Origen')
    destino = fields.Char(string='Destino')
    lote = fields.Char(string='Lote')
    cantidad_salida = fields.Float(string='Salida')
    cantidad_entrada = fields.Float(string='Entrada')
    precio = fields.Float(string='Precio Unitario', groups="base.group_sale_manager")
    cantidad_en_fecha = fields.Float(string='Stock a la Fecha')
    valor_inventario_fecha = fields.Float(string='Valor Inventario Fecha', groups="base.group_sale_manager")

    def _select(self, cr, date_from='', date_to='', product_id='', location_id=''):
        sql_kardexvalorado = """
            select
              date,
              pp.id                           as product_id,
              --product_id,
              picking,
              CASE
              WHEN tipo_picking = 'incoming'
                THEN 'Proveedores'
              WHEN tipo_picking = 'outgoing'
                THEN 'Clientes'
              WHEN tipo_picking = 'internal'
                THEN 'Interno o Ajuste'
              ELSE 'Otros'
              END                                        AS tipo,
              lote,
              origin,
              --lot_id,
              name_mov,
              origen,
              destino,
              cantidad,
              CASE WHEN cantidad > 0
                THEN
                  cantidad
              ELSE
                0.0
              END                                        AS cantidad_entrada,
              --10
              CASE WHEN cantidad < 0
                THEN
                  cantidad * (-1)
              ELSE
                0.0
              END                                        AS cantidad_salida,
              price_unit                                 AS precio,
              (total_en_fecha + cantidad)                AS cantidad_en_fecha,
              (cantidad * price_unit)                    AS total_inventario,
              (total_en_fecha_valor + costo_total) AS valor_inventario_fecha
            FROM (
                   select
                     *,
                     lag(total_en_fecha)
                     OVER (
                       ORDER BY move_id, date, in_date) as valor_anterior,
                     lag(total_en_fecha_valor)
                     OVER (
                       ORDER BY move_id, date, in_date) as valor_anterior_valor
                   from (
                          select
                            *,
                            SUM(cantidad)
                            OVER (
                              PARTITION BY product_id
                              ORDER BY move_id, date, in_date) - cantidad AS total_en_fecha,
                            SUM(costo_total)
                            OVER (
                              PARTITION BY product_id
                              ORDER BY move_id, date, in_date) - (costo_total) AS total_en_fecha_valor
                          from (
                                 select
                                   (t0.date - '4 hr' :: interval) as date,
                                   t5.in_date,
                                   t0.id                          as move_id,
                                   t0.product_id,
                                   t4.product_tmpl_id,
                                   spt.code                       as tipo_picking,
                                   coalesce(spl.name, '')         as lote,
                                   coalesce(t3.name, '')          as picking,
                                   coalesce(t0.origin, '')        as origin,
                                   t0.name                        as name_mov,
                                   t1.complete_name               as origen,
                                   t2.complete_name               as destino,
                                   CASE
                                   WHEN t0.location_id != """ + str(location_id) + """ and t0.location_dest_id = """ + str(location_id) + """
                                     THEN t5.qty
                                   WHEN t0.location_id = """ + str(location_id) + """ and t0.location_dest_id != """ + str(location_id) + """
                                     THEN t5.qty * (-1)
                                   END                            AS cantidad,
                                   CASE
                                   WHEN t0.location_id != """ + str(location_id) + """ and t0.location_dest_id = """ + str(location_id) + """
                                     THEN t5.qty * t0.price_unit
                                   WHEN t0.location_id = """ + str(location_id) + """ and t0.location_dest_id != """ + str(location_id) + """
                                     THEN t5.qty * t0.price_unit * (-1)
                                   END                            AS costo_total,
                                   t0.price_unit
                                 from stock_move t0
                                   inner join stock_location t1 on t1.id = t0.location_id
                                   inner join stock_location t2 on t2.id = t0.location_dest_id
                                   left join stock_picking t3 on t3.id = t0.picking_id
                                   inner join product_product t4 on t4.id = t0.product_id
                                   inner join (SELECT
                                                 sm.id       AS move_id,
                                                 sq.lot_id,
                                                 sq.in_date,
                                                 sum(sq.qty) as qty
                                               FROM stock_move sm
                                                 INNER JOIN stock_quant_move_rel smr ON smr.move_id = sm.id
                                                 INNER JOIN stock_quant sq ON sq.id = smr.quant_id
                                                 where sq.qty > 0
                                               GROUP BY sm.id, sq.lot_id, sq.in_date
                                              ) t5 ON t5.move_id = t0.id
                                   LEFT JOIN stock_production_lot spl on spl.id = t5.lot_id
                                   LEFT JOIN stock_picking_type spt on spt.id = t0.picking_type_id
                                 where t0.product_id=""" + str(product_id) + """
                                        and (t0.location_id=""" + str(location_id) + """ or t0.location_dest_id = """ + str(location_id) + """)
                                       and t0.location_id != t0.location_dest_id
                                       and t0.state in ('done')
                                       order by t0.id, t0.date
                               ) as foo
                        ) as foo2
                 ) as foo3
              inner join product_product pp on pp.id = foo3.product_id
            order by foo3.move_id, foo3.date, foo3.in_date
        """
        return sql_kardexvalorado

    def init(self, cr, date_from=time.strftime("%Y-%m-%d"), date_to=time.strftime("%Y-%m-%d"), product_id=0,
             location_id=0):
        sql = """ DROP VIEW IF EXISTS poi_report_kardex_inv;
                  CREATE or REPLACE VIEW poi_report_kardex_inv as ((
                      SELECT row_number() over() as id, *
                        FROM ((
                            %s
                        )) as asd
              ))""" % (self._select(cr, date_from, date_to, product_id, location_id))
        cr.execute(sql)
