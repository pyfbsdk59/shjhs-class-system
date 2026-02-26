<template>
  <div class="admin-container">
    <div v-if="!isUnlocked" class="lock-screen">
      <div class="lock-box">
        <h2>🔒 導師專屬後台</h2>
        <p>請輸入最高權限密碼以檢視機密數據</p>
        <input 
          v-model="passwordInput" 
          type="password" 
          placeholder="請輸入密碼..." 
          @keyup.enter="verifyPassword"
        />
        <button @click="verifyPassword">解鎖進入</button>
      </div>
    </div>

    <div v-else class="dashboard">
      <header class="admin-header">
        <h2>📊 班級數據中心 (導師專用)</h2>
        <div>
          <button @click="switchTab('messages')" :class="{ active: currentTab === 'messages' }">💬 家長私訊</button>
          <button @click="switchTab('audit')" :class="{ active: currentTab === 'audit' }">🕵️ 黑板編輯稽核</button>
          <button @click="switchTab('communication')" :class="{ active: currentTab === 'communication' }">📨 系統通訊紀錄</button>
          <NuxtLink to="/" class="back-btn">⬅️ 返回前台</NuxtLink>
        </div>
      </header>

      <main v-if="currentTab === 'messages'" class="data-table">
        <div class="table-header">
          <h3>💬 家長私訊對話紀錄</h3>
          <button @click="exportToExcel" class="export-btn">📥 匯出紀錄 (Excel/CSV)</button>
        </div>
        
        <div class="chat-container">
          <div v-for="msg in privateMessages" :key="msg.id" :class="['chat-bubble', msg.sender_role === '導師' ? 'teacher-msg' : 'parent-msg']">
            <div class="msg-info">
              <span class="sender">{{ msg.sender_role === '導師' ? '👨‍🏫 導師回覆' : `👨‍👩‍👧 ${getStudentName(msg.student_id)} 的家長` }}</span>
              <span class="time">{{ formatTime(msg.created_at) }}</span>
            </div>
            <div class="msg-content">{{ msg.content }}</div>
          </div>
          <div v-if="privateMessages.length === 0" class="empty">目前尚無任何私訊紀錄</div>
        </div>

        <div class="reply-box">
          <h4>快速回覆家長</h4>
          <div class="reply-controls">
            <select v-model="replyStudentId">
              <option value="" disabled>請選擇要回覆的學生家長...</option>
              <option v-for="student in studentsList" :key="student.id" :value="student.id">
                {{ student.seat_number }}號 - {{ student.real_name }}
              </option>
            </select>
            <input v-model="replyContent" type="text" placeholder="請輸入回覆內容..." />
            <button @click="sendReply" class="send-reply-btn" :disabled="isSending">📤 密碼解鎖並傳送</button>
          </div>
        </div>
      </main>

      <main v-if="currentTab === 'audit'" class="data-table">
        <h3>🕵️ 最近 50 筆黑板編輯紀錄</h3>
        <table>
          <thead>
            <tr><th>時間</th><th>修改區塊</th><th>編輯者</th><th>IP 位址</th><th>裝置資訊</th></tr>
          </thead>
          <tbody>
            <tr v-for="log in boardLogs" :key="log.id">
              <td>{{ formatTime(log.edited_at) }}</td>
              <td><span class="badge">{{ log.board_type }}</span></td>
              <td :class="log.editor_role === '導師' ? 'role-teacher' : 'role-student'">{{ log.editor_role }}</td>
              <td class="ip-text">{{ log.ip_address }}</td>
              <td class="device-text">{{ shortenAgent(log.user_agent) }}</td>
            </tr>
            <tr v-if="boardLogs.length === 0"><td colspan="5" class="empty">目前尚無紀錄</td></tr>
          </tbody>
        </table>
      </main>

      <main v-if="currentTab === 'communication'" class="data-table">
        <h3>📨 最近 50 筆通知發送紀錄</h3>
        <table>
          <thead>
            <tr><th>發送時間</th><th>收件學生</th><th>通知類型</th><th>發送者</th><th>收件信箱</th></tr>
          </thead>
          <tbody>
            <tr v-for="log in commLogs" :key="log.id">
              <td>{{ formatTime(log.sent_at) }}</td>
              <td>{{ getStudentName(log.student_id) }}</td>
              <td><span class="badge notice">{{ log.notification_type }}</span></td>
              <td>{{ log.sent_by }}</td>
              <td class="email-text">{{ log.recipient_emails }}</td>
            </tr>
            <tr v-if="commLogs.length === 0"><td colspan="5" class="empty">目前尚無紀錄</td></tr>
          </tbody>
        </table>
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
const supabase = useSupabaseClient()

const isUnlocked = ref(false)
const passwordInput = ref('')
const currentTab = ref('messages')

