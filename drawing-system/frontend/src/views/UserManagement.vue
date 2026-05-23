<!-- ========================================================
  Vue 3 系统管理页面（用户管理 + 产品型号管理）
  文件: frontend/src/views/UserManagement.vue
  技术栈: Vue 3 + Element Plus + Composition API
======================================================== -->
<template>
  <div class="admin-page">
    <!-- 页面标题 -->
    <div class="page-header">
      <h2>工作台</h2>
      <div class="header-actions">
        <el-button type="danger" plain @click="handleLogout">
          <el-icon><SwitchButton /></el-icon>退出登录
        </el-button>
      </div>
    </div>

    <el-tabs v-model="activeTab" type="border-card">
      <el-tab-pane v-if="hasPagePermission('users')" label="用户管理" name="users">
        <!-- 搜索筛选区 -->
    <el-card class="search-card" shadow="never">
      <el-form :model="searchForm" inline>
        <el-form-item label="角色">
          <el-select v-model="searchForm.role" placeholder="全部角色" clearable style="width: 140px">
            <el-option
              v-for="item in roleOptions"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
        </el-form-item>
        
        <el-form-item label="部门">
          <el-input v-model="searchForm.department" placeholder="输入部门" clearable style="width: 150px" />
        </el-form-item>
        
        <el-form-item label="关键词">
          <el-input
            v-model="searchForm.keyword"
            placeholder="用户名/姓名/邮箱"
            clearable
            style="width: 200px"
            @keyup.enter="handleSearch"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </el-form-item>
        
        <el-form-item>
          <el-button type="primary" @click="handleSearch">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

        <!-- 数据表格 -->
    <el-card shadow="never" style="margin-top: 16px">
      <el-table :data="userList" v-loading="loading" stripe>
        <el-table-column type="index" width="50" label="序号" />
        
        <el-table-column prop="username" label="登录账号" width="120" />
        
        <el-table-column prop="name" label="姓名" width="100" />
        
        <el-table-column prop="role" label="角色" width="110">
          <template #default="{ row }">
            <el-tag :type="getRoleTagType(row.role)" size="small">
              {{ getRoleLabel(row.role) }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column prop="department" label="部门" width="120" />
        
        <el-table-column prop="email" label="邮箱" min-width="180" show-overflow-tooltip />
        
        <el-table-column prop="phone" label="电话" width="130" />
        
        <el-table-column prop="is_active" label="状态" width="80">
          <template #default="{ row }">
            <el-switch
              v-model="row.is_active"
              active-text=""
              inactive-text=""
              @change="handleToggleStatus(row)"
            />
          </template>
        </el-table-column>
        
        <el-table-column prop="created_at" label="创建时间" width="160">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="160" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="handleEdit(row)">编辑</el-button>
            <el-button link type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-wrapper">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.pageSize"
          :total="pagination.total"
          :page-sizes="[10, 20, 50, 100]"
          layout="total, sizes, prev, pager, next"
          @size-change="handleSizeChange"
          @current-change="handlePageChange"
        />
      </div>
    </el-card>

    <!-- 新增/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogTitle"
      width="520px"
      destroy-on-close
    >
      <el-form
        ref="formRef"
        :model="formData"
        :rules="formRules"
        label-width="90px"
        style="padding-right: 20px"
      >
        <el-form-item label="登录账号" prop="username">
          <el-input
            v-model="formData.username"
            placeholder="如 zhangsan"
            :disabled="isEdit"
          />
        </el-form-item>

        <el-form-item label="显示姓名" prop="name">
          <el-input v-model="formData.name" placeholder="如 张三" />
        </el-form-item>

        <el-form-item :label="isEdit ? '新密码' : '初始密码'" prop="password">
          <el-input
            v-model="formData.password"
            type="password"
            placeholder="isEdit ? '留空则不修改' : '至少4位'"
            show-password
          />
          <el-text v-if="isEdit" type="info" size="small">留空表示不修改密码</el-text>
        </el-form-item>

        <el-form-item label="角色" prop="role">
          <el-select v-model="formData.role" placeholder="请选择角色" style="width: 100%">
            <el-option
              v-for="item in roleOptions"
              :key="item.value"
              :label="item.label"
              :value="item.value"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="所属部门" prop="department">
          <el-input v-model="formData.department" placeholder="如 设计一部" />
        </el-form-item>

        <el-form-item label="邮箱" prop="email">
          <el-input v-model="formData.email" placeholder="如 zhangsan@company.com" />
        </el-form-item>

        <el-form-item label="电话" prop="phone">
          <el-input v-model="formData.phone" placeholder="如 13800138001" />
        </el-form-item>

        <el-form-item label="是否启用" prop="is_active">
          <el-switch v-model="formData.is_active" />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit" :loading="submitLoading">
          确定
        </el-button>
      </template>
        </el-dialog>
      </el-tab-pane>

      <el-tab-pane v-if="hasPagePermission('users')" label="角色管理" name="roles">
        <RoleManagement />
      </el-tab-pane>
      <el-tab-pane v-if="hasPagePermission('users')" label="产品型号管理" name="product-models">
        <ProductModelManagement />
      </el-tab-pane>
      <el-tab-pane v-if="hasPagePermission('designer')" label="销售预测管理" name="designer">
        <Designer :embedded="true" />
      </el-tab-pane>
      <el-tab-pane v-if="hasPagePermission('bom')" label="BOM管理" name="bom">
        <BomManagement />
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search, SwitchButton } from '@element-plus/icons-vue'
import ProductModelManagement from './ProductModelManagement.vue'
import RoleManagement from './RoleManagement.vue'
import Designer from './Designer.vue'
import BomManagement from './BomManagement.vue'

