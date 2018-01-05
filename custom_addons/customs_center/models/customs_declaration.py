# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
import odoo.addons.decimal_precision as dp
import odoo.addons.queue_job.job as q_job
from odoo.tools import config
import logging, os, shutil
from lxml import etree
from collections import OrderedDict
import uuid
from datetime import datetime, timedelta
# from custom_addons.customs_center.utils.to_xml_message import delegate_to_xml
from ..utils.to_xml_message import delegate_to_xml
_logger = logging.getLogger(__name__)

RECV_XML_BASE_PATH = config.options.get('recv_xml_message_path', '/var/log/customs_message/recv_xml_message')
ERROR_XML_BASE_PATH = config.options.get('error_xml_message_path','/var/log/customs_message/error_xml_message')
BAKUP_XML_BASE_PATH = config.options.get('bakup_xml_message_path','/var/log/customs_message/bakup_xml_message')

PARSE_XG_TO_WLY_PATH = config.options.get('parse_xg_to_wly_path')
PARSE_XG_TO_WLY_ATTACH_PATH = config.options.get('parse_xg_to_wly_attach_path')
PARSE_SEND_ERROR_XML_PATH = config.options.get('parse_send_error_xml_path')
GENERATE_REC_WLY_TO_XG_PATH = config.options.get('generate_rec_wly_to_xg_path')
GENERATE_REC_WLY_TO_XG_ATTACH_PATH = config.options.get('generate_rec_wly_to_xg_attach_path')
BACKUP_SEND_XML_PATH = config.options.get('backup_send_xml_path')   # 新光原始报文备份目录


# parse_xg_to_wly_path = /mnt/odooshare/about_wly_xml_data/send/xinguang_to_wly
# parse_xg_to_wly_attach_path = /mnt/odooshare/about_wly_xml_data/send/xinguang_to_wly_attach_send
# parse_send_error_xml_path = /mnt/odooshare/about_wly_xml_data/send/error_xml_message
# generate_rec_wly_to_xg_path = /mnt/odooshare/about_wly_xml_data/send/wly_to_xinguang
# generate_rec_wly_to_xg_attach_path = /mnt/odooshare/about_wly_xml_data/send/wly_to_xinguang_attach_rec
# backup_send_xml_path = /mnt/odooshare/about_wly_xml_data/send/backup_send_xml
#
# generate_wly_to_ex_path = /mnt/odooshare/about_wly_xml_data/receive/wly_to_ex
# generate_wly_to_ex_attach_path = /mnt/odooshare/about_wly_xml_data/receive/wly_to_ex_attach_send
# parse_rec_ex_to_wly = /mnt/odooshare/about_wly_xml_data/receive/ex_to_wly
# parse_rec_ex_to_wly_attach = /mnt/odooshare/about_wly_xml_data/receive/ex_to_wly_attach_rec
# parse_rec_error_xml_path = /mnt/odooshare/about_wly_xml_data/receive/error_xml_message
# backup_rec_xml_path = /mnt/odooshare/about_wly_xml_data/receive/backup_rec_xml




def check_and_mkdir(*path):
    for p in path:
        if not os.path.exists(p):
            os.mkdir(p)


