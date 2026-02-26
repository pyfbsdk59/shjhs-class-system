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
        <div class="header-buttons">
          <button @click="switchTab('board')" :class="{ active: currentTab === 'board' }">📢 須知推播</button>
          <button @click="switchTab('messages')" :class="{ active: currentTab === 'messages' }">💬 私訊管理</button>
          <button @click="switchTab('students')" :class="{ active: currentTab === 'students' }">👩‍🎓 學生管理</button>
          <button @click="switchTab('audit')" :class="{ active: currentTab === 'audit' }">🕵️ 黑板稽核</button>
          <button @click="switchTab('communication')" :class="{ active: currentTab === 'communication' }">📨 系統紀錄</button>
          <NuxtLink to="/" class="back-btn">⬅️ 返回前台</NuxtLink>
        </div>
      </header>

      <main v-if="currentTab === 'board'" class="data-table">
        <div class="table-header">
          <h3>📢 家長須知管理與 Email 推播</h3>
          <p class="subtitle">今日日期：{{ todayDisplay }}</p>
        </div>

        <div class="board-editor-container">
          <div class="notice-edit-list">
            <div v-for="(notice, index) in adminNotices" :key="index" class="edit-item">
              <span class="bullet">📌</span>
              <input v-model="adminNotices[index]" type="text" class="edit-input notice-input" placeholder="請輸入須知事項..." />
              <button @click="removeAdminNotice(index)" class="del-row-btn">🗑️</button>
            </div>
            <button @click="addAdminNotice" class="add-btn">➕ 新增一筆須知</button>
          </div>

          <div class="action-bar">
            <button @click="saveAdminNotices" class="save-btn" :disabled="isSavingBoard">
              {{ isSavingBoard ? '儲存中...' : '💾 儲存並同步至大平板' }}
            </button>
            <button @click="sendNoticeEmail" class="email-btn" :disabled="isSendingEmail">
              {{ isSendingEmail ? '寄送中...' : '📧 密碼解鎖並推播至全班家長 (Bcc)' }}
            </button>
          </div>
        </div>
      </main>

      <main v-if="currentTab === 'messages'" class="data-table">
        <div class="table-header">
          <h3>💬 班級私訊管理</h3>
          <button @click="exportToExcel" class="export-btn">📥 匯出紀錄</button>
        </div>
        <div class="chat-selector">
          <label>切換對話頻道：</label>
          <select v-model="activeChatThread" @change="markCurrentThreadAsRead">
            <option value="" disabled selected>請選擇要查看的對話...</option>
            <optgroup label="👨‍👩‍👧 家長群"><option v-for="s in studentsList" :key="'p-'+s.id" :value="s.id+'_家長'">{{ s.seat_number }}號 {{ s.real_name }} 的家長</option></optgroup>
            <optgroup label="👩‍🎓 學生群"><option v-for="s in studentsList" :key="'s-'+s.id" :value="s.id+'_學生'">{{ s.seat_number }}號 {{ s.real_name }} (學生)</option></optgroup>
          </select>
        </div>
        <div v-if="!activeChatThread" class="empty-prompt">👈 請從上方選擇一個對話群組。</div>
        <div v-else>
          <div class="chat-container" id="adminChatContainer">
            <div v-if="filteredMessages.length === 0" class="empty">此頻道目前尚無通訊紀錄</div>
            <div v-for="msg in filteredMessages" :key="msg.id" :class="['chat-bubble', msg.sender_role === '導師' ? 'teacher-msg' : 'other-msg']">
              <div class="msg-info"><span class="sender">{{ msg.sender_role }}</span><span class="time">{{ formatTime(msg.created_at) }}</span></div>
              <div class="msg-content">{{ msg.content }}</div>
            </div>
          </div>
          <div class="reply-box">
            <input v-model="replyContent" type="text" placeholder="輸入回覆..." @keyup.enter="sendReply" />
            <button @click="sendReply" class="send-reply-btn" :disabled="isSending">📤 傳送</button>
          </div>
        </div>
      </main>

      <main v-if="currentTab === 'students'" class="data-table">
        <div class="table-header">
          <h3>👩‍🎓 學生名單與資料維護</h3>
          <div class="export-actions">
            <button @click="exportStudents('json')" class="export-btn json-btn">📤 匯出 JSON</button>
            <button @click="exportStudents('csv')" class="export-btn">📤 匯出 CSV</button>
          </div>
        </div>
        <div class="import-section">
          <div class="import-controls">
            <input type="file" accept=".json, .csv" @change="handleFileUpload" ref="fileInput" />
            <button @click="processImport" class="import-btn" :disabled="!selectedFile || isImporting">🚀 執行匯入</button>
          </div>
        </div>
        <div class="table-responsive">
          <table class="student-edit-table">
            <thead>
              <tr><th>座號</th><th>姓名</th><th>隱藏名</th><th>生日</th><th>後5碼</th><th>家長信箱 1</th><th>家長信箱 2</th><th>操作</th></tr>
            </thead>
            <tbody>
              <tr v-for="student in adminStudents" :key="student.id">
                <td><input type="number" v-model="student.seat_number" class="edit-input num-input"/></td>
                <td><input type="text" v-model="student.real_name" class="edit-input"/></td>
                <td><input type="text" v-model="student.hidden_name" class="edit-input"/></td>
                <td><input type="text" v-model="student.birthday" class="edit-input"/></td>
                <td><input type="text" v-model="student.id_last_5" maxlength="5" class="edit-input"/></td>
                <td><input type="email" v-model="student.parent_email_1" class="edit-input email-input"/></td>
                <td><input type="email" v-model="student.parent_email_2" class="edit-input email-input"/></td>
                <td class="action-cell">
                  <button @click="saveStudent(student)" class="save-row-btn">💾 儲存</button>
                  <button @click="deleteStudent(student.id, student.real_name)" class="del-row-btn">🗑️</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </main>

      <main v-if="currentTab === 'audit'" class="data-table">
        <h3>🕵️ 黑板編輯稽核紀錄</h3>
        <table>
          <thead><tr><th>時間</th><th>修改區塊</th><th>編輯者</th><th>IP 位址</th></tr></thead>
          <tbody>
            <tr v-for="log in boardLogs" :key="log.id">
              <td>{{ formatTime(log.edited_at) }}</td><td><span class="badge">{{ log.board_type }}</span></td>
              <td :class="log.editor_role === '導師' ? 'role-teacher' : 'role-student'">{{ log.editor_role }}</td>
              <td class="ip-text">{{ log.ip_address }}</td>
            </tr>
          </tbody>
        </table>
      </main>

      <main v-if="currentTab === 'communication'" class="data-table">
        <h3>📨 系統通知發送紀錄</h3>
        <table>
          <thead><tr><th>發送時間</th><th>收件學生</th><th>通知類型</th><th>收件信箱</th></tr></thead>
          <tbody>
            <tr v-for="log in commLogs" :key="log.id">
              <td>{{ formatTime(log.sent_at) }}</td><td>{{ getStudentName(log.student_id) }}</td>
              <td><span class="badge notice">{{ log.notification_type }}</span></td><td class="email-text">{{ log.recipient_emails }}</td>
            </tr>
          </tbody>
        </table>
      </main>

    </div>
  </div>
