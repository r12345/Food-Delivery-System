import { createRouter, createWebHistory } from 'vue-router'
import { useAuth } from '../stores/auth'

const routes = [
  { path: '/login', component: () => import('../views/user/Login.vue') },
  {
    path: '/',
    component: () => import('../layouts/UserLayout.vue'),
    children: [
      { path: '', component: () => import('../views/user/Home.vue') },
      { path: 'shop/:id', component: () => import('../views/user/Shop.vue') },
      { path: 'checkout', component: () => import('../views/user/Checkout.vue') },
      { path: 'orders', component: () => import('../views/user/Orders.vue') },
      { path: 'address', component: () => import('../views/user/Address.vue') },
      { path: 'profile', component: () => import('../views/user/Profile.vue') }
    ]
  },
  {
    path: '/merchant',
    component: () => import('../layouts/MerchantLayout.vue'),
    meta: { role: 'merchant' },
    children: [
      { path: '', component: () => import('../views/merchant/Dashboard.vue') },
      { path: 'shop', component: () => import('../views/merchant/ShopInfo.vue') },
      { path: 'foods', component: () => import('../views/merchant/Foods.vue') },
      { path: 'orders', component: () => import('../views/merchant/Orders.vue') },
      { path: 'finance', component: () => import('../views/merchant/Finance.vue') },
      { path: 'reviews', component: () => import('../views/merchant/Reviews.vue') },
      { path: 'coupons', component: () => import('../views/merchant/Coupons.vue') }
    ]
  },
  {
    path: '/admin',
    component: () => import('../layouts/AdminLayout.vue'),
    meta: { role: 'admin' },
    children: [
      { path: '', component: () => import('../views/admin/Dashboard.vue') },
      { path: 'users', component: () => import('../views/admin/Users.vue') },
      { path: 'merchants', component: () => import('../views/admin/Merchants.vue') },
      { path: 'orders', component: () => import('../views/admin/Orders.vue') },
      { path: 'riders', component: () => import('../views/admin/Riders.vue') },
      { path: 'marketing', component: () => import('../views/admin/Marketing.vue') },
      { path: 'admins', component: () => import('../views/admin/Admins.vue') }
    ]
  },
  { path: '/:pathMatch(.*)*', redirect: '/' }
]

const router = createRouter({ history: createWebHistory(), routes })

router.beforeEach(to => {
  const auth = useAuth()
  if (to.meta.role) {
    if (!auth.isLogged || auth.role !== to.meta.role) return '/login'
  }
  if (to.path === '/login' && auth.isLogged) {
    if (auth.role === 'merchant') return '/merchant'
    if (auth.role === 'admin') return '/admin'
    return '/'
  }
})

export default router
