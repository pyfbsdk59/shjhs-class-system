<template>
  <div class="message-container">
    <div class="message-card">
      <div class="card-header">
        <h2>💬 私訊班級導師</h2>
        <p>請先進行身分驗證，輸入內容後將直接傳送至導師後台。</p>
      </div>

      <form @submit.prevent="submitMessage" class="message-form">
        <div class="form-group">
          <label>👩‍🎓 選擇學生</label>
          <select v-model="selectedStudentId" required :disabled="isLoading">
            <option value="" disabled selected>請選擇座號與姓名...</option>
            <option v-for="student in students" :key="student.id" :value="student.id">
              {{ student.seat_number }}號 - {{ student.hidden_name }}
            </option>
          </select>
        </div>

        <div class="form-group">
          <label>🎂 學生生日 (身分驗證)</label>
          <input 
            v-model="studentBirthday" 
            type="text" 
            placeholder="請輸入西元生日 (例如: 20130514)" 
            required 
            :disabled="isLoading"
          />
        </div>

        <div class="form-group">
          <label>📝 訊息內容</label>
          <textarea 
            v-model="messageContent" 
            rows="5" 
            placeholder="請輸入您想對導師說的話..." 
            required 
            :disabled="isLoading"
          ></textarea>
        </div>

        <div v-if="sysMessage.text" :class="['message-box', sysMessage.type]">
          {{ sysMessage.text }}
        </div>

        <button type="submit" class="submit-btn" :disabled="isLoading">
          {{ isLoading ? '傳送中...' : '📤 驗證並傳送' }}
        </button>
        
        <div style="text-align: center; margin-top: 15px;">
          <NuxtLink to="/" class="back-link">返回打卡首頁</NuxtLink>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
const supabase = useSupabaseClient()

const students = ref([])
const selectedStudentId = ref('')
const studentBirthday = ref('')
const messageContent = ref('')
const isLoading = ref(false)
const sysMessage = ref({ type: '', text: '' })

const showMessage = (type, text) => {
  sysMessage.value = { type, text }
  if (type === 'success') {
    setTimeout(() => { sysMessage.value = { type: '', text: '' } }, 5000)
  }
}

const fetchStudents = async () => {
  const { data } = await supabase.from('students').select('id, seat_number, hidden_name').order('seat_number', { ascending: true })
  if (data) students.value = data
}

const submitMessage = async () => {
  if (!selectedStudentId.value || !studentBirthday.value || !messageContent.value) return
  isLoading.value = true
  sysMessage.value = { type: '', text: '' }

  try {
    // 步驟 A：最高機密身分驗證 (核對生日)
    const { data: verifyData, error: verifyError } = await supabase
      .from('students').select('id').eq('id', selectedStudentId.value).eq('birthday', studentBirthday.value).single()

    if (verifyError || !verifyData) {
      showMessage('error', '❌ 身分驗證失敗：學生生日輸入錯誤！')
      isLoading.value = false; return
    }

    // 步驟 B：寫入私訊資料庫
    const { error: insertError } = await supabase.from('private_messages').insert({
      student_id: selectedStudentId.value,
      sender_role: '家長',
      content: messageContent.value
    })

    if (insertError) throw insertError

    showMessage('success', '🎉 訊息傳送成功！導師將會盡快查看並回覆。')
    messageContent.value = '' // 清空訊息，保留學生資料方便連續發送
    studentBirthday.value = ''

  } catch (error) {
    showMessage('error', '系統發生錯誤，請稍後再試。')
  } finally {
    isLoading.value = false
  }
}

onMounted(() => fetchStudents())
</script>

<style scoped>
.message-container { min-height: 100vh; display: flex; justify-content: center; align-items: center; background-color: #f0fdf4; padding: 20px; font-family: 'sans-serif'; }
.message-card { background: white; width: 100%; max-width: 500px; border-radius: 16px; box-shadow: 0 10px 25px rgba(0,0,0,0.08); padding: 30px; border-top: 8px solid #10b981; }
.card-header { text-align: center; margin-bottom: 30px; }
.card-header h2 { color: #047857; margin-bottom: 10px; font-size: 1.6rem; }
.card-header p { color: #6b7280; font-size: 0.95rem; line-height: 1.5; }
.form-group { margin-bottom: 20px; }
.form-group label { display: block; margin-bottom: 8px; font-weight: bold; color: #374151; }
select, input, textarea { width: 100%; padding: 12px 15px; border: 1px solid #d1d5db; border-radius: 8px; font-size: 1.1rem; background-color: #f9fafb; box-sizing: border-box; transition: border-color 0.2s; font-family: inherit; }
select:focus, input:focus, textarea:focus { outline: none; border-color: #10b981; background-color: white; }
.submit-btn { width: 100%; padding: 14px; background-color: #10b981; color: white; border: none; border-radius: 8px; font-size: 1.2rem; font-weight: bold; cursor: pointer; transition: background-color 0.2s; margin-top: 10px; }
.submit-btn:hover:not(:disabled) { background-color: #059669; }
.submit-btn:disabled { background-color: #9ca3af; cursor: not-allowed; }
.message-box { padding: 12px; border-radius: 8px; margin-bottom: 20px; text-align: center; font-weight: bold; }
.message-box.error { background-color: #fee2e2; color: #dc2626; border: 1px solid #fecaca; }
.message-box.success { background-color: #d1fae5; color: #059669; border: 1px solid #a7f3d0; }
.back-link { color: #10b981; text-decoration: none; font-weight: bold; font-size: 0.9rem; }
.back-link:hover { text-decoration: underline; }
</style>