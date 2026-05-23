-- ========================================================
-- 生产管理系统 - PostgreSQL 初始化脚本
-- 版本: v1.0
-- 用途: 创建数据库表结构、索引、初始数据
-- 执行方式: psql -U postgres -d drawing_system -f init.sql
-- ========================================================

-- --------------------------------------------------------
-- 1. 用户表
-- 内网系统，不走注册，管理员直接录入账号
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id          SERIAL PRIMARY KEY,
    username    VARCHAR(50) UNIQUE NOT NULL,
    password    VARCHAR(255) NOT NULL,          -- bcrypt哈希存储
    name        VARCHAR(50) NOT NULL,           -- 显示姓名
    role        VARCHAR(20) NOT NULL 
                CHECK (role IN ('designer', 'reviewer', 'approver', 'admin')),
    email       VARCHAR(100),
    phone       VARCHAR(20),
    department  VARCHAR(50),                    -- 部门
    is_active   BOOLEAN DEFAULT TRUE,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE users IS '系统用户表';
COMMENT ON COLUMN users.role IS '角色: designer销售, reviewer仓库管理员, approver生产排产管理, admin管理员';

-- --------------------------------------------------------
-- 2. 图纸主数据表
-- 核心台账，一张图一条记录
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS drawings (
    id                  SERIAL PRIMARY KEY,
    drawing_no          VARCHAR(50) UNIQUE NOT NULL,    -- 图号，如 ASM-2024-001
    name                VARCHAR(200) NOT NULL,          -- 图名
    category            VARCHAR(50),                    -- 类别: 装配图/零件图/标准件/工装图
    version             VARCHAR(10) DEFAULT 'V1.0',     -- 当前版本
    status              VARCHAR(20) DEFAULT 'draft' 
                        CHECK (status IN (
                            'draft',            -- 草稿
                            'pending_review',   -- 待审核
                            'reviewed',         -- 已审核（待批准）
                            'pending_approval', -- 待批准
                            'published',        -- 已发布
                            'rejected',         -- 已驳回
                            'obsolete'          -- 已作废
                        )),
    
    -- 人员关联
    designer_id         INTEGER REFERENCES users(id),   -- 销售
    reviewer_id         INTEGER REFERENCES users(id),   -- 指定仓库管理员
    approver_id         INTEGER REFERENCES users(id),   -- 指定生产排产管理
    
    -- 文件存储
    file_path           VARCHAR(500) NOT NULL,          -- NAS完整路径
    thumbnail_path      VARCHAR(500),                   -- 缩略图路径
    file_size           BIGINT,                         -- 文件大小(字节)
    file_format         VARCHAR(10),                    -- pdf/dwg/step
    
    -- 技术信息（可选，AI/OCR后期自动填充）
    material            VARCHAR(100),                   -- 材料
    surface_treatment   VARCHAR(200),                   -- 表面处理
    weight              DECIMAL(10,3),                  -- 重量(kg)
    dimensions          VARCHAR(100),                   -- 外形尺寸，如 120x80x50
    scale               VARCHAR(10),                    -- 比例
    sheet_no            VARCHAR(20),                    -- 图幅/张数
    
    -- 流程时间戳
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    submitted_at        TIMESTAMP,                      -- 提交审核时间
    reviewed_at         TIMESTAMP,                      -- 审核完成时间
    approved_at         TIMESTAMP,                      -- 批准时间
    published_at        TIMESTAMP,                      -- 正式发布时间
    obsolete_at         TIMESTAMP,                      -- 作废时间
    
    -- 备注
    design_notes        TEXT,                           -- 设计说明
    review_comment      TEXT,                           -- 审核意见
    approve_comment     TEXT,                           -- 批准意见
    change_summary      TEXT                            -- 变更摘要
);

COMMENT ON TABLE drawings IS '图纸主数据台账';
COMMENT ON COLUMN drawings.status IS '图纸状态: draft草稿, pending_review待审核, reviewed已审核, pending_approval待批准, published已发布, rejected已驳回, obsolete已作废';

-- --------------------------------------------------------
-- 3. 图纸版本历史表
-- 每次版本升级时备份上一版本信息
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS drawing_versions (
    id              SERIAL PRIMARY KEY,
    drawing_id      INTEGER NOT NULL REFERENCES drawings(id) ON DELETE CASCADE,
    version         VARCHAR(10) NOT NULL,               -- 版本号
    file_path       VARCHAR(500) NOT NULL,              -- 该版本的文件路径
    change_desc     TEXT,                               -- 版本变更说明
    created_by      INTEGER REFERENCES users(id),
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(drawing_id, version)
);

COMMENT ON TABLE drawing_versions IS '图纸版本历史';

