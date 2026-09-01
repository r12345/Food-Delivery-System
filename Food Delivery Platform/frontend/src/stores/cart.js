import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getCart } from '../api'

export const useCart = defineStore('cart', () => {
  const count = ref(0)
  const groups = ref([])

  async function refresh() {
    try {
      const res = await getCart()
      groups.value = res.list
      count.value = res.list.reduce((s, g) => s + g.items.reduce((a, i) => a + i.quantity, 0), 0)
    } catch { /* 未登录时忽略 */ }
  }
  function setCount(c) { count.value = c }

  return { count, groups, refresh, setCount }
})
