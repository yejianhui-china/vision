# ========================================================
# 料号编码规则配置
# 格式: 性质.大类.小类 + 6位流水号
# 示例: ZS.CP.ZJ000001
# ========================================================

# 第一段：料号性质代码
NATURE_CODES = {
    "ZS": {"name": "正式料号", "desc": "量产产品使用的标准物料"},
    "SY": {"name": "试用料号", "desc": "试产/验证阶段物料"},
    "LS": {"name": "临时料号", "desc": "临时替代、维修备件、打样"},
    "DK": {"name": "客供料号", "desc": "客户指定或客户提供的物料"},
    "WB": {"name": "外购标准件", "desc": "直接采购的标准件、通用件"},
}

# 第二段：大类代码
CATEGORY_CODES = {
    "CP": {"name": "成品", "desc": "最终整机产品、套装、配件包", "types": ["product"]},
    "BP": {"name": "半成品", "desc": "需继续加工的中间产品、PCBA、毛坯件", "types": ["semi_product"]},
    "ZJ": {"name": "组件", "desc": "由多个零件装配而成的功能单元/子模组", "types": ["component"]},
    "JG": {"name": "结构件", "desc": "外壳、支架、面板、散热器等机械零件", "types": ["part"]},
    "DZ": {"name": "电子元器件", "desc": "芯片、阻容感、传感器、连接器等", "types": ["part"]},
    "PC": {"name": "PCB&FPC", "desc": "刚性电路板、柔性电路板", "types": ["part"]},
    "XL": {"name": "线缆", "desc": "排线、同轴线、电源线、天线等", "types": ["part"]},
    "GJ": {"name": "紧固件", "desc": "螺丝、螺母、铜柱、卡扣等", "types": ["part"]},
    "FL": {"name": "辅料", "desc": "导热材料、泡棉、胶带、标签、说明书等", "types": ["part"]},
    "BC": {"name": "包材", "desc": "彩盒、纸箱、吸塑、纸托、胶带等", "types": ["part"]},
    "WG": {"name": "外购模块", "desc": "电源适配器、电池包、摄像头模组等成品模块", "types": ["part"]},
    "RJ": {"name": "软件/固件", "desc": "Bootloader、主程序、资源文件、算法授权", "types": ["part"]},
    "GZ": {"name": "工装治具", "desc": "组装治具、测试治具、烧录工装、老化架", "types": ["part"]},
    "QT": {"name": "其他", "desc": "不属于以上类别的物料", "types": ["part"]},
}