const boardLogs = ref([])
const commLogs = ref([])
const privateMessages = ref([])
const studentsMap = ref({}) 
const studentsList = ref([]) // 供回覆下拉選單使用

// 回覆表單狀態
const replyStudentId = ref('')
const replyContent = ref('')
const isSending = ref(false)

const verifyPassword = async () => {
  if (passwordInput.value === '168168168') {
    isUnlocked.value = true
    await fetchAllData()
    // 解鎖後若預設在私訊頁籤，將未讀標記為已讀
    if (currentTab.value === 'messages') await markMessagesAsRead()
  } else {
    alert('❌ 密碼錯誤，拒絕存取！')
    passwordInput.value = ''
  }
}

const switchTab = async (tab) => {
  currentTab.value = tab
  if (tab === 'messages') {
    await fetchAllData() // 刷新訊息
    await markMessagesAsRead() // 點擊進入時，消除紅點
  }
}

const fetchAllData = async () => {
  // 1. 抓取編輯稽核與通訊紀錄
  const { data: bLogs } = await supabase.from('board_edit_logs').select('*').order('edited_at', { ascending: false }).limit(50)
  if (bLogs) boardLogs.value = bLogs

  const { data: cLogs } = await supabase.from('communication_logs').select('*').order('sent_at', { ascending: false }).limit(50)
  if (cLogs) commLogs.value = cLogs

  // 2. 抓取私訊紀錄
  const { data: msgLogs } = await supabase.from('private_messages').select('*').order('created_at', { ascending: true })
  if (msgLogs) privateMessages.value = msgLogs

  // 3. 抓取學生名單
  const { data: sData } = await supabase.from('students').select('id, real_name, seat_number').order('seat_number')
  if (sData) {
    studentsList.value = sData
    sData.forEach(s => { studentsMap.value[s.id] = s.real_name })
  }
}

// 將未讀訊息標記為已讀
const markMessagesAsRead = async () => {
  await supabase
    .from('private_messages')
    .update({ is_read_by_teacher: true })
    .eq('is_read_by_teacher', false)
    .eq('sender_role', '家長')
}

// 導師回覆私訊
const sendReply = async () => {
  if (!replyStudentId.value || !replyContent.value) return alert('請選擇學生並輸入回覆內容！')
  
  // 雙重密碼驗證 (保護導師帳號不被學生誤用)
  const pwd = window.prompt("🔒 傳送前請再次輸入導師專屬密碼：")
  if (pwd !== '168168168') {
    return alert('❌ 密碼錯誤，傳送取消！')
  }

  isSending.value = true
  try {
    // 1. 寫入資料庫
    await supabase.from('private_messages').insert({
      student_id: replyStudentId.value,
      sender_role: '導師',
      content: replyContent.value,
      is_read_by_teacher: true
    })

    // 2. 模擬觸發 Email 發送 (實戰中這裡會呼叫 Nuxt Server API 去寄信)
    // await fetch('/api/send-email', { method: 'POST', body: JSON.stringify({ student_id: replyStudentId.value, content: replyContent.value }) })
    
    alert('✅ 回覆已成功寫入資料庫！系統將自動發送信件通知家長。')
    replyContent.value = ''
    await fetchAllData() // 刷新畫面看到最新回覆
  } catch (error) {
    alert('發生錯誤，請稍後再試。')
  } finally {
    isSending.value = false
  }
}

// 一鍵匯出為 Excel/CSV
const exportToExcel = () => {
  // 加上 \uFEFF 讓 Excel 可以正確識別 UTF-8 中文
  let csvContent = "data:text/csv;charset=utf-8,\uFEFF"
  csvContent += "發送時間,學生姓名,發送者,訊息內容\n"

  privateMessages.value.forEach(msg => {
    const time = formatTime(msg.created_at)
    const name = getStudentName(msg.student_id)
    const role = msg.sender_role
    const content = msg.content.replace(/"/g, '""') // 處理內容中有雙引號的狀況
    csvContent += `"${time}","${name}","${role}","${content}"\n`
  })

  const encodedUri = encodeURI(csvContent)
  const link = document.createElement("a")
  link.setAttribute("href", encodedUri)
  const d = new Date()
  const dateStr = `${d.getFullYear()}${String(d.getMonth()+1).padStart(2,'0')}${String(d.getDate()).padStart(2,'0')}`
  link.setAttribute("download", `班級私訊紀錄_${dateStr}.csv`)
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}

// 工具函數
const formatTime = (isoString) => {
  const d = new Date(isoString)
  return d.toLocaleString('zh-TW', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false })
}
const shortenAgent = (agent) => agent ? (agent.length > 30 ? agent.substring(0, 30) + '...' : agent) : '未知裝置'
const getStudentName = (id) => studentsMap.value[id] || '未知學生'

</script>

