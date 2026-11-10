# -*- coding: utf-8 -*-
"""
桌面宠物猫 - Desktop Pet Cat
形象参考:虎斑白底、半眯眼、嫌弃脸

操作:
  左键拖动    - 移动位置
  双击        - 撸一下
  右键        - 弹出菜单(跟着鼠标走 / 番茄钟 / 退出)
  闲置60秒    - 自动睡觉,点它或动鼠标(跟随模式)会醒
  整点        - 自动报时
"""
import os
import sys
import json
import math
import time
import random
from datetime import datetime
from PyQt5.QtWidgets import QApplication, QWidget, QMenu, QAction, QActionGroup
from PyQt5.QtCore import Qt, QTimer, QPoint
from PyQt5.QtGui import QPainter, QPainterPath, QColor, QBrush, QPen, QFont, QCursor


SIZE_OPTIONS = [("迷你", 0.5), ("小", 0.75), ("中(默认)", 1.0),
                ("大", 1.5), ("超大", 2.0)]
CONFIG_PATH = os.path.join(os.path.expanduser("~"), ".desktop_cat.json")


def load_scale():
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            v = float(json.load(f).get("scale", 1.0))
        return v if 0.3 <= v <= 3.0 else 1.0
    except Exception:
        return 1.0


def save_scale(v):
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump({"scale": v}, f)
    except Exception:
        pass


# 台词库(每句尽量不超过 14 个字,气泡放得下)
IDLE_LINES = [
    "哼。", "喵~", "......", "无聊。", "别看我。", "摸鱼中。", "打扰了。",
    "困。", "饿了。",
    "又在摸鱼?算我一个。", "代码写完了吗?", "你的 bug 我都看见了。",
    "我不是胖,是毛蓬。", "猫生苦短,及时摸鱼。", "再看收费了。",
    "你盯着我干嘛,好看?", "本喵今天不营业。", "你的发际线还好吗?",
    "这屏幕比你好看。", "我在监督你工作。", "发呆是一门艺术。",
    "工资发了吗?请我吃鱼。", "今天也是嫌弃你的一天。",
    "你刚才那个表情,我记住了。", "宇宙的尽头是罐头。",
    "我的尾巴比你的进度快。", "你已经盯屏幕很久了。",
]
LATE_NIGHT_LINES = [
    "还不睡?头发不要了?", "凌晨了喂,快睡!", "熬夜的人最帅,才怪。",
    "夜猫子本猫都困了。",
]
MORNING_LINES = [
    "早啊,打工人。", "早饭吃了没?", "一日之计在于摸鱼。",
]
NOON_LINES = ["该吃饭了吧?", "午饭吃啥?带我一口。", "饭后犯困,懂的都懂。"]
POKE_LINES = [
    "干嘛?", "放我下来。", "哎?", "再拽我咬你!", "喂喂喂,没礼貌!",
    "我的毛!", "非礼啦喵!", "拎猫要付费的。", "本喵不是玩具!",
    "你是不是想挨挠?",
]
PAT_LINES = [
    "喵喵喵!", "呼噜噜...", "再摸摸~", "哼哼~", "别烦我啦", "算你有眼光。",
    "往左一点...对...", "收费:一条小鱼干。", "摸够了没有?",
    "再摸要收摸摸费了。", "你的手,还行。",
]
SASS_LINES = [
    "键盘上不许放脚。", "投喂请按响铃。", "我在思考猫生。", "别看了,不加班。",
    "我睡觉的时候最帅。", "你的待办事项在哭泣。", "不想上班,想上树。",
    "老板不在,我就是老板。", "今天的摸鱼 KPI 完成。",
    "代码是你写的,锅我不背。", "我只负责可爱,其他免谈。",
    "你再看,我就长在屏幕上。", "建议:先喝水再加班。",
    "给我开个罐头再聊。", "别回头,身后有只猫(是我)。",
    "你敲键盘的样子像在弹琴。", "存档了吗?我不管,问就是没有。",
    "你这个需求,我拒绝。", "我的爪子很贵,不外借。",
    "别问,问就是在加班(睡觉)。",
]
WAKE_LINES = [
    "唔...谁啊?", "我才没睡着!", "几点了...", "梦里正吃鱼呢!",
    "吵醒猫要赔鱼干。",
]
POMO_START_LINES = ["专注25分钟,开始!", "开工,我给你站岗。", "本喵陪你卷。"]
POMO_END_LINES = [
    "时间到!休息5分钟~", "番茄熟了,摸会儿鱼。", "25分钟到,伸个懒腰!",
    "辛苦了,喝口水。",
]
CHIME_LINES = [
    "{h}点整啦~", "{h}点啦,动一动!", "{h}点了,该喝水了。",
    "{h}点,摸鱼进度条+1。",
]

