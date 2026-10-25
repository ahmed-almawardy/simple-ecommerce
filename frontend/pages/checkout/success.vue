<script setup lang="ts">
const shop = useShop()
const route = useRoute()
const order = ref<any>(null)
const state = ref<'loading' | 'paid' | 'pending' | 'error' | 'login'>('loading')
const canceled = ref(false)
let stopped = false

async function checkPayment() {
  const rawId = String(route.query.order_id || '')
  if (!/^\d+$/.test(rawId)) { state.value = 'error'; return }
  if (!shop.token.value) { state.value = 'login'; return }
  for (let attempt = 0; attempt < 25 && !stopped; attempt++) {
    try {
      order.value = await shop.api(`/orders/${rawId}`)
      if (order.value.status === 'paid') {
        state.value = 'paid'
        shop.cart.value = []
        if (import.meta.client) localStorage.setItem('nova_cart', '[]')
        return
      }
      state.value = 'pending'
    } catch {
      state.value = 'error'
      return
    }
    await new Promise((resolve) => setTimeout(resolve, 2200))
  }
  if (!stopped && state.value !== 'paid') state.value = 'pending'
}

onMounted(async () => { await shop.initialize(); await checkPayment() })
onBeforeUnmount(() => { stopped = true })
</script>

<template>
  <div class="form-page"><section class="form-card">
    <template v-if="state === 'loading'"><p class="eyebrow">PAYMENT STATUS</p><h1>Confirming your order.</h1><p class="form-intro">We're checking the secure payment result.</p></template>
    <template v-else-if="state === 'paid'"><div class="success-mark">✓</div><p class="eyebrow">PAYMENT CONFIRMED</p><h1>You're all set.</h1><p class="form-intro">Order #{{ order.id }} is paid. A confirmation email has been sent if email delivery is configured.</p><div class="summary-row total"><span>Paid</span><span>{{ shop.formatPrice(order.amount_cents, order.currency.toUpperCase()) }}</span></div><NuxtLink to="/account" class="button full-width" style="margin-top:20px">VIEW YOUR ORDERS ↗</NuxtLink></template>
    <template v-else-if="state === 'pending'"><p class="eyebrow">PAYMENT PROCESSING</p><h1>Almost there.</h1><p class="form-intro">Your payment provider is still confirming order #{{ route.query.order_id }}. Refresh your account in a moment. Do not pay again while the provider is still processing the first attempt.</p><NuxtLink to="/account" class="button full-width">VIEW MY ACCOUNT ↗</NuxtLink></template>
    <template v-else-if="state === 'login'"><p class="eyebrow">ORDER LOOKUP</p><h1>Sign in to view your order.</h1><p class="form-intro">Your payment may have completed, but this session is not signed in. Sign in with the account used at checkout.</p><NuxtLink :to="`/auth/login?redirect=${encodeURIComponent(route.fullPath)}`" class="button full-width">SIGN IN ↗</NuxtLink></template>
    <template v-else><p class="eyebrow">ORDER LOOKUP</p><h1>We couldn't verify this order.</h1><p class="form-intro">The payment provider may still be processing, or the order link may be incomplete. Check your email and account before trying to pay again.</p><NuxtLink to="/account" class="button full-width">GO TO MY ACCOUNT ↗</NuxtLink></template>
  </section></div>
</template>
