# -*- coding: utf-8 -*-
from odoo import models, fields, api


class DecContainer(models.Model):
    """ 关务中心 集装箱信息 """
    _name = 'customs_center.dec_container'
    rec_name = 'containerNo'
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    _description = 'customs center container'

    containerNo = fields.Char(string="container No")  # 集装箱号
    weight = fields.Float(string="Gross Weight")      # 自重
    spec_code = fields.Selection(string="State", selection=[('S', 'Small Container'),('L', 'Large Container')], default='S')  # 规格
