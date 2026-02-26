import os
import smtplib
from email.mime.text import MIMEText
from datetime import datetime, timedelta
from supabase import create_client, Client

# 1. 取得環境變數 (GitHub Secrets 會提供這些)
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
SENDER_EMAIL = os.environ.get("SENDER_EMAIL")
SENDER_PASSWORD = os.environ.get("SENDER_PASSWORD")

# 初始化 Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def main():
    # 2. 處理台灣時間 (UTC+8)
    tw_time = datetime.utcnow() + timedelta(hours=8)
    today_iso = tw_time.strftime('%Y-%m-%d')
    current_time_str = tw_time.strftime('%H:%M')
    
    print(f"[{tw_time}] 開始執行遲到檢查腳本，今日日期: {today_iso}")

    # 3. 抓取全班名單與今日打卡紀錄
    students_res = supabase.table('students').select('*').execute()
    attendances_res = supabase.table('attendances').select('*').eq('record_date', today_iso).execute()
    parents_res = supabase.table('parents').select('*').execute()

    students = students_res.data
    attendances = attendances_res.data
    parents = parents_res.data

    # 4. 找出遲到/未到的學生
    absent_students = []
    for student in students:
        # 尋找該名學生今天的打卡紀錄
        record = next((a for a in attendances if a['student_id'] == student['id']), None)
        # 如果「沒有紀錄」或是「狀態為未到」，就判定為缺席
        if not record or record['status'] == '未到':
            absent_students.append(student)

    if not absent_students:
        print("🎉 今天全班都準時到校，無須寄送通知！")
        return

    # 5. 準備 SMTP 伺服器 (以 Gmail 為例)
    print(f"共有 {len(absent_students)} 名學生未到，準備寄信...")
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
    except Exception as e:
        print(f"❌ SMTP 登入失敗: {e}")
        return

    # 6. 逐一寄信並寫入 Log
    for student in absent_students:
        # 找出這位學生的家長信箱
        student_parents = [p['email'] for p in parents if p['student_id'] == student['id']]
        
        if not student_parents:
            print(f"⚠️ 學生 {student['real_name']} 未綁定家長信箱，跳過。")
            continue

        emails_str = ", ".join(student_parents)
        
        # 信件內容設計
        content = (
            f"親愛的家長您好：\n\n"
            f"系統偵測到您的孩子 【{student['real_name']}】 於今日 ({today_iso}) {current_time_str} "
            f"尚未完成到校打卡，特此通知。\n\n"
            f"若孩子已請假，請忽略此信件；若孩子已出門，請您留意其通勤安全，並可透過聯絡簿或電話與導師聯繫。\n\n"
            f"班級導師 敬上\n(此為系統自動發送，請勿直接回信)"
        )
        
        msg = MIMEText(content)
        msg['Subject'] = f"⚠️ 學校出缺席通知 - {student['real_name']} 尚未打卡"
        msg['From'] = SENDER_EMAIL
        msg['To'] = emails_str

        # 寄出信件
        try:
            server.send_message(msg)
            print(f"✅ 已寄送通知給 {student['real_name']} 的家長 ({emails_str})")
            
            # 寫入 Supabase 通訊紀錄 (稽核用)
            supabase.table('communication_logs').insert({
                'student_id': student['id'],
                'notification_type': '遲到自動通知',
                'sent_by': 'System Cron',
                'recipient_emails': emails_str,
                'message_content': content
            }).execute()
            
        except Exception as e:
            print(f"❌ 寄給 {student['real_name']} 失敗: {e}")

    server.quit()
    print("腳本執行完畢！")

if __name__ == "__main__":
    main()