import request from '../utils/request'

const activeTab = ref('users')

function hasPagePermission(pageCode) {
  const pages = JSON.parse(localStorage.getItem('pages') || '[]')
  return pages.some(p => p.code === pageCode)
}

function getDefaultTab() {
  const allTabs = ['users', 'users', 'users', 'designer', 'bom']
  for (const code of allTabs) {
    if (hasPagePermission(code)) return code
  }
  return 'users'
}

onMounted(() => {
  activeTab.value = getDefaultTab()
})

const router = useRouter()

// ========================================================
// 配置
// ========================================================
const API_BASE = '/api'

// ========================================================
// 响应式数据
// ========================================================
const loading = ref(false)
const submitLoading = ref(false)
const dialogVisible = ref(false)
const isEdit = ref(false)
const editId = ref(null)
const formRef = ref(null)

const userList = ref([])
const roleOptions = ref([])

const searchForm = reactive({
  role: '',
  department: '',
  keyword: ''
})

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

const formData = reactive({
  username: '',
  name: '',
  password: '',
  role: '',
  department: '',
  email: '',
  phone: '',
  is_active: true
})

const dialogTitle = computed(() => isEdit.value ? '编辑用户' : '新增用户')

// 表单校验规则
const formRules = {
  username: [
    { required: true, message: '请输入登录账号', trigger: 'blur' },
    { min: 2, max: 50, message: '长度2-50位', trigger: 'blur' }
  ],
  name: [
    { required: true, message: '请输入显示姓名', trigger: 'blur' }
  ],
  password: [
    { required: !isEdit.value, message: '请输入密码', trigger: 'blur' },
    { min: 4, max: 100, message: '长度至少4位', trigger: 'blur' }
  ],
  role: [
    { required: true, message: '请选择角色', trigger: 'change' }
  ]
}

// ========================================================
// 工具函数
// ========================================================
function getRoleLabel(role) {
  const map = {
    designer: '销售',
    reviewer: '仓库管理员',
    approver: '生产排产管理',
    admin: '管理员'
  }
  return map[role] || role
}

function getRoleTagType(role) {
  const map = {
    designer: '',       // 默认
    reviewer: 'success',
    approver: 'warning',
    admin: 'danger'
  }
  return map[role] || ''
}

