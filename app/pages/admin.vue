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
          <button @click="switchTab('messages')" :class="{ active: currentTab === 'messages' }">💬 私訊管理</button>
          <button @click="switchTab('students')" :class="{ active: currentTab === 'students' }">👩‍🎓 學生管理</button>
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

        <div v-if="!activeChatThread" class="empty-prompt">👈 請從上方選擇一個對話群組來檢視歷史訊息與回覆。</div>

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

      <main v-if="currentTab === 'students'" class="data-table">
        <div class="table-header">
          <h3>👩‍🎓 學生名單與資料維護</h3>
        </div>

        <div class="import-section">
          <div class="import-info">
            <h4>📁 批次匯入學生資料 (JSON 格式)</h4>
            <p>請準備包含 <code>school_name, enroll_year, class_name, student_id, seat_number, real_name, hidden_name, birthday, id_last_5</code> 欄位的 JSON 陣列檔案。</p>
          </div>
          <div class="import-controls">
            <input type="file" accept=".json" @change="handleFileUpload" ref="fileInput" />
            <button @click="processJsonImport" class="import-btn" :disabled="!selectedJsonFile || isImporting">
              {{ isImporting ? '匯入中...' : '🚀 執行匯入' }}
            </button>
          </div>
        </div>

        <div class="table-responsive">
          <table class="student-edit-table">
            <thead>
              <tr>
                <th width="60">座號</th>
                <th width="90">學號</th>
                <th width="100">姓名</th>
                <th width="100">隱藏名</th>
                <th width="100">生日(YYYYMMDD)</th>
                <th width="90">身分證後5碼</th>
                <th width="120">學校/入學/班級</th>
                <th width="120">操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="student in adminStudents" :key="student.id">
                <td><input type="number" v-model="student.seat_number" class="edit-input num-input"/></td>
                <td><input type="text" v-model="student.student_id" class="edit-input"/></td>
                <td><input type="text" v-model="student.real_name" class="edit-input"/></td>
                <td><input type="text" v-model="student.hidden_name" class="edit-input"/></td>
                <td><input type="text" v-model="student.birthday" class="edit-input"/></td>
                <td><input type="text" v-model="student.id_last_5" maxlength="5" class="edit-input"/></td>
                <td>
                  <input type="text" v-model="student.school_name" class="edit-input small-input" title="學校"/>
                  <input type="number" v-model="student.enroll_year" class="edit-input small-input" title="入學年"/>
                  <input type="text" v-model="student.class_name" class="edit-input small-input" title="班級"/>
                </td>
                <td class="action-cell">
                  <button @click="saveStudent(student)" class="save-row-btn">💾 儲存</button>
                  <button @click="deleteStudent(student.id, student.real_name)" class="del-row-btn">🗑️</button>
                </td>
              </tr>
              <tr v-if="adminStudents.length === 0"><td colspan="8" class="empty">目前尚無學生資料，請由上方匯入</td></tr>
            </tbody>
          </table>
        </div>
      </main>

      <main v-if="currentTab === 'audit'" class="data-table">
        <h3>🕵️ 最近 50 筆黑板編輯紀錄</h3>
        <table>
          <thead><tr><th>時間</th><th>修改區塊</th><th>編輯者</th><th>IP 位址</th><th>裝置資訊</th></tr></thead>
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
          <thead><tr><th>發送時間</th><th>收件學生</th><th>通知類型</th><th>發送者</th><th>收件信箱</th></tr></thead>
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
import { ref, computed, nextTick } from 'vue'
const supabase = useSupabaseClient()

const isUnlocked = ref(false); const passwordInput = ref(''); const currentTab = ref('messages')
const boardLogs = ref([]); const commLogs = ref([]); const allMessages = ref([])
const studentsMap = ref({}); const studentsList = ref([])

// 學生資料管理專用
const adminStudents = ref([])
const selectedJsonFile = ref(null)
const fileInput = ref(null)
const isImporting = ref(false)

// 聊天室專用狀態
const activeChatThread = ref(''); const replyContent = ref(''); const isSending = ref(false)

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

const fetchAllData = async () => {
  // 抓取稽核與紀錄
  const { data: bLogs } = await supabase.from('board_edit_logs').select('*').order('edited_at', { ascending: false }).limit(50)
  if (bLogs) boardLogs.value = bLogs
  const { data: cLogs } = await supabase.from('communication_logs').select('*').order('sent_at', { ascending: false }).limit(50)
  if (cLogs) commLogs.value = cLogs

  // 抓取全班完整資料供「學生管理」頁籤使用
  const { data: sData } = await supabase.from('students').select('*').order('seat_number')
  if (sData) {
    adminStudents.value = sData // 綁定到編輯表格
    studentsList.value = sData  // 綁定到下拉選單
    sData.forEach(s => { studentsMap.value[s.id] = s.real_name })
  }

  // 抓取私訊
  const { data: msgLogs } = await supabase.from('private_messages').select('*').order('created_at', { ascending: true })
  if (msgLogs) { allMessages.value = msgLogs; scrollToBottom() }
}

