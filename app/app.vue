<template>
  <div class="dashboard-container">
    
    <div class="left-panel">
      <div class="clock-card">
        <h2>🕒 {{ currentTime }}</h2>
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
          <span class="status-text">{{ student.status }}</span>
          <span v-if="student.status === '已到' && student.punch_time" class="time-text">
            {{ student.punch_time }}
          </span>
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
          
          <button v-if="!isEditingBoard" @click="isEditingBoard = true" class="edit-btn">✏️ 編輯</button>
          <div v-else class="edit-actions">
            <button @click="addTask" class="add-btn">➕ 新增事項</button>
            <button @click="saveContactBook" class="save-btn">💾 儲存</button>
          </div>
        </div>
        
        <ul v-if="!isEditingBoard" class="task-list">
          <li v-for="(task, index) in tasks" :key="index">
            <span class="number">{{ index + 1 }}</span> {{ task }}
          </li>
          <li v-if="tasks.length === 0" style="color: #999;">目前尚無聯絡簿事項...</li>
        </ul>

        <ul v-else class="task-list editing">
          <li v-for="(task, index) in tasks" :key="'edit-'+index" class="edit-item">
            <span class="number">{{ index + 1 }}</span>
            <input v-model="tasks[index]" type="text" class="edit-input" placeholder="請輸入聯絡簿事項..." />
            <button @click="removeTask(index)" class="delete-btn">🗑️</button>
          </li>
        </ul>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'

// 呼叫 Supabase 客戶端 (確保 nuxt.config.ts 已經設定好模組)
const supabase = useSupabaseClient()

// ==================== 基礎日期與時間處理 ====================
const currentTime = ref('')
let timer = null

// 產生 YYYY-MM-DD 格式，供寫入資料庫判斷「今日」使用
const d = new Date()
const todayISO = `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`
// 產生中文日期供黑板顯示
const todayDisplay = d.toLocaleDateString('zh-TW', { year: 'numeric', month: 'long', day: 'numeric', weekday: 'long' })

const updateClock = () => {
  currentTime.value = new Date().toLocaleTimeString('zh-TW', { hour12: false })
}

// ==================== 學生與打卡邏輯 ====================
const students = ref([])
const isUpdating = ref(false)

// 自動計算人數
const presentCount = computed(() => students.value.filter(s => s.status === '已到').length)
const absentCount = computed(() => students.value.filter(s => s.status === '未到').length)

// 從資料庫讀取全班名單與今日打卡紀錄
const fetchStudentsAndAttendance = async () => {
  // 1. 抓取所有學生 (照座號排序)
  const { data: studentData } = await supabase.from('students').select('*').order('seat_number')
  
  // 2. 抓取「今天」的打卡紀錄
  const { data: attendanceData } = await supabase.from('attendances').select('*').eq('record_date', todayISO)

  if (studentData) {
    // 3. 將兩者資料合併比對
    students.value = studentData.map(student => {
      const record = attendanceData?.find(a => a.student_id === student.id)
      return {
        ...student,
        status: record ? record.status : '未到',
        punch_time: record ? record.punch_time : null // 帶入打卡時間
      }
    })
  }
}

// 點擊號碼牌：切換狀態並寫入 Supabase (Upsert：有則更新，無則新增)
const toggleStatus = async (student) => {
  isUpdating.value = true
  
  // 決定新的狀態
  const newStatus = student.status === '未到' ? '已到' : '未到'
  // 產生 24小時制 的打卡時間 (例如 07:45:30)，若退回「未到」則清空時間
  const newPunchTime = newStatus === '已到' ? new Date().toLocaleTimeString('zh-TW', { hour12: false }) : null

  // 備份舊狀態 (若雲端更新失敗時可還原)
  const oldStatus = student.status
  const oldPunchTime = student.punch_time

  // 畫面先樂觀更新，讓觸控體驗零延遲
  student.status = newStatus
  student.punch_time = newPunchTime

  // 寫入 Supabase
  const { error } = await supabase.from('attendances').upsert({
    student_id: student.id,
    record_date: todayISO,
    status: newStatus,
    punch_time: newPunchTime
  }, { onConflict: 'student_id, record_date' }) // 依賴複合唯一金鑰

  if (error) {
    alert('打卡狀態更新失敗！請檢查網路連線。')
    // 失敗則退回原本狀態
    student.status = oldStatus
    student.punch_time = oldPunchTime
  }
  isUpdating.value = false
}

// ==================== 聯絡簿邏輯 ====================
const tasks = ref([])
const isEditingBoard = ref(false)

// 從資料庫讀取今日聯絡簿
const fetchContactBook = async () => {
  const { data } = await supabase.from('contact_books').select('tasks').eq('record_date', todayISO).single()
  
  if (data && data.tasks) {
    tasks.value = data.tasks
  } else {
    // 若今天還沒建立聯絡簿，給予預設假資料方便測試
    tasks.value = ['國習 P.30-32', '數作 Ch.3', '交午餐回條'] 
  }
}

// 編輯模式：新增/刪除事項
const addTask = () => tasks.value.push('')
const removeTask = (index) => tasks.value.splice(index, 1)

