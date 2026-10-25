<script setup lang="ts">
const shop = useShop()
const { token, cart, cartCount, subtotalCents } = shop
const route = useRoute()
const ready = ref(false)
const busy = ref(false)
const errorMessage = ref('')
const form = reactive({ shipping_name: '', shipping_address: '', shipping_phone: '', shipping_city: '', shipping_country: 'EG' })
onMounted(async () => {
  await shop.initialize()
  if (shop.user.value) form.shipping_name = shop.user.value.full_name
  ready.value = true
})

async function beginCheckout() {
  errorMessage.value = ''
  if (!token.value) {
    await navigateTo('/auth/login?redirect=/checkout')
    return
  }
  if (!cartCount.value) {
    errorMessage.value = 'Your cart is empty. Add a product before checkout.'
    return
  }
  busy.value = true
  try {
    const response = await shop.api<{ checkout_url: string; order_id: number }>('/checkout/session', { method: 'POST', body: form })
    if (import.meta.client) window.location.assign(response.checkout_url)
  } catch (error: any) {
    errorMessage.value = error?.data?.detail || 'We could not start checkout. Please try again.'
    busy.value = false
  }
}
</script>

<template>
  <div>
    <div class="page-head"><div class="breadcrumb"><NuxtLink to="/cart">YOUR CART</NuxtLink> &nbsp;/&nbsp; CHECKOUT</div><h1 class="page-title">The final step.</h1><p class="page-subtitle">Add your delivery details, then continue to the secure payment page.</p></div>
    <div v-if="route.query.canceled" class="section" style="padding-bottom:0"><div class="form-error">Payment was canceled. Your cart is still saved, so you can try again when you're ready.</div></div>
    <div v-if="!ready" class="checkout-grid"><p class="loading-text">Preparing checkout…</p></div>
    <div v-else-if="!cartCount" class="section" style="text-align:center"><h2 class="section-title">Your cart is empty.</h2><NuxtLink to="/products" class="button" style="margin-top:20px">SHOP THE STORE ↗</NuxtLink></div>
    <div v-else class="checkout-grid">
      <section><div class="eyebrow">DELIVERY DETAILS</div><h1 style="margin-top:12px">Where should it go?</h1><p class="checkout-hint">Your details are used only to process this order and delivery.</p>
        <div v-if="!token" class="form-error">Please sign in or create an account before checking out, so we can connect the order to you.</div>
        <form @submit.prevent="beginCheckout">
          <div class="form-field"><label for="shipping_name">FULL NAME</label><input id="shipping_name" v-model.trim="form.shipping_name" class="field-input" required minlength="2" maxlength="120" autocomplete="name" /></div>
          <div class="form-field"><label for="shipping_phone">MOBILE NUMBER</label><input id="shipping_phone" v-model.trim="form.shipping_phone" class="field-input" type="tel" autocomplete="tel" placeholder="+20 1xx xxx xxxx" required minlength="7" maxlength="40" /></div>
          <div class="form-field"><label for="shipping_address">DELIVERY ADDRESS</label><textarea id="shipping_address" v-model.trim="form.shipping_address" class="field-input textarea" required minlength="5" maxlength="500" autocomplete="street-address" placeholder="Street, building, area" /></div>
          <div class="form-field"><label for="shipping_city">CITY / GOVERNORATE</label><input id="shipping_city" v-model.trim="form.shipping_city" class="field-input" required minlength="2" maxlength="100" placeholder="Cairo, Giza, Alexandria…" autocomplete="address-level2" /></div>
          <div class="form-field"><label for="shipping_country">COUNTRY</label><select id="shipping_country" v-model="form.shipping_country" class="field-input" required><option value="EG">Egypt</option></select></div>
          <div v-if="errorMessage" class="form-error" role="alert">{{ errorMessage }}</div>
          <button class="button" type="submit" :disabled="busy || !form.shipping_name || !form.shipping_address || !form.shipping_phone || !form.shipping_city" style="min-width:230px">{{ busy ? 'CONNECTING TO SECURE CHECKOUT…' : 'CONTINUE TO PAYMENT ↗' }}</button>
        </form>
        <div class="secure-note"><span>◈</span><span>Payment details are handled by the payment provider. NOVA does not store your card number.</span></div>
      </section>
      <aside class="summary-card"><h2>Your order</h2><div v-for="line in cart" :key="line.product.id" class="summary-row"><span>{{ line.product.name }} × {{ line.quantity }}</span><span>{{ shop.formatPrice(line.product.price_cents * line.quantity) }}</span></div><div class="summary-row"><span>Shipping</span><span>Free</span></div><div class="summary-row total"><span>Total</span><span>{{ shop.formatPrice(subtotalCents) }}</span></div><p class="summary-note">Taxes and delivery rules are not calculated in this demo. Configure them for your market before going live.</p><NuxtLink to="/cart" class="text-link">← EDIT YOUR CART</NuxtLink></aside>
    </div>
  </div>
</template>