// ==================== 學生資料管理邏輯 ====================

// 處理選擇檔案
const handleFileUpload = (event) => {
  const file = event.target.files[0]
  if (file && file.type === "application/json") { selectedJsonFile.value = file } 
  else { alert("請上傳正確的 .json 檔案！"); selectedJsonFile.value = null; fileInput.value.value = "" }
}

// 執行 JSON 匯入
const processJsonImport = async () => {
  if (!selectedJsonFile.value) return
  isImporting.value = true
  const reader = new FileReader()
  
  reader.onload = async (e) => {
    try {
      const parsedData = JSON.parse(e.target.result)
      if (!Array.isArray(parsedData)) throw new Error("JSON 格式錯誤，必須是一個陣列 (Array)。")
      
      const { error } = await supabase.from('students').insert(parsedData)
      if (error) throw error

      alert(`✅ 成功匯入 ${parsedData.length} 筆學生資料！`)
      selectedJsonFile.value = null; fileInput.value.value = "" // 重置輸入框
      await fetchAllData() // 刷新表格
    } catch (error) {
      alert(`❌ 匯入失敗：\n${error.message}\n請檢查 JSON 欄位與格式是否正確。`)
    } finally {
      isImporting.value = false
    }
  }
  reader.readAsText(selectedJsonFile.value)
}

// 單筆儲存手動修改
const saveStudent = async (student) => {
  const { error } = await supabase.from('students').update({
    seat_number: student.seat_number,
    student_id: student.student_id,
    real_name: student.real_name,
    hidden_name: student.hidden_name,
    birthday: student.birthday,
    id_last_5: student.id_last_5,
    school_name: student.school_name,
    enroll_year: student.enroll_year,
    class_name: student.class_name
  }).eq('id', student.id)

  if (error) alert(`❌ 更新 ${student.real_name} 失敗！`)
  else alert(`✅ ${student.real_name} 的資料已更新！`)
}

// 單筆刪除學生
const deleteStudent = async (id, name) => {
  if (!window.confirm(`⚠️ 警告：確定要刪除「${name}」的所有資料嗎？這將會同步刪除他的打卡與私訊紀錄！`)) return
  
  const { error } = await supabase.from('students').delete().eq('id', id)
  if (error) alert('❌ 刪除失敗！')
  else { alert(`✅ 已刪除 ${name}`); await fetchAllData() }
}

// ==================== 私訊與其他邏輯 ====================

const markCurrentThreadAsRead = async () => {
  if (!activeChatThread.value) return
  const [targetId, targetType] = activeChatThread.value.split('_')
  await supabase.from('private_messages').update({ is_read_by_teacher: true }).eq('student_id', targetId).eq('chat_type', targetType).eq('is_read_by_teacher', false)
  scrollToBottom()
}

const sendReply = async () => {
  if (!activeChatThread.value || !replyContent.value.trim()) return
  const pwd = window.prompt("🔒 傳送前請再次輸入導師專屬密碼：")
  if (pwd !== '168168168') return alert('❌ 密碼錯誤，傳送取消！')

  const [targetId, targetType] = activeChatThread.value.split('_'); isSending.value = true
  try {
    await supabase.from('private_messages').insert({ student_id: targetId, sender_role: '導師', chat_type: targetType, content: replyContent.value, is_read_by_teacher: true })
    alert('✅ 回覆成功！'); replyContent.value = ''; await fetchAllData()
  } catch (error) { alert('發生錯誤') } finally { isSending.value = false }
}

