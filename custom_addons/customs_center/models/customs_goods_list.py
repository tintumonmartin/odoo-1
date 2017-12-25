# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
import logging
from collections import OrderedDict
_logger = logging.getLogger(__name__)


class CusGoodsList(models.Model):
    """ 通关清单-商品列表 """
    _name = 'customs_center.cus_goods_list'
    # rec_name = 'goods_name'
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    _description = 'Customs cus Goods List'

    goods_name = fields.Char(string="goods name")  # 商品名称
    # 关联通关清单 多对一
    customs_order_id = fields.Many2one(comodel_name="customs_center.customs_order", string="customs Order", copy=False)
    # 关联报关单 多对一
    customs_declaration_id = fields.Many2one(comodel_name="customs_center.customs_dec", string="customs declaration", copy=False)

    cus_goods_tariff_id = fields.Many2one(comodel_name="basedata.cus_goods_tariff", string="cus goods Code TS", required=False, )  # 海关税则编码

    # 关联商品归类信息
    goods_classification_id = fields.Many2one(comodel_name="customs_center.goods_classify", string="Goods Classification", required=False,)  # 客户料号

    goods_model = fields.Char(string="goods model", required=False, )  # 规格型号

    deal_qty = fields.Integer(string="deal quantity", required=False, default=1)  # 成交数量
    deal_unit_price = fields.Monetary(string="deal unit price", )    # 成交单价/申报单价
    deal_unit = fields.Many2one(comodel_name="basedata.cus_unit", string="deal unit", required=False, )    # 成交单位
    deal_total_price = fields.Monetary(string="deal total price", )  # 成交总价/申报单价
    currency_id = fields.Many2one(comodel_name="basedata.cus_currency", string="currency id", required=False, )  # 币制
    first_qty = fields.Integer(string="first quantity", required=False,)  # 第一法定数量
    first_unit = fields.Many2one(comodel_name="basedata.cus_unit", string="First Unit", )  # 第一计量单位

    second_qty = fields.Integer(string="second quantity",)  # 第二法定数量
    second_unit = fields.Many2one(comodel_name="basedata.cus_unit", string="second Unit", )  # 第二计量单位
    origin_country_id = fields.Many2one(comodel_name="delegate_country", string="origin country", )  # 原产国
    destination_country_id = fields.Many2one(comodel_name="delegate_country", string="destination country", )  # 目的国
    duty_mode_id = fields.Many2one(comodel_name="basedata.cus_duty_mode", string="Duty Mode", )  # 征免方式
    ManualSN = fields.Char(string="Manual SN")  # 备案序号

    # # 是否属于报关单 已在视图层面action过滤 暂不需要该字段
    # customs_dec_goods_own = fields.Selection(selection=[('yes', 'YES'),    # 是否属于报关单
    #                                     ('no', 'NO')
    #                                     ], string='archive status', readonly=True, default='no')
    # @api.onchange('customs_declaration_id')
    # def _change_customs_dec_own(self):
    #     """ 为了区分通关清单和报关单共用一张表 """
    #     for goods_list in self:
    #         if goods_list.customs_declaration_id:
    #             goods_list.customs_dec_goods_own = 'yes'

    # 是否归类
    classify_status = fields.Selection(selection=[('yes', 'YES'),    # 商品是否归类
                                        ('no', 'NO')  # 未归类
                                        ], string='archive status', readonly=True, default='no')


    @api.onchange('cus_goods_tariff_id')
    def _generate_about_name(self):
        """根据当前海关税则编码的变化 改变商品名称 并通过onchange装饰器，自动执行_generate_about_name方法"""
        for goods_list in self:
            if goods_list.cus_goods_tariff_id:
                goods_list.goods_name = goods_list.cus_goods_tariff_id.NameCN


    @api.multi
    def goods_classified_btn(self):
        """ 将历史申报商品 归类按钮 """
        for line in self:
            print(line.currency_id.id)
            print(line.line.destination_country_id.id)
            return {
                'name': "customs center goods classified",
                'type': "ir.actions.act_window",
                'view_type': 'form',
                'view_mode': 'form, tree',
                'res_model': 'customs_center.goods_classify',
                'views': [[False, 'form']],
                'context': {
                    'default_cus_goods_tariff_id': line.cus_goods_tariff_id.id,
                    'default_goods_model': line.goods_model, # 规格型号
                    'default_business_company_id': line.customs_declaration_id.business_company_id.id,  # 经营单位
                    'default_origin_country_id': line.origin_country_id.id,  # 原产国
                    'default_destination_country_id': line.destination_country_id.id,  # 目的国
                    'default_goods_name': line.goods_name,  # 商品名称
                    'default_first_unit': line.first_unit.id,  # 第一计量单位
                    'default_second_unit': line.second_unit.id,  # 第二计量单位
                    'default_deal_unit_price': line.deal_unit.id,  # 成交单位
                    'default_currency_id': line.currency_id.id,  # 币制
                    # 'default_supervision_condition': line.inout,  # 监管条件
                    'default_duty_mode_id':line.duty_mode_id.id,  # 征免方式
                    'default_ManualNo': line.customs_declaration_id.ManualNo,  # 备案号
                    'default_ManualSN': line.ManualSN,  # 备案序号
                },
                'target': 'current'
            }


        # for line in self:
        #     dic = {
        #         'cus_goods_tariff_id': line.inout, # 商品编号
        #         'goods_model': line.inout, # 规格型号
        #         'business_company_id': line.business_company_id.id,  # 经营单位
        #         'origin_country_id': line.inout,  # 原产国
        #         'destination_country_id': line.inout,  # 目的国
        #         'goods_name': line.inout,  # 商品名称
        #         'first_unit': line.inout,  # 第一计量单位
        #         'second_unit': line.inout,  # 第二计量单位
        #         'deal_unit_price': line.inout,  # 成交单价
        #         'currency_id': line.inout,  # 币制
        #         'supervision_condition': line.inout,  # 监管条件
        #         'duty_mode_id': line.inout,  # 征免方式
        #         'ManualNo': line.ManualNo,  # 备案号
        #         'ManualSN': line.inout,  # 备案序号
        #     }
        #     print(line.cus_goods_list_ids)
        #     print(line.cus_goods_list_ids.ids)
        #     print(self.env['customs_center.cus_goods_list'].customs_order_id.ids)
        #     # customs_center.cus_goods_list(1, 2)
        #     # [1, 2]
        #     # []
        #
        #     dic = {item: dic[item] for item in dic if dic[item]}
        #     dic.update(dic)
        #
        #     customs_declaration_obj = self.env['customs_center.customs_dec'].create(dic)
        #
        #     # 获取当前对象下的报关单ID
        #     # customs_order_obj = self.env['customs_center.customs_order']
        #     # print(customs_order_obj)
        #     # customs_clearance_obj = customs_order_obj.customs_declaration_ids
        #     print(customs_declaration_obj)
        #     return {
        #         'name': "Customs Center Clearance",
        #         'type': "ir.actions.act_window",
        #         'view_type': 'form',
        #         'view_mode': 'form, tree',
        #         'res_model': 'customs_center.customs_dec',
        #         'views': [[False, 'form']],
        #         'res_id': customs_declaration_obj.id,
        #         # 'target': 'current'
        #         'target': 'main'
        #     }




    # @api.model
    # def create(self, values):
    #     self.product_id_change()
    #         # for field in onchange_fields:
    #         #     if field not in values:
    #         #         values[field] = line._fields[field].convert_to_write(line[field], line)
    #     line = super(CusGoodsList, self).create(values)
    #     return line
    #
    # @api.multi
    # @api.onchange('cus_goods_tariff_id')
    # def product_id_change(self):
    #     if not self.cus_goods_tariff_id:
    #         return {'domain': {'goods_name': []}}
    #
    #     for goods_list in self:
    #         if goods_list.cus_goods_tariff_id:
    #             goods_list.goods_name = goods_list.cus_goods_tariff_id.NameCN
    #             return goods_list.goods_name
    #             # return {'domain': {'goods_name': goods_list.cus_goods_tariff_id.NameCN}}




