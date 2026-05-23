# 生产管理系统 - 用户管理模块

## 已交付文件

```
drawing-system/
├── database/
│   └── init_users.sql          # 用户表数据库初始化脚本
├── backend/
│   ├── requirements.txt        # Python依赖
│   └── app/
│       ├── __init__.py
│       ├── main.py             # FastAPI入口
│       ├── database.py         # 数据库连接
│       ├── models.py           # SQLAlchemy模型
│       └── routers/
│           ├── __init__.py
│           └── users.py        # 用户管理API
└── frontend/
    └── src/
        ├── main.js             # Vue入口
        ├── App.vue             # 根组件
        ├── router/
        │   └── index.js        # 路由配置
        └── views/
            └── UserManagement.vue  # 用户管理页面
```

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Vue 3 + Element Plus |
| 后端 | FastAPI + SQLAlchemy |
| 数据库 | PostgreSQL |

## 快速启动

### 1. 初始化数据库

```bash
# 创建数据库
createdb -U postgres drawing_system

# 执行用户表初始化脚本
psql -U postgres -d drawing_system -f database/init_users.sql
```

### 2. 启动后端

```bash
cd backend

# 安装依赖（需要Python 3.9+）
pip install -r requirements.txt

# 修改 database.py 里的数据库密码
# 默认: postgresql://postgres:your_password@localhost:5432/drawing_system

# 启动服务
uvicorn app.main:app --reload --port 8000
```

后端启动后访问: http://localhost:8000/docs

### 3. 启动前端

```bash
cd frontend

# 安装依赖（需要Node.js 18+）
npm create vue@latest .       # 如已有Vue项目则跳过
npm install
npm install element-plus @element-plus/icons-vue axios

# 启动开发服务器
npm run dev
```

前端启动后访问: http://localhost:5173

## API 接口清单

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/users` | 用户列表（支持分页/筛选/搜索） |
| GET | `/api/users/roles` | 获取角色下拉选项 |
| GET | `/api/users/{id}` | 用户详情 |
| POST | `/api/users` | 创建用户 |
| PUT | `/api/users/{id}` | 更新用户 |
| DELETE | `/api/users/{id}` | 删除用户 |
| POST | `/api/users/{id}/toggle-status` | 切换启用/禁用状态 |

## 前端功能

- [x] 用户列表（分页、筛选、搜索）
- [x] 新增用户（带表单校验）
- [x] 编辑用户（密码可选修改）
- [x] 删除用户（二次确认）
- [x] 启用/禁用开关
- [x] 角色标签颜色区分
- [x] 日期格式化显示
