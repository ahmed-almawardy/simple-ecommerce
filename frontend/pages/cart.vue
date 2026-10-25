<script setup lang="ts">
const shop = useShop()
const { cart, cartCount, subtotalCents } = shop
const ready = ref(false)
onMounted(async () => { await shop.initialize(); ready.value = true })
</script>

<template>
  <div>
    <div class="page-head"><div class="breadcrumb"><NuxtLink to="/">HOME</NuxtLink> &nbsp;/&nbsp; YOUR CART</div><h1 class="page-title">Your cart.</h1><p class="page-subtitle">Review your items before heading to checkout.</p></div>
    <div v-if="!ready" class="cart-layout"><p class="loading-text">Getting your cart ready…</p></div>
    <div v-else-if="!cart.length" class="section" style="text-align:center;min-height:300px"><div class="eyebrow">NOTHING IN HERE YET</div><h2 class="section-title" style="margin:15px 0">Room for something good.</h2><p class="section-note" style="margin:0 auto 25px">Explore home appliances and technology for your home.</p><NuxtLink to="/products" class="button">SHOP THE STORE ↗</NuxtLink></div>
    <div v-else class="cart-layout">
      <section><h2 class="cart-title">Your items<span style="color:#2467a9">.</span></h2><p class="cart-subtitle">{{ cartCount }} item{{ cartCount === 1 ? '' : 's' }} in your cart</p>
        <article v-for="line in cart" :key="line.product.id" class="cart-line">
          <NuxtLink :to="`/products/${line.product.slug}`" class="cart-line-image"><img :src="line.product.image_url" :alt="line.product.name" /></NuxtLink>
          <div><NuxtLink :to="`/products/${line.product.slug}`" class="cart-line-name">{{ line.product.name }}</NuxtLink><p class="cart-line-category">{{ line.product.category }}</p><span class="cart-line-price">{{ shop.formatPrice(line.product.price_cents) }}</span><div class="quantity-control"><button :aria-label="`Decrease ${line.product.name} quantity`" @click="shop.setQuantity(line.product.id, line.quantity - 1)">−</button><span>{{ line.quantity }}</span><button :aria-label="`Increase ${line.product.name} quantity`" :disabled="line.quantity >= Math.min(line.product.stock, 20)" @click="shop.setQuantity(line.product.id, line.quantity + 1)">+</button></div><button class="remove-button" @click="shop.removeFromCart(line.product.id)">Remove</button></div>
          <div class="cart-line-total">{{ shop.formatPrice(line.product.price_cents * line.quantity) }}</div>
        </article>
        <NuxtLink to="/products" class="text-link" style="margin-top:25px">← KEEP EXPLORING</NuxtLink>
      </section>
      <aside class="summary-card"><h2>Order summary</h2><div class="summary-row"><span>Subtotal</span><span>{{ shop.formatPrice(subtotalCents) }}</span></div><div class="summary-row"><span>Shipping</span><span>Complimentary</span></div><div class="summary-row"><span>Taxes</span><span>Not calculated in demo</span></div><div class="summary-row total"><span>Estimated total</span><span>{{ shop.formatPrice(subtotalCents) }}</span></div><p class="summary-note">Secure, hosted checkout. Your payment details are handled by the payment provider, not stored by NOVA.</p><NuxtLink to="/checkout" class="button full-width">CONTINUE TO CHECKOUT ↗</NuxtLink><div style="text-align:center;margin-top:18px;font-size:9px;color:var(--muted);letter-spacing:.08em">VISA · MASTERCARD · MORE</div></aside>
    </div>
  </div>
</template>
