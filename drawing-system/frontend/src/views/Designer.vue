<!-- ========================================================
  销售预测管理页面
  文件: frontend/src/views/Designer.vue
  功能: 新建销售预测单、排产申请
======================================================== -->
<template>
  <div class="designer-page">
    <!-- 页面标题 -->
    <div v-if="!embedded" class="page-header">
      <h2>销售预测管理</h2>
      <div class="header-actions">
        <el-button type="primary" @click="openPartDialog">
          <el-icon><Plus /></el-icon>新建销售预测单
        </el-button>
        <el-button type="warning" @click="openPrototypeDialog">
          <el-icon><Document /></el-icon>排产申请
        </el-button>
        <el-button type="danger" plain @click="handleLogout">
          <el-icon><SwitchButton /></el-icon>退出登录
        </el-button>
      </div>
    </div>
    <div v-else style="margin-bottom: 16px;">
      <el-button type="primary" size="small" @click="openPartDialog">
        <el-icon><Plus /></el-icon>新建销售预测单
      </el-button>
      <el-button type="warning" size="small" @click="openPrototypeDialog">
        <el-icon><Document /></el-icon>排产申请
      </el-button>
    </div>

    <!-- 销售预测单列表 -->
    <el-card shadow="never">
      <el-table
        :data="partList"
        v-loading="loading"
        row-key="id"
      >
        <el-table-column prop="part_number" label="预测单号" width="150" />
        <el-table-column prop="name" label="产品名称" min-width="150" />
        <el-table-column prop="spec" label="规格型号" min-width="120" />
        <el-table-column label="预测周期" width="120">
          <template #default="{ row }">
            {{ row.extra_data?.forecast_period || '-' }}
          </template>
        </el-table-column>
        <el-table-column label="数量时间轴" min-width="200">
          <template #default="{ row }">
            <div v-if="row.extra_data?.monthly_forecasts?.length">
              <el-tag v-for="(m, i) in row.extra_data.monthly_forecasts" :key="i" size="small" style="margin-right: 6px; margin-bottom: 4px;">
                {{ m.year }}-{{ String(m.month).padStart(2, '0') }}: {{ m.quantity }}
              </el-tag>
            </div>
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column label="预测金额" width="120">
          <template #default="{ row }">
            {{ row.extra_data?.forecast_amount || '-' }}
          </template>
        </el-table-column>
        <el-table-column label="审批状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getApprovalStatusType(row.approval_status)" size="small">
              {{ getApprovalStatusLabel(row.approval_status) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="创建时间" width="170">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button link type="danger" @click="handleDeletePart(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 新建销售预测单弹窗 -->
    <el-dialog v-model="partDialogVisible" title="新建销售预测单" width="800px" destroy-on-close>
      <el-form :model="partForm" :rules="partRules" ref="partFormRef" label-width="110px">
        <h4 class="section-title">单据头</h4>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="预测单号" prop="part_number">
              <el-input v-model="partForm.part_number" placeholder="例如：FC-2026-001" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="预测周期">
              <el-input v-model="partForm.forecast_period" placeholder="例如：2026 Q2" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="版本号">
              <el-input v-model="partForm.version" placeholder="V1.0" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="审批状态">
              <el-select v-model="partForm.approval_status" placeholder="请选择" style="width: 100%">
                <el-option label="草稿" value="draft" />
                <el-option label="待审批" value="pending" />
                <el-option label="已审批" value="approved" />
                <el-option label="已驳回" value="rejected" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <h4 class="section-title">预测对象</h4>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="客户/区域/渠道">
              <el-input v-model="partForm.customer_region_channel" placeholder="客户、区域或渠道" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="产品型号" prop="product_model_id">
              <el-select
                v-model="selectedProductModelId"
                placeholder="请选择产品型号"
                clearable
                style="width: 100%"
                @change="onProductModelChange"
              >
                <el-option
                  v-for="m in productModelList"
                  :key="m.id"
                  :label="`${m.product_code} - ${m.product_name}`"
                  :value="m.id"
                />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="产品编码">
              <el-input v-model="partForm.product_code" disabled />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="产品名称" prop="name">
              <el-input v-model="partForm.name" disabled />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="规格型号">
              <el-input v-model="partForm.spec" disabled />
            </el-form-item>
          </el-col>
        </el-row>

        <h4 class="section-title">数量时间轴</h4>
        <div
          v-for="(item, index) in partForm.monthly_forecasts"
          :key="index"
          class="forecast-row"
        >
          <el-row :gutter="12" align="middle">
            <el-col :span="6">
              <el-form-item :label="index === 0 ? '年份' : ''">
                <el-select v-model="item.year" placeholder="选择年份" style="width: 100%">
                  <el-option
                    v-for="y in yearOptions"
                    :key="y"
                    :label="y + '年'"
                    :value="y"
                  />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="6">
              <el-form-item :label="index === 0 ? '月份' : ''">
                <el-select v-model="item.month" placeholder="选择月份" style="width: 100%">
                  <el-option
                    v-for="m in 12"
                    :key="m"
                    :label="m + '月'"
                    :value="m"
                  />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item :label="index === 0 ? '预测数量' : ''">
                <el-input-number v-model="item.quantity" :min="0" controls-position="right" style="width: 100%" />
              </el-form-item>
            </el-col>
            <el-col :span="4" style="display: flex; align-items: center; padding-bottom: 18px;">
              <el-button type="danger" size="small" plain @click="removeForecastMonth(index)">
                删除
              </el-button>
            </el-col>
          </el-row>
        </div>
        <el-button type="primary" size="small" @click="addForecastMonth">
          <el-icon><Plus /></el-icon> 添加月份
        </el-button>

        <h4 class="section-title">辅助信息</h4>
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="单位">
              <el-input v-model="partForm.unit" placeholder="个/件/套" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="单价">
              <el-input-number v-model="partForm.unit_price" :min="0" :precision="2" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="预测金额">
              <el-input-number v-model="partForm.forecast_amount" :min="0" :precision="2" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="历史同期销量">
              <el-input-number v-model="partForm.historical_sales" :min="0" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="预测依据">
              <el-input v-model="partForm.forecast_basis" placeholder="请输入预测依据" />
            </el-form-item>
          </el-col>
        </el-row>

        <h4 class="section-title">备注</h4>
        <el-form-item label="备注说明">
          <el-input v-model="partForm.description" type="textarea" :rows="3" placeholder="备注、签字栏、变更记录等" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="partDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitPart" :loading="submitLoading">确定</el-button>
      </template>
    </el-dialog>

    <!-- 排产申请弹窗 -->
    <el-dialog v-model="prototypeDialogVisible" title="发起排产申请" width="520px" destroy-on-close>
      <el-form :model="prototypeForm" :rules="prototypeRules" ref="prototypeFormRef" label-width="100px">
        <el-form-item label="选择预测单" prop="part_id">
          <el-select v-model="prototypeForm.part_id" placeholder="请选择预测单" style="width: 100%">
            <el-option
              v-for="p in partList"
              :key="p.id"
              :label="`${p.part_number} - ${p.name}`"
              :value="p.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="数量" prop="quantity">
          <el-input-number v-model="prototypeForm.quantity" :min="1" style="width: 100%" />
        </el-form-item>
        <el-form-item label="申请原因" prop="reason">
          <el-input v-model="prototypeForm.reason" type="textarea" :rows="3" placeholder="请输入申请原因" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="prototypeDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitPrototype" :loading="submitLoading">提交申请</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Document, SwitchButton } from '@element-plus/icons-vue'
import request from '../utils/request'

const props = defineProps({
  embedded: { type: Boolean, default: false }
})

const router = useRouter()
const API_BASE = '/api/designer'

// 年份下拉选项（前后各5年）
const currentYear = new Date().getFullYear()
const yearOptions = Array.from({ length: 11 }, (_, i) => currentYear - 5 + i)

// ========================================================
// 响应式数据
// ========================================================
const loading = ref(false)
const submitLoading = ref(false)
const partList = ref([])
const productModelList = ref([])
const selectedProductModelId = ref(null)

// 销售预测单弹窗
const partDialogVisible = ref(false)
const partFormRef = ref(null)
const partForm = reactive({
  part_number: '',
  forecast_period: '',
  version: 'V1.0',
  approval_status: 'draft',
  customer_region_channel: '',
  product_code: '',
  name: '',
  spec: '',
  monthly_forecasts: [],
  unit: '',
  unit_price: null,
  forecast_amount: null,
  historical_sales: null,
  forecast_basis: '',
  description: ''
})
const partRules = {
  part_number: [
    { required: true, message: '请输入预测单号', trigger: 'blur' }
  ],
  product_model_id: [
    { required: true, message: '请选择产品型号', trigger: 'change' }
  ],
  name: [
    { required: true, message: '请输入产品名称', trigger: 'blur' }
  ]
}

// 排产弹窗
const prototypeDialogVisible = ref(false)
const prototypeFormRef = ref(null)
const prototypeForm = reactive({
  part_id: null,
  quantity: 1,
  reason: ''
})
const prototypeRules = {
  part_id: [
    { required: true, message: '请选择预测单', trigger: 'change' }
  ],
  quantity: [
    { required: true, message: '请输入数量', trigger: 'blur' }
  ],
  reason: [
    { required: true, message: '请输入申请原因', trigger: 'blur' }
  ]
}

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

function getStatusType(status) {
  const map = {
    draft: 'info',
    approved: 'success',
    obsoleted: 'danger'
  }
  return map[status] || 'info'
}

function getStatusLabel(status) {
  const map = {
    draft: '草稿',
    approved: '已批准',
    obsoleted: '已废弃'
  }
  return map[status] || status
}

function getApprovalStatusType(status) {
  const map = {
    draft: 'info',
    pending: 'warning',
    approved: 'success',
    rejected: 'danger'
  }
  return map[status] || 'info'
}

function getApprovalStatusLabel(status) {
  const map = {
    draft: '草稿',
    pending: '待审批',
    approved: '已审批',
    rejected: '已驳回'
  }
  return map[status] || status
}

function handleLogout() {
  localStorage.removeItem('token')
  localStorage.removeItem('user')
  ElMessage.success('已退出登录')
  router.push('/login')
}

// ========================================================
// API 请求
// ========================================================
async function fetchPartList() {
  loading.value = true
  try {
    const res = await request.get(`${API_BASE}/parts`)
    partList.value = res.data.items || []
  } catch (err) {
    ElMessage.error('获取预测单列表失败')
  } finally {
    loading.value = false
  }
}

// 新建销售预测单
function openPartDialog() {
  partForm.part_number = ''
  partForm.forecast_period = ''
  partForm.version = 'V1.0'
  partForm.approval_status = 'draft'
  partForm.customer_region_channel = ''
  partForm.product_code = ''
  partForm.name = ''
  partForm.spec = ''
  partForm.monthly_forecasts = []
  partForm.unit = ''
  partForm.unit_price = null
  partForm.forecast_amount = null
  partForm.historical_sales = null
  partForm.forecast_basis = ''
  partForm.description = ''
  selectedProductModelId.value = null
  partDialogVisible.value = true
}

function onProductModelChange(modelId) {
  const model = productModelList.value.find(m => m.id === modelId)
  if (model) {
    partForm.product_code = model.product_code
    partForm.name = model.product_name
    partForm.spec = model.spec_model || ''
  } else {
    partForm.product_code = ''
    partForm.name = ''
    partForm.spec = ''
  }
}

async function fetchProductModels() {
  try {
    const res = await request.get('/api/product-models', {
      params: { limit: 999 }
    })
    productModelList.value = res.data.items || []
  } catch (err) {
    ElMessage.error('获取产品型号列表失败')
  }
}

function addForecastMonth() {
  const now = new Date()
  partForm.monthly_forecasts.push({
    year: now.getFullYear(),
    month: now.getMonth() + 1,
    quantity: null
  })
}

function removeForecastMonth(index) {
  partForm.monthly_forecasts.splice(index, 1)
}

async function submitPart() {
  const valid = await partFormRef.value.validate().catch(() => false)
  if (!valid) return

  submitLoading.value = true
  try {
    await request.post(`${API_BASE}/parts`, {
      part_number: partForm.part_number,
      name: partForm.name,
      spec: partForm.spec || undefined,
      description: partForm.description || undefined,
      forecast_period: partForm.forecast_period || undefined,
      version: partForm.version || undefined,
      approval_status: partForm.approval_status || undefined,
      customer_region_channel: partForm.customer_region_channel || undefined,
      product_code: partForm.product_code || undefined,
      monthly_forecasts: partForm.monthly_forecasts.length > 0 ? partForm.monthly_forecasts : undefined,
      unit: partForm.unit || undefined,
      unit_price: partForm.unit_price || undefined,
      forecast_amount: partForm.forecast_amount || undefined,
      historical_sales: partForm.historical_sales || undefined,
      forecast_basis: partForm.forecast_basis || undefined
    })
    ElMessage.success('销售预测单创建成功')
    partDialogVisible.value = false
    fetchPartList()
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '创建失败')
  } finally {
    submitLoading.value = false
  }
}

