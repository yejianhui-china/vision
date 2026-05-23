// ========================================================
// Vue Router 配置
// 文件: frontend/src/router/index.js
// ========================================================

import { createRouter, createWebHashHistory } from 'vue-router'
import { ElMessage } from 'element-plus'
import Login from '../views/Login.vue'
import UserManagement from '../views/UserManagement.vue'
import Designer from '../views/Designer.vue'

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: Login,
    meta: { public: true, title: '登录' }
  },
  {
    path: '/',
    redirect: '/users'
  },
  {
    path: '/users',
    name: 'UserManagement',
    component: UserManagement,
    meta: { title: '用户管理', requiresAuth: true, roles: ['admin'] }
  },
  {
    path: '/designer',
    name: 'Designer',
    component: Designer,
    meta: { title: '销售预测管理', requiresAuth: true, roles: ['designer', 'admin'] }
  }
]

const router = createRouter({
  history: createWebHashHistory(),
  routes
})

/**
 * 获取用户有权限访问的第一个路由路径
 */
function getFirstAccessibleRoute(role) {
  const accessible = routes.find(
    r => r.path !== '/' && r.path !== '/login' && r.meta?.roles?.includes(role)
  )
  return accessible ? accessible.path : null
}

// 路由守卫
router.beforeEach((to, from, next) => {
  // 设置页面标题
  document.title = to.meta.title ? `${to.meta.title} - 生产管理系统` : '生产管理系统'

  const token = localStorage.getItem('token')
  const userStr = localStorage.getItem('user')
  const user = userStr ? JSON.parse(userStr) : null
  const role = user?.role

  // ========== 1. 公开页面（登录页）==========
  if (to.meta.public) {
    // 已登录用户访问登录页，自动跳转到有权限的页面
    if (to.path === '/login' && token && role) {
      const target = getFirstAccessibleRoute(role)
      if (target) {
        next(target)
        return
      }
    }
    next()
    return
  }

  // ========== 2. 需要登录 ==========
  if (!token) {
    next('/login')
    return
  }

  // ========== 3. 角色权限检查 ==========
  if (to.meta.roles && !to.meta.roles.includes(role)) {
    ElMessage.error('您没有权限访问该页面')
    // 清除登录状态，强制回登录页
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    next('/login')
    return
  }

  next()
})

export default router
