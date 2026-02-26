<template>
  <div class="dashboard-container">
    
    <div class="top-notice-board chalkboard">
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
        <li v-for="(notice, index) in notices" :key="'n-'+index"><span class="bullet">📌</span> {{ notice }}</li>
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

    <div class="main-content">
      
      <div class="left-panel">
        <div class="clock-card">
          <h2>🕒 {{ currentTime }}</h2>
<div class="nav-links">
            <NuxtLink to="/parent-bind" class="nav-btn parent-btn">👨‍👩‍👧 綁定</NuxtLink>
            <NuxtLink to="/parent-message" class="nav-btn msg-btn">💬 家長私訊</NuxtLink>
            <NuxtLink to="/student-message" class="nav-btn stu-btn">💬 學生私訊</NuxtLink>
            <NuxtLink to="/admin" class="nav-btn admin-btn">
              ⚙️ 後台 <span v-if="unreadCount > 0" class="notification-badge">{{ unreadCount }}</span>
            </NuxtLink>
          </div>
        </div>

        <div class="stats-row">
          <div class="stat-box total">應到: {{ students.length }}</div>
          <div class="stat-box present">已到: {{ presentCount }}</div>
          <div class="stat-box absent">未到: {{ absentCount }}</div>
        </div>

        <div class="punch-grid">
          <button 
            v-for="student in students" :key="student.id"
            :class="['punch-btn', student.status === '已到' ? 'is-present' : 'is-absent']"
            @click="toggleStatus(student)" :disabled="isUpdating"
          >
            <span class="seat-num">{{ student.seat_number }}</span>
            <span class="hidden-name">{{ student.hidden_name }}</span>
            <span class="status-text">{{ student.status }}</span>
            <span v-if="student.status === '已到' && student.punch_time" class="time-text">{{ student.punch_time }}</span>
          </button>
        </div>
      </div>

      <div class="right-panel">
        <div class="chalkboard">
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
            <li v-for="(task, index) in tasks" :key="'t-'+index"><span class="number">{{ index + 1 }}</span> {{ task }}</li>
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

// 日期時間邏輯
const currentTime = ref('')
let timer = null
const d = new Date()
const todayISO = `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`
const todayDisplay = d.toLocaleDateString('zh-TW', { year: 'numeric', month: 'long', day: 'numeric', weekday: 'long' })

const updateClock = () => { currentTime.value = new Date().toLocaleTimeString('zh-TW', { hour12: false }) }

// 學生打卡邏輯
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
      return { ...student, status: record ? record.status : '未到', punch_time: record ? record.punch_time : null }
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
  const { error } = await supabase.from('attendances').upsert({ student_id: student.id, record_date: todayISO, status: newStatus, punch_time: newPunchTime }, { onConflict: 'student_id, record_date' })
  if (error) { student.status = oldStatus; student.punch_time = oldPunchTime }
  isUpdating.value = false
}

// 黑板與聯絡簿邏輯
const notices = ref([])
const tasks = ref([])
const isEditingNotices = ref(false)
const isEditingTasks = ref(false)
const currentNoticeEditor = ref('')
const currentTaskEditor = ref('')

const fetchContactBook = async () => {
  const { data } = await supabase.from('contact_books').select('tasks, notices').eq('record_date', todayISO).single()
  if (data) { tasks.value = data.tasks || []; notices.value = data.notices || [] }
}

const requestEdit = (type) => {
  const pwd = window.prompt("🔒 請輸入權限密碼：")
  if (!pwd) return
  if (type === 'notices') {
    if (pwd === '168168168') { currentNoticeEditor.value = '導師'; isEditingNotices.value = true } else { alert("❌ 密碼錯誤！") }
  } else if (type === 'tasks') {
    if (pwd === '168168168') { currentTaskEditor.value = '導師'; isEditingTasks.value = true }
    else if (pwd === '268268268') { currentTaskEditor.value = '股長'; isEditingTasks.value = true }
    else { alert("❌ 密碼錯誤！") }
  }
}

const addNotice = () => notices.value.push('')
const removeNotice = (index) => notices.value.splice(index, 1)
const addTask = () => tasks.value.push('')
const removeTask = (index) => tasks.value.splice(index, 1)

const saveBoard = async (type) => {
  notices.value = notices.value.filter(n => n.trim() !== '')
  tasks.value = tasks.value.filter(t => t.trim() !== '')
  const { error } = await supabase.from('contact_books').upsert({ record_date: todayISO, notices: notices.value, tasks: tasks.value }, { onConflict: 'record_date' })
  if (!error) {
    if (type === 'notices') isEditingNotices.value = false
    if (type === 'tasks') isEditingTasks.value = false
  }
}

// 未讀訊息檢查邏輯
const unreadCount = ref(0)
const fetchUnreadCount = async () => {
  const { count } = await supabase
    .from('private_messages')
    .select('*', { count: 'exact', head: true })
    .eq('is_read_by_teacher', false)
    .in('sender_role', ['家長', '學生']) // 同時檢查家長與學生的未讀
  if (count !== null) unreadCount.value = count
}

onMounted(() => {
  updateClock()
  timer = setInterval(updateClock, 1000)
  fetchStudentsAndAttendance()
  fetchContactBook()
  fetchUnreadCount() // 載入時檢查未讀訊息
  setInterval(fetchUnreadCount, 60000) // 每分鐘背景檢查一次新訊息
})
onUnmounted(() => clearInterval(timer))
</script>