# 第三段：小类代码（按大类分组）
SUBCATEGORY_CODES = {
    # 成品 CP
    "CP": {
        "ZJ": {"name": "整机", "desc": "完整产品整机、单机"},
        "PJ": {"name": "配件/套装", "desc": "配件包、充电套装、扩展套装"},
        "LX": {"name": "零售包装件", "desc": "含完整包装的可销售单元"},
        "QT": {"name": "其他成品", "desc": "不属于以上分类的成品"},
    },
    # 半成品 BP
    "BP": {
        "JG": {"name": "结构半成品", "desc": "注塑毛坯、未表面处理的结构件、焊接前钣金件"},
        "DZ": {"name": "电子半成品", "desc": "贴装完成的PCBA（未烧录/未测试）、裸板"},
        "ZH": {"name": "综合半成品", "desc": "部分装配的子单元（未达组件层级）"},
        "QT": {"name": "其他半成品", "desc": "不属于以上分类的半成品"},
    },
    # 组件 ZJ
    "ZJ": {
        "DC": {"name": "电池组件", "desc": "电池+保护板+连接器装配体"},
        "XS": {"name": "显示组件", "desc": "显示屏+触摸+排线装配体"},
        "TX": {"name": "通信组件", "desc": "天线+馈线+支架装配体"},
        "SR": {"name": "散热组件", "desc": "散热片+风扇+导热垫装配体"},
        "AN": {"name": "按键组件", "desc": "按键+硅胶+导电基装配体"},
        "FS": {"name": "防水组件", "desc": "密封圈+防水胶+透气阀装配体"},
        "JK": {"name": "结构组件", "desc": "多结构件装配的功能子单元"},
        "QT": {"name": "其他组件", "desc": "不属于以上分类的组件"},
    },
    # 结构件 JG
    "JG": {
        "JJ": {"name": "机加件", "desc": "CNC加工件、车削件、铣削件"},
        "ZS": {"name": "注塑件", "desc": "塑料外壳、按键、卡扣"},
        "BJ": {"name": "钣金件", "desc": "不锈钢支架、弹片、屏蔽罩"},
        "YZ": {"name": "压铸件", "desc": "锌合金压铸件、铝合金压铸件"},
        "XM": {"name": "橡胶/硅胶件", "desc": "密封圈、按键硅胶、脚垫"},
        "JP": {"name": "镜片/面板", "desc": "PMMA/PC镜片、触摸屏盖板"},
        "SR": {"name": "散热件", "desc": "散热片、导热管、风扇"},
        "TX": {"name": "弹簧/弹性件", "desc": "压簧、扭簧、弹片"},
    },
    # 电子元器件 DZ
    "DZ": {
        "ZK": {"name": "主控芯片", "desc": "MCU、MPU、SoC、FPGA"},
        "CC": {"name": "存储芯片", "desc": "Flash、EEPROM、SRAM、SD卡"},
        "PM": {"name": "电源管理", "desc": "PMIC、DC-DC、LDO、充电IC、电池保护"},
        "TX": {"name": "通信芯片", "desc": "WiFi/BT模块、4G/5G模组、NFC、GPS"},
        "CG": {"name": "传感器", "desc": "温度、湿度、加速度、光感、霍尔"},
        "DK": {"name": "阻容感", "desc": "电阻、电容、电感、磁珠、晶振"},
        "LJ": {"name": "连接器", "desc": "FPC连接器、排针、USB座、电池座"},
        "XS": {"name": "显示器件", "desc": "LCD、OLED、触摸屏、背光模组"},
        "SJ": {"name": "声学器件", "desc": "扬声器、麦克风、蜂鸣器、马达"},
        "ER": {"name": "二极管", "desc": "LED、肖特基、稳压管、TVS"},
        "SR": {"name": "三极管/晶体管", "desc": "MOSFET、IGBT、三极管"},
        "IC": {"name": "其他IC", "desc": "运放、比较器、逻辑器件、接口芯片"},
    },
    # PCB & FPC
    "PC": {
        "ZB": {"name": "主板", "desc": "主PCB"},
        "FB": {"name": "副板", "desc": "小板/子板"},
        "KB": {"name": "按键板", "desc": "按键PCB"},
        "WB": {"name": "软板/排线板", "desc": "FPC软板"},
        "GB": {"name": "钢网", "desc": "SMT印刷钢网"},
    },
    # 线缆 XL
    "XL": {
        "PX": {"name": "排线/FFC", "desc": "FFC/FPC排线"},
        "TZ": {"name": "同轴线", "desc": "射频同轴线、IPEX跳线"},
        "DX": {"name": "电源线", "desc": "电池连接线、DC线"},
        "YX": {"name": "音频线", "desc": "扬声器线、麦克风线"},
        "TX": {"name": "天线", "desc": "FPC天线、陶瓷天线、金属天线"},
        "SB": {"name": "数据线", "desc": "USB线、调试线"},
    },
    # 紧固件 GJ
    "GJ": {
        "LS": {"name": "螺丝", "desc": "机牙螺丝、自攻螺丝"},
        "LM": {"name": "螺母/螺柱", "desc": "六角螺母、铜柱、螺柱"},
        "DL": {"name": "垫圈/弹垫", "desc": "平垫、弹簧垫圈、止退垫"},
        "KK": {"name": "卡扣", "desc": "塑料卡扣、定位销、卡簧"},
        "CZ": {"name": "磁铁/磁吸", "desc": "磁铁、磁吸组件"},
    },
    # 辅料 FL
    "FL": {
        "DR": {"name": "导热材料", "desc": "硅脂、导热垫、导热胶"},
        "HM": {"name": "泡棉/海绵", "desc": "EVA、IXPE、EPDM泡棉"},
        "JM": {"name": "胶带/胶类", "desc": "3M双面胶、UV胶、结构胶"},
        "MY": {"name": "绝缘/麦拉", "desc": "绝缘片、麦拉、青稞纸"},
        "BQ": {"name": "标签", "desc": "SN标签、环保标签、防拆贴"},
        "SL": {"name": "印刷品", "desc": "说明书、保修卡、彩页"},
        "FJ": {"name": "防尘/过滤", "desc": "防尘网、防水透气膜"},
        "QT": {"name": "其他辅料", "desc": "干燥剂、扎带、防静电袋"},
    },
    # 包材 BC
    "BC": {
        "NH": {"name": "内盒/彩盒", "desc": "产品包装盒"},
        "WX": {"name": "外箱/纸箱", "desc": "运输外箱"},
        "NT": {"name": "内托", "desc": "吸塑、纸托、EVA内衬"},
        "BD": {"name": "缓冲/填充", "desc": "气泡袋、填充物、护角"},
        "ZD": {"name": "打包材料", "desc": "封箱胶带、打包带、缠绕膜"},
    },
    # 外购模块 WG
    "WG": {
        "DY": {"name": "电源适配器", "desc": "充电器、适配器"},
        "DC": {"name": "电池/电池组", "desc": "锂电池、电池包"},
        "CM": {"name": "摄像头模组", "desc": "摄像头、镜头模组"},
        "MD": {"name": "马达/电机", "desc": "步进、伺服、有刷电机"},
        "CD": {"name": "充电模块", "desc": "无线充电模组"},
        "QT": {"name": "其他模块", "desc": "传感器模组、指纹模组等"},
    },
    # 软件/固件 RJ
    "RJ": {
        "BT": {"name": "Bootloader", "desc": "启动引导程序"},
        "ZJ": {"name": "主程序", "desc": "主固件/APP"},
        "SJ": {"name": "算法/数据", "desc": "算法授权、校准数据、资源文件"},
        "DL": {"name": "底层驱动", "desc": "驱动程序、BSP"},
    },
    # 工装治具 GZ
    "GZ": {
        "ZZ": {"name": "组装治具", "desc": "定位夹具、压合治具"},
        "CZ": {"name": "测试治具", "desc": "ICT治具、FCT治具、射频测试架"},
        "SZ": {"name": "烧录治具", "desc": "程序烧录工装"},
        "QZ": {"name": "其他工装", "desc": "气密测试、老化架、拆解工装"},
    },
    # 其他 QT
    "QT": {
        "QT": {"name": "其他", "desc": "不属于以上分类的物料"},
    },
}


def get_next_part_number(db, nature_code: str, category_code: str, subcategory_code: str) -> str:
    """生成下一个料号"""
    from .models import PartNumberCounter

    category_key = f"{nature_code}.{category_code}.{subcategory_code}"

    # 查找或创建计数器
    counter = db.query(PartNumberCounter).filter(PartNumberCounter.category_code == category_key).first()
    if not counter:
        counter = PartNumberCounter(category_code=category_key, last_sequence=0)
        db.add(counter)
        db.flush()

    # 递增流水号
    counter.last_sequence += 1
    sequence = counter.last_sequence

    # 生成料号：性质.大类.小类 + 6位流水号
    return f"{nature_code}.{category_code}.{subcategory_code}{sequence:06d}"