class CustomsDeclaration(models.Model):
    """ 报关单 """
    _name = 'customs_center.customs_dec'
    _rec_name = 'name'
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    _description = 'Customs Declaration'

    name = fields.Char(string="Name")  # 报关单流水号
    client_seq_no = fields.Char(string="client seq No")  # 报关单客户端编号
    # 关联工作单
    work_sheet_id = fields.Many2one(comodel_name="work_sheet", string="Work Sheet")  # 工作单ID

    # 关联通关清单 多对一
    customs_order_id = fields.Many2one(comodel_name="customs_center.customs_order", string="customs Order")
    cus_ciq_No = fields.Char(string="cus Ciq No")  # 关检关联号
    custom_master_id = fields.Many2one(comodel_name="delegate_customs", string="Dec Custom")  # 申报口岸 / 申报地海关

    entry_type_id = fields.Many2one(comodel_name="basedata.cus_entry_type", string="Entry Type")  # 报关单类型 关联报关单类型字典表，待新增
    bill_type_id = fields.Many2one(comodel_name="basedata.cus_filing_bill_type", string="bill Type")    # 备案清单 待新建，备案清单类型表
    inout = fields.Selection(string="InOut", selection=[('i', u'进口'), ('e', u'出口'), ], required=True)  # 进出口类型
    dec_seq_no = fields.Char(string="DecSeqNo")  # 统一编号
    pre_entry_id = fields.Char(string="PreEntryId")  # 预录入编号
    entry_id = fields.Char(string="EntryId")  # 海关编号
    ManualNo = fields.Char(string="Manual No")  # 备案号
    customer_contract_no = fields.Char(string="Customer Contract No")  # 合同协议号
    in_out_date = fields.Datetime(string="InoutDate", required=True, default=fields.Datetime.now)   # 进出口日期
    dec_date = fields.Datetime(string="DecDate", required=True, default=fields.Datetime.now)   # 申报日期
    customs_id = fields.Many2one(comodel_name="delegate_customs", string="Customs")  # 进出口岸

    transport_mode_id = fields.Many2one(comodel_name="delegate_transport_mode",
                                        string="Transport Mode")  # 运输方式
    NativeShipName = fields.Char(string="Native Ship Name")  # 运输工具名称
    VoyageNo = fields.Char(string="Voyage No")           # 航次号

    bill_no = fields.Char(string="Bill No")           # 提运单号
    trade_mode_id = fields.Many2one(comodel_name="delegate_trade_mode", string="Trade Mode")  # 监管方式
    CutMode_id = fields.Many2one(comodel_name="basedata.cus_cut_mode", string="CutMode id")  # 征免性质   征免性质表待新建
    in_ratio = fields.Integer(string="In ratio")  # 征免比例
    licenseNo = fields.Char(string="Bill No")  # 许可证号
    licenseNo_id = fields.One2many(comodel_name="customs_center.dec_lic_doc",
                                inverse_name="customs_declaration_id", string="License No")  # 许可证号    一对多 关联随附单证模型

    origin_arrival_country_id = fields.Many2one(comodel_name="delegate_country",
                                                string="Origin Arrival Country")  # 启运/抵达国
    port_id = fields.Many2one(comodel_name="delegate_port", string="Port", )  # 装货/指运港
    region_id = fields.Many2one(comodel_name="delegate_region", string="Region")  # 境内目的/货源地
    trade_terms_id = fields.Many2one(comodel_name="delegate_trade_terms", string="Trade Term")  # 成交方式 or 贸易条款


    # payment_mark = fields.Selection(string="payment mark", selection=[('1', u'经营单位'),
    #                                                     ('2', u'收货单位'),
    #                                                     ('3', u'申报单位')], )  # 纳税单位

    # 关联 纳税单位标识类型 替换 上边注释
    payment_mark = fields.Many2one(comodel_name="customs_center.pay_mark_type", string="payment mark")   # 纳税单位

    # fee_mark = fields.Selection(string="FeeMark", selection=[('1', u'1-率'),
    #                                                     ('2', u'2-单价'),
    #                                                     ('3', u'3-总价')], )  # 运费标记
    # insurance_mark = fields.Selection(string="InsurMark", selection=[('1', '1-率'),
    #                                                     ('3', '3-总价')], )  # 保险费标记
    # other_mark = fields.Selection(string="OtherMark", selection=[('1', u'1-率'),
    #                                                     ('3', u'3-总价')], )  # 杂费标记

    # 关联 费用标识类型 替换 上边注释
    fee_mark = fields.Many2one(comodel_name="customs_center.exp_mark_type", string="FeeMark")  # 运费标记
    insurance_mark = fields.Many2one(comodel_name="customs_center.exp_mark_type", string="insurance_mark") # 保险费标记
    other_mark = fields.Many2one(comodel_name="customs_center.exp_mark_type", string="other_mark") # 杂费标记

    # promise1 = fields.Selection(string="promise1", selection=[('0', u'0-否'),
    #                                                     ('1', u'1-是'),
    #                                                     ('9', u'9-空')], )  # 特殊关系确认
    # promise2 = fields.Selection(string="promise2", selection=[('0', u'0-否'),
    #                                                     ('1', u'1-是'),
    #                                                     ('9', u'9-空')], )  # 价格影响确认
    # promise3 = fields.Selection(string="promise3", selection=[('0', u'0-否'),
    #                                                     ('1', u'1-是'),
    #                                                     ('9', u'9-空')], )  # 支付特许权使用费确认

    # 关联 是否标识类型 替换 上边注释
    promise1 = fields.Many2one(comodel_name="customs_center.whet_mark_type", string="promise1") # 特殊关系确认
    promise2 = fields.Many2one(comodel_name="customs_center.whet_mark_type", string="promise2") # 价格影响确认
    promise3 = fields.Many2one(comodel_name="customs_center.whet_mark_type", string="promise3") # 支付特许权使用费确认

    fee_rate = fields.Float(string="FeeRate", digits=dp.get_precision('Product Price'),)  # 运费/率
    fee_currency_id = fields.Many2one(comodel_name="basedata.cus_currency", string="FeeCurrency", required=False, )  # 运费币制

    insurance_rate = fields.Float(string="InsurRate", digits=dp.get_precision('Product Price'),)  # 保险费/率
    insurance_currency_id = fields.Many2one(comodel_name="basedata.cus_currency", string="InsurCurrency_id", required=False, )  # 保险费币制

    other_rate = fields.Float(string="OtherRate", digits=dp.get_precision('Product Price'),)  # 杂费/率
    other_currency_id = fields.Many2one(comodel_name="basedata.cus_currency", string="OtherCurrency_id", required=False, )  # 杂费币制

    qty = fields.Integer(string="Qty")  # 件数
    gross_weight = fields.Float(string="Gross Weight")  # 毛重
    net_weight = fields.Float(string="Net Weight")  # 净重
    remarks = fields.Text(string="Marks")  # 备注
    packing_id = fields.Many2one(comodel_name="delegate_packing", string="Package Type")  # 包装种类、方式
    trade_country_id = fields.Many2one(comodel_name="delegate_country",
                                       string="Trade Country")  # 贸易国别



    rel_dec_No = fields.Char(string="RelDec No")  # 关联报关单
    rel_man_No = fields.Char(string="License No")  # 关联 备案
    bonded_No = fields.Char(string="Bonded No")  # 监管场所
    customs_field = fields.Char(string="CustomsField")  # 货场代码

    customer_id = fields.Many2one(comodel_name="res.partner", string="Customer")  # 客户

    # # 集成通3.0 XML报文相关字段
    # agent_code = fields.Char(string="Agent Code", required=True, )  # 申报单位代码
    # cop_code = fields.Char(string="Cop Code", required=True, )      # 录入单位代码
    # cop_name = fields.Char(string="Cop Name", required=True, )      # 录入单位名称
    # custom_master = fields.Char(string="Custom Master", required=True, )  # 申报地海关代码

    declare_company_id = fields.Many2one(comodel_name="basedata.cus_register_company", string="declare company name")  # 申报单位 新建企业库表
    input_company_id = fields.Many2one(comodel_name="basedata.cus_register_company", string="input company id")  # 消费使用单位 新建企业库表
    business_company_id = fields.Many2one(comodel_name="basedata.cus_register_company", string="business company name")    # 收发货人 新建企业库表

    @api.onchange('business_company_id')
    def _compute_input_company(self):
        """根据当前选中的收发货人 改变 消费使用单位"""
        for customs_dec in self:
            if customs_dec.business_company_id != 0:
                customs_dec.input_company_id = customs_dec.business_company_id

    cop_code = fields.Char(string="cop code")  # 录入单位企业组织机构代码
    cop_name = fields.Char(string="cop name")  # 录入单位企业名称
    cop_code_scc = fields.Char(string="cop Social credit uniform coding")  # 录入单位社会信用统一编码
    inputer_name = fields.Char(string="inputer name")  # 录入员姓名
    oper_name = fields.Char(string="oper name")     # 操作员姓名
    certificate = fields.Char(string="oper card certificate")   # 操作员卡的证书号
    ic_code = fields.Char(string="IC number")  # 操作员IC卡号/录入员IC卡号
    cus_dec_dir = fields.Char(string="customs dec path")  # 企业报文服务器存放路径

    # cop_code_scc = fields.Char(string="cop Social credit uniform coding")  # 录入单位社会信用统一编码
    # owner_code_scc = fields.Char(string="owner Social credit uniform coding")   # 货主单位/生产消费单位 社会信用统一编码
    # trade_code_scc = fields.Char(string="owner Social credit uniform coding")   # 经营单位 / 收发货人 统一编码

    decl_trn_rel = fields.Selection(string="DeclTrnRel", selection=[('0', u'一般报关单'), ('1', u'转关提前报关单')])   # 报关/转关关系标志
    ediId = fields.Selection(string="ediId", selection=[('1', u'普通报关'), ('3', u'北方转关提前'),
                                                        ('5', u'南方转关提前'), ('6', u'普通报关')], )  # 报关标志
    # trade_code = fields.Char(string="Trade Code", required=True, )  # 经营单位编号

    # 关联报关单商品列表 1对多关系
    # dec_goods_list_ids = fields.One2many(comodel_name="customs_center.dec_goods_list",
    #                                     inverse_name="customs_declaration_id", string="dec goods name")
    # 通关清单 和报关单共用一张商品表的时候 下方的写法
    dec_goods_list_ids = fields.One2many(comodel_name="customs_center.cus_goods_list",
                                         inverse_name="customs_declaration_id", string="dec goods name")
    # 报关单 关联合规模型 一对多 冗余字段 用于修改历史商品列表 通过关联报关单 确认是否已归类
    dec_goods_classified_ids = fields.One2many(comodel_name="customs_center.goods_classify",
                                         inverse_name="customs_declaration_id", string="goods classified")

    customs_declaration_state = fields.Selection(string="State", selection=[('draft', 'Draft'),
                                                        ('succeed', 'Success'),
                                                        ('cancel', 'Cancel'),
                                                        ('failure', 'Failure')], default='draft')  # 报关单状态
    receipt_ids = fields.One2many(comodel_name="customs_center.dec_result", inverse_name="customs_declaration_id",
                                  string="Recipts", required=False, )

    cus_dec_sent_state = fields.Selection(string="Sent State", selection=[('draft', 'Draft'),
                                                                      ('succeed', 'Success'),
                                                                      ('cancel', 'Cancel'),
                                                                      ('failure', 'Failure')],default='draft')  # 报关单发送单一窗口状态

    @api.model
    def create(self, vals):
        """设置报关单命名规则"""
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('code_customs_declaration') or _('New')
            # vals['client_seq_no'] = str(uuid.uuid1())
            vals['client_seq_no'] = str((datetime.now()+timedelta(hours=8)).strftime('%y%m%d%H%M%S%f'))
        result = super(CustomsDeclaration, self).create(vals)

        return result


    @api.model
    # @q_job.job
    def parse_original_xml(self):
        """解析原始报文入库 生成报关单"""

        # 设置文件路径path
        # company_xml_parse_path = self.env['customs_center.customs_dec'].browse(cus_dec_dir) #  做成前端界面可配置
        company_xml_parse_path = u'BYJC_DXPENT0000016165' #  做成前端界面可配置
        parse_xml_path = os.path.join(PARSE_XG_TO_WLY_PATH, company_xml_parse_path.encode('utf-8'))  # 新光原始报文解析目录
        parse_attach_path = os.path.join(PARSE_XG_TO_WLY_ATTACH_PATH, company_xml_parse_path.encode('utf-8')) # 新光随附单据解析目录
        error_xml_path = os.path.join(PARSE_SEND_ERROR_XML_PATH, company_xml_parse_path.encode('utf-8'))
        backup_xml_path = os.path.join(BACKUP_SEND_XML_PATH, company_xml_parse_path.encode('utf-8'))  # 新光原始报文备份目录

        # 检查并生成相应的目录
        check_and_mkdir(parse_xml_path, parse_attach_path, error_xml_path, backup_xml_path)

        files = os.listdir(parse_xml_path)
        files = [filename for filename in files if filename.endswith('.xml')]
        if not files:
            return True
        files = [os.path.join(parse_xml_path, i) for i in files]

        # 读文件，用lxml解析报文
        for xml_message in files:
            with open(xml_message, 'r') as f:
                tree = etree.parse(f)
                root = tree.getroot()
                # response_dic = {}
                customs_dec_dic = {}
                root_name = etree.QName(root).localname
                if root_name == u'DecMessage':
                    head_node = root.find('DecHead')
                    body_list = root.find('DecLists')
                    body_containers_list = root.find('DecContainers')
                    body_license_docus_list = root.find('DecLicenseDocus')
                    body_free_test_list = root.find('DecFreeTxt')
                    body_dec_sign = root.find('DecSign')
                    trn_head_info = root.find('TrnHead')
                    trn_list_info = root.find('TrnList')
                    trn_containers_info = root.find('TrnContainers')
                    trn_conta_goods_list = root.find('TrnContaGoodsList')
                    e_doc_realation_info = root.find('EdocRealation')

                    # customs_dec_dic = OrderedDict()
                    customs_dec_dic['DecHead'] = {}
                    for child in head_node.iterchildren():
                        if child.text:
                            customs_dec_dic['DecHead'][child.tag] = child.text
                    print("*************************************************************************")
                    print(customs_dec_dic)

                    # 报文中的商品列表
                    customs_dec_dic['DecLists'] = {}
                    for child in body_list.iterchildren():
                        d_list = 0
                        customs_dec_dic['DecLists'][d_list] = {}
                        for child_son in child.iterchildren():
                            if child_son.text:
                                customs_dec_dic['DecLists'][d_list][child_son.tag] = child_son.text
                                d_list += 1

                    customs_dec_dic['DecContainers'] = {}
                    for child in body_containers_list.iterchildren():
                        if child.text:
                            customs_dec_dic['DecContainers'][child.tag] = child.text

                    customs_dec_dic['DecLicenseDocus'] = {}
                    for child in body_license_docus_list.iterchildren():
                        if child.text:
                            customs_dec_dic['DecLicenseDocus'][child.tag] = child.text

                    customs_dec_dic['DecFreeTxt'] = {}
                    for child in body_free_test_list.iterchildren():
                        if child.text:
                            customs_dec_dic['DecFreeTxt'][child.tag] = child.text

                    customs_dec_dic['DecFreeTxt'] = {}
                    for child in body_free_test_list.iterchildren():
                        if child.text:
                            customs_dec_dic['DecFreeTxt'][child.tag] = child.text

                    customs_dec_dic['DecSign'] = {}
                    for child in body_dec_sign.iterchildren():
                        if child.text:
                            customs_dec_dic['DecSign'][child.tag] = child.text

                    customs_dec_dic['TrnHead'] = {}
                    for child in trn_head_info.iterchildren():
                        if child.text:
                            customs_dec_dic['TrnHead'][child.tag] = child.text

                    customs_dec_dic['TrnList'] = {}
                    for child in trn_list_info.iterchildren():
                        if child.text:
                            customs_dec_dic['TrnList'][child.tag] = child.text

                    customs_dec_dic['TrnContainers'] = {}
                    for child in trn_containers_info.iterchildren():
                        if child.text:
                            customs_dec_dic['TrnContainers'][child.tag] = child.text

                    customs_dec_dic['TrnContaGoodsList'] = {}
                    for child in trn_conta_goods_list.iterchildren():
                        if child.text:
                            customs_dec_dic['TrnContaGoodsList'][child.tag] = child.text

                    customs_dec_dic['EdocRealation'] = {}
                    for child in e_doc_realation_info.iterchildren():
                        if child.text:
                            customs_dec_dic['EdocRealation'][child.tag] = child.text

                else:
                    _logger.error(u'Find error format xml message: %s' % xml_message.decode('utf-8'))
                    shutil.move(xml_message, error_path)
                    continue

            if customs_dec_dic:
                client_seq_no = customs_dec_dic['DecSign']['ClientSeqNo']  # 报关单客户端编号
                inout = customs_dec_dic['DecHead']['IEFlag']  # u'进出口标志'

                custom_master_code = customs_dec_dic['DecHead']['CustomMaster']  # u'申报地海关'
                custom_master_id = self.env['delegate_customs'].search([('code', '=', custom_master_code)])

                dec_seq_no = customs_dec_dic['DecHead']['AgentCodeScc'] # u'统一编号'  申报单位统一编码
                pre_entry_id = customs_dec_dic['DecHead']['PreEntryId'] # u'预录入编号'

                # customs_code = customs_dec_dic.get('DecHead')['IEPort']  # u'进出口岸'
                customs_code = customs_dec_dic['DecHead']['IEPort']  # u'进出口岸'
                customs_id = self.env['delegate_customs'].search([('code', '=', customs_code)])

                ManualNo = customs_dec_dic['DecHead']['ManualNo']  # u'备案号'
                customer_contract_no = customs_dec_dic['DecHead']['ContrNo']  # u'合同编号'

                in_out_date = customs_dec_dic['DecHead']['IEDate']  # u'进出口日期'

                business_company_register_code = customs_dec_dic['DecHead']['TradeCode']   # 收发货人
                business_company_id = self.env['basedata.cus_register_company'].search([('register_code', '=', business_company_register_code)])

                input_company_unified_code = customs_dec_dic['DecHead']['OwnerCodeScc']   # 消费使用单位 货主单位
                input_company_id = self.env['basedata.cus_register_company'].search([('unified_social_credit_code', '=', input_company_unified_code)])

                declare_company_register_code = customs_dec_dic['DecHead']['AgentCode']   # 申报单位
                declare_company_id = self.env['basedata.cus_register_company'].search([('register_code', '=', declare_company_register_code)])

                transport_mode_code = customs_dec_dic['DecHead']['TrafMode']  # u'运输方式'
                transport_mode_id = self.env['delegate_transport_mode'].search([('code', '=', transport_mode_code)])

                NativeShipName = customs_dec_dic['DecHead']['TrafName']  # u'运输工具名称'
                VoyageNo = customs_dec_dic['TrnList']['VoyageNo']  # u'航次号'
                bill_no = customs_dec_dic['DecHead']['BillNo']  # u'提运单号'

                trade_mode_code = customs_dec_dic['DecHead']['TradeMode']  # u'监管方式'
                trade_mode_id = self.env['delegate_trade_mode'].search([('Code', '=', trade_mode_code)])

                CutMode_code = customs_dec_dic['DecHead']['CutMode']  # u'征免性质'
                CutMode_id = self.env['basedata.cus_cut_mode'].search([('Code', '=', CutMode_code)])

                payment_mark_code = customs_dec_dic['DecHead']['PaymentMark']  # u'纳税单位'
                payment_mark = self.env['customs_center.pay_mark_type'].search([('Code', '=', payment_mark_code)])

                licenseNo = customs_dec_dic['DecHead']['LicenseNo']  # u'许可证编号'

                origin_arrival_country_code = customs_dec_dic['DecHead']['TradeCountry']  # u'启运国/抵达国'
                origin_arrival_country_id = self.env['delegate_country'].search([('Code', '=', origin_arrival_country_code)])

                port_code = customs_dec_dic['DecHead']['DistinatePort']  # u'装货/指运港'
                port_id = self.env['delegate_port'].search([('Code', '=', port_code)])

                region_code = customs_dec_dic['DecHead']['DistrictCode']  # u'境内目的/货源地'
                region_id = self.env['delegate_region'].search([('Code', '=', region_code)])

                trade_terms_code = customs_dec_dic['DecHead']['TransMode']  # u'成交方式 or 贸易条款'
                trade_terms_id = self.env['delegate_trade_terms'].search([('Code', '=', trade_terms_code)])

                fee_mark_code = customs_dec_dic['DecHead']['FeeMark']  # u'运费标记'
                fee_mark = self.env['customs_center.exp_mark_type'].search([('Code', '=', fee_mark_code)])
                fee_rate = customs_dec_dic['DecHead']['FeeRate']  # u'运费／率'

                fee_currency_code = customs_dec_dic['DecHead']['FeeCurr']  # u'运费币制'
                fee_currency_id = self.env['basedata.cus_currency'].search([('Code', '=', fee_currency_code)])

                insurance_mark_code = customs_dec_dic['DecHead']['InsurMark']  # u'保险费标记'
                insurance_mark = self.env['customs_center.exp_mark_type'].search([('Code', '=', insurance_mark_code)])
                insurance_rate = customs_dec_dic['DecHead']['InsurRate']  # u'保险费／率'

                insurance_currency_code = customs_dec_dic['DecHead']['InsurCurr']  # u'保险费币制'
                insurance_currency_id = self.env['basedata.cus_currency'].search([('Code', '=', insurance_currency_code)])

                other_mark_code = customs_dec_dic['DecHead']['OtherMark']  # u'杂费标记'
                other_mark = self.env['customs_center.exp_mark_type'].search([('Code', '=', other_mark_code)])
                other_rate = customs_dec_dic['DecHead']['OtherRate']  # u'杂费／率'

                other_currency_code = customs_dec_dic['DecHead']['OtherCurr']  # u'杂费币制'
                other_currency_id = self.env['basedata.cus_currency'].search([('Code', '=', other_currency_code)])

                qty = customs_dec_dic['DecHead']['PackNo']  # u'件数'

                packing_code = customs_dec_dic['DecHead']['WrapType']  # u'包装种类'
                packing_id = self.env['delegate_packing'].search([('Code', '=', packing_code)])

                gross_weight = customs_dec_dic['DecHead']['GrossWet']  # u'毛重'
                net_weight = customs_dec_dic['DecHead']['NetWt']  # u'净重'

                trade_country_code = customs_dec_dic['DecHead']['TradeAreaCode']  # u'境内目的/货源地'
                trade_country_id = self.env['delegate_region'].search([('Code', '=', trade_country_code)])

                in_ratio = customs_dec_dic['DecHead']['PayWay']  # u'征税比例' in_ratio  报文PayWay

                promise1_promise2_promise3_code = customs_dec_dic['DecHead']['PromiseItmes']  # u'承诺事项'  字符串拼接
                promise1_code = str(promise1_promise2_promise3_code)[0]
                promise2_code = str(promise1_promise2_promise3_code)[1]
                promise3_code = str(promise1_promise2_promise3_code)[2]
                promise1 = self.env['customs_center.whet_mark_type'].search([('Code', '=', promise1_code)])  # 特殊关系确认
                promise2 = self.env['customs_center.whet_mark_type'].search([('Code', '=', promise2_code)])  # 价格影响确认
                promise3 = self.env['customs_center.whet_mark_type'].search([('Code', '=', promise3_code)])  # 支付特许权使用费确认

                entry_type_code = customs_dec_dic['DecHead']['EntryType']  # u'报关单类型'
                entry_type_id = self.env['basedata.cus_entry_type'].search([('Code', '=', entry_type_code)])

                remarks = customs_dec_dic['DecHead']['NoteS']  # u'备注'

                cop_code = customs_dec_dic['DecHead']['CopCode']  # u'录入单位企业组织机构代码'
                cop_name = customs_dec_dic['DecHead']['CopName']  # u'录入单位名称'
                cop_code_scc = customs_dec_dic['DecHead']['CopCodeScc']  # u'录入单位社会信用统一编码'
                inputer_name = customs_dec_dic['DecHead']['InputerName']  # u'录入员姓名'
                oper_name = customs_dec_dic['DecSign']['OperName']  # u'操作员姓名'
                certificate = customs_dec_dic['DecSign']['Certificate']  # u'操作员卡的证书号'
                ic_code = customs_dec_dic['DecHead']['TypistNo']  # u'操作员IC卡号/录入员IC卡号'

                # print(customs_dec_dic)
                customs_dec_dic = {
                    'client_seq_no': client_seq_no,  # 报关单客户端编号
                    'inout': inout,  # u'进出口标志'
                    'custom_master_id': custom_master_id[0].id,  # 申报口岸 / 申报地海关
                    'dec_seq_no': dec_seq_no,  # u'统一编号'
                    'pre_entry_id': pre_entry_id,  # u'预录入编号'
                    'customs_id': customs_id[0].id,  # u'进出口岸'
                    'ManualNo': ManualNo,  # u'备案号'
                    'customer_contract_no': customer_contract_no,  # u'合同协议号'
                    'in_out_date': in_out_date,  # u'进出口日期'
                    'business_company_id': business_company_id[0].id,  # 收发货人
                    'input_company_id': input_company_id[0].id,  # 消费使用单位 货主单位
                    'declare_company_id': declare_company_id[0].id,  # 申报单位
                    'transport_mode_id': transport_mode_id[0].id,  # u'运输方式'
                    'NativeShipName': NativeShipName,  # u'运输工具名称'
                    'VoyageNo': VoyageNo,  # u'航次号'
                    'bill_no': bill_no,  # u'提运单号'
                    'trade_mode_id': trade_mode_id[0].id,  # u'监管方式'
                    'CutMode_id': CutMode_id[0].id,  # u'征免性质'
                    'payment_mark': payment_mark[0].id,  # 纳税单位 id
                    'licenseNo': licenseNo,  # u'许可证编号'
                    'origin_arrival_country_id': origin_arrival_country_id[0].id, # 启运国/抵达国
                    'port_id': port_id[0].id,  # 装货/指运港 id
                    'region_id': region_id[0].id,  # 境内目的/货源地 id
                    'trade_terms_id': trade_terms_id[0].id,  # 成交方式 or 贸易条款 id
                    'fee_mark': fee_mark[0].id,  # # 运费标记 id
                    'fee_rate': fee_rate,  # 运费/率
                    'fee_currency_id': fee_currency_id[0].id,  # 运费币制
                    'insurance_mark': insurance_mark[0].id,  # 保险费标记
                    'insurance_rate': insurance_rate,  # 保险费/率
                    'insurance_currency_id': insurance_currency_id[0].id,  # 保险费币制
                    'other_mark': other_mark,  # 杂费标记
                    'other_rate': other_rate,  # 杂费/率
                    'other_currency_id': other_currency_id[0].id,  # 杂费币制
                    'qty': qty,  # 件数
                    'packing_id': packing_id,  # 包装种类、方式 id
                    'gross_weight': gross_weight,  # 毛重
                    'net_weight': net_weight,  # 净重
                    'trade_country_id': trade_country_id[0].id,  # 贸易国别 id
                    'in_ratio': in_ratio,  #  u'征税比例' in_ratio  报文PayWay
                    'promise1': promise1,  # 特殊关系确认
                    'promise2': promise2,   # 价格影响确认
                    'promise3': promise3,    # 支付特许权使用费确认
                    'entry_type_id': entry_type_id[0].id,  # 报关单类型 关联报关单类型字典表
                    'remarks': remarks,  # 备注
                    'cop_code': cop_code,  # 录入单位企业组织机构代码
                    'cop_name': cop_name,  # 录入单位名称
                    'cop_code_scc': cop_code_scc,  # 录入单位社会信用统一编码
                    'inputer_name': inputer_name,  # 录入员姓名
                    'oper_name': oper_name,  # 操作员姓名
                    'certificate': certificate,  # 操作员卡的证书号
                    'ic_code': ic_code,  # 操作员IC卡号/录入员IC卡号
                }

            # 报文中的商品列表
            # customs_dec_dic['DecLists'] = {}
            # for child in body_list.iterchildren():
            #     d_list = 0
            #     customs_dec_dic['DecLists'][d_list] = {}
            #     for child_son in child.iterchildren():
            #         if child_son.text:
            #             customs_dec_dic['DecLists'][d_list][child_son.tag] = child_son.text
            #             d_list += 1

            # customs_dec_dic['DecLists']
            # {
            # 0: {'ClassMark':'888','CodeTS':'aaa','ContrItem':'bbb','DeclPrice':'ccc'},
            # 1: {'ClassMark':'888','CodeTS':'aaa','ContrItem':'bbb','DeclPrice':'ccc'},
            # 2: {'ClassMark':'888','CodeTS':'aaa','ContrItem':'bbb','DeclPrice':'ccc'}
            # }

            # 商品列表 字典
            dec_goods_list_dic = customs_dec_dic['DecLists']

            try:
                customs_declaration_obj = self.env['customs_center.customs_dec'].create(customs_dec_dic)
                customs_declaration_obj.dec_goods_list_ids |= self.env['customs_center.cus_goods_list'].search(
                    [('id', 'in', cus_goods_list_ids)])




            # 报关单 关联合规模型 一对多 冗余字段 用于修改历史商品列表 通过关联报关单 确认是否已归类
            dec_goods_classified_ids = fields.One2many(comodel_name="customs_center.goods_classify",
                                                       inverse_name="customs_declaration_id", string="goods classified")
            product_node_name = OrderedDict()
            product_node_name['ClassMark'] = None  # u'归类标志'
            product_node_name['CodeTS'] = str(item.cus_goods_tariff_id.Code_t)  # u'商品编号'
            product_node_name['ContrItem'] = None  # u'备案序号'
            product_node_name['DeclPrice'] = str(item.deal_unit_price)  # u'申报单价'
            product_node_name['DeclTotal'] = str(item.deal_total_price)  # u'申报总价'
            product_node_name['DutyMode'] = str(item.duty_mode_id.Code)  # u'征减免税方式'
            product_node_name['ExgNo'] = None  # u'货号'
            product_node_name['ExgVersion'] = None  # u'版本号'
            product_node_name['Factor'] = None  # u'申报计量单位与法定单位比例因子'
            product_node_name['FirstQty'] = str(item.first_qty)  # u'第一法定数量'
            # product_node_name['FirstUnit'] = item.first_unit.Code   # u'第一计量单位'
            product_node_name['FirstUnit'] = item.first_unit  # u'第一计量单位'
            product_node_name['GUnit'] = item.deal_unit.Code  # u'申报/成交计量单位'
            product_node_name['GModel'] = str(item.goods_model)  # u'商品规格、型号'
            product_node_name['GName'] = item.goods_name  # u'商品名称'
            product_node_name['GNo'] = str(i)  # u'商品序号'
            product_node_name['GQty'] = str(item.deal_qty)  # u'申报数量（成交计量单位）'
            product_node_name['OriginCountry'] = item.origin_country_id.Code  # u'原产地'
            # product_node_name['SecondUnit'] = item.second_unit.Code   # u'第二计量单位'
            product_node_name['SecondUnit'] = item.second_unit  # u'第二计量单位'
            product_node_name['SecondQty'] = str(item.second_qty)  # u'第二法定数量'
            product_node_name['TradeCurr'] = item.currency_id.Code  # u'成交币制'
            product_node_name['UseTo'] = None  # u'用途/生产厂家'
            product_node_name['WorkUsd'] = None  # u'工缴费'
            product_node_name['DestinationCountry'] = item.destination_country_id.Code  # u'最终目的国(地区)'

            except Exception, error_info:
                _logger.error(u'{} {}'.format(xml_message.decode('utf-8'), str(error_info).decode('utf-8')))
                shutil.move(xml_message, error_path)
                continue
            else:
                shutil.move(xml_message, bakup_path)
                _logger.info(u'Had parsed the xml message %s' % xml_message.decode('utf-8'))




    @api.multi
    def customs_delegate_to_xml(self):
        """ 根据报关单生成xml报文 存放到指定目录 """
        self.update({'cus_dec_sent_state': 'succeed'})
        for line in self:
            delegate_to_xml(line)
        return True

    @api.multi
    def dec_send_success(self):
        pass
        return True


    @api.model
    @q_job.job
    def parse_receipt_xml(self):
        """解析回执报文"""

        # 设置文件路径path
        company_name = self.env.user.company_id.name
        recv_path = os.path.join(RECV_XML_BASE_PATH, company_name.encode('utf-8'))
        error_path = os.path.join(ERROR_XML_BASE_PATH, company_name.encode('utf-8'))
        bakup_path = os.path.join(BAKUP_XML_BASE_PATH, company_name.encode('utf-8'))
        # 检查并生成相应的目录
        check_and_mkdir(recv_path, error_path, bakup_path)

        files = os.listdir(recv_path)
        files = [filename for filename in files if filename.endswith('.xml')]
        if not files:
            return True
        files = [os.path.join(recv_path, i) for i in files]

        # 读文件，用lxml解析报文
        for xml_message in files:
            with open(xml_message, 'r') as f:
                tree = etree.parse(f)
                root = tree.getroot()
                response_dic = {}
                business_dic = {}
                root_name = etree.QName(root).localname
                if root_name == u'DecImportResponse':
                    for child in root.iterchildren():
                        key = etree.QName(child).localname
                        value = child.text
                        response_dic[key] = value
                elif root_name == u'DEC_DATA':
                    result_node = root.find('DEC_RESULT')
                    result_info_node = root.find('RESULT_INFO')
                    business_dic['DEC_RESULT'] = {}
                    for child in result_node.iterchildren():
                        if child.text:
                            business_dic['DEC_RESULT'][child.tag] = child.text
                            business_dic['RESULT_INFO'] = result_info_node.text if result_info_node.text else ''
                else:
                    _logger.error(u'Find error format xml message: %s' % xml_message.decode('utf-8'))
                    shutil.move(xml_message, error_path)
                    continue
            # 根据报文中客户端代码找到关联的报关单
            rep_client_no = response_dic.get('ClientSeqNo')
            bus_client_no = business_dic['DEC_RESULT'].get('CLIENTSEQ_NO') if business_dic.get('DEC_RESULT') else None
            dec_sheets = self.env['customs_center.customs_dec'].search(
                [('name', '=', rep_client_no or bus_client_no)])
            if not dec_sheets:
                _logger.error(
                    u'{} Can\'t find related declaration sheet according to ClientSeqNo {}'
                        .format(xml_message.decode('utf-8'), rep_client_no or bus_client_no))
                shutil.move(xml_message, error_path)
                continue
            dec_sheet = dec_sheets[0]
            if not dec_sheet.dec_seq_no:
                dec_sheet.dec_seq_no = response_dic.get('SeqNo') or business_dic.get('SEQ_NO')
            if response_dic:
                resp_code = response_dic.get('ResponseCode')
                status = self.env['customs_center.dec_res_status'].search([('code', '=', resp_code)])
                print(response_dic)
                message = response_dic['ErrorMessage']
            else:
                resp_code = business_dic['DEC_RESULT']['CHANNEL']
                status = self.env['customs_center.dec_res_status'].search([('code', '=', resp_code)])
                message = business_dic['RESULT_INFO']

            if not status:
                _logger.error(
                    u'%s Can\'t find related statu obj according to response code' % xml_message.decode('utf-8'))
                shutil.move(xml_message, error_path)
                continue
            receipt_dic = {
                'status_id': status[0].id,
                'message': message,
                'customs_declaration_id': dec_sheet.id
            }
            try:
                self.env['customs_center.dec_result'].create(receipt_dic)
            except Exception, error_info:
                _logger.error(u'{} {}'.format(xml_message.decode('utf-8'), str(error_info).decode('utf-8')))
                shutil.move(xml_message, error_path)
                continue
            else:
                shutil.move(xml_message, bakup_path)
                _logger.info(u'Had parsed the xml message %s' % xml_message.decode('utf-8'))

    @api.multi
    def create_customs_declearation(self):
        """创建商品列表"""

        return True


