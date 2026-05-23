<!-- ========================================================
  Vue 3 角色管理页面
  文件: frontend/src/views/RoleManagement.vue
  技术栈: Vue 3 + Element Plus + Composition API
======================================================== -->
<template>
  <div class="role-page">
    <!-- 页面标题 -->
    <div class="page-header">
      <h2>角色管理</h2>
      <div class="header-actions">
        <el-button type="primary" @click="handleAdd">
          <el-icon><Plus /></el-icon>新增角色
        </el-button>
      </div>
    </div>

    <!-- 数据表格 -->
    <el-card shadow="never">
      <el-table :data="roleList" v-loading="loading" stripe>
        <el-table-column type="index" width="50" label="序号" />

        <el-table-column prop="code" label="角色编码" width="150" />

        <el-table-column prop="name" label="角色名称" width="150" />

        <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />

        <el-table-column prop="is_active" label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
              {{ row.is_active ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="created_at" label="创建时间" width="160">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>

        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="handleEdit(row)">编辑</el-button>
            <el-button link type="primary" @click="handleConfigPages(row)">权限配置</el-button>
            <el-button link type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 新增/编辑角色对话框 -->
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
        <el-form-item label="角色名称" prop="name">
          <el-input v-model="formData.name" placeholder="如 系统管理员" />
        </el-form-item>

        <el-form-item label="角色编码" prop="code">
          <el-input
            v-model="formData.code"
            placeholder="如 admin"
            :disabled="isEdit"
          />
        </el-form-item>

        <el-form-item label="描述" prop="description">
          <el-input
            v-model="formData.description"
            type="textarea"
            :rows="3"
            placeholder="角色描述"
          />
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

    <!-- 权限配置对话框 -->
    <el-dialog
      v-model="pagesDialogVisible"
      title="页面权限配置"
      width="480px"
      destroy-on-close
    >
      <el-form label-width="0">
        <el-form-item>
          <el-checkbox-group v-model="selectedPages">
            <el-checkbox
              v-for="page in pageList"
              :key="page.id"
              :label="page.id"
            >
              {{ page.name }}
            </el-checkbox>
          </el-checkbox-group>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="pagesDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSavePages" :loading="pagesSubmitLoading">
          保存
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'

import request from '../utils/request'

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

const roleList = ref([])

const formData = reactive({
  name: '',
  code: '',
  description: '',
  is_active: true
})

const dialogTitle = computed(() => isEdit.value ? '编辑角色' : '新增角色')

// 表单校验规则
const formRules = {
  name: [
    { required: true, message: '请输入角色名称', trigger: 'blur' }
  ],
  code: [
    { required: true, message: '请输入角色编码', trigger: 'blur' },
    { pattern: /^[a-zA-Z0-9_]+$/, message: '仅允许字母、数字、下划线', trigger: 'blur' }
  ]
}

// 页面权限配置相关
const pagesDialogVisible = ref(false)
const pagesSubmitLoading = ref(false)
const pageList = ref([])
const selectedPages = ref([])
const configRoleId = ref(null)

// ========================================================
// 工具函数
// ========================================================
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
async function fetchRoleList() {
  loading.value = true
  try {
    const res = await request.get(`${API_BASE}/roles`)
    roleList.value = res.data.items || []
  } catch (err) {
    ElMessage.error('获取角色列表失败：' + (err.response?.data?.detail || err.message))
  } finally {
    loading.value = false
  }
}

async function fetchPageList() {
  try {
    const res = await request.get(`${API_BASE}/roles/pages/all`)
    pageList.value = res.data || []
  } catch (err) {
    ElMessage.error('获取页面列表失败：' + (err.response?.data?.detail || err.message))
  }
}

// ========================================================
// 事件处理
// ========================================================
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
    name: row.name,
    code: row.code,
    description: row.description || '',
    is_active: row.is_active
  })
  dialogVisible.value = true
}

function resetForm() {
  Object.assign(formData, {
    name: '',
    code: '',
    description: '',
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
      await request.put(`${API_BASE}/roles/${editId.value}`, formData)
      ElMessage.success('角色更新成功')
    } else {
      await request.post(`${API_BASE}/roles`, formData)
      ElMessage.success('角色创建成功')
    }
    dialogVisible.value = false
    fetchRoleList()
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '操作失败')
  } finally {
    submitLoading.value = false
  }
}

// 删除角色
async function handleDelete(row) {
  try {
    await ElMessageBox.confirm(
      `确定删除角色 "${row.name}"（${row.code}）吗？此操作不可恢复。`,
      '确认删除',
      { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' }
    )
    await request.delete(`${API_BASE}/roles/${row.id}`)
    ElMessage.success('角色已删除')
    fetchRoleList()
  } catch (err) {
    if (err !== 'cancel') {
      ElMessage.error(err.response?.data?.detail || '删除失败')
    }
  }
}

// 打开权限配置对话框
async function handleConfigPages(row) {
  configRoleId.value = row.id
  selectedPages.value = row.pages ? row.pages.map(p => p.id) : []
  await fetchPageList()
  pagesDialogVisible.value = true
}

// 保存权限配置
async function handleSavePages() {
  pagesSubmitLoading.value = true
  try {
    await request.put(`${API_BASE}/roles/${configRoleId.value}/pages`, {
      page_ids: selectedPages.value
    })
    ElMessage.success('权限配置已保存')
    pagesDialogVisible.value = false
    fetchRoleList()
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '保存失败')
  } finally {
    pagesSubmitLoading.value = false
  }
}

// ========================================================
// 生命周期
// ========================================================
onMounted(() => {
  fetchRoleList()
})
</script>

<style scoped>
.role-page {
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

:deep(.el-checkbox-group) {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

:deep(.el-checkbox) {
  margin-right: 0;
}
</style>