</template>

<script setup>
import { ref, computed, nextTick } from 'vue'
const supabase = useSupabaseClient()

// 日期時間處理
const d = new Date()
const todayISO = `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`
const todayDisplay = d.toLocaleDateString('zh-TW', { year: 'numeric', month: 'long', day: 'numeric', weekday: 'long' })

const isUnlocked = ref(false); const passwordInput = ref(''); const currentTab = ref('board')
const boardLogs = ref([]); const commLogs = ref([]); const allMessages = ref([])
const studentsMap = ref({}); const studentsList = ref([]); const adminStudents = ref([])

// 須知推播專用狀態
const adminNotices = ref([])
const isSavingBoard = ref(false)
const isSendingEmail = ref(false)

// (其他狀態省略以聚焦新功能...)
const activeChatThread = ref(''); const replyContent = ref(''); const isSending = ref(false)
const selectedFile = ref(null); const fileInput = ref(null); const isImporting = ref(false)

const filteredMessages = computed(() => {
  if (!activeChatThread.value) return []
  const [targetId, targetType] = activeChatThread.value.split('_')
  return allMessages.value.filter(m => m.student_id === targetId && m.chat_type === targetType)
})

const verifyPassword = async () => {
  if (passwordInput.value === '168168168') { isUnlocked.value = true; await fetchAllData() } 
  else { alert('❌ 密碼錯誤！'); passwordInput.value = '' }
}

const switchTab = async (tab) => { currentTab.value = tab; await fetchAllData() }

