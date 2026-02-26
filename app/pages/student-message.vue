<template>
  <div class="message-container">
    <div class="message-card">
      
      <div v-if="!isVerified" class="verify-section">
        <div class="card-header">
          <h2>💬 學生私訊導師</h2>
          <p>請先輸入生日進行身分驗證，以進入專屬對話視窗。</p>
        </div>

        <form @submit.prevent="verifyIdentity" class="message-form">
          <div class="form-group">
            <label>👩‍🎓 我是 (選擇座號)</label>
            <select v-model="selectedStudentId" required :disabled="isLoading">
              <option value="" disabled selected>請選擇座號與姓名...</option>
              <option v-for="student in students" :key="student.id" :value="student.id">
                {{ student.seat_number }}號 - {{ student.hidden_name }}
              </option>
            </select>
          </div>

          <div class="form-group">
            <label>🎂 我的生日 (身分驗證)</label>
            <input v-model="studentBirthday" type="password" placeholder="例如: 20130514" required :disabled="isLoading" />
          </div>

          <div v-if="sysMessage.text" :class="['message-box', sysMessage.type]">{{ sysMessage.text }}</div>

          <button type="submit" class="submit-btn" :disabled="isLoading">
            {{ isLoading ? '驗證中...' : '🔐 進入聊天室' }}
          </button>
          
          <div style="text-align: center; margin-top: 15px;">
            <NuxtLink to="/" class="back-link">返回首頁</NuxtLink>
          </div>
        </form>
      </div>

      <div v-else class="chat-section">
        <div class="chat-header">
          <h3>💬 私訊導師 ({{ verifiedStudentName }})</h3>
          <button @click="logout" class="logout-btn">登出</button>
        </div>

        <div class="chat-history" id="chatContainer">
          <div v-if="chatMessages.length === 0" class="empty-chat">目前無對話紀錄，請在下方輸入訊息。</div>
          <div v-for="msg in chatMessages" :key="msg.id" :class="['chat-bubble', msg.sender_role === '學生' ? 'my-msg' : 'teacher-msg']">
            <div class="msg-info">
              <span class="sender">{{ msg.sender_role === '學生' ? '我' : '👨‍🏫 導師' }}</span>
              <span class="time">{{ formatTime(msg.created_at) }}</span>
            </div>
            <div class="msg-content">{{ msg.content }}</div>
          </div>
        </div>

        <form @submit.prevent="sendMessage" class="reply-form">
          <textarea v-model="newMessage" rows="2" placeholder="請輸入訊息..." required :disabled="isSending"></textarea>
          <button type="submit" class="send-btn" :disabled="isSending">{{ isSending ? '...' : '📤 傳送' }}</button>
        </form>
      </div>

    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
const supabase = useSupabaseClient()

const students = ref([]); const selectedStudentId = ref(''); const studentBirthday = ref('')
const isLoading = ref(false); const isSending = ref(false); const isVerified = ref(false)
const verifiedStudentName = ref(''); const sysMessage = ref({ type: '', text: '' })
const chatMessages = ref([]); const newMessage = ref('')

const showMessage = (type, text) => {
  sysMessage.value = { type, text }
  if (type === 'success') setTimeout(() => { sysMessage.value = { type: '', text: '' } }, 3000)
}

const fetchStudents = async () => {
  const { data } = await supabase.from('students').select('id, seat_number, hidden_name').order('seat_number')
  if (data) students.value = data
}

const verifyIdentity = async () => {
  if (!selectedStudentId.value || !studentBirthday.value) return
  isLoading.value = true; sysMessage.value = { type: '', text: '' }
  try {
    const { data, error } = await supabase.from('students').select('id, real_name').eq('id', selectedStudentId.value).eq('birthday', studentBirthday.value).single()
    if (error || !data) { showMessage('error', '❌ 生日錯誤！'); isLoading.value = false; return }
    verifiedStudentName.value = data.real_name; isVerified.value = true
    await loadChatHistory()
  } catch (error) { showMessage('error', '系統錯誤'); } finally { isLoading.value = false }
}

const loadChatHistory = async () => {
  const { data } = await supabase.from('private_messages').select('*')
    .eq('student_id', selectedStudentId.value).eq('chat_type', '學生').order('created_at', { ascending: true })
  if (data) { chatMessages.value = data; scrollToBottom() }
}

const sendMessage = async () => {
  if (!newMessage.value.trim()) return
  isSending.value = true
  try {
    await supabase.from('private_messages').insert({
      student_id: selectedStudentId.value, sender_role: '學生', chat_type: '學生', content: newMessage.value, is_read_by_teacher: false
    })
    newMessage.value = ''; await loadChatHistory()
  } catch (error) { alert('傳送失敗') } finally { isSending.value = false }
}

