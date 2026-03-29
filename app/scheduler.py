# app/scheduler.py
"""
定时任务调度器 - 主动提醒和定期检查
"""
import schedule
import time
import threading
from typing import Callable, Optional
from datetime import datetime


class NotificationScheduler:
    """通知调度器"""

    def __init__(self, agent=None):
        self.agent = agent
        self.jobs = []
        self.running = False
        self.thread = None

    def start(self):
        """启动调度器"""
        self.running = True
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        print("📅 通知调度器已启动")

    def stop(self):
        """停止调度器"""
        self.running = False
        schedule.clear()
        print("📅 通知调度器已停止")

    def _run(self):
        """调度器主循环"""
        while self.running:
            schedule.run_pending()
            time.sleep(1)

    def add_daily_checkin(self, user_id: str, hour: int = 9, minute: int = 0):
        """添加每日主动询问"""

        def job():
            if self.agent:
                result = self.agent.active_checkin(user_id)
                if result and result.get("message"):
                    print(f"[{datetime.now()}] 主动询问 {user_id}: {result['message']}")
                    self._send_notification(user_id, result["message"])

        schedule.every().day.at(f"{hour:02d}:{minute:02d}").do(job)
        self.jobs.append(("daily_checkin", user_id, hour, minute))
        print(f"✅ 已添加每日询问: {user_id} 每天 {hour}:{minute:02d}")

    def add_weekly_report(self, user_id: str, weekday: int = 6, hour: int = 20):
        """添加周报提醒"""

        def job():
            if self.agent:
                status = self.agent.memory.get_user_profile(user_id)
                working = self.agent.memory.get_working_memory(user_id)
                report = f"📊 本周报告\n"
                report += f"- 运动次数: {len(working.recent_exercises)}\n"
                report += f"- 活跃目标: {len(status.active_goals)}\n"
                report += f"- 完成目标: {len(status.completed_goals)}\n"
                report += f"下周继续加油！💪"

                self._send_notification(user_id, report)

        schedule.every().week.at(f"{weekday}:{hour:02d}:00").do(job)
        print(f"✅ 已添加周报: {user_id} 每周{weekday} {hour}:00")

    def add_exercise_reminder(self, user_id: str, hour: int = 18, minute: int = 0):
        """添加运动提醒"""

        def job():
            reminder = "🏃 该运动啦！\n\n"
            reminder += "今天记得抽时间活动一下，哪怕只是散步15分钟也对健康有益。\n"
            reminder += "运动完记得来记录哦！✨"
            self._send_notification(user_id, reminder)

        schedule.every().day.at(f"{hour:02d}:{minute:02d}").do(job)
        print(f"✅ 已添加运动提醒: {user_id} 每天 {hour}:{minute:02d}")

    def _send_notification(self, user_id: str, message: str):
        """发送通知（可扩展）"""
        print(f"📧 通知 {user_id}: {message[:50]}...")