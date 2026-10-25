<script setup lang="ts">
const shop = useShop()
const route = useRoute()
const fullName = ref('')
const email = ref('')
const password = ref('')
const confirmPassword = ref('')
const busy = ref(false)
const errorMessage = ref('')

async function submit() {
  errorMessage.value = ''
  if (password.value.length < 8) { errorMessage.value = 'Use a password with at least 8 characters.'; return }
  if (password.value !== confirmPassword.value) { errorMessage.value = 'The passwords do not match.'; return }
  busy.value = true
  try {
    await shop.register(fullName.value, email.value, password.value)
    const requested = String(route.query.redirect || '/account')
    const redirect = requested.startsWith('/') && !requested.startsWith('//') ? requested : '/account'
    await navigateTo(redirect)
  } catch (error: any) {
    errorMessage.value = error?.data?.detail || 'We could not create your account. Please try again.'
  } finally { busy.value = false }
}
onMounted(() => shop.initialize())
</script>

<template>
  <div class="form-page"><section class="form-card">
    <div class="eyebrow">WELCOME TO NOVA</div><h1>Create your account.</h1><p class="form-intro">A few details and you're in. We'll send a welcome email once your account is created.</p>
    <form @submit.prevent="submit"><div class="form-field"><label for="fullName">FULL NAME</label><input id="fullName" v-model.trim="fullName" class="field-input" autocomplete="name" required minlength="2" maxlength="120" /></div><div class="form-field"><label for="email">EMAIL ADDRESS</label><input id="email" v-model.trim="email" class="field-input" type="email" autocomplete="email" required /></div><div class="form-field"><label for="password">PASSWORD</label><input id="password" v-model="password" class="field-input" type="password" autocomplete="new-password" minlength="8" required /><small style="display:block;color:var(--muted);margin-top:7px;font-size:10px">Use at least 8 characters.</small></div><div class="form-field"><label for="confirmPassword">CONFIRM PASSWORD</label><input id="confirmPassword" v-model="confirmPassword" class="field-input" type="password" autocomplete="new-password" required /></div><div v-if="errorMessage" class="form-error" role="alert">{{ errorMessage }}</div><button class="button full-width" type="submit" :disabled="busy">{{ busy ? 'CREATING ACCOUNT…' : 'CREATE ACCOUNT ↗' }}</button></form>
    <p class="form-switch">Already have an account? <NuxtLink :to="`/auth/login${route.query.redirect ? `?redirect=${encodeURIComponent(String(route.query.redirect))}` : ''}`">Sign in</NuxtLink></p>
  </section></div>
</template>
