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

    # goods_name = fields.Char(string="goods name", required=False, )  # 商品名称
    # 关联通关清单 多对一
    customs_order_id = fields.Many2one(comodel_name="customs_center.customs_order", string="customs Order")

    cus_goods_tariff_id = fields.Many2one(comodel_name="basedata.cus_goods_tariff", string="cus goods Code TS", required=False, )  # 海关税则编码
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


class DecGoodsList(models.Model):
    """ 报关单-商品列表 """
    _name = 'customs_center.dec_goods_list'
    # rec_name = 'goods_name'
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    _description = 'Customs dec Goods List'

    # goods_name = fields.Char(string="goods name", required=False, )  # 商品名称
    # 关联报关单 多对一
    customs_declaration_id = fields.Many2one(comodel_name="customs_center.customs_dec",
                                       string="customs declaration")
    cus_goods_tariff_id = fields.Many2one(comodel_name="basedata.cus_goods_tariff", string="cus goods Code TS", required=False, )  # 海关税则编码
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