// ==================== 抓取資料 ====================
const fetchAllData = async () => {
  // 1. 抓取今日須知
  const { data: boardData } = await supabase.from('contact_books').select('notices').eq('record_date', todayISO).single()
  adminNotices.value = boardData?.notices || []

  // 2. 抓取稽核與紀錄
  const { data: bLogs } = await supabase.from('board_edit_logs').select('*').order('edited_at', { ascending: false }).limit(50)
  if (bLogs) boardLogs.value = bLogs
  const { data: cLogs } = await supabase.from('communication_logs').select('*').order('sent_at', { ascending: false }).limit(50)
  if (cLogs) commLogs.value = cLogs

  // 3. 抓取學生與家長
  const { data: sData } = await supabase.from('students').select('*').order('seat_number')
  const { data: pData } = await supabase.from('parents').select('*')
  if (sData) {
    studentsList.value = sData
    sData.forEach(s => { studentsMap.value[s.id] = s.real_name })
    adminStudents.value = sData.map(student => {
      const parents = pData ? pData.filter(p => p.student_id === student.id) : []
      return { ...student, parent_email_1: parents[0]?.email || '', parent_email_2: parents[1]?.email || '' }
    })
  }

  // 4. 抓取私訊
  const { data: msgLogs } = await supabase.from('private_messages').select('*').order('created_at', { ascending: true })
  if (msgLogs) { allMessages.value = msgLogs; scrollToBottom() }
}

// ==================== 須知推播邏輯 (全新) ====================
const addAdminNotice = () => adminNotices.value.push('')
const removeAdminNotice = (index) => adminNotices.value.splice(index, 1)

// 儲存須知
const saveAdminNotices = async () => {
  isSavingBoard.value = true
  adminNotices.value = adminNotices.value.filter(n => n.trim() !== '')

  // 確保不要覆蓋到前台股長寫的聯絡簿 (tasks)
  const { data: currentBoard } = await supabase.from('contact_books').select('tasks').eq('record_date', todayISO).single()
  const currentTasks = currentBoard?.tasks || []

  const { error } = await supabase.from('contact_books').upsert({
    record_date: todayISO,
    notices: adminNotices.value,
    tasks: currentTasks
  }, { onConflict: 'record_date' })

  if (error) {
    alert('❌ 儲存失敗！')
  } else {
    // 寫入稽核紀錄
    await supabase.from('board_edit_logs').insert({ board_date: todayISO, board_type: '家長須知 (後台)', editor_role: '導師', new_content: adminNotices.value })
    alert('✅ 儲存成功！已同步至教室前台。')
  }
  isSavingBoard.value = false
}

// 寄送群發信件 (Bcc)
const sendNoticeEmail = async () => {
  const pwd = window.prompt("🔒 準備寄送全班群發信，請輸入導師專屬密碼：")
  if (pwd !== '168168168') return alert('❌ 密碼錯誤，傳送取消！')

  if (adminNotices.value.length === 0) return alert('⚠️ 目前沒有任何須知事項可以發送！')

  isSendingEmail.value = true
  try {
    // 1. 抓取所有家長信箱
    const { data: parents } = await supabase.from('parents').select('email')
    if (!parents || parents.length === 0) throw new Error("目前沒有任何家長綁定信箱。")

    // 2. 去除重複信箱，組成 Bcc 名單
    const uniqueEmails = [...new Set(parents.map(p => p.email))]

    // 3. 組合信件內容
    const noticeText = adminNotices.value.map((n, i) => `${i + 1}. ${n}`).join('\n')
    const emailContent = `親愛的家長您好：\n\n以下為今日 (${todayDisplay}) 的重要班級須知，請您撥冗查閱：\n\n${noticeText}\n\n若有任何問題，歡迎登入系統私訊聯繫。\n\n班級導師 敬上`

    // 💡 實戰中這裡會呼叫您的後端 API 執行寄信
    // await fetch('/api/send-bulk-email', { method: 'POST', body: JSON.stringify({ bcc: uniqueEmails, content: emailContent }) })
    console.log(`[模擬寄信] 以密件副本(Bcc)發送給 ${uniqueEmails.length} 個信箱`, uniqueEmails)

    // 4. 寫入系統通訊紀錄 (作為鐵證！)
    await supabase.from('communication_logs').insert({
      notification_type: '家長須知群發',
      sent_by: '導師',
      recipient_emails: `全班家長 (${uniqueEmails.length} 個信箱, 密件副本)`,
      message_content: emailContent
    })

    alert(`✅ 推播成功！已將須知事項以「密件副本(Bcc)」發送至 ${uniqueEmails.length} 個家長信箱。`)
    await fetchAllData() // 刷新紀錄頁籤
  } catch (error) {
    alert(`❌ 發送失敗：${error.message}`)
  } finally {
    isSendingEmail.value = false
  }
}

