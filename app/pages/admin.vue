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
          <button @click="currentTab = 'audit'" :class="{ active: currentTab === 'audit' }">🕵️ 黑板編輯稽核</button>
          <button @click="currentTab = 'communication'" :class="{ active: currentTab === 'communication' }">📨 系統通訊紀錄</button>
          <NuxtLink to="/" class="back-btn">⬅️ 返回前台</NuxtLink>
        </div>
      </header>

      <main v-if="currentTab === 'audit'" class="data-table">
        <h3>🕵️ 最近 50 筆黑板編輯紀錄</h3>
        <table>
          <thead>
            <tr>
              <th>時間</th>
              <th>修改區塊</th>
              <th>編輯者</th>
              <th>IP 位址</th>
              <th>裝置資訊 (擷取)</th>
            </tr>
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
            <tr>
              <th>發送時間</th>
              <th>收件學生</th>
              <th>通知類型</th>
              <th>發送者</th>
              <th>收件信箱</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="log in commLogs" :key="log.id">
              <td>{{ formatTime(log.sent_at) }}</td>
              <td>{{ getStudentName(log.student_id) }}</td>
              <td><span class="badge notice">{{ log.notification_type }}</span></td>
              <td>{{ log.sent_by }}</td>
              <td class="email-text">{{ log.recipient_emails }}</td>
            </tr>
            <tr v-if="commLogs.length === 0"><td colspan="5" class="empty">目前尚無通訊紀錄</td></tr>
          </tbody>
        </table>
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
const supabase = useSupabaseClient()

// 密碼防護邏輯
const isUnlocked = ref(false)
const passwordInput = ref('')
const currentTab = ref('audit') // 預設顯示稽核紀錄

// 資料陣列
const boardLogs = ref([])
const commLogs = ref([])
const studentsMap = ref({}) // 用來快速對應 student_id 到學生姓名

// 驗證密碼
const verifyPassword = async () => {
  if (passwordInput.value === '168168168') {
    isUnlocked.value = true
    await fetchAllData() // 解鎖成功才去撈資料
  } else {
    alert('❌ 密碼錯誤，拒絕存取！')
    passwordInput.value = ''
  }
}

// 撈取資料 (限制最新 50 筆避免載入過久)
const fetchAllData = async () => {
  // 1. 抓取編輯稽核紀錄
  const { data: bLogs } = await supabase.from('board_edit_logs').select('*').order('edited_at', { ascending: false }).limit(50)
  if (bLogs) boardLogs.value = bLogs

  // 2. 抓取通訊紀錄
  const { data: cLogs } = await supabase.from('communication_logs').select('*').order('sent_at', { ascending: false }).limit(50)
  if (cLogs) commLogs.value = cLogs

  // 3. 抓取學生名單 (為了對應通訊紀錄的 UUID 到學生姓名)
  const { data: sData } = await supabase.from('students').select('id, real_name')
  if (sData) {
    sData.forEach(s => { studentsMap.value[s.id] = s.real_name })
  }
}

// 格式化時間工具
const formatTime = (isoString) => {
  const d = new Date(isoString)
  return d.toLocaleString('zh-TW', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false })
}

// 擷取裝置資訊工具 (User-Agent 通常很長，取前 30 個字就好)
const shortenAgent = (agent) => {
  if (!agent) return '未知裝置'
  return agent.length > 30 ? agent.substring(0, 30) + '...' : agent
}

// 取得學生姓名
const getStudentName = (id) => studentsMap.value[id] || '未知學生'

</script>

<style scoped>
/* 滿版背景設定 */
.admin-container { min-height: 100vh; background-color: #f1f5f9; font-family: sans-serif; }

/* 鎖定畫面樣式 */
.lock-screen { display: flex; justify-content: center; align-items: center; height: 100vh; background-color: #1e293b; }
.lock-box { background: white; padding: 40px; border-radius: 12px; text-align: center; box-shadow: 0 10px 25px rgba(0,0,0,0.5); width: 400px; }
.lock-box h2 { color: #334155; margin-bottom: 10px; }
.lock-box p { color: #64748b; margin-bottom: 25px; }
.lock-box input { width: 100%; padding: 12px; margin-bottom: 20px; border: 1px solid #cbd5e1; border-radius: 6px; font-size: 1.2rem; text-align: center; box-sizing: border-box; }
.lock-box button { width: 100%; padding: 12px; background-color: #3b82f6; color: white; border: none; border-radius: 6px; font-size: 1.1rem; cursor: pointer; font-weight: bold; }
.lock-box button:hover { background-color: #2563eb; }

/* 後台主畫面樣式 */
.dashboard { max-width: 1200px; margin: 0 auto; padding: 30px; }
.admin-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; background: white; padding: 20px 30px; border-radius: 12px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); }
.admin-header h2 { margin: 0; color: #0f172a; }
.admin-header button { margin-right: 10px; padding: 10px 20px; border: none; border-radius: 6px; cursor: pointer; font-weight: bold; background: #e2e8f0; color: #475569; }
.admin-header button.active { background: #3b82f6; color: white; }
.back-btn { text-decoration: none; padding: 10px 20px; border-radius: 6px; font-weight: bold; background: #ef4444; color: white; display: inline-block; }

/* 表格樣式 */
.data-table { background: white; padding: 25px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
.data-table h3 { margin-top: 0; color: #334155; border-bottom: 2px solid #e2e8f0; padding-bottom: 15px; margin-bottom: 20px; }
table { width: 100%; border-collapse: collapse; text-align: left; }
th, td { padding: 12px 15px; border-bottom: 1px solid #f1f5f9; }
th { background-color: #f8fafc; color: #64748b; font-weight: bold; }
tr:hover { background-color: #f8fafc; }
.empty { text-align: center; color: #94a3b8; padding: 30px !important; }

/* 標籤與文字微調 */
.badge { background: #e0e7ff; color: #4338ca; padding: 4px 10px; border-radius: 20px; font-size: 0.85rem; font-weight: bold; }
.badge.notice { background: #fef3c7; color: #b45309; }
.role-teacher { color: #dc2626; font-weight: bold; }
.role-student { color: #059669; font-weight: bold; }
.ip-text { font-family: monospace; color: #475569; }
.device-text, .email-text { font-size: 0.9rem; color: #64748b; }
</style>