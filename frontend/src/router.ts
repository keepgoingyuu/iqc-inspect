import { createRouter, createWebHistory } from 'vue-router'
import { currentUser, loadCurrentUser } from './store'

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/login', component: () => import('./views/LoginView.vue') },
    { path: '/', component: () => import('./views/SheetListView.vue') },
    { path: '/sheets/:id', component: () => import('./views/SheetDetailView.vue') },
    { path: '/products', component: () => import('./views/ProductsView.vue') },
  ],
})

router.beforeEach(async (to) => {
  if (to.path === '/login') return true
  if (!currentUser.value) {
    await loadCurrentUser().catch(() => null)
  }
  if (!currentUser.value) return '/login'
  return true
})