const logout = () => { isVerified.value = false; studentBirthday.value = ''; chatMessages.value = [] }
const formatTime = (isoString) => new Date(isoString).toLocaleString('zh-TW', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
const scrollToBottom = () => { nextTick(() => { const container = document.getElementById('chatContainer'); if (container) container.scrollTop = container.scrollHeight }) }
onMounted(() => fetchStudents())
</script>

<style scoped>
/* 樣式與 parent-message 完全共用，只需稍作調整背景顏色區分即可 */
.message-container { min-height: 100vh; display: flex; justify-content: center; align-items: center; background-color: #eff6ff; padding: 10px; font-family: 'sans-serif'; }
.message-card { background: white; width: 100%; max-width: 500px; border-radius: 16px; box-shadow: 0 10px 25px rgba(0,0,0,0.08); overflow: hidden; border-top: 8px solid #3b82f6; }
.verify-section { padding: 30px; }
.card-header { text-align: center; margin-bottom: 30px; }
.card-header h2 { color: #1e40af; margin-bottom: 10px; font-size: 1.6rem; }
.card-header p { color: #6b7280; font-size: 0.95rem; line-height: 1.5; }
.form-group { margin-bottom: 20px; }
.form-group label { display: block; margin-bottom: 8px; font-weight: bold; color: #374151; }
select, input { width: 100%; padding: 12px 15px; border: 1px solid #d1d5db; border-radius: 8px; font-size: 1.1rem; background-color: #f9fafb; box-sizing: border-box; }
select:focus, input:focus { outline: none; border-color: #3b82f6; background-color: white; }
.submit-btn { width: 100%; padding: 14px; background-color: #3b82f6; color: white; border: none; border-radius: 8px; font-size: 1.2rem; font-weight: bold; cursor: pointer; transition: 0.2s; margin-top: 10px; }
.submit-btn:hover:not(:disabled) { background-color: #2563eb; }
.message-box { padding: 12px; border-radius: 8px; margin-bottom: 20px; text-align: center; font-weight: bold; }
.message-box.error { background-color: #fee2e2; color: #dc2626; border: 1px solid #fecaca; }
.back-link { color: #3b82f6; text-decoration: none; font-weight: bold; font-size: 0.9rem; }
.chat-section { display: flex; flex-direction: column; height: 80vh; max-height: 650px; }
.chat-header { display: flex; justify-content: space-between; align-items: center; padding: 15px 20px; background: #dbeafe; border-bottom: 1px solid #bfdbfe; }
.chat-header h3 { margin: 0; color: #1e40af; font-size: 1.1rem; }
.logout-btn { background: #ef4444; color: white; border: none; padding: 6px 12px; border-radius: 6px; font-size: 0.9rem; cursor: pointer; }
.chat-history { flex: 1; overflow-y: auto; padding: 20px; background: #f8fafc; display: flex; flex-direction: column; gap: 15px; }
.empty-chat { text-align: center; color: #94a3b8; font-size: 0.95rem; margin-top: 50px; }
.chat-bubble { max-width: 80%; padding: 10px 14px; border-radius: 12px; box-shadow: 0 1px 2px rgba(0,0,0,0.1); display: flex; flex-direction: column; }
.my-msg { background: #dbeafe; align-self: flex-end; border-bottom-right-radius: 2px; }
.teacher-msg { background: #dcfce7; align-self: flex-start; border-bottom-left-radius: 2px; }
.msg-info { display: flex; justify-content: space-between; gap: 15px; margin-bottom: 4px; font-size: 0.75rem; color: #64748b; }
.my-msg .sender { color: #1d4ed8; font-weight: bold; }
.teacher-msg .sender { color: #15803d; font-weight: bold; }
.msg-content { font-size: 1.05rem; color: #1e293b; line-height: 1.4; white-space: pre-wrap; word-break: break-all; }
.reply-form { display: flex; gap: 10px; padding: 15px; background: white; border-top: 1px solid #e2e8f0; }
.reply-form textarea { flex: 1; padding: 10px; border: 1px solid #cbd5e1; border-radius: 8px; font-size: 1rem; resize: none; font-family: inherit; }
.reply-form textarea:focus { outline: none; border-color: #3b82f6; }
.send-btn { background: #3b82f6; color: white; border: none; padding: 0 20px; border-radius: 8px; font-weight: bold; cursor: pointer; white-space: nowrap; }
</style>