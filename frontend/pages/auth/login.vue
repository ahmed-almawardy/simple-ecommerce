<script setup lang="ts">
const shop = useShop()
const route = useRoute()
const email = ref('')
const password = ref('')
const busy = ref(false)
const errorMessage = ref('')

async function submit() {
  busy.value = true
  errorMessage.value = ''
  try {
    await shop.login(email.value, password.value)
    const requested = String(route.query.redirect || '/account')
    const redirect = requested.startsWith('/') && !requested.startsWith('//') ? requested : '/account'
    await navigateTo(redirect)
  } catch (error: any) {
    errorMessage.value = error?.data?.detail || 'Sign in failed. Please check your details and try again.'
  } finally { busy.value = false }
}
onMounted(() => shop.initialize())
</script>

<template>
  <div class="form-page"><section class="form-card">
    <div class="eyebrow">GOOD TO SEE YOU AGAIN</div><h1>Welcome back.</h1><p class="form-intro">Sign in to sync your cart and manage your orders in one place.</p>
    <form @submit.prevent="submit"><div class="form-field"><label for="email">EMAIL ADDRESS</label><input id="email" v-model.trim="email" class="field-input" type="email" autocomplete="email" required /></div><div class="form-field"><label for="password">PASSWORD</label><input id="password" v-model="password" class="field-input" type="password" autocomplete="current-password" required /></div><div v-if="errorMessage" class="form-error" role="alert">{{ errorMessage }}</div><button class="button full-width" type="submit" :disabled="busy">{{ busy ? 'SIGNING YOU IN…' : 'SIGN IN ↗' }}</button></form>
    <p class="form-switch">New to NOVA? <NuxtLink :to="`/auth/register${route.query.redirect ? `?redirect=${encodeURIComponent(String(route.query.redirect))}` : ''}`">Create an account</NuxtLink></p>
  </section></div>
</template>
