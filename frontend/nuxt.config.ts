export default defineNuxtConfig({
  compatibilityDate: '2025-05-15',
  devtools: { enabled: true },
  modules: ['@vercel/analytics'],
  css: ['~/assets/css/main.css'],
  runtimeConfig: {
    public: {
      apiBase: process.env.NUXT_PUBLIC_API_BASE || 'http://localhost:8000/api',
      currency: process.env.NUXT_PUBLIC_CURRENCY || 'EGP',
      storeName: 'NOVA'
    }
  },
  app: {
    head: {
      title: 'NOVA — Home, appliances and everyday tech',
      meta: [
        { name: 'description', content: 'Home appliances, kitchen machines and consumer electronics for better everyday living.' },
        { name: 'theme-color', content: '#f5f4ef' }
      ],
      link: [{ rel: 'preconnect', href: 'https://images.unsplash.com' }]
    }
  }
})
