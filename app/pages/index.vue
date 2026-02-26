<template>
  <div class="dashboard-container">
    
    <div class="left-panel">
      <div class="clock-card">
        <h2>🕒 {{ currentTime }}</h2>
        <div class="nav-links">
          <NuxtLink to="/parent-bind" class="nav-btn parent-btn">👨‍👩‍👧 家長綁定</NuxtLink>
          <NuxtLink to="/admin" class="nav-btn admin-btn">⚙️ 導師後台</NuxtLink>
        </div>
      </div>

      <div class="stats-row">
        <div class="stat-box total">應到: {{ students.length }}</div>
        <div class="stat-box present">已到: {{ presentCount }}</div>
        <div class="stat-box absent">未到: {{ absentCount }}</div>
      </div>

      <div class="punch-grid">
        <button 
          v-for="student in students" 
          :key="student.id"
          :class="['punch-btn', student.status === '已到' ? 'is-present' : 'is-absent']"
          @click="toggleStatus(student)"
          :disabled="isUpdating"
        >
          <span class="seat-num">{{ student.seat_number }}</span>
          <span class="hidden-name">{{ student.hidden_name }}</span>
          <span class="status-text">{{ student.status }}</span>
          <span v-if="student.status === '已到' && student.punch_time" class="time-text">
            {{ student.punch_time }}
          </span>
        </button>
      </div>
    </div>

    <div class="right-panel">
      <div class="chalkboard">
        
        <div class="section-container">
          <div class="board-header">
            <h3 class="notice-title">📢 家長須知事項</h3>
            <button v-if="!isEditingNotices" @click="requestEdit('notices')" class="edit-btn">✏️ 編輯</button>
            <div v-else class="edit-actions">
              <span class="editor-badge">{{ currentNoticeEditor }}編輯中</span>
              <button @click="addNotice" class="add-btn">➕ 新增</button>
              <button @click="saveBoard('notices')" class="save-btn">💾 儲存</button>
            </div>
          </div>
          
          <ul v-if="!isEditingNotices" class="task-list notice-list">
            <li v-for="(notice, index) in notices" :key="'n-'+index">
              <span class="bullet">📌</span> {{ notice }}
            </li>
            <li v-if="notices.length === 0" class="empty-text">目前無特別須知事項</li>
          </ul>

          <ul v-else class="task-list editing">
            <li v-for="(notice, index) in notices" :key="'edit-n-'+index" class="edit-item">
              <span class="bullet">📌</span>
              <input v-model="notices[index]" type="text" class="edit-input notice-input" placeholder="輸入家長須知..." />
              <button @click="removeNotice(index)" class="delete-btn">🗑️</button>
            </li>
          </ul>
        </div>

        <hr class="board-divider" />

        <div class="section-container">
          <div class="board-header">
            <div>
              <h3>⭐ 今日聯絡簿</h3>
              <p class="date-text">{{ todayDisplay }}</p>
            </div>
            <button v-if="!isEditingTasks" @click="requestEdit('tasks')" class="edit-btn">✏️ 編輯</button>
            <div v-else class="edit-actions">
              <span class="editor-badge">{{ currentTaskEditor }}編輯中</span>
              <button @click="addTask" class="add-btn">➕ 新增</button>
              <button @click="saveBoard('tasks')" class="save-btn">💾 儲存</button>
            </div>
          </div>
          
          <ul v-if="!isEditingTasks" class="task-list">
            <li v-for="(task, index) in tasks" :key="'t-'+index">
              <span class="number">{{ index + 1 }}</span> {{ task }}
            </li>
            <li v-if="tasks.length === 0" class="empty-text">目前尚無聯絡簿事項...</li>
          </ul>

          <ul v-else class="task-list editing">
            <li v-for="(task, index) in tasks" :key="'edit-t-'+index" class="edit-item">
              <span class="number">{{ index + 1 }}</span>
              <input v-model="tasks[index]" type="text" class="edit-input" placeholder="輸入聯絡簿事項..." />
              <button @click="removeTask(index)" class="delete-btn">🗑️</button>
            </li>
          </ul>
        </div>

      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
const supabase = useSupabaseClient()

// ==================== 基礎日期與時間 ====================
const currentTime = ref('')
let timer = null
const d = new Date()
const todayISO = `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`
const todayDisplay = d.toLocaleDateString('zh-TW', { year: 'numeric', month: 'long', day: 'numeric', weekday: 'long' })

const updateClock = () => {
  currentTime.value = new Date().toLocaleTimeString('zh-TW', { hour12: false })
}

// ==================== 左側：學生與打卡 ====================
const students = ref([])
const isUpdating = ref(false)

