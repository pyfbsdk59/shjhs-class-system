<template>
  <div class="admin-container">
    <div v-if="!isUnlocked" class="lock-screen">
      <div class="lock-box">
        <h2>🔒 導師專屬後台</h2>
        <input v-model="passwordInput" type="password" placeholder="請輸入密碼..." @keyup.enter="verifyPassword"/>
        <button @click="verifyPassword">解鎖進入</button>
      </div>
    </div>

    <div v-else class="dashboard">
      <header class="admin-header">
        <h2>📊 班級數據中心 (導師專用)</h2>
        <div>
          <button @click="switchTab('messages')" :class="{ active: currentTab === 'messages' }">💬 私訊管理</button>
          <button @click="switchTab('audit')" :class="{ active: currentTab === 'audit' }">🕵️ 黑板稽核</button>
          <button @click="switchTab('communication')" :class="{ active: currentTab === 'communication' }">📨 系統紀錄</button>
          <NuxtLink to="/" class="back-btn">⬅️ 返回前台</NuxtLink>
        </div>
      </header>

      <main v-if="currentTab === 'messages'" class="data-table">
        <div class="table-header">
          <h3>💬 班級私訊管理</h3>
          <button @click="exportToExcel" class="export-btn">📥 匯出所有紀錄</button>
        </div>
        
        <div class="chat-selector">
          <label>切換對話頻道：</label>
          <select v-model="activeChatThread" @change="markCurrentThreadAsRead">
            <option value="" disabled selected>請選擇要查看的對話...</option>
            <optgroup label="👨‍👩‍👧 家長群">
              <option v-for="student in studentsList" :key="'parent-'+student.id" :value="student.id + '_家長'">
                {{ student.seat_number }}號 {{ student.real_name }} 的家長
              </option>
            </optgroup>
            <optgroup label="👩‍🎓 學生群">
              <option v-for="student in studentsList" :key="'student-'+student.id" :value="student.id + '_學生'">
                {{ student.seat_number }}號 {{ student.real_name }} (學生)
              </option>
            </optgroup>
          </select>
        </div>

        <div v-if="!activeChatThread" class="empty-prompt">
          👈 請從上方選擇一個對話群組來檢視歷史訊息與回覆。
        </div>

        <div v-else>
          <div class="chat-container" id="adminChatContainer">
            <div v-if="filteredMessages.length === 0" class="empty">此頻道目前尚無通訊紀錄</div>
            <div v-for="msg in filteredMessages" :key="msg.id" :class="['chat-bubble', msg.sender_role === '導師' ? 'teacher-msg' : 'other-msg']">
              <div class="msg-info">
                <span class="sender">{{ msg.sender_role === '導師' ? '我 (導師)' : msg.sender_role }}</span>
                <span class="time">{{ formatTime(msg.created_at) }}</span>
              </div>
              <div class="msg-content">{{ msg.content }}</div>
            </div>
          </div>

          <div class="reply-box">
            <input v-model="replyContent" type="text" placeholder="請輸入回覆內容..." @keyup.enter="sendReply" />
            <button @click="sendReply" class="send-reply-btn" :disabled="isSending">📤 密碼解鎖並傳送</button>
          </div>
        </div>
      </main>

      </div>
  </div>
</template>

<script setup>
import { ref, computed, nextTick } from 'vue'
const supabase = useSupabaseClient()

const isUnlocked = ref(false); const passwordInput = ref(''); const currentTab = ref('messages')
const boardLogs = ref([]); const commLogs = ref([])
const allMessages = ref([]); const studentsMap = ref({}); const studentsList = ref([])

// 聊天室專用狀態
const activeChatThread = ref('') // 格式：'studentId_chatType' 例如 'uuid-123_家長'
const replyContent = ref('')
const isSending = ref(false)

// 根據上方下拉選單，自動過濾出目前的對話紀錄
const filteredMessages = computed(() => {
  if (!activeChatThread.value) return []
  const [targetId, targetType] = activeChatThread.value.split('_')
  return allMessages.value.filter(m => m.student_id === targetId && m.chat_type === targetType)
})

const verifyPassword = async () => {
  if (passwordInput.value === '168168168') {
    isUnlocked.value = true
    await fetchAllData()
  } else { alert('❌ 密碼錯誤！'); passwordInput.value = '' }
}

const switchTab = async (tab) => {
  currentTab.value = tab
  if (tab === 'messages') await fetchAllData()
}

const fetchAllData = async () => {
  const { data: bLogs } = await supabase.from('board_edit_logs').select('*').order('edited_at', { ascending: false }).limit(50)
  if (bLogs) boardLogs.value = bLogs

  const { data: cLogs } = await supabase.from('communication_logs').select('*').order('sent_at', { ascending: false }).limit(50)
  if (cLogs) commLogs.value = cLogs

  const { data: sData } = await supabase.from('students').select('*').order('seat_number')
  if (sData) {
    studentsList.value = sData
    sData.forEach(s => { studentsMap.value[s.id] = s.real_name })
  }

  const { data: msgLogs } = await supabase.from('private_messages').select('*').order('created_at', { ascending: true })
  if (msgLogs) {
    allMessages.value = msgLogs
    scrollToBottom()
  }
}

// 選擇對話時，消除該頻道的未讀紅點
const markCurrentThreadAsRead = async () => {
  if (!activeChatThread.value) return
  const [targetId, targetType] = activeChatThread.value.split('_')
  await supabase.from('private_messages')
    .update({ is_read_by_teacher: true })
    .eq('student_id', targetId).eq('chat_type', targetType).eq('is_read_by_teacher', false)
  scrollToBottom()
}

