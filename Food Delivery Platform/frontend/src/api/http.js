import axios from 'axios'
import { ElMessage } from 'element-plus'

const http = axios.create({ baseURL: '/api', timeout: 15000 })

http.interceptors.request.use(cfg => {
  const t = localStorage.getItem('token')
  if (t) cfg.headers.Authorization = 'Bearer ' + t
  return cfg
})

// 防止并发 401 时弹出多条提示 / 多次跳转
let redirecting = false

http.interceptors.response.use(
  res => res.data,
  err => {
    const status = err.response?.status
    let detail = err.response?.data?.detail
    if (Array.isArray(detail)) {
      // FastAPI 参数校验错误为数组，取第一条可读信息
      detail = detail[0]?.msg || '请求参数有误'
    }
    if (typeof detail !== 'string') detail = '请求失败'

    if (status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      if (!redirecting && !location.pathname.startsWith('/login')) {
        redirecting = true
        ElMessage.warning('登录已过期，请重新登录')
        setTimeout(() => { location.href = '/login' }, 600)
      }
      return Promise.reject(err)
    }
    ElMessage.error(detail)
    return Promise.reject(err)
  }
)

export default http