const presentCount = computed(() => students.value.filter(s => s.status === '已到').length)
const absentCount = computed(() => students.value.filter(s => s.status === '未到').length)

const fetchStudentsAndAttendance = async () => {
  const { data: studentData } = await supabase.from('students').select('*').order('seat_number')
  const { data: attendanceData } = await supabase.from('attendances').select('*').eq('record_date', todayISO)

  if (studentData) {
    students.value = studentData.map(student => {
      const record = attendanceData?.find(a => a.student_id === student.id)
      return {
        ...student,
        status: record ? record.status : '未到',
        punch_time: record ? record.punch_time : null
      }
    })
  }
}

const toggleStatus = async (student) => {
  isUpdating.value = true
  const newStatus = student.status === '未到' ? '已到' : '未到'
  const newPunchTime = newStatus === '已到' ? new Date().toLocaleTimeString('zh-TW', { hour12: false }) : null

  const oldStatus = student.status
  const oldPunchTime = student.punch_time

  student.status = newStatus
  student.punch_time = newPunchTime

  const { error } = await supabase.from('attendances').upsert({
    student_id: student.id,
    record_date: todayISO,
    status: newStatus,
    punch_time: newPunchTime
  }, { onConflict: 'student_id, record_date' })

  if (error) {
    student.status = oldStatus
    student.punch_time = oldPunchTime
  }
  isUpdating.value = false
}

// ==================== 右側：電子黑板邏輯 ====================
const notices = ref([])
const tasks = ref([])
const isEditingNotices = ref(false)
const isEditingTasks = ref(false)
const currentNoticeEditor = ref('')
const currentTaskEditor = ref('')

// 從資料庫讀取黑板內容
const fetchContactBook = async () => {
  const { data } = await supabase.from('contact_books').select('tasks, notices').eq('record_date', todayISO).single()
  if (data) {
    tasks.value = data.tasks || []
    notices.value = data.notices || []
  } else {
    // 假資料預設值
    notices.value = ['記得量體溫', '下週起換季服裝']
    tasks.value = ['國習 P.30-32', '數作 Ch.3', '交午餐回條']
  }
}

// === 權限與密碼驗證邏輯 ===
const requestEdit = (type) => {
  const pwd = window.prompt("🔒 請輸入權限密碼：")
  if (!pwd) return // 取消輸入

  if (type === 'notices') {
    if (pwd === '168168168') {
      currentNoticeEditor.value = '導師'
      isEditingNotices.value = true
    } else {
      alert("❌ 密碼錯誤！只有導師可以編輯家長須知。")
    }
  } else if (type === 'tasks') {
    if (pwd === '168168168') {
      currentTaskEditor.value = '導師'
      isEditingTasks.value = true
    } else if (pwd === '268268268') {
      currentTaskEditor.value = '股長'
      isEditingTasks.value = true
    } else {
      alert("❌ 密碼錯誤！")
    }
  }
}

// 新增/刪除
const addNotice = () => notices.value.push('')
const removeNotice = (index) => notices.value.splice(index, 1)
const addTask = () => tasks.value.push('')
const removeTask = (index) => tasks.value.splice(index, 1)

// === 存檔與寫入稽核紀錄 ===
const saveBoard = async (type) => {
  // 1. 過濾空白輸入
  notices.value = notices.value.filter(n => n.trim() !== '')
  tasks.value = tasks.value.filter(t => t.trim() !== '')

  // 2. 更新到 contact_books (必須同時傳入兩者，以免覆蓋遺失)
  const { error } = await supabase.from('contact_books').upsert({
    record_date: todayISO,
    notices: notices.value,
    tasks: tasks.value
  }, { onConflict: 'record_date' })

  if (error) { alert('儲存失敗！'); return; }

  // 3. 抓取當下使用者的 IP (使用免費的 ipify API)
  let ip = '無法取得'
  try {
    const res = await fetch('https://api.ipify.org?format=json')
    const ipData = await res.json()
    ip = ipData.ip
  } catch (e) { console.warn('IP 抓取失敗') }

  // 4. 準備稽核紀錄寫入資料
  const editorRole = type === 'notices' ? currentNoticeEditor.value : currentTaskEditor.value
  const boardType = type === 'notices' ? '家長須知' : '聯絡簿'
  const contentToSave = type === 'notices' ? notices.value : tasks.value

  // 寫入 Supabase Log 表
  await supabase.from('board_edit_logs').insert({
    board_date: todayISO,
    board_type: boardType,
    editor_role: editorRole,
    ip_address: ip,
    user_agent: navigator.userAgent, // 紀錄瀏覽器與裝置資訊
    new_content: contentToSave
  })

  // 5. 關閉編輯模式
  if (type === 'notices') isEditingNotices.value = false
  if (type === 'tasks') isEditingTasks.value = false
}