-- --------------------------------------------------------
-- 4. BOM表（自关联实现多级结构）
-- 支持装配体→子装配体→零件的树状结构
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS bom_items (
    id              SERIAL PRIMARY KEY,
    
    -- 层级关系
    parent_id       INTEGER REFERENCES bom_items(id) ON DELETE CASCADE,  -- NULL表示顶层
    drawing_id      INTEGER REFERENCES drawings(id),                      -- 关联图纸
    
    -- 物料信息
    item_no         VARCHAR(50) NOT NULL,       -- 件号（本层级唯一）
    item_name       VARCHAR(200) NOT NULL,      -- 件名
    quantity        DECIMAL(10,2) DEFAULT 1,     -- 数量（支持小数，如0.5米）
    unit            VARCHAR(20) DEFAULT '件',     -- 单位
    
    -- 版本控制
    version         VARCHAR(10) DEFAULT 'V1.0', -- BOM版本
    is_standard     BOOLEAN DEFAULT FALSE,      -- 是否标准件
    is_optional     BOOLEAN DEFAULT FALSE,      -- 是否可选件
    is_alternative  BOOLEAN DEFAULT FALSE,      -- 是否替代料
    alt_for         INTEGER REFERENCES bom_items(id),  -- 替代哪个件
    
    -- 工艺信息
    material        VARCHAR(100),
    weight          DECIMAL(10,3),
    supplier        VARCHAR(100),               -- 供应商
    remark          VARCHAR(255),
    
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 同一父件下件号唯一
    UNIQUE(parent_id, item_no)
);

COMMENT ON TABLE bom_items IS 'BOM清单（支持多级自关联）';
COMMENT ON COLUMN bom_items.parent_id IS '父件ID，NULL表示顶层装配体';

-- --------------------------------------------------------
-- 5. 工程变更单（ECO）
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS eco (
    id              SERIAL PRIMARY KEY,
    eco_no          VARCHAR(50) UNIQUE NOT NULL,    -- 变更单号 ECO-2024-001
    
    -- 关联图纸（可关联多张，用逗号分隔图号或走中间表）
    primary_drawing_id  INTEGER REFERENCES drawings(id),
    affected_drawings   TEXT,                       -- 影响的其他图号列表，JSON或逗号分隔
    
    -- 变更内容
    change_type     VARCHAR(20) 
                    CHECK (change_type IN (
                        'dimension',    -- 尺寸变更
                        'material',     -- 材料变更
                        'surface',      -- 表面处理变更
                        'tolerance',    -- 公差变更
                        'add',          -- 新增
                        'remove',       -- 删除
                        'replace',      -- 替换
                        'other'         -- 其他
                    )),
    reason          TEXT NOT NULL,                  -- 变更原因/背景
    before_desc     TEXT,                           -- 变更前描述
    after_desc      TEXT,                           -- 变更后描述
    impact_analysis TEXT,                           -- 影响分析
    
    -- 人员
    applicant_id    INTEGER REFERENCES users(id),
    reviewer_id     INTEGER REFERENCES users(id),
    approver_id     INTEGER REFERENCES users(id),
    
    -- 流程状态
    status          VARCHAR(20) DEFAULT 'draft' 
                    CHECK (status IN (
                        'draft',        -- 草稿
                        'submitted',    -- 已提交
                        'reviewing',    -- 审核中
                        'approved',     -- 已批准
                        'rejected',     -- 已拒绝
                        'implemented'   -- 已执行
                    )),
    
    -- 时间戳
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    submitted_at    TIMESTAMP,
    approved_at     TIMESTAMP,
    rejected_at     TIMESTAMP,
    implemented_at  TIMESTAMP,
    
    -- 备注
    review_comment  TEXT,
    approve_comment TEXT
);

COMMENT ON TABLE eco IS '工程变更单（ECO）';

-- --------------------------------------------------------
-- 6. 变更与图纸关联表（多对多）
-- 一个ECO可以影响多张图纸
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS eco_drawings (
    id              SERIAL PRIMARY KEY,
    eco_id          INTEGER NOT NULL REFERENCES eco(id) ON DELETE CASCADE,
    drawing_id      INTEGER NOT NULL REFERENCES drawings(id) ON DELETE CASCADE,
    change_desc     TEXT,                               -- 该图纸的具体变更内容
    old_version     VARCHAR(10),                        -- 变更前版本
    new_version     VARCHAR(10),                        -- 变更后版本
    UNIQUE(eco_id, drawing_id)
);

