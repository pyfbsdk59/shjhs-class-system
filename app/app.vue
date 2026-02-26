<template>
  <div class="dashboard-container">
    
    <div class="left-panel">
      <div class="clock-card">
        <h2>🕒 {{ currentTime }}</h2>
      </div>

      <div class="stats-row">
        <div class="stat-box total">應到: 30</div>
        <div class="stat-box present">已到: {{ presentCount }}</div>
        <div class="stat-box absent">未到: {{ absentCount }}</div>
      </div>

      <div class="punch-grid">
        <button 
          v-for="student in students" 
          :key="student.seat_number"
          :class="['punch-btn', student.status === '已到' ? 'is-present' : 'is-absent']"
          @click="toggleStatus(student)"
        >
          <span class="seat-num">{{ student.seat_number }}</span>
          <span class="status-text">{{ student.status }}</span>
        </button>
      </div>
    </div>

    <div class="right-panel">
      <div class="chalkboard">
        <div class="board-header">
          <h3>⭐ 今日聯絡簿</h3>
          <p class="date-text">2026年2月26日 星期四</p>
        </div>
        
        <ul class="task-list">
          <li><span class="number">1</span> 國習 P.30-32</li>
          <li><span class="number">2</span> 數作 Ch.3</li>
          <li><span class="number">3</span> 明帶水彩用具</li>
          <li><span class="number">4</span> 交午餐回條</li>
          <li><span class="number">5</span> 週五戶外教學</li>
        </ul>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'

// --- 時鐘邏輯 ---
const currentTime = ref('')
let timer = null

const updateClock = () => {
  const now = new Date()
  currentTime.value = now.toLocaleTimeString('zh-TW', { hour12: false })
}

// --- 學生打卡邏輯 ---
// 這裡先產生 30 個假學生資料作為 UI 測試。下一步我們再把它換成從 Supabase 撈取！
const students = ref(
  Array.from({ length: 30 }, (_, i) => ({
    seat_number: i + 1,
    status: '未到' // 預設狀態
  }))
)

// 計算人數
const presentCount = computed(() => students.value.filter(s => s.status === '已到').length)
const absentCount = computed(() => students.value.filter(s => s.status === '未到').length)

// 點擊按鈕切換狀態
const toggleStatus = (student) => {
  student.status = student.status === '未到' ? '已到' : '未到'
  // 💡 之後我們要在這裡加上 await supabase.from('...').update(...) 將狀態寫回資料庫
}

// --- 生命週期 ---
onMounted(() => {
  updateClock()
  timer = setInterval(updateClock, 1000) // 每秒更新時鐘
})

onUnmounted(() => {
  clearInterval(timer) // 離開頁面時清除計時器
})
</script>

<style scoped>
/* 整體排版：左右切分 */
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

/* --- 左側樣式 --- */
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

/* 30 宮格 CSS Grid */
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
  transform: scale(0.95);
}
.seat-num { font-size: 1.5rem; font-weight: bold; margin-bottom: 5px; }
.status-text { font-size: 0.9rem; }

/* 缺席樣式 (粉紅) */
.is-absent { background-color: #ffe4e6; color: #e11d48; border: 1px solid #fecdd3; }
/* 出席樣式 (淺綠) */
.is-present { background-color: #dcfce7; color: #16a34a; border: 1px solid #bbf7d0; }


/* --- 右側黑板樣式 --- */
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
}
.board-header h3 {
  color: #fbbf24; /* 粉筆黃 */
  font-size: 1.8rem;
  margin: 0 0 10px 0;
}
.date-text { font-size: 1.2rem; margin: 0; }

.task-list {
  list-style: none;
  padding: 0;
  font-size: 1.4rem;
  line-height: 2;
}
.task-list li { margin-bottom: 15px; display: flex; align-items: center;}
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
}
</style>