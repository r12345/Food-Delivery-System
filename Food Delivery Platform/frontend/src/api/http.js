import axios from 'axios'
import { ElMessage } from 'element-plus'

const http = axios.create({ baseURL: '/api', timeout: 15000 })

http.interceptors.request.use(cfg => {
  const t = localStorage.getItem('token')
  if (t) cfg.headers.Authorization = 'Bearer ' + t
  return cfg
})

http.interceptors.response.use(
  res => res.data,
  err => {
    const status = err.response?.status
    let detail = err.response?.data?.detail
    if (typeof detail !== 'string') detail = '请求失败'
    if (status === 401) {
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      if (!location.pathname.startsWith('/login')) {
        ElMessage.warning('登录已过期，请重新登录')
        setTimeout(() => (location.href = '/login'), 600)
        return new Promise(() => {})
      }
    } else {
      ElMessage.error(detail)
    }
    return Promise.reject(err)
  }
)

export default http