// 儲存聯絡簿至 Supabase
const saveContactBook = async () => {
  // 過濾掉空白的輸入框，避免存入空字串
  const validTasks = tasks.value.filter(t => t.trim() !== '')
  tasks.value = validTasks

  const { error } = await supabase.from('contact_books').upsert({
    record_date: todayISO,
    tasks: validTasks
  }, { onConflict: 'record_date' })

  if (error) {
    alert('聯絡簿儲存失敗！')
  } else {
    isEditingBoard.value = false // 存檔成功，關閉編輯模式
  }
}

// ==================== 生命週期 ====================
onMounted(() => {
  updateClock()
  timer = setInterval(updateClock, 1000) // 每秒更新時鐘
  fetchStudentsAndAttendance()           // 抓取學生名單與打卡紀錄
  fetchContactBook()                     // 抓取聯絡簿
})

onUnmounted(() => {
  clearInterval(timer) // 離開頁面時清除計時器，避免記憶體洩漏
})
</script>

<style scoped>
/* ==================== 整體排版 ==================== */
.dashboard-container {
  display: flex;
  gap: 20px;
  padding: 20px;
  background-color: #f5f7fa;
  min-height: 100vh;
  font-family: 'sans-serif';
}

.left-panel, .right-panel {
  flex: 1; /* 左右各佔一半 */
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* ==================== 左側樣式 (時鐘與統計) ==================== */
.clock-card {
  background: white;
  border-radius: 12px;
  text-align: center;
  padding: 10px;
  box-shadow: 0 4px 6px rgba(0,0,0,0.05);
  font-size: 2rem;
  color: #2c3e50;
  border: 2px solid #e2e8f0;
}

.stats-row {
  display: flex;
  justify-content: space-between;
  gap: 10px;
}

.stat-box {
  flex: 1;
  text-align: center;
  padding: 10px;
  border-radius: 8px;
  font-weight: bold;
  border: 1px solid #ddd;
}
.stat-box.total { background: #fff3cd; color: #856404; }
.stat-box.present { background: #d4edda; color: #155724; }
.stat-box.absent { background: #f8d7da; color: #721c24; }

/* ==================== 30 宮格打卡按鈕 ==================== */
.punch-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr); /* 一排 5 個 */
  gap: 10px;
}

.punch-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 15px 5px;
  border-radius: 8px;
  border: none;
  cursor: pointer;
  transition: transform 0.1s, box-shadow 0.1s;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}
.punch-btn:active {
  transform: scale(0.95); /* 點擊縮放回饋 */
}
.punch-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.seat-num { font-size: 1.5rem; font-weight: bold; margin-bottom: 5px; }
.status-text { font-size: 0.9rem; }
.time-text { font-size: 0.8rem; margin-top: 5px; opacity: 0.8; font-family: monospace; } /* 打卡時間專屬樣式 */

/* 缺席樣式 (粉紅) */
.is-absent { background-color: #ffe4e6; color: #e11d48; border: 1px solid #fecdd3; }
/* 出席樣式 (淺綠) */
.is-present { background-color: #dcfce7; color: #16a34a; border: 1px solid #bbf7d0; }

/* ==================== 右側黑板樣式 ==================== */
.chalkboard {
  background-color: #2d4a3e; /* 深綠色黑板 */
  border: 12px solid #8b5a2b; /* 木頭邊框 */
  border-radius: 16px;
  padding: 30px;
  color: #fdf6e3;
  box-shadow: inset 0 0 20px rgba(0,0,0,0.5), 5px 5px 15px rgba(0,0,0,0.2);
  height: 100%;
}

.board-header {
  border-bottom: 2px dashed #fdf6e3;
  padding-bottom: 15px;
  margin-bottom: 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.board-header h3 {
  color: #fbbf24; /* 粉筆黃 */
  font-size: 1.8rem;
  margin: 0 0 5px 0;
}
.date-text { font-size: 1.2rem; margin: 0; }

.task-list {
  list-style: none;
  padding: 0;
  font-size: 1.4rem;
  line-height: 2;
}

.task-list li {
  margin-bottom: 15px;
  display: flex;
  align-items: center;
}

.task-list .number {
  background-color: #6b8e23;
  color: white;
  border-radius: 50%;
  width: 30px;
  height: 30px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  margin-right: 15px;
  font-size: 1rem;
  flex-shrink: 0;
}

/* ==================== 黑板編輯模式專屬按鈕與輸入框 ==================== */
button { font-family: inherit; }
.edit-btn, .save-btn, .add-btn {
  background: #fbbf24;
  border: none;
  padding: 8px 15px;
  border-radius: 6px;
  font-weight: bold;
  cursor: pointer;
  color: #5f3f00;
  font-size: 1rem;
}
.save-btn { background: #4ade80; color: #064e3b; margin-left: 10px; }
.add-btn { background: #cbd5e1; color: #1e293b; }

.edit-item { gap: 10px; }
.edit-input {
  flex: 1;
  font-size: 1.2rem;
  padding: 5px 10px;
  border-radius: 4px;
  border: none;
  background: rgba(255,255,255,0.9);
}
.delete-btn {
  background: #ef4444;
  color: white;
  border: none;
  padding: 5px 10px;
  border-radius: 4px;
  cursor: pointer;
}
</style>