-- --------------------------------------------------------
-- 7. 审批历史记录（审计追踪）
-- 谁在什么时候把什么改成了什么
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS approval_history (
    id              SERIAL PRIMARY KEY,
    drawing_id      INTEGER REFERENCES drawings(id),
    eco_id          INTEGER REFERENCES eco(id),
    
    from_status     VARCHAR(20),                      -- 原状态
    to_status       VARCHAR(20),                      -- 新状态
    action          VARCHAR(20) 
                    CHECK (action IN (
                        'create',       -- 创建
                        'submit',       -- 提交
                        'review_pass',  -- 审核通过
                        'review_reject',-- 审核驳回
                        'approve',      -- 批准
                        'reject',       -- 驳回
                        'publish',      -- 发布
                        'revoke',       -- 撤销
                        'obsolete',     -- 作废
                        'modify'        -- 修改信息
                    )),
    
    actor_id        INTEGER REFERENCES users(id),     -- 操作人
    actor_name      VARCHAR(50),                      -- 冗余存储，防用户改名后历史丢失
    comment         TEXT,                             -- 操作备注/意见
    
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE approval_history IS '审批历史与审计日志';

-- --------------------------------------------------------
-- 8. 系统配置表
-- 编号规则、通知设置等
-- --------------------------------------------------------
CREATE TABLE IF NOT EXISTS system_config (
    id          SERIAL PRIMARY KEY,
    config_key  VARCHAR(100) UNIQUE NOT NULL,
    config_value TEXT,
    description VARCHAR(255),
    updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by  INTEGER REFERENCES users(id)
);

COMMENT ON TABLE system_config IS '系统配置表';

-- ========================================================
-- 索引（查询加速）
-- ========================================================

-- 用户表索引
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active);

-- 图纸表索引
CREATE INDEX IF NOT EXISTS idx_drawings_status ON drawings(status);
CREATE INDEX IF NOT EXISTS idx_drawings_designer ON drawings(designer_id);
CREATE INDEX IF NOT EXISTS idx_drawings_reviewer ON drawings(reviewer_id);
CREATE INDEX IF NOT EXISTS idx_drawings_approver ON drawings(approver_id);
CREATE INDEX IF NOT EXISTS idx_drawings_category ON drawings(category);
CREATE INDEX IF NOT EXISTS idx_drawings_drawing_no ON drawings(drawing_no);
CREATE INDEX IF NOT EXISTS idx_drawings_created ON drawings(created_at);
CREATE INDEX IF NOT EXISTS idx_drawings_published ON drawings(published_at);

-- 版本历史索引
CREATE INDEX IF NOT EXISTS idx_versions_drawing ON drawing_versions(drawing_id);

-- BOM表索引
CREATE INDEX IF NOT EXISTS idx_bom_parent ON bom_items(parent_id);
CREATE INDEX IF NOT EXISTS idx_bom_drawing ON bom_items(drawing_id);
CREATE INDEX IF NOT EXISTS idx_bom_item_no ON bom_items(item_no);

-- ECO索引
CREATE INDEX IF NOT EXISTS idx_eco_status ON eco(status);
CREATE INDEX IF NOT EXISTS idx_eco_drawing ON eco(primary_drawing_id);
CREATE INDEX IF NOT EXISTS idx_eco_applicant ON eco(applicant_id);
CREATE INDEX IF NOT EXISTS idx_eco_eco_no ON eco(eco_no);

-- 审批历史索引
CREATE INDEX IF NOT EXISTS idx_history_drawing ON approval_history(drawing_id);
CREATE INDEX IF NOT EXISTS idx_history_eco ON approval_history(eco_id);
CREATE INDEX IF NOT EXISTS idx_history_actor ON approval_history(actor_id);
CREATE INDEX IF NOT EXISTS idx_history_created ON approval_history(created_at);

-- ========================================================
-- 初始数据
-- ========================================================

-- 系统默认管理员账号
-- 密码: admin123（生产环境必须修改！）
-- 使用 bcrypt 哈希值，后端验证时需要对应
INSERT INTO users (username, password, name, role, email, department, is_active)
VALUES 
    ('admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewKyNiAYMyzJ/I1q', '系统管理员', 'admin', 'admin@company.com', '技术部', TRUE);

-- 图号编码规则示例配置
INSERT INTO system_config (config_key, config_value, description)
VALUES 
    ('drawing_no_prefix', 'ASM,PRT,STD', '图号前缀规则：装配、零件、标准件'),
    ('drawing_no_year', 'TRUE', '图号是否包含年份'),
    ('drawing_no_seq_len', '3', '图号序列号位数'),
    ('current_year', '2024', '当前年份（用于编号）'),
    ('eco_prefix', 'ECO', '变更单前缀'),
    ('eco_seq_len', '3', '变更单序列号位数'),
    ('version_format', 'VX.Y', '版本号格式：V1.0, V1.1, V2.0'),
    ('nas_root', '\\\\NAS\\drawings', 'NAS根路径');

-- ========================================================
-- 触发器：自动更新 updated_at 字段
-- ========================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 为用户表添加触发器
CREATE TRIGGER update_users_updated_at 
    BEFORE UPDATE ON users 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- 为图纸表添加触发器
CREATE TRIGGER update_drawings_updated_at 
    BEFORE UPDATE ON drawings 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- 为BOM表添加触发器
CREATE TRIGGER update_bom_updated_at 
    BEFORE UPDATE ON bom_items 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- ========================================================
-- 完成
-- ========================================================

-- 验证：查看创建的表
\dt

-- 查看初始数据
SELECT * FROM users;
SELECT * FROM system_config;
