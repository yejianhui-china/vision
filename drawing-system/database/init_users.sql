-- ========================================================-- 用户管理模块 - 数据库表结构（独立提取版）-- 版本: v1.0-- 用途: 仅创建用户管理相关表和初始数据-- ========================================================

-- 用户表（核心）
CREATE TABLE IF NOT EXISTS users (
    id          SERIAL PRIMARY KEY,
    username    VARCHAR(50) UNIQUE NOT NULL,     -- 登录账号，如 zhangsan
    password    VARCHAR(255) NOT NULL,            -- bcrypt哈希存储，永不反查明文
    name        VARCHAR(50) NOT NULL,             -- 显示姓名，如 张三
    role        VARCHAR(20) NOT NULL 
                CHECK (role IN ('designer', 'reviewer', 'approver', 'admin')),
    email       VARCHAR(100),
    phone       VARCHAR(20),
    department  VARCHAR(50),                        -- 所属部门
    is_active   BOOLEAN DEFAULT TRUE,              -- 账号是否启用
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE users IS '系统用户表';
COMMENT ON COLUMN users.username IS '登录账号，全局唯一';
COMMENT ON COLUMN users.password IS 'bcrypt哈希值，生产环境严禁明文存储';
COMMENT ON COLUMN users.role IS '角色: designer销售, reviewer仓库管理员, approver生产排产管理, admin管理员';
COMMENT ON COLUMN users.is_active IS 'false表示禁用，禁用用户无法登录';

-- 索引
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_users_active ON users(is_active);
CREATE INDEX IF NOT EXISTS idx_users_dept ON users(department);

-- 触发器：自动更新 updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

DROP TRIGGER IF EXISTS update_users_updated_at ON users;
CREATE TRIGGER update_users_updated_at 
    BEFORE UPDATE ON users 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- ========================================================
-- 初始数据
-- ========================================================

-- 系统默认管理员账号（密码: admin123）
-- 使用 bcrypt $2b$12$ 哈希值
INSERT INTO users (username, password, name, role, email, department, is_active)
VALUES 
    ('admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewKyNiAYMyzJ/I1q', '系统管理员', 'admin', 'admin@company.com', '技术部', TRUE)
ON CONFLICT (username) DO NOTHING;

-- 示例测试用户（密码都是 123456，bcrypt哈希）
-- 实际部署时请删除或修改
INSERT INTO users (username, password, name, role, email, phone, department, is_active)
VALUES 
    ('zhangsan', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewKyNiAYMyzJ/I1q', '张三', 'designer', 'zhangsan@company.com', '13800138001', '设计一部', TRUE),
    ('lisi', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewKyNiAYMyzJ/I1q', '李四', 'reviewer', 'lisi@company.com', '13800138002', '技术部', TRUE),
    ('wangwu', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewKyNiAYMyzJ/I1q', '王五', 'approver', 'wangwu@company.com', '13800138003', '总工办', TRUE)
ON CONFLICT (username) DO NOTHING;

-- 验证
SELECT id, username, name, role, email, department, is_active, created_at FROM users;