class WorkSheet(models.Model):
    """" 工作单 """
    _inherit = 'work_sheet'

    customs_declaration_ids = fields.One2many(comodel_name="customs_center.customs_order", inverse_name="work_sheet_id",
                                        string="Customs Order")
    # 报关单状态
    customs_declaration_state = fields.Selection(string="State", selection=[('draft', 'Draft'),
                                                                ('succeed', 'Success'),
                                                                ('cancel', 'Cancel'),
                                                                ('failure', 'Failure')], compute='_get_customs_state')

    @api.depends('customs_declaration_ids')
    def _get_customs_state(self):
        """ 获取当前工作单对应的通关清单 状态"""
        for sheet in self:
            if sheet.customs_declaration_ids:
                customs_obj = sheet.customs_declaration_ids[0]
                sheet.customs_declaration_state = customs_obj.customs_declaration_state


class DecLicenseDoc(models.Model):
    """ 随附单证 """
    _name = 'customs_center.dec_lic_doc'
    _rec_name = 'dec_license_no'
    _description = 'DecLicenseDoc'

    dec_license_no = fields.Char(string="license no")  # 单证编号
    # 多对一关联 报关单
    customs_declaration_id = fields.Many2one(comodel_name="customs_center.customs_dec",
                                       string="customs declaration")
    dec_license_doc_type_id = fields.Many2one(comodel_name="basedata.dec_license_doc_type", string="DecLicenseDoc type")   # 单证类型/单证代码