<style scoped>
/* 全局排版改為垂直流向，適應「須知在最上方」 */
.dashboard-container { display: flex; flex-direction: column; gap: 20px; padding: 20px; background-color: #f5f7fa; min-height: 100vh; font-family: 'sans-serif'; }
.main-content { display: flex; gap: 20px; }
.left-panel, .right-panel { flex: 1; display: flex; flex-direction: column; gap: 20px; }

/* 頂部家長須知專屬樣式 */
.top-notice-board { margin-bottom: 0px; }

/* 時鐘與按鈕區 */
.stu-btn { background-color: #3b82f6; }
.clock-card { background: white; border-radius: 12px; text-align: center; padding: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); border: 2px solid #e2e8f0; }
.clock-card h2 { margin: 0 0 10px 0; font-size: 2rem; color: #2c3e50; }
.nav-links { display: flex; justify-content: center; gap: 8px; flex-wrap: wrap; }
.nav-btn { position: relative; text-decoration: none; padding: 8px 12px; border-radius: 6px; font-size: 0.95rem; font-weight: bold; transition: opacity 0.2s; color: white; }
.nav-btn:hover { opacity: 0.8; }
.parent-btn { background-color: #f59e0b; }
.msg-btn { background-color: #10b981; }
.admin-btn { background-color: #64748b; }
.notification-badge { position: absolute; top: -8px; right: -8px; background-color: #ef4444; color: white; font-size: 0.75rem; font-weight: bold; padding: 2px 6px; border-radius: 10px; border: 2px solid white; animation: pulse 2s infinite; }

@keyframes pulse {
  0% { transform: scale(1); }
  50% { transform: scale(1.1); }
  100% { transform: scale(1); }
}

/* 統計區與打卡區 */
.stats-row { display: flex; justify-content: space-between; gap: 10px; }
.stat-box { flex: 1; text-align: center; padding: 10px; border-radius: 8px; font-weight: bold; border: 1px solid #ddd; }
.stat-box.total { background: #fff3cd; color: #856404; }
.stat-box.present { background: #d4edda; color: #155724; }
.stat-box.absent { background: #f8d7da; color: #721c24; }

.punch-grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 10px; }
.punch-btn { display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 12px 2px; border-radius: 8px; border: none; cursor: pointer; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
.seat-num { font-size: 1.3rem; font-weight: bold; margin-bottom: 2px; }
.hidden-name { font-size: 1rem; font-weight: bold; margin-bottom: 5px; opacity: 0.85; }
.status-text { font-size: 0.85rem; }
.time-text { font-size: 0.75rem; margin-top: 5px; opacity: 0.8; font-family: monospace; }
.is-absent { background-color: #ffe4e6; color: #e11d48; border: 1px solid #fecdd3; }
.is-present { background-color: #dcfce7; color: #16a34a; border: 1px solid #bbf7d0; }

/* 黑板共用樣式 */
.chalkboard { background-color: #2d4a3e; border: 10px solid #8b5a2b; border-radius: 12px; padding: 20px; color: #fdf6e3; box-shadow: inset 0 0 20px rgba(0,0,0,0.5); }
.board-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px; border-bottom: 2px dashed rgba(253, 246, 227, 0.4); padding-bottom: 10px; }
.board-header h3 { font-size: 1.5rem; margin: 0 0 5px 0; color: #fbbf24; }
.notice-title { color: #fca5a5 !important; }
.date-text { font-size: 1rem; margin: 0; opacity: 0.9; }

.task-list { list-style: none; padding: 0; font-size: 1.2rem; line-height: 1.6; }
.task-list li { margin-bottom: 12px; display: flex; align-items: center; }
.bullet { margin-right: 12px; font-size: 1.1rem; }
.number { background-color: #6b8e23; color: white; border-radius: 50%; width: 24px; height: 24px; display: inline-flex; align-items: center; justify-content: center; margin-right: 12px; font-size: 0.9rem; flex-shrink: 0; }
.empty-text { color: #9ca3af; font-style: italic; }

/* 編輯按鈕與輸入框 */
button { font-family: inherit; }
.edit-btn, .save-btn, .add-btn { background: #fbbf24; border: none; padding: 6px 12px; border-radius: 6px; font-weight: bold; cursor: pointer; color: #5f3f00; font-size: 0.9rem; }
.save-btn { background: #4ade80; color: #064e3b; margin-left: 10px; }
.add-btn { background: #cbd5e1; color: #1e293b; }
.editor-badge { background: #dc2626; color: white; padding: 4px 8px; border-radius: 4px; font-size: 0.8rem; margin-right: 10px; font-weight: bold; }

.edit-item { gap: 10px; width: 100%; }
.edit-input { flex: 1; font-size: 1.1rem; padding: 5px 10px; border-radius: 4px; border: none; background: rgba(255,255,255,0.9); width: 100%; box-sizing: border-box; }
.notice-input { background: #fee2e2; }
.delete-btn { background: #ef4444; color: white; border: none; padding: 5px 10px; border-radius: 4px; cursor: pointer; }

/* ==================== 手機 RWD 響應式設定 ==================== */
@media (max-width: 768px) {
  .dashboard-container { padding: 10px; }
  .main-content { flex-direction: column; } /* 手機版改為上下排列 */
  .punch-grid { grid-template-columns: repeat(5, 1fr); gap: 5px; } /* 維持一排五個，但縮小間距 */
  .punch-btn { padding: 8px 2px; }
  .seat-num { font-size: 1.1rem; }
  .hidden-name { font-size: 0.85rem; }
  .status-text { font-size: 0.75rem; }
  .chalkboard { padding: 15px; border-width: 6px; }
  .board-header { flex-direction: column; align-items: flex-start; gap: 10px; }
  .edit-actions { width: 100%; display: flex; flex-wrap: wrap; gap: 5px; }
}
</style>