# class DecGoodsList(models.Model):
#     """ 报关单-商品列表 """
#     _name = 'customs_center.dec_goods_list'
#     # rec_name = 'goods_name'
#     _inherit = ['mail.thread', 'ir.needaction_mixin']
#     _description = 'Customs dec Goods List'
#
#     # goods_name = fields.Char(string="goods name", required=False, )  # 商品名称
#     # 关联报关单 多对一
#     customs_declaration_id = fields.Many2one(comodel_name="customs_center.customs_dec",
#                                        string="customs declaration")
#     cus_goods_tariff_id = fields.Many2one(comodel_name="basedata.cus_goods_tariff", string="cus goods Code TS", required=False, )  # 海关税则编码
#     goods_model = fields.Char(string="goods model", required=False, )  # 规格型号
#
#     deal_qty = fields.Integer(string="deal quantity", required=False, default=1)  # 成交数量
#     deal_unit_price = fields.Monetary(string="deal unit price", )    # 成交单价/申报单价
#     deal_unit = fields.Many2one(comodel_name="basedata.cus_unit", string="deal unit", required=False, )    # 成交单位
#     deal_total_price = fields.Monetary(string="deal total price", )  # 成交总价/申报单价
#     currency_id = fields.Many2one(comodel_name="basedata.cus_currency", string="currency id", required=False, )  # 币制
#     first_qty = fields.Integer(string="first quantity", required=False,)  # 第一法定数量
#     first_unit = fields.Many2one(comodel_name="basedata.cus_unit", string="First Unit", )  # 第一计量单位
#
#     second_qty = fields.Integer(string="second quantity",)  # 第二法定数量
#     second_unit = fields.Many2one(comodel_name="basedata.cus_unit", string="second Unit", )  # 第二计量单位
#     origin_country_id = fields.Many2one(comodel_name="delegate_country", string="origin country", )  # 原产国
#     destination_country_id = fields.Many2one(comodel_name="delegate_country", string="destination country", )  # 目的国
#     duty_mode_id = fields.Many2one(comodel_name="basedata.cus_duty_mode", string="Duty Mode", )  # 征免方式