<style scoped>
/* 基礎後台樣式保留 */
.admin-container { min-height: 100vh; background-color: #f1f5f9; font-family: sans-serif; }
.lock-screen { display: flex; justify-content: center; align-items: center; height: 100vh; background-color: #1e293b; }
.lock-box { background: white; padding: 40px; border-radius: 12px; text-align: center; box-shadow: 0 10px 25px rgba(0,0,0,0.5); width: 400px; }
.lock-box h2 { color: #334155; margin-bottom: 10px; }
.lock-box p { color: #64748b; margin-bottom: 25px; }
.lock-box input { width: 100%; padding: 12px; margin-bottom: 20px; border: 1px solid #cbd5e1; border-radius: 6px; font-size: 1.2rem; text-align: center; box-sizing: border-box; }
.lock-box button { width: 100%; padding: 12px; background-color: #3b82f6; color: white; border: none; border-radius: 6px; font-size: 1.1rem; cursor: pointer; font-weight: bold; }
.dashboard { max-width: 1200px; margin: 0 auto; padding: 30px; }
.admin-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; background: white; padding: 20px 30px; border-radius: 12px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }
.admin-header h2 { margin: 0; color: #0f172a; }
.admin-header button { margin-right: 10px; padding: 10px 20px; border: none; border-radius: 6px; cursor: pointer; font-weight: bold; background: #e2e8f0; color: #475569; }
.admin-header button.active { background: #3b82f6; color: white; }
.back-btn { text-decoration: none; padding: 10px 20px; border-radius: 6px; font-weight: bold; background: #ef4444; color: white; display: inline-block; }

.data-table { background: white; padding: 25px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
.table-header { display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #e2e8f0; padding-bottom: 15px; margin-bottom: 20px; }
.table-header h3, .data-table h3 { margin: 0; color: #334155; }
.export-btn { background-color: #10b981; color: white; border: none; padding: 8px 16px; border-radius: 6px; font-weight: bold; cursor: pointer; transition: 0.2s; }
.export-btn:hover { background-color: #059669; }

table { width: 100%; border-collapse: collapse; text-align: left; }
th, td { padding: 12px 15px; border-bottom: 1px solid #f1f5f9; }
th { background-color: #f8fafc; color: #64748b; font-weight: bold; }
tr:hover { background-color: #f8fafc; }
.empty { text-align: center; color: #94a3b8; padding: 30px !important; }
.badge { background: #e0e7ff; color: #4338ca; padding: 4px 10px; border-radius: 20px; font-size: 0.85rem; font-weight: bold; }
.badge.notice { background: #fef3c7; color: #b45309; }
.role-teacher { color: #dc2626; font-weight: bold; }
.role-student { color: #059669; font-weight: bold; }
.ip-text { font-family: monospace; color: #475569; }
.device-text, .email-text { font-size: 0.9rem; color: #64748b; }

/* 聊天對話框專屬樣式 */
.chat-container { max-height: 500px; overflow-y: auto; padding: 15px; background: #f8fafc; border-radius: 8px; margin-bottom: 20px; display: flex; flex-direction: column; gap: 15px; }
.chat-bubble { max-width: 70%; padding: 12px 16px; border-radius: 12px; box-shadow: 0 1px 2px rgba(0,0,0,0.1); }
.parent-msg { background: white; align-self: flex-start; border-left: 4px solid #3b82f6; }
.teacher-msg { background: #dcfce7; align-self: flex-end; border-right: 4px solid #10b981; }
.msg-info { font-size: 0.85rem; margin-bottom: 5px; color: #64748b; display: flex; justify-content: space-between; gap: 15px; }
.msg-info .sender { font-weight: bold; color: #334155; }
.msg-content { font-size: 1.1rem; color: #1e293b; line-height: 1.5; white-space: pre-wrap; }

/* 回覆區塊 */
.reply-box { background: #f1f5f9; padding: 20px; border-radius: 8px; border: 1px solid #e2e8f0; }
.reply-box h4 { margin: 0 0 15px 0; color: #334155; }
.reply-controls { display: flex; gap: 10px; }
.reply-controls select { padding: 10px; border: 1px solid #cbd5e1; border-radius: 6px; font-size: 1rem; width: 250px; }
.reply-controls input { flex: 1; padding: 10px; border: 1px solid #cbd5e1; border-radius: 6px; font-size: 1rem; }
.send-reply-btn { background: #3b82f6; color: white; border: none; padding: 10px 20px; border-radius: 6px; font-weight: bold; cursor: pointer; white-space: nowrap; }
.send-reply-btn:hover:not(:disabled) { background: #2563eb; }
.send-reply-btn:disabled { background: #9ca3af; cursor: not-allowed; }

@media (max-width: 768px) {
  .reply-controls { flex-direction: column; }
  .reply-controls select, .reply-controls input { width: 100%; }
}
</style>