// 删除预测单
async function handleDeletePart(row) {
  try {
    await ElMessageBox.confirm(
      `确定删除预测单 "${row.part_number}"（${row.name}）吗？关联的图纸和排产记录将一并删除。`,
      '确认删除',
      { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' }
    )
    await request.delete(`${API_BASE}/parts/${row.id}`)
    ElMessage.success('预测单已删除')
    fetchPartList()
  } catch (err) {
    if (err !== 'cancel') {
      ElMessage.error(err.response?.data?.detail || '删除失败')
    }
  }
}

// 排产申请
function openPrototypeDialog() {
  prototypeForm.part_id = null
  prototypeForm.quantity = 1
  prototypeForm.reason = ''
  prototypeDialogVisible.value = true
}

async function submitPrototype() {
  const valid = await prototypeFormRef.value.validate().catch(() => false)
  if (!valid) return

  submitLoading.value = true
  try {
    await request.post(`${API_BASE}/prototypes`, {
      part_id: prototypeForm.part_id,
      quantity: prototypeForm.quantity,
      reason: prototypeForm.reason
    })
    ElMessage.success('排产申请已提交')
    prototypeDialogVisible.value = false
  } catch (err) {
    ElMessage.error(err.response?.data?.detail || '提交失败')
  } finally {
    submitLoading.value = false
  }
}

// ========================================================
// 生命周期
// ========================================================
onMounted(() => {
  fetchPartList()
  fetchProductModels()
})
</script>

<style scoped>
.designer-page {
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

.section-title {
  margin: 16px 0 12px;
  font-size: 15px;
  font-weight: 600;
  color: #303133;
  border-left: 4px solid #409eff;
  padding-left: 10px;
}

.section-title:first-child {
  margin-top: 0;
}
</style>