onMounted(() => {
  updateClock()
  timer = setInterval(updateClock, 1000)
  fetchStudentsAndAttendance()
  fetchContactBook()
})
onUnmounted(() => clearInterval(timer))
</script>

<style scoped>
/* 首頁導覽按鈕樣式 */
.nav-links { display: flex; justify-content: center; gap: 10px; margin-top: 10px; }
.nav-btn { text-decoration: none; padding: 6px 12px; border-radius: 6px; font-size: 0.9rem; font-weight: bold; transition: opacity 0.2s; }
.nav-btn:hover { opacity: 0.8; }
.parent-btn { background-color: #f59e0b; color: white; }
.admin-btn { background-color: #64748b; color: white; }

/* 基礎排版保留 */
.dashboard-container { display: flex; gap: 20px; padding: 20px; background-color: #f5f7fa; min-height: 100vh; font-family: 'sans-serif'; }
.left-panel, .right-panel { flex: 1; display: flex; flex-direction: column; gap: 20px; }
.clock-card { background: white; border-radius: 12px; text-align: center; padding: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); font-size: 2rem; color: #2c3e50; border: 2px solid #e2e8f0; }
.stats-row { display: flex; justify-content: space-between; gap: 10px; }
.stat-box { flex: 1; text-align: center; padding: 10px; border-radius: 8px; font-weight: bold; border: 1px solid #ddd; }
.stat-box.total { background: #fff3cd; color: #856404; }
.stat-box.present { background: #d4edda; color: #155724; }
.stat-box.absent { background: #f8d7da; color: #721c24; }

.punch-grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 10px; }
.punch-btn { display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 15px 5px; border-radius: 8px; border: none; cursor: pointer; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
.seat-num { font-size: 1.5rem; font-weight: bold; margin-bottom: 2px; }
.hidden-name { font-size: 1.1rem; font-weight: bold; margin-bottom: 5px; opacity: 0.85; } /* 隱藏姓名樣式 */
.status-text { font-size: 0.9rem; }
.time-text { font-size: 0.8rem; margin-top: 5px; opacity: 0.8; font-family: monospace; }
.is-absent { background-color: #ffe4e6; color: #e11d48; border: 1px solid #fecdd3; }
.is-present { background-color: #dcfce7; color: #16a34a; border: 1px solid #bbf7d0; }

/* 黑板樣式優化，加入捲動條 */
.chalkboard { background-color: #2d4a3e; border: 12px solid #8b5a2b; border-radius: 16px; padding: 25px; color: #fdf6e3; box-shadow: inset 0 0 20px rgba(0,0,0,0.5), 5px 5px 15px rgba(0,0,0,0.2); height: 100%; overflow-y: auto; }
.board-divider { border: none; border-top: 2px dashed #8b5a2b; margin: 25px 0; opacity: 0.7; }

.board-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; }
.board-header h3 { font-size: 1.6rem; margin: 0 0 5px 0; color: #fbbf24; }
.notice-title { color: #fca5a5 !important; } /* 讓家長須知標題顏色不同 (粉筆紅) */
.date-text { font-size: 1.1rem; margin: 0; opacity: 0.9; }

.task-list { list-style: none; padding: 0; font-size: 1.3rem; line-height: 1.8; }
.task-list li { margin-bottom: 15px; display: flex; align-items: center; }
.bullet { margin-right: 15px; font-size: 1.2rem; }
.number { background-color: #6b8e23; color: white; border-radius: 50%; width: 28px; height: 28px; display: inline-flex; align-items: center; justify-content: center; margin-right: 15px; font-size: 1rem; flex-shrink: 0; }
.empty-text { color: #9ca3af; font-style: italic; }

button { font-family: inherit; }
.edit-btn, .save-btn, .add-btn { background: #fbbf24; border: none; padding: 6px 12px; border-radius: 6px; font-weight: bold; cursor: pointer; color: #5f3f00; font-size: 0.9rem; }
.save-btn { background: #4ade80; color: #064e3b; margin-left: 10px; }
.add-btn { background: #cbd5e1; color: #1e293b; }
.editor-badge { background: #dc2626; color: white; padding: 4px 8px; border-radius: 4px; font-size: 0.8rem; margin-right: 10px; font-weight: bold; }

.edit-item { gap: 10px; }
.edit-input { flex: 1; font-size: 1.1rem; padding: 5px 10px; border-radius: 4px; border: none; background: rgba(255,255,255,0.9); }
.notice-input { background: #fee2e2; } /* 編輯須知時輸入框底色不同 */
.delete-btn { background: #ef4444; color: white; border: none; padding: 5px 10px; border-radius: 4px; cursor: pointer; }
</style>