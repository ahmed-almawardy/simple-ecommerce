export interface Product {
  id: number
  slug: string
  name: string
  description: string
  price_cents: number
  category: string
  image_url: string
  is_featured: boolean
  stock: number
}

export interface User {
  id: number
  email: string
  full_name: string
  created_at: string
}

export interface CartLine {
  product: Product
  quantity: number
}

type AuthResponse = { access_token: string; token_type: string; user: User }
type CartResponse = { items: CartLine[]; subtotal_cents: number; item_count: number }

export const useShop = () => {
  const config = useRuntimeConfig()
  const token = useCookie<string | null>('nova_access_token', { sameSite: 'lax', secure: !import.meta.dev })
  const user = useState<User | null>('nova_user', () => null)
  const cart = useState<CartLine[]>('nova_cart', () => [])
  const initialized = useState<boolean>('nova_cart_initialized', () => false)
  const notice = useState<string>('nova_notice', () => '')

  const cartCount = computed(() => cart.value.reduce((sum, line) => sum + line.quantity, 0))
  const subtotalCents = computed(() => cart.value.reduce((sum, line) => sum + line.product.price_cents * line.quantity, 0))

  async function api<T>(path: string, options: Record<string, any> = {}): Promise<T> {
    const headers: Record<string, string> = { ...((options.headers || {}) as Record<string, string>) }
    if (token.value) headers.Authorization = `Bearer ${token.value}`
    return await $fetch<T>(`${String(config.public.apiBase).replace(/\/$/, '')}${path}`, { ...options, headers })
  }

  function saveLocalCart() {
    if (!import.meta.client) return
    localStorage.setItem('nova_cart', JSON.stringify(cart.value))
  }

  function loadLocalCart() {
    if (!import.meta.client || initialized.value) return
    try {
      const value = localStorage.getItem('nova_cart')
      if (value) {
        const parsed = JSON.parse(value)
        if (Array.isArray(parsed)) cart.value = parsed
      }
    } catch {
      localStorage.removeItem('nova_cart')
    }
    initialized.value = true
  }

  async function refreshCartFromApi() {
    const data = await api<CartResponse>('/cart')
    cart.value = data.items || []
    saveLocalCart()
  }

  async function syncCartToApi() {
    if (!token.value) return
    for (const line of [...cart.value]) {
      await api(`/cart/items/${line.product.id}`, { method: 'PUT', body: { quantity: line.quantity } })
    }
    await refreshCartFromApi()
  }

  async function initialize() {
    if (!import.meta.client) return
    loadLocalCart()
    if (token.value) {
      try {
        if (!user.value) user.value = await api<User>('/auth/me')
        await refreshCartFromApi()
      } catch {
        token.value = null
        user.value = null
      }
    }
  }

  async function addToCart(product: Product, quantity = 1) {
    loadLocalCart()
    const existing = cart.value.find((line) => line.product.id === product.id)
    const nextQty = Math.min(product.stock, 20, (existing?.quantity || 0) + quantity)
    if (nextQty < 1) return
    if (existing) existing.quantity = nextQty
    else cart.value.push({ product, quantity: nextQty })
    saveLocalCart()
    notice.value = `${product.name} added to your cart.`
    if (token.value) {
      try {
        await api(`/cart/items/${product.id}`, { method: 'PUT', body: { quantity: nextQty } })
      } catch (error: any) {
        notice.value = error?.data?.detail || 'Saved locally. Sign in again to sync your cart.'
      }
    }
    if (import.meta.client) window.setTimeout(() => { notice.value = '' }, 3000)
  }

  async function setQuantity(productId: number, quantity: number) {
    loadLocalCart()
    const row = cart.value.find((line) => line.product.id === productId)
    if (!row) return
    if (quantity <= 0) {
      cart.value = cart.value.filter((line) => line.product.id !== productId)
    } else {
      row.quantity = Math.min(quantity, row.product.stock, 20)
    }
    saveLocalCart()
    if (token.value) {
      try {
        await api(`/cart/items/${productId}`, { method: 'PUT', body: { quantity: quantity <= 0 ? 0 : row.quantity } })
        await refreshCartFromApi()
      } catch (error: any) {
        notice.value = error?.data?.detail || 'Could not sync your cart with the server.'
      }
    }
  }

  async function removeFromCart(productId: number) {
    await setQuantity(productId, 0)
  }

  async function login(email: string, password: string) {
    loadLocalCart()
    const response = await api<AuthResponse>('/auth/login', { method: 'POST', body: { email, password } })
    token.value = response.access_token
    user.value = response.user
    await syncCartToApi()
  }

  async function register(full_name: string, email: string, password: string) {
    loadLocalCart()
    const response = await api<AuthResponse>('/auth/register', { method: 'POST', body: { full_name, email, password } })
    token.value = response.access_token
    user.value = response.user
    await syncCartToApi()
  }

  function logout() {
    token.value = null
    user.value = null
    notice.value = 'You have signed out.'
    if (import.meta.client) window.setTimeout(() => { notice.value = '' }, 2500)
  }

  function formatPrice(cents: number, currency?: string) {
    const activeCurrency = currency || String(config.public.currency || 'EGP').toUpperCase()
    return new Intl.NumberFormat('en-US', { style: 'currency', currency: activeCurrency, maximumFractionDigits: 2 }).format(cents / 100)
  }

  return { token, user, cart, cartCount, subtotalCents, notice, api, initialize, addToCart, setQuantity, removeFromCart, login, register, logout, formatPrice, refreshCartFromApi }
}
