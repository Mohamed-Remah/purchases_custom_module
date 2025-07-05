from odoo import models,fields,api
from odoo.exceptions import ValidationError


class AssemblyOrder(models.Model):
    _name = 'custom.assembly.order'
    _description = 'Custom Assembly Order'


    name = fields.Char(default='New',readonly=True)
    product_ids = fields.Many2many('product.product' , string='Finished Products')
    quantities_str = fields.Char(string='Quantities (e.g 3-2-1)')
    location_id = fields.Many2one('stock.location' , string='Sub Inventory')
    component_line_ids = fields.One2many('custom.assembly.component.line','order_id',string='Required Component')

    @api.model
    def create(self,vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('custom_assembly_order_seq') or 'New'
        return super().create(vals)

    @api.onchange('product_ids', 'quantities_str', 'location_id')
    def _onchange_products_quantities(self):
        self.component_line_ids = False
        # لو الحقول دى فاضيه وقف المعالجه
        if not self.product_ids or not self.quantities_str:
            return

        # نحول من string الى list num مثلا من ("1-2-3") الر ["1","2","3"]
        quantities = [q.strip() for q in self.quantities_str.split('-') if q.strip().isdigit()]
        print(quantities)
        if len(quantities) != len(self.product_ids):
            raise ValidationError("عدد الكميات يجب أن يساوي عدد المنتجات المحددة!")

        # بنربت كل منتج بالكميه المقابله ليها ثم نحولها ال dictionaryt
        product_qty_map = dict(zip(self.product_ids, map(float, quantities)))
        print(product_qty_map)
        component_map = {}
        # بنلف على كل منتج + كميته
        for product, qty in product_qty_map.items():
            #BOM وصفة التصنيع (المكونات)
            # bom = self.env['mrp.bom']._bom_find(product=product)
            # bom =bom_data.get('bom') if isinstance(bom_data, dict) else bom_data
            bom = self.env['mrp.bom'].search([('product_tmpl_id', '=' ,product.product_tmpl_id.id),('type' , '=' , 'normal')],limit=1)
            if not bom:
                continue
            # حساب المكونات المطلوبه لهذا المنتج مع الكميه المحدده
            bom_lines = bom.explode(product, qty)[0]

            for line, line_data in bom_lines:
                prod = line.product_id
                req_qty = line.product_qty * line_data['qty'] / bom.product_qty

                if prod.id in component_map:
                    component_map[prod.id]['required_qty'] += req_qty
                else:
                    component_map[prod.id] = {
                        'product_id': prod.id,
                        'required_qty': req_qty,
                    }

        lines = []
        for comp in component_map.values():
            prod = self.env['product.product'].browse(comp['product_id'])
            available_qty = prod.with_context(location=self.location_id.id).qty_available
            missing = max(0.0, comp['required_qty'] - available_qty)
            purchase_cost = missing * prod.standard_price
            lines.append((0, 0, {
                'product_id': prod.id,
                'required_qty': comp['required_qty'],
                'available_qty': available_qty,
                'missing_qty': missing,
                'purchase_cost': purchase_cost
            }))

        self.component_line_ids = lines
        print(lines)

    # def print_report(self):
    #     pass



class MrpKitLine(models.Model):
    _name = 'custom.assembly.component.line'
    _description = 'component line for Assembly order'

    order_id = fields.Many2one('custom.assembly.order',string='Kit Order')
    product_id = fields.Many2one('product.product', string='component')
    required_qty = fields.Float(string='Required Quantity')
    available_qty = fields.Float(string='Available in Sub-Inventory')
    missing_qty = fields.Float(string='Missing Quantity')
    purchase_cost = fields.Float(string='Estimated purchase Cost')
