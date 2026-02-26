<template>
  <div class="bind-container">
    <div class="bind-card">
      <div class="card-header">
        <h2>👨‍👩‍👧 家長系統通知綁定</h2>
        <p>請選擇您的孩子並完成身分驗證，以便接收出缺席與緊急通知。</p>
      </div>

      <form @submit.prevent="submitBinding" class="bind-form">
        <div class="form-group">
          <label for="student">👩‍🎓 選擇學生</label>
          <select id="student" v-model="selectedStudentId" required :disabled="isLoading">
            <option value="" disabled selected>請選擇座號與姓名...</option>
            <option v-for="student in students" :key="student.id" :value="student.id">
              {{ student.seat_number }}號 - {{ student.hidden_name }}
            </option>
          </select>
        </div>

        <div class="form-group">
          <label for="birthday">🎂 學生生日 (身分驗證)</label>
          <input 
            id="birthday" 
            v-model="studentBirthday" 
            type="text" 
            placeholder="請輸入西元生日 (例如: 20130514)" 
            required 
            :disabled="isLoading"
          />
        </div>

        <div class="form-group">
          <label for="email">✉️ 您的 Email 信箱</label>
          <input 
            id="email" 
            v-model="parentEmail" 
            type="email" 
            placeholder="例如: example@gmail.com" 
            required 
            :disabled="isLoading"
          />
        </div>

        <div v-if="sysMessage.text" :class="['message-box', sysMessage.type]">
          {{ sysMessage.text }}
        </div>

        <button type="submit" class="submit-btn" :disabled="isLoading">
          {{ isLoading ? '處理中...' : '✅ 驗證並綁定' }}
        </button>
        
        <div style="text-align: center; margin-top: 15px;">
          <NuxtLink to="/" class="back-link">返回打卡首頁</NuxtLink>
        </div>
      </form>
      
      <div class="footer-note">
        * 註：每位學生最多綁定 2 組家長信箱。若需修改已綁定的信箱，請透過聯絡簿聯繫導師。
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
const supabase = useSupabaseClient()

const students = ref([])
const selectedStudentId = ref('')
const studentBirthday = ref('') // 新增：綁定生日輸入框
const parentEmail = ref('')
const isLoading = ref(false)
const sysMessage = ref({ type: '', text: '' })

const showMessage = (type, text) => {
  sysMessage.value = { type, text }
  if (type === 'success') {
    setTimeout(() => { sysMessage.value = { type: '', text: '' } }, 5000)
  }
}

// 載入名單 (只抓 id, 座號, 隱藏姓名，絕對不抓生日到前端)
const fetchStudents = async () => {
  const { data, error } = await supabase
    .from('students')
    .select('id, seat_number, hidden_name') 
    .order('seat_number', { ascending: true })

  if (!error) students.value = data
}

// 處理綁定與驗證邏輯
const submitBinding = async () => {
  if (!selectedStudentId.value || !parentEmail.value || !studentBirthday.value) return
  
  isLoading.value = true
  sysMessage.value = { type: '', text: '' } 

  try {
    // 💡 步驟 A：最高機密身分驗證！向資料庫比對 ID 與生日是否完全吻合
    const { data: verifyData, error: verifyError } = await supabase
      .from('students')
      .select('id')
      .eq('id', selectedStudentId.value)
      .eq('birthday', studentBirthday.value)
      .single() // 只預期拿到一筆相符的資料

    // 若查無資料 (代表生日打錯了)
    if (verifyError || !verifyData) {
      showMessage('error', '❌ 身分驗證失敗：學生生日輸入錯誤！')
      isLoading.value = false
      return
    }

    // 步驟 B：檢查該學生目前綁定了幾個信箱
    const { data: existingParents } = await supabase.from('parents').select('id').eq('student_id', selectedStudentId.value)
    if (existingParents.length >= 2) {
      showMessage('error', '❌ 綁定失敗：此學生已達到綁定上限 (2位)。')
      isLoading.value = false
      return
    }

    // 步驟 C：檢查 Email 是否重複綁定
    const { data: duplicateEmail } = await supabase.from('parents').select('id').eq('student_id', selectedStudentId.value).eq('email', parentEmail.value)
    if (duplicateEmail.length > 0) {
       showMessage('error', '⚠️ 此 Email 已經綁定過這位學生囉！')
       isLoading.value = false
       return
    }

    // 步驟 D：驗證全數通過，正式寫入資料庫
    await supabase.from('parents').insert({ student_id: selectedStudentId.value, email: parentEmail.value })

    showMessage('success', '🎉 驗證與綁定成功！未來系統通知將發送至此信箱。')
    
    // 清空表單
    parentEmail.value = ''
    studentBirthday.value = ''
    selectedStudentId.value = ''

  } catch (error) {
    showMessage('error', '系統發生錯誤，請稍後再試。')
  } finally {
    isLoading.value = false
  }
}

onMounted(() => fetchStudents())
</script>

<style scoped>
/* (保留前一版的 CSS，並新增返回連結樣式) */
.bind-container { min-height: 100vh; display: flex; justify-content: center; align-items: center; background-color: #fdf6e3; padding: 20px; font-family: 'sans-serif'; }
.bind-card { background: white; width: 100%; max-width: 450px; border-radius: 16px; box-shadow: 0 10px 25px rgba(0,0,0,0.08); padding: 30px; border-top: 8px solid #f59e0b; }
.card-header { text-align: center; margin-bottom: 30px; }
.card-header h2 { color: #b45309; margin-bottom: 10px; font-size: 1.6rem; }
.card-header p { color: #78716c; font-size: 0.95rem; line-height: 1.5; }
.form-group { margin-bottom: 20px; }
.form-group label { display: block; margin-bottom: 8px; font-weight: bold; color: #444; }
select, input { width: 100%; padding: 12px 15px; border: 1px solid #d6d3d1; border-radius: 8px; font-size: 1.1rem; background-color: #fafaf9; box-sizing: border-box; transition: border-color 0.2s; }
select:focus, input:focus { outline: none; border-color: #f59e0b; background-color: white; }
select:disabled, input:disabled { opacity: 0.6; cursor: not-allowed; }
.submit-btn { width: 100%; padding: 14px; background-color: #10b981; color: white; border: none; border-radius: 8px; font-size: 1.2rem; font-weight: bold; cursor: pointer; transition: background-color 0.2s; margin-top: 10px; }
.submit-btn:hover:not(:disabled) { background-color: #059669; }
.submit-btn:disabled { background-color: #9ca3af; cursor: not-allowed; }
.message-box { padding: 12px; border-radius: 8px; margin-bottom: 20px; text-align: center; font-weight: bold; }
.message-box.error { background-color: #fee2e2; color: #dc2626; border: 1px solid #fecaca; }
.message-box.success { background-color: #d1fae5; color: #059669; border: 1px solid #a7f3d0; }
.footer-note { margin-top: 25px; font-size: 0.85rem; color: #a8a29e; text-align: center; line-height: 1.4; }
.back-link { color: #f59e0b; text-decoration: none; font-weight: bold; font-size: 0.9rem; }
.back-link:hover { text-decoration: underline; }
</style>