// (以下省略：學生管理、匯入匯出、私訊等舊有邏輯，請沿用上一版的內容)
const handleFileUpload = (e) => { /* ... */ }
const processImport = async () => { /* ... */ }
const saveStudent = async (s) => { /* ... */ }
const deleteStudent = async (id, name) => { /* ... */ }
const exportStudents = (type) => { /* ... */ }
const markCurrentThreadAsRead = async () => { /* ... */ }
const sendReply = async () => { /* ... */ }
const exportToExcel = () => { /* ... */ }
const formatTime = (isoString) => new Date(isoString).toLocaleString('zh-TW', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
const getStudentName = (id) => studentsMap.value[id] || '未知'
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
.dashboard { max-width: 1300px; margin: 0 auto; padding: 20px; }
.admin-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 25px; background: white; padding: 15px 25px; border-radius: 12px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); flex-wrap: wrap; gap: 15px; }
.admin-header h2 { margin: 0; color: #0f172a; }
.header-buttons { display: flex; gap: 8px; flex-wrap: wrap; }
.header-buttons button { padding: 8px 15px; border: none; border-radius: 6px; cursor: pointer; font-weight: bold; background: #e2e8f0; color: #475569; }
.header-buttons button.active { background: #3b82f6; color: white; }
.back-btn { text-decoration: none; padding: 8px 15px; border-radius: 6px; font-weight: bold; background: #ef4444; color: white; display: inline-block; }
.data-table { background: white; padding: 25px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
.table-header { display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #e2e8f0; padding-bottom: 15px; margin-bottom: 20px; }
.subtitle { color: #64748b; margin: 0; font-weight: bold; }

/* 須知推播專屬樣式 */
.board-editor-container { background: #f8fafc; border: 1px solid #cbd5e1; border-radius: 8px; padding: 20px; }
.notice-edit-list { display: flex; flex-direction: column; gap: 15px; margin-bottom: 25px; }
.edit-item { display: flex; align-items: center; gap: 10px; }
.bullet { font-size: 1.2rem; }
.notice-input { flex: 1; font-size: 1.1rem; padding: 10px 15px; border: 1px solid #94a3b8; border-radius: 6px; background: white; }
.notice-input:focus { border-color: #3b82f6; outline: none; box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2); }
.add-btn { background: #e2e8f0; color: #334155; border: 1px dashed #94a3b8; padding: 10px; border-radius: 6px; font-weight: bold; cursor: pointer; transition: 0.2s; margin-top: 10px; }
.add-btn:hover { background: #cbd5e1; }
.action-bar { display: flex; justify-content: space-between; align-items: center; border-top: 2px dashed #cbd5e1; padding-top: 20px; gap: 15px; flex-wrap: wrap; }
.save-btn { background: #3b82f6; color: white; border: none; padding: 12px 24px; border-radius: 8px; font-size: 1.1rem; font-weight: bold; cursor: pointer; }
.email-btn { background: #f59e0b; color: white; border: none; padding: 12px 24px; border-radius: 8px; font-size: 1.1rem; font-weight: bold; cursor: pointer; }
.save-btn:disabled, .email-btn:disabled { background: #9ca3af; cursor: not-allowed; }

/* 其他保留的樣式... (請將之前版本的 table, chat, empty 等共用樣式貼在下方) */
.badge { background: #e0e7ff; color: #4338ca; padding: 4px 10px; border-radius: 20px; font-size: 0.85rem; font-weight: bold; }
.badge.notice { background: #fef3c7; color: #b45309; }
.del-row-btn { background: #ef4444; color: white; border: none; padding: 8px 12px; border-radius: 6px; cursor: pointer; }
table { width: 100%; border-collapse: collapse; text-align: left; font-size: 0.95rem; }
th, td { padding: 10px 8px; border-bottom: 1px solid #f1f5f9; }
th { background-color: #f8fafc; color: #64748b; font-weight: bold; }
.empty { text-align: center; color: #94a3b8; padding: 30px !important; }
</style>