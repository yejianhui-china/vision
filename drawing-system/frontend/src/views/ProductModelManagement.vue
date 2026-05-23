<!-- ========================================================
  产品型号管理页面
  文件: frontend/src/views/ProductModelManagement.vue
======================================================== -->
<template>
  <div class="product-model-management">
    <!-- 页面标题 -->
    <div class="page-header">
      <h2>产品型号管理</h2>
      <div class="header-actions">
        <el-button type="primary" @click="handleAdd">
          <el-icon><Plus /></el-icon>新增产品型号
        </el-button>
      </div>
    </div>

    <!-- 搜索筛选区 -->
    <el-card class="search-card" shadow="never">
      <el-form :model="searchForm" inline>
        <el-form-item label="关键词">
          <el-input
            v-model="searchForm.keyword"
            placeholder="产品编码/名称"
            clearable
            style="width: 220px"
            @keyup.enter="handleSearch"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </el-form-item>

        <el-form-item label="状态">
          <el-select v-model="searchForm.is_active" placeholder="全部状态" clearable style="width: 120px">
            <el-option label="启用" :value="true" />
            <el-option label="禁用" :value="false" />
          </el-select>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" @click="handleSearch">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 数据表格 -->
    <el-card shadow="never">
      <el-table :data="modelList" v-loading="loading" stripe>
        <el-table-column prop="product_code" label="产品编码" width="150" />
        <el-table-column prop="product_name" label="产品名称" min-width="180" />
        <el-table-column prop="spec_model" label="规格型号" min-width="150" />
        <el-table-column prop="unit" label="单位" width="80" />
        <el-table-column prop="is_active" label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'danger'" size="small">
              {{ row.is_active ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="170">
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
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next"
          @size-change="handleSizeChange"
          @current-change="handlePageChange"
        />
      </div>
    </el-card>

    <!-- 新增/编辑弹窗 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑产品型号' : '新增产品型号'"
      width="560px"
      destroy-on-close
    >
      <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
        <el-form-item label="产品编码" prop="product_code">
          <el-input v-model="form.product_code" placeholder="例如：PM-2026-001" :disabled="isEdit" />
        </el-form-item>
        <el-form-item label="产品名称" prop="product_name">
          <el-input v-model="form.product_name" placeholder="请输入产品名称" />
        </el-form-item>
        <el-form-item label="规格型号">
          <el-input v-model="form.spec_model" placeholder="请输入规格型号" />
        </el-form-item>
        <el-form-item label="单位">
          <el-input v-model="form.unit" placeholder="个/件/套/台" />
        </el-form-item>
        <el-form-item label="状态">
          <el-radio-group v-model="form.is_active">
            <el-radio :label="true">启用</el-radio>
            <el-radio :label="false">禁用</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.description" type="textarea" :rows="3" placeholder="请输入备注" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitForm" :loading="submitLoading">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Search } from '@element-plus/icons-vue'
import request from '../utils/request'

const API_BASE = '/api/product-models'

// 响应式数据
const loading = ref(false)
const submitLoading = ref(false)
const modelList = ref([])
const dialogVisible = ref(false)
const isEdit = ref(false)
const formRef = ref(null)
const currentId = ref(null)

const searchForm = reactive({
  keyword: '',
  is_active: undefined
})

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

const form = reactive({
  product_code: '',
  product_name: '',
  spec_model: '',
  unit: '',
  description: '',
  is_active: true
})

const rules = {
  product_code: [
    { required: true, message: '请输入产品编码', trigger: 'blur' }
  ],
  product_name: [
    { required: true, message: '请输入产品名称', trigger: 'blur' }
  ]
}

// 工具函数
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

// API 请求
async function fetchList() {
  loading.value = true
  try {
    const res = await request.get(API_BASE, {
      params: {
        keyword: searchForm.keyword || undefined,
        is_active: searchForm.is_active,
        skip: (pagination.page - 1) * pagination.pageSize,
        limit: pagination.pageSize
      }
    })
    modelList.value = res.data.items || []
    pagination.total = res.data.total || 0
  } catch (err) {
    ElMessage.error('获取产品型号列表失败')
  } finally {
    loading.value = false
  }
}

function handleSearch() {
  pagination.page = 1
  fetchList()
}

function handleReset() {
  searchForm.keyword = ''
  searchForm.is_active = undefined
  pagination.page = 1
  fetchList()
}

function handleSizeChange(size) {
  pagination.pageSize = size
  pagination.page = 1
  fetchList()
}

function handlePageChange(page) {
  pagination.page = page
  fetchList()
}

function resetForm() {
  form.product_code = ''
  form.product_name = ''
  form.spec_model = ''
  form.unit = ''
  form.description = ''
  form.is_active = true
}

function handleAdd() {
  isEdit.value = false
  currentId.value = null
  resetForm()
  dialogVisible.value = true
}

function handleEdit(row) {
  isEdit.value = true
  currentId.value = row.id
  form.product_code = row.product_code
  form.product_name = row.product_name
  form.spec_model = row.spec_model || ''
  form.unit = row.unit || ''
  form.description = row.description || ''
  form.is_active = row.is_active
  dialogVisible.value = true
}

async function submitForm() {
  const valid = await formRef.value.validate().catch(() => false)
  if (!valid) return

  submitLoading.value = true
  try {
    if (isEdit.value) {
      await request.put(`${API_BASE}/${currentId.value}`, {
        product_name: form.product_name,
        spec_model: form.spec_model || undefined,
        unit: form.unit || undefined,
        description: form.description || undefined,
        is_active: form.is_active
      })
      ElMessage.success('产品型号已更新')
    } else {
      await request.post(API_BASE, {
        product_code: form.product_code,
        product_name: form.product_name,
        spec_model: form.spec_model || undefined,
        unit: form.unit || undefined,
        description: form.description || undefined,
        is_active: form.is_active
      })
      ElMessage.success('产品型号创建成功')
    }
    dialogVisible.value = false
    fetchList()
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '操作失败')
  } finally {
    submitLoading.value = false
  }
}

async function handleDelete(row) {
  try {
    await ElMessageBox.confirm(
      `确定删除产品型号 "${row.product_code}"（${row.product_name}）吗？`,
      '确认删除',
      { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' }
    )
    await request.delete(`${API_BASE}/${row.id}`)
    ElMessage.success('产品型号已删除')
    fetchList()
  } catch (err) {
    if (err !== 'cancel') {
      ElMessage.error(err.response?.data?.detail || '删除失败')
    }
  }
}

onMounted(() => {
  fetchList()
})
</script>

<style scoped>
.product-model-management {
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
  margin-bottom: 16px;
}

.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}
</style>
