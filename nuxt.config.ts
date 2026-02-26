// nuxt.config.ts
export default defineNuxtConfig({
  modules: ['@nuxtjs/supabase'],
  
  // supabase 模組的設定，告訴它不要強制所有頁面都要登入才能看
  supabase: {
    redirect: false 
  }
})