class GoodsWizard(models.TransientModel):
    _name = 'customs_center.goods_wizard'
    _description = 'Customs Goods Wizard'

    cus_goods_tariff_id = fields.Many2one(comodel_name="basedata.cus_goods_tariff", string="cus goods Code TS", required=False, )
    goods_model = fields.Char(string="goods model", required=False, )
    deal_qty = fields.Integer(string="deal quantity", default=1, required=False, )
    deal_unit_price = fields.Monetary(string="deal unit price")
    deal_unit = fields.Many2one(comodel_name="basedata.cus_unit", string="deal unit", required=False, )
    deal_total_price = fields.Monetary(string="deal total price")
    currency_id = fields.Many2one(comodel_name="basedata.cus_currency", string="currency id", required=False, )
    first_qty = fields.Integer(string="first quantity", required=False, )
    first_unit = fields.Many2one(comodel_name="basedata.cus_unit", string="First Unit", required=False, )
    second_qty = fields.Integer(string="second quantity", required=False, )
    second_unit = fields.Many2one(comodel_name="basedata.cus_unit", string="second Unit", required=False, )
    origin_country_id = fields.Many2one(comodel_name="delegate_country", string="origin country", required=False, )
    destination_country_id = fields.Many2one(comodel_name="delegate_country", string="destination country", required=False, )
    duty_mode_id = fields.Many2one(comodel_name="basedata.cus_duty_mode", string="Duty Mode", required=False, )
    goods_classification_id = fields.Many2one(comodel_name="customs_center.goods_classify", string="Goods Classification", required=False, )    # 客户料号
    supervision_condition = fields.Char(string="supervision condition", required=False, )


    @api.onchange('deal_qty', 'deal_unit_price')
    def _compute_total_goods_price(self):
        """根据当前商品列表的成交单价 X 成交数量数量 计算出商品单行总价"""
        if self.deal_qty != 0:
            self.deal_total_price = self.deal_qty * self.deal_unit_price


    @api.onchange('cus_goods_tariff_id')
    def _generate_about_name(self):
        """根据当前海关税则编码的变化 改变商品名称 并通过onchange装饰器，自动执行_generate_about_name方法"""
        if self.cus_goods_tariff_id:
            self.goods_name = self.cus_goods_tariff_id.NameCN
            self.first_unit = self.cus_goods_tariff_id.first_unit
            self.second_unit = self.cus_goods_tariff_id.second_unit
            self.supervision_condition = self.cus_goods_tariff_id.supervision_condition

    @api.onchange('goods_classification_id')
    def _generate_about_goods_info(self):
        """根据当前合规客户料号的变化 改变商品名称 商品编码等信息 并通过onchange装饰器，自动执行_generate_about_name方法"""
        if self.goods_classification_id:
            self.cus_goods_tariff_id = self.goods_classification_id.cus_goods_tariff_id
            self.goods_name = self.goods_classification_id.goods_name
            self.goods_model = self.goods_classification_id.goods_model
            self.first_unit = self.goods_classification_id.first_unit
            self.second_unit = self.goods_classification_id.second_unit
            self.origin_country_id = self.goods_classification_id.origin_country_id
            self.destination_country_id = self.goods_classification_id.destination_country_id
            self.duty_mode_id = self.goods_classification_id.duty_mode_id
            self.ManualSN = self.goods_classification_id.ManualSN
            self.supervision_condition = self.goods_classification_id.supervision_condition


    @api.multi
    def create_goods_list(self):
        """创建报关单商品列表"""

        return True