function formatDate(dateStr) {
  if (!dateStr) return '-'
  const d = new Date(dateStr)
  return d.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// ========================================================
// API 请求
// ========================================================
async function fetchRoleOptions() {
  try {
    const res = await request.get(`${API_BASE}/users/roles`)
    roleOptions.value = res.data
  } catch (err) {
    console.error('获取角色列表失败', err)
  }
}

async function fetchUserList() {
  loading.value = true
  try {
    const params = {
      skip: (pagination.page - 1) * pagination.pageSize,
      limit: pagination.pageSize,
      ...searchForm
    }
    // 过滤空值
    Object.keys(params).forEach(key => {
      if (params[key] === '' || params[key] === null || params[key] === undefined) {
        delete params[key]
      }
    })
    
    const res = await request.get(`${API_BASE}/users`, { params })
    userList.value = res.data.items
    pagination.total = res.data.total
  } catch (err) {
    ElMessage.error('获取用户列表失败：' + (err.response?.data?.detail || err.message))
  } finally {
    loading.value = false
  }
}

// ========================================================
// 事件处理
// ========================================================
function handleLogout() {
  localStorage.removeItem('token')
  localStorage.removeItem('user')
  ElMessage.success('已退出登录')
  router.push('/login')
}

function handleSearch() {
  pagination.page = 1
  fetchUserList()
}

function handleReset() {
  searchForm.role = ''
  searchForm.department = ''
  searchForm.keyword = ''
  pagination.page = 1
  fetchUserList()
}

function handleSizeChange(val) {
  pagination.pageSize = val
  pagination.page = 1
  fetchUserList()
}

function handlePageChange(val) {
  pagination.page = val
  fetchUserList()
}

// 打开新增对话框
function handleAdd() {
  isEdit.value = false
  editId.value = null
  resetForm()
  dialogVisible.value = true
}

// 打开编辑对话框
function handleEdit(row) {
  isEdit.value = true
  editId.value = row.id
  Object.assign(formData, {
    username: row.username,
    name: row.name,
    password: '',          // 编辑时密码留空
    role: row.role,
    department: row.department || '',
    email: row.email || '',
    phone: row.phone || '',
    is_active: row.is_active
  })
  dialogVisible.value = true
}

function resetForm() {
  Object.assign(formData, {
    username: '',
    name: '',
    password: '',
    role: '',
    department: '',
    email: '',
    phone: '',
    is_active: true
  })
  if (formRef.value) {
    formRef.value.resetFields()
  }
}

// 提交表单
async function handleSubmit() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return
  
  submitLoading.value = true
  try {
    if (isEdit.value) {
      // 编辑：过滤空密码
      const payload = { ...formData }
      if (!payload.password) delete payload.password
      delete payload.username  // 编辑时不传用户名
      
      await request.put(`${API_BASE}/users/${editId.value}`, payload)
      ElMessage.success('用户更新成功')
    } else {
      await request.post(`${API_BASE}/users`, formData)
      ElMessage.success('用户创建成功')
    }
    dialogVisible.value = false
    fetchUserList()
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '操作失败')
  } finally {
    submitLoading.value = false
  }
}

// 切换启用状态
async function handleToggleStatus(row) {
  try {
    await request.post(`${API_BASE}/users/${row.id}/toggle-status`)
    ElMessage.success(`用户已${row.is_active ? '启用' : '禁用'}`)
  } catch (err) {
    // 失败时把开关状态改回来
    row.is_active = !row.is_active
    ElMessage.error(err.response?.data?.detail || '操作失败')
  }
}

// 删除用户
async function handleDelete(row) {
  try {
    await ElMessageBox.confirm(
      `确定删除用户 "${row.name}"（${row.username}）吗？此操作不可恢复。`,
      '确认删除',
      { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' }
    )
    await request.delete(`${API_BASE}/users/${row.id}`)
    ElMessage.success('用户已删除')
    fetchUserList()
  } catch (err) {
    if (err !== 'cancel') {
      ElMessage.error(err.response?.data?.detail || '删除失败')
    }
  }
}

// ========================================================
// 生命周期
// ========================================================
onMounted(() => {
  fetchRoleOptions()
  fetchUserList()
})
</script>

<style scoped>
.admin-page {
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 500;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.search-card {
  :deep(.el-card__body) {
    padding-bottom: 12px;
  }
}

.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #e4e7ed;
}
</style>
