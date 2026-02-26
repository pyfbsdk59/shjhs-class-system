<template>
  <div>
    <h1>連線測試：學生名單</h1>
    <ul>
      <li v-for="student in students" :key="student.id">
        {{ student.seat_number }}號 - {{ student.hidden_name }}
      </li>
    </ul>
    <p v-if="!students.length">載入中... 或是資料庫還沒有資料喔！</p>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

// 呼叫 Supabase 客戶端
const supabase = useSupabaseClient()
const students = ref([])

// 網頁一載入，就去抓資料
onMounted(async () => {
  // 從 students 表格抓取 id, seat_number, hidden_name
  const { data, error } = await supabase
    .from('students')
    .select('id, seat_number, hidden_name')
    .order('seat_number', { ascending: true }) // 照座號排序

  if (error) {
    console.error('抓取失敗:', error)
  } else {
    students.value = data
  }
})
</script>