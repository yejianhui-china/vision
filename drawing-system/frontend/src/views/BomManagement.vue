<template>
  <div class="bom-management">
    <el-row :gutter="20">
      <!-- 左侧：物料列表 -->
      <el-col :span="8">
        <el-card class="material-list-card">
          <template #header>
            <div class="card-header">
              <span>物料列表</span>
              <el-button type="primary" size="small" @click="openAddMaterialDialog">新增物料</el-button>
            </div>
          </template>

          <!-- 搜索栏 -->
          <div class="search-bar">
            <el-select
              v-model="searchType"
              placeholder="类型"
              clearable
              size="small"
              style="width: 100px; margin-right: 8px;"
            >
              <el-option label="成品" value="product" />
              <el-option label="半成品" value="semi_product" />
              <el-option label="组件" value="component" />
              <el-option label="零件" value="part" />
            </el-select>
            <el-input
              v-model="searchKeyword"
              placeholder="搜索料号/名称"
              size="small"
              clearable
              style="width: 160px; margin-right: 8px;"
              @keyup.enter="fetchMaterials"
            />
            <el-button type="primary" size="small" @click="fetchMaterials">搜索</el-button>
          </div>

          <!-- 物料列表 -->
          <el-table
            :data="materialList"
            highlight-current-row
            @row-click="handleMaterialClick"
            style="margin-top: 10px;"
            size="small"
            height="calc(100vh - 260px)"
          >
            <el-table-column prop="part_number" label="料号" min-width="120" />
            <el-table-column prop="name" label="名称" min-width="100" />
            <el-table-column prop="type" label="类型" width="80">
              <template #default="{ row }">
                <el-tag :type="getTypeTagType(row.type)" size="small">
                  {{ getTypeLabel(row.type) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="60" fixed="right">
              <template #default="{ row }">
                <el-button
                  type="danger"
                  link
                  size="small"
                  @click.stop="deleteMaterial(row)"
                >
                  删除
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>

      <!-- 右侧：BOM 树形结构 -->
      <el-col :span="16">
        <el-card class="bom-tree-card">
          <template #header>
            <div class="card-header">
              <span>BOM 结构</span>
              <span v-if="selectedMaterial" class="selected-material-info">
                {{ selectedMaterial.part_number }} - {{ selectedMaterial.name }}
              </span>
              <el-button
                v-if="selectedMaterial"
                type="primary"
                size="small"
                @click="openAddChildDialog"
              >
                添加子物料
              </el-button>
            </div>
          </template>

          <div v-if="!selectedMaterial" class="empty-tip">
            <el-empty description="请从左侧选择一个物料" />
          </div>

          <el-tree
            v-else
            :data="bomTree"
            :props="treeProps"
            node-key="id"
            default-expand-all
            :expand-on-click-node="false"
            class="bom-tree"
          >
            <template #default="{ node, data }">
              <div
                class="custom-tree-node"
                :class="`level-${data._level}`"
              >
                <div class="node-content">
                  <el-tag
                    :type="getLevelTagType(data._level)"
                    size="small"
                    class="level-tag"
                  >
                    L{{ data._level }}
                  </el-tag>
                  <span class="part-number">{{ data.part?.part_number }}</span>
                  <span class="part-name">{{ data.part?.name }}</span>
                  <el-tag :type="getTypeTagType(data.part?.type)" size="small">
                    {{ getTypeLabel(data.part?.type) }}
                  </el-tag>
                  <span class="quantity">×{{ data.quantity || 1 }}</span>
                </div>
                <div class="node-actions">
                  <el-button
                    type="primary"
                    link
                    size="small"
                    @click.stop="openEditQuantityDialog(data)"
                  >
                    修改数量
                  </el-button>
                  <el-button
                    type="danger"
                    link
                    size="small"
                    @click.stop="deleteBomRelation(data)"
                  >
                    删除
                  </el-button>
                </div>
              </div>
            </template>
          </el-tree>
        </el-card>
      </el-col>
    </el-row>

    <!-- 新增物料对话框 -->
    <el-dialog
      v-model="addMaterialDialogVisible"
      title="新增物料"
      width="600px"
      destroy-on-close
    >
      <el-form
        ref="materialFormRef"
        :model="materialForm"
        :rules="materialRules"
        label-width="100px"
      >
        <el-form-item label="料号性质" prop="nature_code">
          <el-select
            v-model="materialForm.nature_code"
            placeholder="请选择料号性质"
            @change="handleNatureChange"
            style="width: 100%;"
          >
            <el-option
              v-for="item in natureOptions"
              :key="item.code"
              :label="item.code + ' - ' + item.name"
              :value="item.code"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="大类" prop="category_code">
          <el-select
            v-model="materialForm.category_code"
            placeholder="请选择大类"
            style="width: 100%;"
            @change="handleCategoryChange"
          >
            <el-option
              v-for="item in categoryOptions"
              :key="item.code"
              :label="item.code + ' - ' + item.name"
              :value="item.code"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="小类" prop="subcategory_code">
          <el-select
            v-model="materialForm.subcategory_code"
            placeholder="请选择小类"
            style="width: 100%;"
            @change="updatePreview"
          >
            <el-option
              v-for="item in subcategoryOptions"
              :key="item.code"
              :label="item.code + ' - ' + item.name"
              :value="item.code"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="预览料号">
          <el-input
            v-model="previewPartNumber"
            readonly
            placeholder="自动生成的预览料号"
          />
        </el-form-item>

        <el-form-item label="名称" prop="name">
          <el-input v-model="materialForm.name" placeholder="请输入名称" />
        </el-form-item>

        <el-form-item label="规格" prop="specification">
          <el-input v-model="materialForm.specification" placeholder="请输入规格" />
        </el-form-item>

        <el-form-item label="单位" prop="unit">
          <el-input v-model="materialForm.unit" placeholder="请输入单位" />
        </el-form-item>

        <el-form-item label="描述" prop="description">
          <el-input
            v-model="materialForm.description"
            type="textarea"
            :rows="3"
            placeholder="请输入描述"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="addMaterialDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitMaterial" :loading="materialSubmitting">
          提交
        </el-button>
      </template>
    </el-dialog>

    <!-- 添加子物料对话框 -->
    <el-dialog
      v-model="addChildDialogVisible"
      title="添加子物料"
      width="500px"
      destroy-on-close
    >
      <el-form
        ref="childFormRef"
        :model="childForm"
        :rules="childRules"
        label-width="100px"
      >
        <el-form-item label="父物料">
          <el-input
            :value="selectedMaterial ? `${selectedMaterial.part_number} - ${selectedMaterial.name}` : ''"
            disabled
          />
        </el-form-item>

        <el-form-item label="子物料" prop="child_id">
          <el-select
            v-model="childForm.child_id"
            placeholder="请选择子物料"
            filterable
            style="width: 100%;"
          >
            <el-option
              v-for="m in availableChildMaterials"
              :key="m.id"
              :label="`${m.part_number} - ${m.name}`"
              :value="m.id"
            />
          </el-select>
        </el-form-item>

        <el-form-item label="数量" prop="quantity">
          <el-input-number
            v-model="childForm.quantity"
            :min="1"
            :precision="0"
            style="width: 100%;"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="addChildDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitChild" :loading="childSubmitting">
          提交
        </el-button>
      </template>
    </el-dialog>

    <!-- 修改数量对话框 -->
    <el-dialog
      v-model="editQuantityDialogVisible"
      title="修改数量"
      width="400px"
      destroy-on-close
    >
      <el-form
        ref="quantityFormRef"
        :model="quantityForm"
        :rules="quantityRules"
        label-width="80px"
      >
        <el-form-item label="物料">
          <el-input
            :value="`${editingNode?.part_number} - ${editingNode?.name}`"
            disabled
          />
        </el-form-item>

        <el-form-item label="数量" prop="quantity">
          <el-input-number
            v-model="quantityForm.quantity"
            :min="1"
            :precision="0"
            style="width: 100%;"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="editQuantityDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitQuantity" :loading="quantitySubmitting">
          提交
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import request from '../utils/request'

const API_BASE = '/api'
const DESIGNER_BASE = '/api/designer'

// ========== 辅助函数 ==========
function getTypeLabel(type) {
  const map = {
    product: '成品',
    semi_product: '半成品',
    component: '组件',
    part: '零件',
  }
  return map[type] || type
}

function getTypeTagType(type) {
  const map = {
    product: 'danger',
    semi_product: 'warning',
    component: 'primary',
    part: '',
  }
  return map[type] || ''
}

function getLevelTagType(level) {
  const map = {
    1: 'danger',
    2: 'warning',
    3: 'primary',
    4: 'success',
  }
  return map[level] || ''
}

function addLevelToTree(nodes, level = 1) {
  if (!nodes || nodes.length === 0) return
  for (const node of nodes) {
    node._level = level
    if (node.children && node.children.length > 0) {
      addLevelToTree(node.children, level + 1)
    }
  }
}

// ========== 物料列表 ==========
const materialList = ref([])
const searchType = ref('')
const searchKeyword = ref('')
const selectedMaterial = ref(null)

async function fetchMaterials() {
  try {
    const params = {}
    if (searchType.value) params.type = searchType.value
    if (searchKeyword.value) params.keyword = searchKeyword.value
    const res = await request.get(`${API_BASE}/bom/materials`, { params })
    materialList.value = res.data.items || []
  } catch (error) {
    ElMessage.error('获取物料列表失败')
  }
}

function handleMaterialClick(row) {
  selectedMaterial.value = row
  fetchBomTree(row.id)
}

async function deleteMaterial(row) {
  try {
    await ElMessageBox.confirm(
      `确定要删除物料 "${row.part_number} - ${row.name}" 吗？`,
      '确认删除',
      { type: 'warning' }
    )
    await request.delete(`${API_BASE}/bom/materials/${row.id}`)
    ElMessage.success('删除成功')
    if (selectedMaterial.value?.id === row.id) {
      selectedMaterial.value = null
      bomTree.value = []
    }
    fetchMaterials()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

// ========== BOM 树 ==========
const bomTree = ref([])
const treeProps = {
  label: 'name',
  children: 'children',
}

async function fetchBomTree(materialId) {
  try {
    const res = await request.get(`${API_BASE}/bom/tree/${materialId}`)
    const treeData = res.data?.tree || []
    addLevelToTree(treeData, 1)
    bomTree.value = treeData
  } catch (error) {
    ElMessage.error('获取 BOM 树失败')
  }
}

async function deleteBomRelation(data) {
  try {
    await ElMessageBox.confirm(
      `确定要删除 BOM 关系 "${data.part_number} - ${data.name}" 吗？`,
      '确认删除',
      { type: 'warning' }
    )
    await request.delete(`${API_BASE}/bom/${data.relation_id || data.id}`)
    ElMessage.success('删除成功')
    if (selectedMaterial.value) {
      fetchBomTree(selectedMaterial.value.id)
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

// ========== 新增物料 ==========
const addMaterialDialogVisible = ref(false)
const materialFormRef = ref(null)
const materialSubmitting = ref(false)
const partNumberRules = ref([])
const natureOptions = ref([])
const categoryOptions = ref([])
const subcategoryOptions = ref([])
const categoryValue = ref([])
const previewPartNumber = ref('')

const materialForm = reactive({
  nature_code: '',
  category_code: '',
  subcategory_code: '',
  name: '',
  specification: '',
  unit: '',
  description: '',
})

const materialRules = {
  nature_code: [{ required: true, message: '请选择料号性质', trigger: 'change' }],
  category_code: [{ required: true, message: '请选择大类', trigger: 'change' }],
  subcategory_code: [{ required: true, message: '请选择小类', trigger: 'change' }],
  name: [{ required: true, message: '请输入名称', trigger: 'blur' }],
}

async function openAddMaterialDialog() {
  addMaterialDialogVisible.value = true
  // 重置表单
  Object.assign(materialForm, {
    nature_code: '',
    category_code: '',
    subcategory_code: '',
    name: '',
    specification: '',
    unit: '',
    description: '',
  })
  subcategoryOptions.value = []
  previewPartNumber.value = ''
  await fetchPartNumberRules()
}

async function fetchPartNumberRules() {
  try {
    const res = await request.get(`${DESIGNER_BASE}/part-number-rules`)
    partNumberRules.value = res.data || []
    // 提取去重的性质列表
    const natureMap = {}
    partNumberRules.value.forEach(rule => {
      if (!natureMap[rule.nature_code]) {
        natureMap[rule.nature_code] = { code: rule.nature_code, name: rule.nature_name }
      }
    })
    natureOptions.value = Object.values(natureMap)
  } catch (error) {
    ElMessage.error('获取料号规则失败')
  }
}

function handleNatureChange() {
  materialForm.category_code = ''
  materialForm.subcategory_code = ''
  categoryValue.value = []
  subcategoryOptions.value = []
  // 根据选择的性质过滤大类
  const catMap = {}
  partNumberRules.value.forEach(rule => {
    if (rule.nature_code === materialForm.nature_code && !catMap[rule.category_code]) {
      catMap[rule.category_code] = { code: rule.category_code, name: rule.category_name }
    }
  })
  categoryOptions.value = Object.values(catMap)
  updatePreview()
}

function handleCategoryChange(val) {
  materialForm.category_code = val || ''
  materialForm.subcategory_code = ''
  if (val) {
    // 根据选择的大类过滤小类
    const subMap = {}
    partNumberRules.value.forEach(rule => {
      if (rule.nature_code === materialForm.nature_code && rule.category_code === val && !subMap[rule.subcategory_code]) {
        subMap[rule.subcategory_code] = { code: rule.subcategory_code, name: rule.subcategory_name }
      }
    })
    subcategoryOptions.value = Object.values(subMap)
  } else {
    subcategoryOptions.value = []
  }
  updatePreview()
}

async function updatePreview() {
  if (!materialForm.nature_code || !materialForm.category_code || !materialForm.subcategory_code) {
    previewPartNumber.value = ''
    return
  }
  try {
    const res = await request.get(`${DESIGNER_BASE}/part-number-preview`, {
      params: {
        nature_code: materialForm.nature_code,
        category_code: materialForm.category_code,
        subcategory_code: materialForm.subcategory_code,
      },
    })
    previewPartNumber.value = res.data?.preview || ''
  } catch (error) {
    previewPartNumber.value = ''
  }
}

async function submitMaterial() {
  const valid = await materialFormRef.value?.validate().catch(() => false)
  if (!valid) return

  materialSubmitting.value = true
  try {
    const payload = { ...materialForm }
    // 不传 part_number，后端自动生成
    delete payload.part_number
    await request.post(`${DESIGNER_BASE}/parts`, payload)
    ElMessage.success('新增物料成功')
    addMaterialDialogVisible.value = false
    fetchMaterials()
  } catch (error) {
    ElMessage.error('新增物料失败')
  } finally {
    materialSubmitting.value = false
  }
}

// ========== 添加子物料 ==========
const addChildDialogVisible = ref(false)
const childFormRef = ref(null)
const childSubmitting = ref(false)

const childForm = reactive({
  child_id: '',
  quantity: 1,
})

const childRules = {
  child_id: [{ required: true, message: '请选择子物料', trigger: 'change' }],
  quantity: [{ required: true, message: '请输入数量', trigger: 'blur' }],
}

const LEVEL_ORDER = { product: 0, semi_product: 1, component: 2, part: 3 }

function getExistingChildIds(nodes) {
  const ids = new Set()
  nodes.forEach(node => {
    if (node.part?.id) ids.add(node.part.id)
    if (node.children?.length) {
      getExistingChildIds(node.children).forEach(id => ids.add(id))
    }
  })
  return ids
}

const availableChildMaterials = computed(() => {
  if (!selectedMaterial.value) return []
  const parentLevel = LEVEL_ORDER[selectedMaterial.value.type]
  const existingIds = getExistingChildIds(bomTree.value)
  return materialList.value.filter(m => {
    const childLevel = LEVEL_ORDER[m.type]
    return m.id !== selectedMaterial.value.id && childLevel > parentLevel && !existingIds.has(m.id)
  })
})

function openAddChildDialog() {
  addChildDialogVisible.value = true
  childForm.child_id = ''
  childForm.quantity = 1
}

async function submitChild() {
  const valid = await childFormRef.value?.validate().catch(() => false)
  if (!valid) return

  childSubmitting.value = true
  try {
    await request.post(`${API_BASE}/bom`, {
      parent_id: selectedMaterial.value.id,
      child_id: childForm.child_id,
      quantity: childForm.quantity,
    })
    ElMessage.success('添加子物料成功')
    addChildDialogVisible.value = false
    fetchBomTree(selectedMaterial.value.id)
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '添加子物料失败')
  } finally {
    childSubmitting.value = false
  }
}

// ========== 修改数量 ==========
const editQuantityDialogVisible = ref(false)
const quantityFormRef = ref(null)
const quantitySubmitting = ref(false)
const editingNode = ref(null)

const quantityForm = reactive({
  quantity: 1,
})

const quantityRules = {
  quantity: [{ required: true, message: '请输入数量', trigger: 'blur' }],
}

function openEditQuantityDialog(data) {
  editingNode.value = data
  quantityForm.quantity = data.quantity || 1
  editQuantityDialogVisible.value = true
}

async function submitQuantity() {
  const valid = await quantityFormRef.value?.validate().catch(() => false)
  if (!valid) return

  quantitySubmitting.value = true
  try {
    await request.put(`${API_BASE}/bom/${editingNode.value.relation_id || editingNode.value.id}`, {
      quantity: quantityForm.quantity,
    })
    ElMessage.success('修改数量成功')
    editQuantityDialogVisible.value = false
    if (selectedMaterial.value) {
      fetchBomTree(selectedMaterial.value.id)
    }
  } catch (error) {
    ElMessage.error('修改数量失败')
  } finally {
    quantitySubmitting.value = false
  }
}

// ========== 初始化 ==========
onMounted(() => {
  fetchMaterials()
})
</script>

<style scoped>
.bom-management {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.selected-material-info {
  color: #409eff;
  font-weight: bold;
  flex: 1;
  margin: 0 16px;
  text-align: center;
}

.search-bar {
  display: flex;
  align-items: center;
}

.empty-tip {
  padding: 60px 0;
}

.bom-tree {
  height: calc(100vh - 220px);
  overflow: auto;
}

.custom-tree-node {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex: 1;
  padding: 6px 8px;
  margin-left: 4px;
  border-left: 4px solid transparent;
  border-radius: 4px;
}

.custom-tree-node.level-1 {
  border-left-color: #f56c6c;
}

.custom-tree-node.level-2 {
  border-left-color: #e6a23c;
}

.custom-tree-node.level-3 {
  border-left-color: #409eff;
}

.custom-tree-node.level-4 {
  border-left-color: #67c23a;
}

.node-content {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.level-tag {
  min-width: 36px;
  text-align: center;
}

.part-number {
  font-weight: bold;
  color: #303133;
}

.part-name {
  color: #606266;
}

.quantity {
  color: #409eff;
  font-weight: bold;
}

.node-actions {
  display: flex;
  gap: 4px;
}
</style>
