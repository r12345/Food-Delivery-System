import http from './http'

// ---------- 认证 ----------
export const getCaptcha = () => http.get('/auth/captcha')
export const login = d => http.post('/auth/login', d)
export const register = d => http.post('/auth/register', d)
export const forgotPassword = d => http.post('/auth/forgot-password', d)
export const getNotifications = () => http.get('/notifications')
export const readNotifications = () => http.post('/notifications/read')

// ---------- 公共 ----------
export const getRegions = () => http.get('/regions')
export const getDict = key => http.get(`/dicts/${key}`)
export const getHome = () => http.get('/home')

// ---------- 店铺/菜品 ----------
export const getShops = params => http.get('/shops', { params })
export const getShop = id => http.get(`/shops/${id}`)
export const getFood = id => http.get(`/foods/${id}`)
export const getShopEvaluations = (id, params) => http.get(`/shops/${id}/evaluations`, { params })

// ---------- 购物车 ----------
export const getCart = () => http.get('/cart')
export const addCart = d => http.post('/cart', d)
export const updateCart = (id, q) => http.put(`/cart/${id}`, { quantity: q })
export const removeCart = id => http.delete(`/cart/${id}`)
export const clearCart = () => http.delete('/cart')

// ---------- 订单/支付 ----------
export const createOrder = d => http.post('/orders', d)
export const getMyOrders = params => http.get('/orders', { params })
export const getOrder = id => http.get(`/orders/${id}`)
export const payOrder = (id, pay_type) => http.post(`/orders/${id}/pay`, { pay_type })
export const cancelOrder = id => http.post(`/orders/${id}/cancel`)
export const confirmOrder = id => http.post(`/orders/${id}/confirm`)
export const refundOrder = id => http.post(`/orders/${id}/refund`)

// ---------- 评价 ----------
export const createEvaluation = (id, d) => http.post(`/orders/${id}/evaluation`, d)

// ---------- 优惠券 ----------
export const getReceivableCoupons = () => http.get('/coupons')
export const receiveCoupon = id => http.post(`/coupons/${id}/receive`)

// ---------- 个人中心 ----------
export const getMe = () => http.get('/user/me')
export const updateMe = d => http.put('/user/me', d)
export const getAddresses = () => http.get('/user/addresses')
export const addAddress = d => http.post('/user/addresses', d)
export const updateAddress = (id, d) => http.put(`/user/addresses/${id}`, d)
export const deleteAddress = id => http.delete(`/user/addresses/${id}`)
export const getFavorites = () => http.get('/user/favorites')
export const addFavorite = id => http.post(`/user/favorites/${id}`)
export const removeFavorite = id => http.delete(`/user/favorites/${id}`)
export const getFavoriteStatus = id => http.get(`/user/favorites/${id}/status`)
export const getMyCoupons = params => http.get('/user/coupons', { params })
export const getMyEvaluations = () => http.get('/user/evaluations')

// ---------- 商家端 ----------
export const mGetDashboard = () => http.get('/merchant/dashboard')
export const mGetShop = () => http.get('/merchant/shop')
export const mUpdateShop = d => http.put('/merchant/shop', d)
export const mSetOpen = is_open => http.post('/merchant/shop/open', { is_open })
export const mGetCategories = () => http.get('/merchant/categories')
export const mAddCategory = d => http.post('/merchant/categories', d)
export const mUpdateCategory = (id, d) => http.put(`/merchant/categories/${id}`, d)
export const mDeleteCategory = id => http.delete(`/merchant/categories/${id}`)
export const mGetFoods = params => http.get('/merchant/foods', { params })
export const mAddFood = d => http.post('/merchant/foods', d)
export const mUpdateFood = (id, d) => http.put(`/merchant/foods/${id}`, d)
export const mDeleteFood = id => http.delete(`/merchant/foods/${id}`)
export const mGetOrders = params => http.get('/merchant/orders', { params })
export const mAcceptOrder = id => http.post(`/merchant/orders/${id}/accept`)
export const mRejectOrder = (id, reason) => http.post(`/merchant/orders/${id}/reject`, { reason })
export const mDeliverOrder = id => http.post(`/merchant/orders/${id}/deliver`)
export const mFinishOrder = id => http.post(`/merchant/orders/${id}/finish`)
export const mAgreeRefund = id => http.post(`/merchant/orders/${id}/refund-agree`)
export const mFinanceSummary = () => http.get('/merchant/finance/summary')
export const mFinanceRecords = params => http.get('/merchant/finance/records', { params })
export const mWithdraw = amount => http.post('/merchant/finance/withdraw', { amount })
export const mGetEvaluations = params => http.get('/merchant/evaluations', { params })
export const mReplyEvaluation = (id, reply) => http.post(`/merchant/evaluations/${id}/reply`, { reply })
export const mGetCoupons = () => http.get('/merchant/coupons')
export const mAddCoupon = d => http.post('/merchant/coupons', d)

// ---------- 管理端 ----------
export const aGetUsers = params => http.get('/admin/users', { params })
export const aSetUserStatus = (id, status) => http.post(`/admin/users/${id}/status`, { status })
export const aGetShops = params => http.get('/admin/shops', { params })
export const aAuditShop = (id, action) => http.post(`/admin/shops/${id}/audit`, { action })
export const aGetOrders = params => http.get('/admin/orders', { params })
export const aAgreeRefund = id => http.post(`/admin/orders/${id}/refund-agree`)
export const aGetRiders = params => http.get('/admin/riders', { params })
export const aAddRider = d => http.post('/admin/riders', d)
export const aSetRiderStatus = (id, status) => http.post(`/admin/riders/${id}/status`, { status })
export const aGetBanners = () => http.get('/admin/banners')
export const aAddBanner = d => http.post('/admin/banners', d)
export const aDeleteBanner = id => http.delete(`/admin/banners/${id}`)
export const aGetPlatformCoupons = () => http.get('/admin/coupons')
export const aAddPlatformCoupon = d => http.post('/admin/coupons', d)
export const aStatsOverview = () => http.get('/admin/stats/overview')
export const aStatsTrend = () => http.get('/admin/stats/trend')
export const aStatsHotShops = () => http.get('/admin/stats/hot-shops')
export const aStatsStatus = () => http.get('/admin/stats/status')
export const aGetAdmins = () => http.get('/admin/admins')
export const aAddAdmin = d => http.post('/admin/admins', d)
