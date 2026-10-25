<script setup lang="ts">
const shop = useShop()
const { user, token } = shop
const orders = ref<any[]>([])
function formatOrderItems(items: any[]) { return items.map((item) => `${item.product_name} × ${item.quantity}`).join(', ') }
const ready = ref(false)
const errorMessage = ref('')
onMounted(async () => {
  await shop.initialize()
  if (token.value) {
    try { orders.value = await shop.api<any[]>('/orders') }
    catch (error: any) { errorMessage.value = error?.data?.detail || 'Could not load your orders.' }
  }
  ready.value = true
})
async function signOut() {
  shop.logout()
  orders.value = []
  await navigateTo('/')
}
</script>

<template>
  <div>
    <div class="page-head"><div class="breadcrumb"><NuxtLink to="/">HOME</NuxtLink> &nbsp;/&nbsp; ACCOUNT</div><h1 class="page-title">Your NOVA account.</h1><p class="page-subtitle">Your account, orders and saved cart.</p></div>
    <div v-if="!ready" class="account-layout"><p class="loading-text">Loading your account…</p></div>
    <div v-else-if="!user" class="section" style="text-align:center"><div class="eyebrow">YOUR SPACE IS WAITING</div><h2 class="section-title" style="margin:15px 0">Sign in to pick up where you left off.</h2><p class="section-note" style="margin:0 auto 25px">Access your order history and sync your cart across sessions.</p><NuxtLink to="/auth/login" class="button">SIGN IN ↗</NuxtLink><NuxtLink to="/auth/register" class="text-link" style="margin-left:20px">CREATE ACCOUNT</NuxtLink></div>
    <div v-else class="account-layout">
      <div class="account-head"><div><div class="eyebrow">ACCOUNT DETAILS</div><h1>Hi, {{ user.full_name.split(' ')[0] }}.</h1><p class="account-email">{{ user.email }}</p></div><button class="button button-outline" @click="signOut">SIGN OUT</button></div>
      <section style="margin-top:55px"><div class="section-head"><div><div class="eyebrow">YOUR HISTORY</div><h2 class="section-title" style="font-size:35px;margin-top:10px">Orders.</h2></div><NuxtLink to="/products" class="text-link">KEEP SHOPPING ↗</NuxtLink></div>
        <div v-if="errorMessage" class="form-error">{{ errorMessage }}</div>
        <div v-else-if="!orders.length" class="empty-state"><h2>No orders yet.</h2><p class="section-note" style="margin:0 auto 20px">Your next favorite thing is out there.</p><NuxtLink to="/products" class="button">EXPLORE THE COLLECTION ↗</NuxtLink></div>
        <article v-for="order in orders" :key="order.id" class="order-card"><div><strong>Order #{{ order.id }}</strong><p class="order-meta">{{ new Date(order.created_at).toLocaleDateString() }} · {{ formatOrderItems(order.items) }}</p><p class="order-meta">Ship to: {{ order.shipping_address }}</p></div><div style="text-align:right"><span class="status-pill">{{ order.status.replace('_', ' ') }}</span><p style="font-weight:800;font-size:13px">{{ shop.formatPrice(order.amount_cents, order.currency.toUpperCase()) }}</p></div></article>
      </section>
    </div>
  </div>
</template>
