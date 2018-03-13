# –*– coding: utf–8 –*–
from odoo import models,api,fields

class product_demo(models.Model):
    _inherit = 'product.template'

    drag_image_ids = fields.Many2many('ir.attachment')

class widget_data(models.Model):
    _inherit = 'ir.attachment'

    extension = fields.Char()
    sortable = fields.Integer()

    dec_edoc_type = fields.Selection(string=u"随附单据类型",
                                         selection=[('00000001', u'发票'), ('00000002', u'装箱单'), ('00000003', u'提运单'), ('00000004', u'合同'), ('00000005', u'其他'), ('10000001', u'代理委托协议'), ('10000002', u'减免税货物税款担保证明'), ('10000003', u'减免税货物税款担保延期证明')]
                                         ,required=False)

    @api.model
    def upload_dragndrop(self, name, base64, extension, sortable):
        Model = self
        try:
            attachment_id = Model.create({
                'name': name,
                'datas': base64,
                'extension': extension,
                'datas_fname': name,
                'res_model': Model._name,
                'description': '',
                'sortable': sortable,
                'res_id': 0
            })
            args = {
                'filename': name,
                'id':  attachment_id
            }
        except Exception:
            args = {'error': "Something horrible happened"}
        # return out % (simplejson.dumps(callback), simplejson.dumps(args))
        return attachment_id.id

    @api.model
    def attachment_update_description(self, id, description):
        attachment_id = self.env['ir.attachment'].search([('id', '=', int(id))])[0]
        attachment_id.description = description

    @api.model
    def attachment_update_dec_edoc_type(self, id, dec_edoc_type):
        attachment_id = self.env['ir.attachment'].search([('id', '=', int(id))])[0]
        attachment_id.dec_edoc_type=dec_edoc_type

    @api.model
    def update_sort_attachment(self, attachments_ids):
        attachments = self.env['ir.attachment'].search([('id', 'in', attachments_ids)])
        for attach in attachments:
            #cambio il campo sortable
            sort_number = attachments_ids.index(str(attach.id))
            attach.sortable = sort_number


class widget_ir_config_parameter(models.Model):
    _inherit = 'ir.config_parameter'

    @api.model
    def get_base_url(self):
        base_url = ""
        config_parameter_ids = self.env['ir.config_parameter'].search([('key', '=', 'web.base.url')])[0]
        if config_parameter_ids.value:
            base_url = config_parameter_ids.value
        return base_url

widget_data()
widget_ir_config_parameter()