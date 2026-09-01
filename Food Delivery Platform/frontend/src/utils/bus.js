// 轻量事件总线
const handlers = {}

export default {
  on(event, fn) {
    (handlers[event] = handlers[event] || []).push(fn)
  },
  off(event, fn) {
    handlers[event] = (handlers[event] || []).filter(f => f !== fn)
  },
  emit(event, data) {
    (handlers[event] || []).forEach(fn => fn(data))
  }
}
