<script setup lang="ts">
import type { Product } from '~/composables/useShop'
const shop = useShop()
const route = useRoute()
const products = ref<Product[]>([])
const categories = ref<string[]>([])
const loading = ref(true)
const errorMessage = ref('')
const category = ref(String(route.query.category || 'all'))
const search = ref(String(route.query.q || ''))
const sort = ref('featured')
const minPrice = ref('')
const maxPrice = ref('')

async function loadProducts() {
  loading.value = true
  errorMessage.value = ''
  const params = new URLSearchParams()
  if (category.value && category.value !== 'all') params.set('category', category.value)
  if (search.value.trim()) params.set('q', search.value.trim())
  if (minPrice.value !== '') params.set('min_price', minPrice.value)
  if (maxPrice.value !== '') params.set('max_price', maxPrice.value)
  params.set('sort', sort.value)
  try { products.value = await shop.api<Product[]>(`/products?${params.toString()}`) }
  catch (error: any) { errorMessage.value = error?.data?.detail || 'The shop API is not reachable. Start the FastAPI backend and try again.'; products.value = [] }
  finally { loading.value = false }
}

onMounted(async () => {
  await shop.initialize()
  try { categories.value = await shop.api<string[]>('/products/categories') } catch { categories.value = ['Major Appliances', 'Kitchen Appliances', 'TV & Audio', 'Phones & Computing', 'Watches & Wearables', 'Smart Home'] }
  await loadProducts()
})
watch(() => route.query.category, (value) => { category.value = String(value || 'all'); if (import.meta.client) loadProducts() })
watch(sort, () => { if (import.meta.client) loadProducts() })
</script>

<template>
  <div>
    <div class="page-head"><div class="breadcrumb"><NuxtLink to="/">HOME</NuxtLink> &nbsp;/&nbsp; THE STORE</div><h1 class="page-title">Better living<br>starts here.</h1><p class="page-subtitle">Shop home appliances, kitchen machines, televisions, audio, phones, computers and wearables in one place.</p></div>
    <div class="shop-layout">
      <aside class="filter-sidebar">
        <div class="filter-group"><h3>CATEGORY</h3><label class="filter-option"><input v-model="category" type="radio" value="all" @change="loadProducts" /> All products</label><label v-for="item in categories" :key="item" class="filter-option"><input v-model="category" type="radio" :value="item" @change="loadProducts" /> {{ item }}</label></div>
        <div class="filter-group"><h3>PRICE RANGE (EGP)</h3><div class="filter-price-row"><input v-model="minPrice" class="filter-input" type="number" min="0" placeholder="Min" @keyup.enter="loadProducts" /><input v-model="maxPrice" class="filter-input" type="number" min="0" placeholder="Max" @keyup.enter="loadProducts" /></div><button class="text-link" style="margin-top:14px;background:none;border-top:0;border-left:0;border-right:0" @click="loadProducts">APPLY PRICE ↗</button></div>
        <div class="filter-group"><h3>NEED A RESET?</h3><button class="text-link" style="background:none;border:0;border-bottom:1px solid currentColor;padding:0 0 5px" @click="category='all';search='';minPrice='';maxPrice='';sort='featured';loadProducts()">CLEAR ALL FILTERS</button></div>
      </aside>
      <section class="shop-main">
        <div class="shop-toolbar"><span class="results-count">{{ loading ? 'Updating collection…' : `${products.length} item${products.length === 1 ? '' : 's'}` }}</span><input v-model="search" class="search-field" placeholder="Search appliances and technology…" @keyup.enter="loadProducts" /><select v-model="sort" class="sort-select" aria-label="Sort products"><option value="featured">Sort: Featured</option><option value="newest">Newest</option><option value="price_asc">Price: Low to high</option><option value="price_desc">Price: High to low</option><option value="name">Name A–Z</option></select></div>
        <div v-if="loading" class="loading-text">Finding the right product…</div>
        <div v-else-if="errorMessage" class="empty-state"><p>{{ errorMessage }}</p><button class="button" @click="loadProducts">TRY AGAIN ↻</button></div>
        <div v-else-if="products.length" class="product-grid"><ProductCard v-for="(product,index) in products" :key="product.id" :product="product" :index="index" /></div>
        <div v-else class="empty-state"><p class="eyebrow">NO MATCHES THIS TIME</p><h2>Try a different filter.</h2><p class="section-note" style="margin:0 auto 20px">Adjust your category, search or price range to see more products.</p><button class="button button-outline" @click="category='all';search='';minPrice='';maxPrice='';loadProducts()">CLEAR FILTERS</button></div>
      </section>
    </div>
  </div>
</template>