DW, DH = 280, 340   # 设计尺寸(逻辑像素),绘制时按窗口实际大小等比缩放


class DesktopCat(QWidget):
    def __init__(self):
        super().__init__()
        # 无边框 + 透明 + 置顶
        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.scale_factor = load_scale()
        self.resize(int(DW * self.scale_factor), int(DH * self.scale_factor))

        # 状态
        self.eye_openness = 0.35     # 默认半眯 (嫌弃脸)
        self.blink_state = 0
        self.tail_angle = 0
        self.tail_dir = 1
        self.speech = None
        self.speech_timer = 0
        self.drag_pos = None
        self.tick = 0
        self.sleeping = False
        self.last_active = time.time()
        self.follow = False
        self.last_cursor = QCursor.pos()
        self.pomo_end = None
        self.last_chime = None

        # 初始位置:屏幕右下角
        screen = QApplication.primaryScreen().availableGeometry()
        self.move(screen.right() - self.width() - 40,
                  screen.bottom() - self.height() + 20)

        # 动画循环 (尾巴 + 状态)
        self.timer = QTimer()
        self.timer.timeout.connect(self.animate)
        self.timer.start(50)

        # 眨眼
        self.blink_timer = QTimer()
        self.blink_timer.timeout.connect(self.blink)
        self._schedule_blink()

        # 随机发呆说话
        self.idle_timer = QTimer()
        self.idle_timer.timeout.connect(self.idle_action)
        self.idle_timer.start(9000)

        # 整点报时检查
        self.clock_timer = QTimer()
        self.clock_timer.timeout.connect(self.check_clock)
        self.clock_timer.start(15000)

    # ---------- 动画 ----------
    def _schedule_blink(self):
        self.blink_timer.start(random.randint(2500, 5500))

    def blink(self):
        self.blink_state = 1
        QTimer.singleShot(140, self._end_blink)
        self.blink_timer.stop()

    def _end_blink(self):
        self.blink_state = 0
        self._schedule_blink()

    def animate(self):
        self.tick += 1
        speed = 0.25 if self.sleeping else 1.2
        self.tail_angle += self.tail_dir * speed
        if abs(self.tail_angle) > 14:
            self.tail_dir *= -1

        if self.speech and self.speech_timer > 0:
            self.speech_timer -= 1
            if self.speech_timer == 0:
                self.speech = None

        # 跟随鼠标
        if self.follow and not self.drag_pos:
            self.follow_cursor()

        # 番茄钟
        if self.pomo_end is not None and time.time() >= self.pomo_end:
            self.pomo_end = None
            self.wake()
            self.say(random.choice(POMO_END_LINES), 160)

        # 闲置睡觉
        if (not self.sleeping and not self.drag_pos
                and time.time() - self.last_active > 60):
            self.sleeping = True
        self.update()

    def showEvent(self, event):
        super().showEvent(event)
        wh = self.windowHandle()
        if wh is not None and not getattr(self, "_screen_hooked", False):
            self._screen_hooked = True
            wh.screenChanged.connect(self.fix_size)

    def fix_size(self, *args):
        # 跨不同缩放比例的屏幕后,Qt可能改动窗口大小,延迟复位
        QTimer.singleShot(80, lambda: self.resize(
            int(DW * self.scale_factor), int(DH * self.scale_factor)))

    def set_scale(self, f):
        # 以猫脚底中心为锚点缩放,不会跳位置
        cx = self.x() + self.width() // 2
        bottom = self.y() + self.height()
        self.scale_factor = f
        w, h = int(DW * f), int(DH * f)
        self.resize(w, h)
        screen = QApplication.screenAt(QPoint(cx, bottom - 1)) \
            or QApplication.primaryScreen()
        g = screen.availableGeometry()
        nx = max(g.left(), min(cx - w // 2, g.right() - w))
        ny = max(g.top(), min(bottom - h, g.bottom() - h + int(30 * f)))
        self.move(nx, ny)
        save_scale(f)
        self.wake()
        self.say(random.choice(["这样可以吗?", "尺寸已调整。", "好了好了。"]), 50)

    def wake(self):
        self.last_active = time.time()
        self.sleeping = False

    def follow_cursor(self):
        cur = QCursor.pos()
        if cur != self.last_cursor:
            self.last_cursor = cur
            if self.sleeping:
                self.say("唔...?", 40)
            self.wake()
        if self.sleeping:
            return
        g = QApplication.primaryScreen().availableGeometry()
        tx = cur.x() + int(110 * self.scale_factor) - self.width() // 2
        ty = cur.y() + int(50 * self.scale_factor) - self.height()
        tx = max(g.left(), min(tx, g.right() - self.width()))
        ty = max(g.top(), min(ty, g.bottom() - self.height() + int(30 * self.scale_factor)))
        dx, dy = tx - self.x(), ty - self.y()
        dist = math.hypot(dx, dy)
        if dist < 6:
            return
        step = max(2.0, min(8.0, dist * 0.05))
        self.move(int(round(self.x() + dx / dist * step)),
                  int(round(self.y() + dy / dist * step)))

    def check_clock(self):
        now = datetime.now()
        key = (now.date(), now.hour)
        if now.minute == 0 and self.last_chime != key:
            self.last_chime = key
            self.wake()
            self.say(random.choice(CHIME_LINES).format(h=now.hour), 160)

    def toggle_follow(self, checked):
        self.follow = checked
        self.wake()
        self.say("来了来了~" if checked else "不跟了。", 60)

    def start_pomodoro(self):
        self.pomo_end = time.time() + 25 * 60
        self.wake()
        self.say(random.choice(POMO_START_LINES), 80)

    def cancel_pomodoro(self):
        self.pomo_end = None
        self.say("番茄钟取消了。", 60)

    def idle_action(self):
        # 下次随机间隔,不再死板每9秒一句
        self.idle_timer.setInterval(random.randint(6000, 14000))
        if self.sleeping:
            return
        h = datetime.now().hour
        pool = IDLE_LINES
        if random.random() < 0.4:
            if 0 <= h < 5:
                pool = LATE_NIGHT_LINES
            elif 6 <= h < 9:
                pool = MORNING_LINES
            elif 11 <= h < 14:
                pool = NOON_LINES
        self.say(random.choice(pool), 65)

    def say(self, text, duration=60):
        self.speech = text
        self.speech_timer = duration
        self.update()

    # ---------- 绘制 ----------
    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        # 参考照片的配色
        tabby_dark = QColor(75, 62, 48)
        tabby_light = QColor(178, 158, 132)
        tabby_mid = QColor(138, 118, 96)
        white_fur = QColor(246, 241, 233)
        white_shade = QColor(220, 214, 202)
        pink_nose = QColor(202, 132, 132)
        ear_pink = QColor(222, 168, 168)
        eye_green = QColor(150, 172, 128)

        # 窗口被系统改尺寸(跨屏DPI不同)时,整只猫等比缩放,保证完整显示
        sc = min(self.width() / DW, self.height() / DH)
        p.translate(self.width() / 2, self.height())
        p.scale(sc, sc)
        p.translate(-DW / 2, -DH)

        cx = DW // 2
        base_y = DH - 30

        # ---- 尾巴 (在身体后面) ----
        p.save()
        p.translate(cx + 60, base_y - 45)
        p.rotate(self.tail_angle)
        tail_path = QPainterPath()
        tail_path.moveTo(0, 0)
        tail_path.cubicTo(20, -20, 45, -55, 32, -95)
        p.setPen(QPen(tabby_mid, 18, Qt.SolidLine, Qt.RoundCap))
        p.drawPath(tail_path)
        p.setPen(QPen(tabby_dark, 3, Qt.SolidLine, Qt.RoundCap))
        for i in range(3):
            y = -28 - i * 22
            p.drawLine(4 + i * 2, y, 14 + i * 2, y - 3)
        p.restore()

        # ---- 身体 (白色蹲坐) ----
        body = QPainterPath()
        body.moveTo(cx - 72, base_y)
        body.cubicTo(cx - 95, base_y - 90, cx - 62, base_y - 155, cx, base_y - 150)
        body.cubicTo(cx + 62, base_y - 155, cx + 95, base_y - 90, cx + 72, base_y)
        body.closeSubpath()
        p.setBrush(white_fur)
        p.setPen(QPen(white_shade, 1))
        p.drawPath(body)

        # 胸口阴影层次
        chest = QPainterPath()
        chest.addEllipse(cx - 32, base_y - 105, 64, 55)
        p.setBrush(QColor(255, 252, 245, 180))
        p.setPen(Qt.NoPen)
        p.drawPath(chest)

        # ---- 头 ----
        hcx = cx
        hcy = base_y - 185

        head = QPainterPath()
        head.addEllipse(hcx - 62, hcy - 55, 124, 118)
        p.setBrush(tabby_light)
        p.setPen(Qt.NoPen)
        p.drawPath(head)

        # 白色下巴/口鼻
        chin = QPainterPath()
        chin.addEllipse(hcx - 46, hcy - 3, 92, 66)
        p.setBrush(white_fur)
        p.drawPath(chin)

        # 额头虎斑纹 (M 字纹)
        p.setPen(QPen(tabby_dark, 3, Qt.SolidLine, Qt.RoundCap))
        p.drawLine(hcx - 22, hcy - 46, hcx - 17, hcy - 24)
        p.drawLine(hcx - 8, hcy - 50, hcx - 5, hcy - 24)
        p.drawLine(hcx + 8, hcy - 50, hcx + 5, hcy - 24)
        p.drawLine(hcx + 22, hcy - 46, hcx + 17, hcy - 24)
        # 脸颊纹
        p.drawLine(hcx - 56, hcy - 16, hcx - 40, hcy - 10)
        p.drawLine(hcx + 56, hcy - 16, hcx + 40, hcy - 10)
        p.drawLine(hcx - 56, hcy - 4, hcx - 42, hcy + 2)
        p.drawLine(hcx + 56, hcy - 4, hcx + 42, hcy + 2)

        # ---- 耳朵 (大三角) ----
        for side in (-1, 1):
            ear = QPainterPath()
            ear.moveTo(hcx + side * 55, hcy - 40)
            ear.lineTo(hcx + side * 66, hcy - 92)
            ear.lineTo(hcx + side * 25, hcy - 55)
            ear.closeSubpath()
            p.setBrush(tabby_light)
            p.setPen(Qt.NoPen)
            p.drawPath(ear)

            inner = QPainterPath()
            inner.moveTo(hcx + side * 52, hcy - 45)
            inner.lineTo(hcx + side * 58, hcy - 80)
            inner.lineTo(hcx + side * 34, hcy - 56)
            inner.closeSubpath()
            p.setBrush(ear_pink)
            p.drawPath(inner)

        # ---- 眼睛 (标志性的半眯嫌弃脸) ----
        eye_y = hcy - 14
        if self.sleeping:
            p.setPen(QPen(tabby_dark, 2.2, Qt.SolidLine, Qt.RoundCap))
            p.setBrush(Qt.NoBrush)
            for x0 in (hcx - 33, hcx + 13):
                arc = QPainterPath()
                arc.moveTo(x0, eye_y - 1)
                arc.quadTo(x0 + 10, eye_y + 8, x0 + 20, eye_y - 1)
                p.drawPath(arc)
        elif self.blink_state:
            p.setPen(QPen(tabby_dark, 2.2, Qt.SolidLine, Qt.RoundCap))
            p.drawLine(hcx - 32, eye_y, hcx - 14, eye_y)
            p.drawLine(hcx + 14, eye_y, hcx + 32, eye_y)
        else:
            eye_h = 12 * self.eye_openness
            # 左眼
            p.setBrush(eye_green)
            p.setPen(QPen(tabby_dark, 1.5))
            le = QPainterPath()
            le.moveTo(hcx - 34, eye_y)
            le.quadTo(hcx - 23, eye_y - eye_h, hcx - 12, eye_y)
            le.quadTo(hcx - 23, eye_y + eye_h * 0.5, hcx - 34, eye_y)
            p.drawPath(le)
            # 右眼
            re = QPainterPath()
            re.moveTo(hcx + 12, eye_y)
            re.quadTo(hcx + 23, eye_y - eye_h, hcx + 34, eye_y)
            re.quadTo(hcx + 23, eye_y + eye_h * 0.5, hcx + 12, eye_y)
            p.drawPath(re)
            # 竖瞳
            p.setBrush(QColor(28, 28, 28))
            p.setPen(Qt.NoPen)
            p.drawEllipse(int(hcx - 25), int(eye_y - 3), 3, 5)
            p.drawEllipse(int(hcx + 22), int(eye_y - 3), 3, 5)
            # 上眼皮 - 制造嫌弃感
            p.setPen(QPen(tabby_dark, 2.2, Qt.SolidLine, Qt.RoundCap))
            p.drawLine(hcx - 34, eye_y - 2, hcx - 12, eye_y - 5)
            p.drawLine(hcx + 12, eye_y - 5, hcx + 34, eye_y - 2)

        # ---- 鼻子 ----
        nose = QPainterPath()
        nose.moveTo(hcx - 7, hcy + 9)
        nose.lineTo(hcx + 7, hcy + 9)
        nose.lineTo(hcx, hcy + 18)
        nose.closeSubpath()
        p.setBrush(pink_nose)
        p.setPen(QPen(QColor(148, 88, 88), 1))
        p.drawPath(nose)

        # ---- 嘴巴 (Ω) ----
        p.setPen(QPen(tabby_dark, 1.5, Qt.SolidLine, Qt.RoundCap))
        p.setBrush(Qt.NoBrush)
        p.drawLine(hcx, hcy + 18, hcx, hcy + 24)
        m1 = QPainterPath()
        m1.moveTo(hcx, hcy + 24)
        m1.quadTo(hcx - 6, hcy + 28, hcx - 11, hcy + 23)
        p.drawPath(m1)
        m2 = QPainterPath()
        m2.moveTo(hcx, hcy + 24)
        m2.quadTo(hcx + 6, hcy + 28, hcx + 11, hcy + 23)
        p.drawPath(m2)

        # ---- 胡须 ----
        p.setPen(QPen(QColor(232, 226, 216), 1.3))
        for dy, dx2 in [(15, 8), (18, 18), (21, 28)]:
            p.drawLine(hcx - 18, hcy + dy, hcx - 56, hcy + dx2)
            p.drawLine(hcx + 18, hcy + dy, hcx + 56, hcy + dx2)

        # ---- 前爪 ----
        p.setBrush(white_fur)
        p.setPen(QPen(white_shade, 1))
        p.drawEllipse(int(cx - 36), int(base_y - 22), 30, 24)
        p.drawEllipse(int(cx + 6), int(base_y - 22), 30, 24)
        p.setPen(QPen(QColor(205, 200, 190), 1))
        for x in [-31, -22, -13]:
            p.drawLine(int(cx + x), int(base_y - 10), int(cx + x), int(base_y - 2))
        for x in [13, 22, 31]:
            p.drawLine(int(cx + x), int(base_y - 10), int(cx + x), int(base_y - 2))

        # ---- 睡觉 Zzz ----
        if self.sleeping:
            for i in range(3):
                t = (self.tick / 20.0 + i * 1.0) % 3
                alpha = int(255 * (1 - t / 3))
                p.setPen(QColor(90, 100, 140, alpha))
                p.setFont(QFont("Arial", 11 + i * 2, QFont.Bold))
                p.drawText(int(hcx + 50 + t * 14), int(hcy - 55 - t * 18), "Z")

        # ---- 番茄钟倒计时 ----
        if self.pomo_end is not None:
            remain = max(0, int(self.pomo_end - time.time()))
            label = "番茄 %02d:%02d" % (remain // 60, remain % 60)
            p.setFont(QFont("Microsoft YaHei", 9, QFont.Bold))
            lw = p.fontMetrics().horizontalAdvance(label) + 16
            p.setBrush(QColor(214, 80, 68, 225))
            p.setPen(Qt.NoPen)
            p.drawRoundedRect(int(cx - lw / 2), DH - 24, int(lw), 20, 9, 9)
            p.setPen(QColor(255, 255, 255))
            p.drawText(int(cx - lw / 2), DH - 24, int(lw), 20,
                       Qt.AlignCenter, label)

        # ---- 对话气泡 ----
        if self.speech:
            p.setFont(QFont("Microsoft YaHei", 10, QFont.Bold))
            fm = p.fontMetrics()
            tw = fm.horizontalAdvance(self.speech)
            th = fm.height()
            bw, bh = tw + 22, th + 12
            bx = min(cx + 40, DW - bw - 4)
            by = max(2, hcy - 95)

            p.setBrush(QColor(255, 255, 255, 235))
            p.setPen(QPen(QColor(80, 80, 80), 1.5))
            p.drawRoundedRect(int(bx), int(by), int(bw), int(bh), 10, 10)

            tail_b = QPainterPath()
            tail_b.moveTo(bx + 6, by + bh)
            tail_b.lineTo(bx - 4, by + bh + 10)
            tail_b.lineTo(bx + 20, by + bh)
            tail_b.closeSubpath()
            p.setBrush(QColor(255, 255, 255, 235))
            p.setPen(QPen(QColor(80, 80, 80), 1.5))
            p.drawPath(tail_b)

            p.setPen(QColor(40, 40, 40))
            p.drawText(int(bx + 11), int(by + th + 1), self.speech)

    # ---------- 交互 ----------
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            was_sleeping = self.sleeping
            self.wake()
            self.drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            self.say(random.choice(WAKE_LINES if was_sleeping else POKE_LINES), 45)
            event.accept()
        elif event.button() == Qt.RightButton:
            self.show_menu(event.globalPos())

    def mouseMoveEvent(self, event):
        if self.drag_pos and event.buttons() & Qt.LeftButton:
            self.move(event.globalPos() - self.drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self.drag_pos = None
        self.last_active = time.time()

    def mouseDoubleClickEvent(self, event):
        self.wake()
        self.say(random.choice(PAT_LINES), 65)

    def build_menu(self):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu { background:#fff; border:1px solid #bbb; padding:4px; }
            QMenu::item { padding:6px 22px; font-family:'Microsoft YaHei'; }
            QMenu::item:selected { background:#e6e6e6; }
        """)

        a1 = QAction("打个招呼", self)
        a1.triggered.connect(lambda: self.say("你好呀!", 60))
        menu.addAction(a1)

        a2 = QAction("喵一下", self)
        a2.triggered.connect(lambda: self.say("喵~", 50))
        menu.addAction(a2)

        a3 = QAction("来句骚话", self)
        a3.triggered.connect(lambda: self.say(random.choice(SASS_LINES), 90))
        menu.addAction(a3)

        menu.addSeparator()

        # 大小
        size_menu = menu.addMenu("大小")
        group = QActionGroup(size_menu)
        group.setExclusive(True)
        for name, f in SIZE_OPTIONS:
            act = QAction(f"{name}  {int(f * 100)}%", size_menu)
            act.setCheckable(True)
            act.setChecked(abs(f - self.scale_factor) < 0.01)
            act.triggered.connect(lambda _checked, f=f: self.set_scale(f))
            group.addAction(act)
            size_menu.addAction(act)

        af = QAction("跟着鼠标走", self)
        af.setCheckable(True)
        af.setChecked(self.follow)
        af.triggered.connect(self.toggle_follow)
        menu.addAction(af)

        if self.pomo_end is None:
            ap = QAction("开始番茄钟 (25分钟)", self)
            ap.triggered.connect(self.start_pomodoro)
        else:
            ap = QAction("取消番茄钟", self)
            ap.triggered.connect(self.cancel_pomodoro)
        menu.addAction(ap)

        menu.addSeparator()
        aq = QAction("退出", self)
        aq.triggered.connect(QApplication.quit)
        menu.addAction(aq)
        return menu

    def show_menu(self, pos):
        self.wake()
        self.build_menu().exec_(pos)

def main():
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)
    if hasattr(Qt, "HighDpiScaleFactorRoundingPolicy"):
        QApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    app = QApplication(sys.argv)
    cat = DesktopCat()
    cat.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
