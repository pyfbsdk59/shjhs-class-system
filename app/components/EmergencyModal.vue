<template>
  <div class="modal-container">
    <h3>🚨 發送緊急通知</h3>
    
    <div>
      <label>👩‍🎓 選擇學生：</label>
      <select v-model="selectedStudent" @change="fetchParentsEmails">
        <option disabled value="">請選擇學生...</option>
        <option v-for="student in studentList" :key="student.id" :value="student">
          {{ student.seat_number }}號 - {{ student.hidden_name }}
        </option>
      </select>
    </div>

    <div v-if="parentsEmails.length > 0">
      <label>👨‍👩‍👧 收件家長：</label>
      <span v-for="email in parentsEmails" :key="email" class="email-badge">
        ☑️ {{ maskEmail(email) }}
      </span>
    </div>

    <div class="template-buttons" v-if="selectedStudent">
      <button @click="applyTemplate('fever')">🌡️ 發燒/生病</button>
      <button @click="applyTemplate('stomach')">🤢 腸胃不適</button>
      <button @click="applyTemplate('injury')">🩹 意外受傷</button>
    </div>

    <div v-if="selectedStudent">
      <textarea v-model="messageContent" rows="8" style="width: 100%;"></textarea>
    </div>

    <button @click="sendNotification" :disabled="isSending">
      {{ isSending ? '發送中...' : '📤 發送通知並寫入系統紀錄' }}
    </button>
  </div>
</template>

<script setup>
import { ref } from 'vue'
// 假設您已經設定好 Supabase client
// const supabase = useSupabaseClient() 

const studentList = ref([
  // 測試假資料，實戰中請用 supabase.from('students').select('*')
  { id: '1', seat_number: 5, hidden_name: '李Ｏ華', real_name: '李小華' }
])
const selectedStudent = ref('')
const parentsEmails = ref([])
const messageContent = ref('')
const isSending = ref(false)

// 遮蔽 Email (例如 li***@gmail.com)
const maskEmail = (email) => {
  const [name, domain] = email.split('@')
  return `${name.substring(0, 2)}***@${domain}`
}

// 模擬抓取家長 Email
const fetchParentsEmails = async () => {
  // 實戰中：supabase.from('parents').select('email').eq('student_id', selectedStudent.value.id)
  parentsEmails.value = ['li_papa@gmail.com', 'mama123@gmail.com'] 
}

// 帶入公版文字
const applyTemplate = (type) => {
  const name = selectedStudent.value.real_name // 寄給家長可以用真名
  let condition = ''
  if (type === 'fever') condition = '【發燒，目前體溫 ___ 度，已在健康中心休息】'
  if (type === 'stomach') condition = '【嚴重腸胃不適/嘔吐，已在健康中心休息】'
  if (type === 'injury') condition = '【發生意外受傷：___，已做初步包紮處理】'

  messageContent.value = `親愛的家長您好：\n\n您的孩子 ${name} 目前在校身體不適。\n狀況為：${condition}。\n\n為求慎重與孩子健康，請您盡速撥冗至學校將孩子接回就醫休息。\n若有任何問題請隨時透過系統私訊或電話聯繫。\n\n導師 敬上`
}

// 發送與寫入紀錄
const sendNotification = async () => {
  isSending.value = true
  try {
    // 1. 呼叫後端 API 寄信 (實戰中發送 Request 到您的 Nuxt Server API)
    console.log('寄信給:', parentsEmails.value, '內容:', messageContent.value)

    // 2. 寫入 Supabase 紀錄 (非常重要！)
    /* await supabase.from('communication_logs').insert({
      student_id: selectedStudent.value.id,
      notification_type: '生病手動通知',
      sent_by: '導師',
      recipient_emails: parentsEmails.value.join(','),
      message_content: messageContent.value
    })
    */
    alert('✅ 通知已成功發送並留下紀錄！')
  } catch (error) {
    alert('發送失敗：' + error.message)
  } finally {
    isSending.value = false
  }
}
</script>

<style scoped>
/* 簡單樣式點綴 */
.modal-container { border: 2px solid #ddd; padding: 20px; border-radius: 8px; background: #fff; }
.template-buttons button { margin-right: 8px; background: #ffe4e1; border: none; padding: 5px 10px; border-radius: 4px; cursor: pointer; }
.email-badge { background: #e0f7fa; padding: 3px 8px; border-radius: 12px; margin-right: 5px; font-size: 0.9em; }
</style>