const exportToExcel = () => {
  let csvContent = "data:text/csv;charset=utf-8,\uFEFF"; csvContent += "發送時間,學生姓名,對話頻道,發送者,訊息內容\n"
  allMessages.value.forEach(msg => {
    const time = formatTime(msg.created_at); const name = studentsMap.value[msg.student_id] || '未知'; const content = msg.content.replace(/"/g, '""')
    csvContent += `"${time}","${name}","${msg.chat_type}","${msg.sender_role}","${content}"\n`
  })
  const link = document.createElement("a"); link.setAttribute("href", encodeURI(csvContent))
  link.setAttribute("download", `班級私訊紀錄_${new Date().getTime()}.csv`)
  document.body.appendChild(link); link.click(); document.body.removeChild(link)
}

const formatTime = (isoString) => new Date(isoString).toLocaleString('zh-TW', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
const shortenAgent = (agent) => agent ? (agent.length > 30 ? agent.substring(0, 30) + '...' : agent) : '未知'
const getStudentName = (id) => studentsMap.value[id] || '未知'
const scrollToBottom = () => { nextTick(() => { const c = document.getElementById('adminChatContainer'); if (c) c.scrollTop = c.scrollHeight }) }
</script>

<style scoped>
/* 基礎樣式 */
.admin-container { min-height: 100vh; background-color: #f1f5f9; font-family: sans-serif; }
.lock-screen { display: flex; justify-content: center; align-items: center; height: 100vh; background-color: #1e293b; }
.lock-box { background: white; padding: 40px; border-radius: 12px; text-align: center; box-shadow: 0 10px 25px rgba(0,0,0,0.5); width: 400px; }
.lock-box h2 { color: #334155; margin-bottom: 10px; }
.lock-box input { width: 100%; padding: 12px; margin-bottom: 20px; border: 1px solid #cbd5e1; border-radius: 6px; font-size: 1.2rem; text-align: center; }
.lock-box button { width: 100%; padding: 12px; background-color: #3b82f6; color: white; border: none; border-radius: 6px; font-size: 1.1rem; cursor: pointer; font-weight: bold; }
.dashboard { max-width: 1250px; margin: 0 auto; padding: 20px; }
.admin-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 25px; background: white; padding: 15px 25px; border-radius: 12px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); flex-wrap: wrap; gap: 15px; }
.admin-header h2 { margin: 0; color: #0f172a; }
.header-buttons { display: flex; gap: 8px; flex-wrap: wrap; }
.header-buttons button { padding: 8px 15px; border: none; border-radius: 6px; cursor: pointer; font-weight: bold; background: #e2e8f0; color: #475569; }
.header-buttons button.active { background: #3b82f6; color: white; }
.back-btn { text-decoration: none; padding: 8px 15px; border-radius: 6px; font-weight: bold; background: #ef4444; color: white; display: inline-block; }

.data-table { background: white; padding: 25px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
.table-header { display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #e2e8f0; padding-bottom: 15px; margin-bottom: 20px; }
.table-header h3, .data-table h3 { margin: 0; color: #334155; }
.export-btn { background-color: #10b981; color: white; border: none; padding: 8px 16px; border-radius: 6px; font-weight: bold; cursor: pointer; }

table { width: 100%; border-collapse: collapse; text-align: left; font-size: 0.95rem; }
th, td { padding: 10px 8px; border-bottom: 1px solid #f1f5f9; }
th { background-color: #f8fafc; color: #64748b; font-weight: bold; }
tr:hover { background-color: #f8fafc; }
.empty { text-align: center; color: #94a3b8; padding: 30px !important; }

/* 學生資料管理專屬樣式 */
.import-section { background: #f0fdf4; border: 1px dashed #4ade80; padding: 15px 20px; border-radius: 8px; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 15px; }
.import-info h4 { margin: 0 0 5px 0; color: #166534; }
.import-info p { margin: 0; color: #15803d; font-size: 0.9rem; }
.import-info code { background: #dcfce7; padding: 2px 6px; border-radius: 4px; font-family: monospace; }
.import-controls { display: flex; gap: 10px; align-items: center; }
.import-btn { background: #22c55e; color: white; font-weight: bold; border: none; padding: 8px 15px; border-radius: 6px; cursor: pointer; }
.import-btn:disabled { background: #9ca3af; cursor: not-allowed; }

.table-responsive { overflow-x: auto; }
.student-edit-table input { width: 100%; box-sizing: border-box; }
.edit-input { padding: 6px; border: 1px solid #cbd5e1; border-radius: 4px; background: transparent; transition: 0.2s; }
.edit-input:focus { border-color: #3b82f6; background: white; outline: none; box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2); }
.num-input { width: 50px; text-align: center; }
.small-input { font-size: 0.85rem; padding: 4px; margin-bottom: 3px; display: block; }
.action-cell { display: flex; gap: 5px; }
.save-row-btn { background: #3b82f6; color: white; border: none; padding: 6px 10px; border-radius: 4px; cursor: pointer; font-size: 0.85rem; white-space: nowrap; }
.del-row-btn { background: #ef4444; color: white; border: none; padding: 6px 10px; border-radius: 4px; cursor: pointer; }

/* 聊天與紀錄樣式保留... */
.badge { background: #e0e7ff; color: #4338ca; padding: 4px 10px; border-radius: 20px; font-size: 0.85rem; font-weight: bold; }
.badge.notice { background: #fef3c7; color: #b45309; }
.role-teacher { color: #dc2626; font-weight: bold; }
.role-student { color: #059669; font-weight: bold; }
.ip-text { font-family: monospace; color: #475569; }
.device-text, .email-text { font-size: 0.9rem; color: #64748b; }
.chat-selector { margin-bottom: 15px; background: #f8fafc; padding: 15px; border-radius: 8px; border: 1px solid #cbd5e1; }
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