// 導師發送回覆
const sendReply = async () => {
  if (!activeChatThread.value || !replyContent.value.trim()) return
  const pwd = window.prompt("🔒 傳送前請再次輸入導師專屬密碼：")
  if (pwd !== '168168168') return alert('❌ 密碼錯誤，傳送取消！')

  const [targetId, targetType] = activeChatThread.value.split('_')
  isSending.value = true

  try {
    await supabase.from('private_messages').insert({
      student_id: targetId,
      sender_role: '導師',
      chat_type: targetType, // 標記是回覆家長還是回覆學生！
      content: replyContent.value,
      is_read_by_teacher: true
    })
    
    alert('✅ 回覆成功！')
    replyContent.value = ''
    await fetchAllData() // 刷新抓取最新訊息
  } catch (error) { alert('發生錯誤') } finally { isSending.value = false }
}

const exportToExcel = () => {
  let csvContent = "data:text/csv;charset=utf-8,\uFEFF"
  csvContent += "發送時間,學生姓名,對話頻道,發送者,訊息內容\n"
  allMessages.value.forEach(msg => {
    const time = formatTime(msg.created_at)
    const name = studentsMap.value[msg.student_id] || '未知'
    const content = msg.content.replace(/"/g, '""')
    csvContent += `"${time}","${name}","${msg.chat_type}","${msg.sender_role}","${content}"\n`
  })
  const link = document.createElement("a"); link.setAttribute("href", encodeURI(csvContent))
  link.setAttribute("download", `班級私訊紀錄_${new Date().getTime()}.csv`)
  document.body.appendChild(link); link.click(); document.body.removeChild(link)
}

const formatTime = (isoString) => new Date(isoString).toLocaleString('zh-TW', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
const scrollToBottom = () => { nextTick(() => { const c = document.getElementById('adminChatContainer'); if (c) c.scrollTop = c.scrollHeight }) }
</script>

<style scoped>
/* 基礎樣式保留 */
.admin-container { min-height: 100vh; background-color: #f1f5f9; font-family: sans-serif; }
.lock-screen { display: flex; justify-content: center; align-items: center; height: 100vh; background-color: #1e293b; }
.lock-box { background: white; padding: 40px; border-radius: 12px; text-align: center; box-shadow: 0 10px 25px rgba(0,0,0,0.5); width: 400px; }
.lock-box h2 { color: #334155; margin-bottom: 10px; }
.lock-box input { width: 100%; padding: 12px; margin-bottom: 20px; border: 1px solid #cbd5e1; border-radius: 6px; font-size: 1.2rem; text-align: center; }
.lock-box button { width: 100%; padding: 12px; background-color: #3b82f6; color: white; border: none; border-radius: 6px; font-size: 1.1rem; cursor: pointer; font-weight: bold; }
.dashboard { max-width: 1200px; margin: 0 auto; padding: 30px; }
.admin-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; background: white; padding: 20px 30px; border-radius: 12px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }
.admin-header h2 { margin: 0; color: #0f172a; }
.admin-header button { margin-right: 10px; padding: 10px 20px; border: none; border-radius: 6px; cursor: pointer; font-weight: bold; background: #e2e8f0; color: #475569; }
.admin-header button.active { background: #3b82f6; color: white; }
.back-btn { text-decoration: none; padding: 10px 20px; border-radius: 6px; font-weight: bold; background: #ef4444; color: white; display: inline-block; }
.data-table { background: white; padding: 25px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
.table-header { display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #e2e8f0; padding-bottom: 15px; margin-bottom: 20px; }
.export-btn { background-color: #10b981; color: white; border: none; padding: 8px 16px; border-radius: 6px; font-weight: bold; cursor: pointer; }

/* 聊天室專屬選擇器與視窗 */
.chat-selector { margin-bottom: 15px; background: #f8fafc; padding: 15px; border-radius: 8px; border: 1px solid #cbd5e1; }
.chat-selector label { font-weight: bold; color: #334155; margin-right: 10px; }
.chat-selector select { padding: 8px 12px; font-size: 1.1rem; border-radius: 6px; border: 1px solid #94a3b8; width: 300px; }
.empty-prompt { text-align: center; padding: 50px; color: #64748b; font-size: 1.2rem; background: #f8fafc; border-radius: 8px; border: 2px dashed #cbd5e1; }

.chat-container { height: 400px; overflow-y: auto; padding: 20px; background: #f8fafc; border-radius: 8px 8px 0 0; border: 1px solid #e2e8f0; border-bottom: none; display: flex; flex-direction: column; gap: 15px; }
.chat-bubble { max-width: 60%; padding: 12px 16px; border-radius: 12px; box-shadow: 0 1px 2px rgba(0,0,0,0.1); }
.other-msg { background: white; align-self: flex-start; border-left: 4px solid #f59e0b; }
.teacher-msg { background: #dcfce7; align-self: flex-end; border-right: 4px solid #10b981; }
.msg-info { font-size: 0.85rem; margin-bottom: 5px; color: #64748b; display: flex; justify-content: space-between; gap: 15px; }
.msg-info .sender { font-weight: bold; color: #334155; }
.msg-content { font-size: 1.1rem; color: #1e293b; line-height: 1.5; white-space: pre-wrap; }

.reply-box { display: flex; padding: 15px; background: white; border: 1px solid #e2e8f0; border-radius: 0 0 8px 8px; gap: 10px; }
.reply-box input { flex: 1; padding: 12px; border: 1px solid #cbd5e1; border-radius: 6px; font-size: 1.1rem; }
.send-reply-btn { background: #3b82f6; color: white; border: none; padding: 0 20px; border-radius: 6px; font-weight: bold; cursor: pointer; white-space: nowrap; }
</style>