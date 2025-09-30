import sys
import time
import struct
import threading
import serial
import serial.tools.list_ports
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QComboBox, QMessageBox, QFileDialog,
    QGridLayout, QGroupBox, QSplitter, QTextEdit, QTabWidget
)
from PyQt5.QtCore import QTimer, Qt, pyqtSignal, QObject
from PyQt5.QtChart import QChart, QChartView, QLineSeries, QValueAxis
from PyQt5.QtGui import QColor, QPen, QFont
import numpy as np

class SerialDataReader(QObject):
    """Класс для чтения данных с COM-порта в отдельном потоке"""
    data_received = pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()
        self.ser = None
        self.running = False
        self.buffer = bytearray()
        self.thread = None
    
    def start_reading(self, port, baud_rate):
        """Запуск чтения данных"""
        try:
            self.ser = serial.Serial(port, baud_rate, timeout=1)
            self.running = True
            self.thread = threading.Thread(target=self._read_loop, daemon=True)
            self.thread.start()
            return True
        except Exception as e:
            return False, str(e)
    
    def stop_reading(self):
        """Остановка чтения данных"""
        self.running = False
        if self.ser and self.ser.is_open:
            self.ser.close()
        if self.thread:
            self.thread.join(timeout=1)
    
    def _read_loop(self):
        """Основной цикл чтения данных"""
        while self.running:
            try:
                if self.ser.in_waiting > 0:
                    self.buffer.extend(self.ser.read(self.ser.in_waiting))
                
                while len(self.buffer) >= 34 and self.running:
                    if self.buffer[0] == 0xBD and self.buffer[1] == 0xDB and self.buffer[2] == 0x0A:
                        packet = self.buffer[:34]
                        self.buffer = self.buffer[34:]
                        data = self._parse_packet(packet)
                        if data:
                            self.data_received.emit(data)
                    else:
                        self.buffer.pop(0)
            except Exception as e:
                if self.running:
                    print(f"Ошибка чтения: {e}")
                break
            time.sleep(0.001)
    
    def _parse_packet(self, data):
        """Парсинг пакета данных"""
        if len(data) != 34:
            return None
        if data[0] != 0xBD or data[1] != 0xDB or data[2] != 0x0A:
            return None
        
        checksum = 0
        for i in range(33):
            checksum ^= data[i]
        if checksum != data[33]:
            return None
        
        try:
            gx = struct.unpack('<f', data[3:7])[0]
            gy = struct.unpack('<f', data[7:11])[0]
            gz = struct.unpack('<f', data[11:15])[0]
            ax = struct.unpack('<f', data[15:19])[0]
            ay = struct.unpack('<f', data[19:23])[0]
            az = struct.unpack('<f', data[23:27])[0]
            return {'gx': gx, 'gy': gy, 'gz': gz, 'ax': ax, 'ay': ay, 'az': az}
        except Exception:
            return None


class DataDisplayWidget(QWidget):
    """Виджет для отображения текущих значений датчиков"""
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # Группа для гироскопа
        gyro_group = QGroupBox("Гироскоп (°/с)")
        gyro_layout = QGridLayout(gyro_group)
        
        self.gx_label = QLabel("0.00")
        self.gy_label = QLabel("0.00")
        self.gz_label = QLabel("0.00")
        
        gyro_layout.addWidget(QLabel("X:"), 0, 0)
        gyro_layout.addWidget(self.gx_label, 0, 1)
        gyro_layout.addWidget(QLabel("Y:"), 1, 0)
        gyro_layout.addWidget(self.gy_label, 1, 1)
        gyro_layout.addWidget(QLabel("Z:"), 2, 0)
        gyro_layout.addWidget(self.gz_label, 2, 1)
        
        layout.addWidget(gyro_group)
        
        # Группа для акселерометра
        acc_group = QGroupBox("Акселерометр (м/с²)")
        acc_layout = QGridLayout(acc_group)
        
        self.ax_label = QLabel("0.00")
        self.ay_label = QLabel("0.00")
        self.az_label = QLabel("0.00")
        
        acc_layout.addWidget(QLabel("X:"), 0, 0)
        acc_layout.addWidget(self.ax_label, 0, 1)
        acc_layout.addWidget(QLabel("Y:"), 1, 0)
        acc_layout.addWidget(self.ay_label, 1, 1)
        acc_layout.addWidget(QLabel("Z:"), 2, 0)
        acc_layout.addWidget(self.az_label, 2, 1)
        
        layout.addWidget(acc_group)
        
        # Настройка шрифтов
        font = QFont()
        font.setPointSize(12)
        font.setBold(True)
        
        for label in [self.gx_label, self.gy_label, self.gz_label, 
                     self.ax_label, self.ay_label, self.az_label]:
            label.setFont(font)
            label.setStyleSheet("color: #2E8B57; background-color: #F0F8FF; padding: 5px; border: 1px solid #ccc;")
    
    def update_data(self, data):
        """Обновление отображаемых данных"""
        self.gx_label.setText(f"{data['gx']:.2f}")
        self.gy_label.setText(f"{data['gy']:.2f}")
        self.gz_label.setText(f"{data['gz']:.2f}")
        self.ax_label.setText(f"{data['ax']:.2f}")
        self.ay_label.setText(f"{data['ay']:.2f}")
        self.az_label.setText(f"{data['az']:.2f}")


class HorizonWidget(QWidget):
    """Простой искусственный горизонт в круглой рамке.
    Использует roll (крен) и pitch (тангаж) в градусах.
    """
    def __init__(self):
        super().__init__()
        self.roll_deg = 0.0
        self.pitch_deg = 0.0
        self.setMinimumSize(300, 300)

    def set_attitude(self, roll_deg, pitch_deg):
        self.roll_deg = roll_deg
        self.pitch_deg = max(min(pitch_deg, 45.0), -45.0)  # ограничим тангаж
        self.update()

    def paintEvent(self, event):
        from PyQt5.QtGui import QPainter, QBrush, QPainterPath
        from PyQt5.QtCore import QRectF
        size = min(self.width(), self.height())
        cx = self.width() // 2
        cy = self.height() // 2
        radius = size // 2 - 6

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Фон
        painter.fillRect(self.rect(), QColor('#000'))

        # Внешняя круглая рамка
        painter.setPen(QPen(QColor('#E0E0E0'), 3))
        painter.setBrush(QBrush(QColor('#111')))
        outer = QRectF(cx - radius, cy - radius, radius * 2, radius * 2)
        painter.drawEllipse(outer)

        # Внутренняя "окошко" с закруглениями
        inner_margin = radius * 0.18
        inner_rect = QRectF(cx - radius + inner_margin,
                            cy - radius + inner_margin,
                            (radius - inner_margin) * 2,
                            (radius - inner_margin) * 2)

        clip_path = QPainterPath()
        clip_path.addRoundedRect(inner_rect, 28, 28)
        painter.save()
        painter.setClipPath(clip_path)

        # Система горизонта (вращаем по крену)
        painter.translate(inner_rect.center())
        painter.rotate(self.roll_deg)

        pitch_px_per_deg = inner_rect.height() / 2.0 / 35.0
        pitch_offset = self.pitch_deg * pitch_px_per_deg

        # Небо
        painter.setPen(Qt.NoPen)
        painter.setBrush(QBrush(QColor('#2F9DED')))
        painter.drawRect(-1000, -1000 - pitch_offset, 2000, 1000)

        # Земля
        painter.setBrush(QBrush(QColor('#88552C')))
        painter.drawRect(-1000, -pitch_offset, 2000, 1000)

        # Линия горизонта
        painter.setPen(QPen(QColor('white'), 3))
        painter.drawLine(-1200, -pitch_offset, 1200, -pitch_offset)

        # Разметка тангажа (каждые 10°)
        painter.setPen(QPen(QColor('white'), 2))
        for deg in range(-30, 31, 10):
            y = -(deg * pitch_px_per_deg) - pitch_offset
            # короткие штрихи по краям
            painter.drawLine(-130, y, -40, y)
            painter.drawLine(40, y, 130, y)
            if deg != 0:
                # подписи
                painter.setPen(QPen(QColor('white')))
                self._draw_text(painter, -140, y - 2, f"{abs(deg)}")
                self._draw_text(painter, 115, y - 2, f"{abs(deg)}")
                painter.setPen(QPen(QColor('white'), 2))

        painter.restore()

        # Фиксированный самолётик в центре
        painter.setPen(QPen(QColor('white'), 3))
        painter.drawLine(cx - 60, cy, cx - 15, cy)
        painter.drawLine(cx + 15, cy, cx + 60, cy)
        painter.drawLine(cx - 15, cy, cx - 5, cy + 6)
        painter.drawLine(cx + 5, cy + 6, cx + 15, cy)
        painter.setPen(QPen(QColor('white'), 2))
        painter.drawEllipse(QRectF(cx - 6, cy - 6, 12, 12))

        # Верхняя шкала крена (дуга)
        painter.setPen(QPen(QColor('white'), 2))
        arc_radius = radius - 8
        for mark, length in [(0, 16), (10, 10), (20, 10), (30, 14), (45, 10), (60, 10)]:
            for sign in (-1, 1):
                ang = -90 + sign * mark
                a = np.radians(ang)
                sx = cx + arc_radius * np.cos(a)
                sy = cy + arc_radius * np.sin(a)
                ex = cx + (arc_radius - length) * np.cos(a)
                ey = cy + (arc_radius - length) * np.sin(a)
                painter.drawLine(int(sx), int(sy), int(ex), int(ey))

        # Треугольный указатель крена сверху
        painter.setBrush(QBrush(QColor('white')))
        pointer_y = cy - arc_radius - 4
        path = QPainterPath()
        path.moveTo(cx, pointer_y)
        path.lineTo(cx - 10, pointer_y + 16)
        path.lineTo(cx + 10, pointer_y + 16)
        path.closeSubpath()
        painter.drawPath(path)

        painter.end()

    def _draw_text(self, painter, x, y, text):
        from PyQt5.QtGui import QFontMetrics
        fm = QFontMetrics(painter.font())
        w = fm.width(text)
        painter.drawText(int(x - w/2), int(y), text)

class RIM1AMonitorApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("IMU Monitor — Real-time Data Display")
        self.resize(1200, 800)

        # Переменные
        self.serial_reader = SerialDataReader()
        self.max_points = 500

        # Данные
        self.gx_data = []
        self.gy_data = []
        self.gz_data = []
        self.ax_data = []
        self.ay_data = []
        self.az_data = []

        # UI
        self.init_ui()
        
        # Подключение сигналов
        self.serial_reader.data_received.connect(self.on_data_received)

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # Панель управления
        control_layout = QHBoxLayout()
        control_layout.addWidget(QLabel("Порт:"))
        self.port_combo = QComboBox()
        self.update_ports()
        control_layout.addWidget(self.port_combo)

        control_layout.addWidget(QLabel("Скорость (baud):"))
        self.baud_combo = QComboBox()
        self.baud_combo.addItems(["9600", "19200", "38400", "57600", "115200", "230400", "460800", "921600"])
        self.baud_combo.setCurrentText("115200")
        control_layout.addWidget(self.baud_combo)

        self.start_btn = QPushButton("Старт")
        self.start_btn.clicked.connect(self.start_reading)
        control_layout.addWidget(self.start_btn)

        self.stop_btn = QPushButton("Стоп")
        self.stop_btn.clicked.connect(self.stop_reading)
        self.stop_btn.setEnabled(False)
        control_layout.addWidget(self.stop_btn)

        self.clear_btn = QPushButton("Очистить")
        self.clear_btn.clicked.connect(self.clear_data)
        control_layout.addWidget(self.clear_btn)

        self.save_btn = QPushButton("Сохранить")
        self.save_btn.clicked.connect(self.save_plot)
        control_layout.addWidget(self.save_btn)

        main_layout.addLayout(control_layout)

        # Вкладки
        tabs = QTabWidget()

        # Вкладка 1 — Данные и графики
        tab1 = QWidget()
        t1_layout = QVBoxLayout(tab1)
        splitter = QSplitter(Qt.Horizontal)
        # Левая панель — значения
        self.data_display = DataDisplayWidget()
        splitter.addWidget(self.data_display)
        # Правая панель — графики
        charts_widget = QWidget()
        charts_layout = QVBoxLayout(charts_widget)
        self.chart_gyro = self.create_chart("Гироскоп (°/с)")
        self.chart_acc = self.create_chart("Акселерометр (м/с²)")
        self.chart_view_gyro = QChartView(self.chart_gyro)
        self.chart_view_acc = QChartView(self.chart_acc)
        charts_layout.addWidget(self.chart_view_gyro)
        charts_layout.addWidget(self.chart_view_acc)
        splitter.addWidget(charts_widget)
        splitter.setSizes([300, 900])
        t1_layout.addWidget(splitter)
        tabs.addTab(tab1, "Данные")

        # Вкладка 2 — Искусственный горизонт
        tab2 = QWidget()
        t2_layout = QVBoxLayout(tab2)
        self.horizon = HorizonWidget()
        t2_layout.addWidget(self.horizon)
        tabs.addTab(tab2, "Горизонт")

        main_layout.addWidget(tabs)

        # Таймер для обновления
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_plots)

        # Парсер пакетов
        self.last_update_time = 0
        self.autoscale_interval = 2.0

    def create_chart(self, title):
        chart = QChart()
        chart.setTitle(title)
        chart.legend().setVisible(True)
        chart.legend().setAlignment(Qt.AlignRight)

        # Оси
        axis_x = QValueAxis()
        axis_x.setRange(0, self.max_points)
        axis_x.setTickCount(6)
        chart.addAxis(axis_x, Qt.AlignBottom)

        axis_y = QValueAxis()
        axis_y.setRange(-10, 10)  # Можно менять динамически
        axis_y.setTickCount(5)
        chart.addAxis(axis_y, Qt.AlignLeft)

        # Серии для гироскопа
        if "Гироскоп" in title:
            self.series_gx = QLineSeries()
            self.series_gx.setName("Gx")
            self.series_gx.setColor(QColor("red"))
            self.series_gx.setPen(QPen(QColor("red"), 2))
            chart.addSeries(self.series_gx)
            self.series_gx.attachAxis(axis_x)
            self.series_gx.attachAxis(axis_y)

            self.series_gy = QLineSeries()
            self.series_gy.setName("Gy")
            self.series_gy.setColor(QColor("green"))
            self.series_gy.setPen(QPen(QColor("green"), 2))
            chart.addSeries(self.series_gy)
            self.series_gy.attachAxis(axis_x)
            self.series_gy.attachAxis(axis_y)

            self.series_gz = QLineSeries()
            self.series_gz.setName("Gz")
            self.series_gz.setColor(QColor("blue"))
            self.series_gz.setPen(QPen(QColor("blue"), 2))
            chart.addSeries(self.series_gz)
            self.series_gz.attachAxis(axis_x)
            self.series_gz.attachAxis(axis_y)
        
        # Серии для акселерометра
        else:
            self.series_ax = QLineSeries()
            self.series_ax.setName("Ax")
            self.series_ax.setColor(QColor("red"))
            self.series_ax.setPen(QPen(QColor("red"), 2))
            chart.addSeries(self.series_ax)
            self.series_ax.attachAxis(axis_x)
            self.series_ax.attachAxis(axis_y)

            self.series_ay = QLineSeries()
            self.series_ay.setName("Ay")
            self.series_ay.setColor(QColor("green"))
            self.series_ay.setPen(QPen(QColor("green"), 2))
            chart.addSeries(self.series_ay)
            self.series_ay.attachAxis(axis_x)
            self.series_ay.attachAxis(axis_y)

            self.series_az = QLineSeries()
            self.series_az.setName("Az")
            self.series_az.setColor(QColor("blue"))
            self.series_az.setPen(QPen(QColor("blue"), 2))
            chart.addSeries(self.series_az)
            self.series_az.attachAxis(axis_x)
            self.series_az.attachAxis(axis_y)

        return chart

    def update_ports(self):
        ports = [p.device for p in serial.tools.list_ports.comports()]
        if not ports:
            ports = ["Нет портов"]
        self.port_combo.clear()
        self.port_combo.addItems(ports)
        if ports:
            self.port_combo.setCurrentText(ports[0])

    def on_data_received(self, data):
        """Обработка полученных данных"""
        # Обновляем отображение текущих значений
        self.data_display.update_data(data)
        
        # Добавляем данные в буферы
        self.append_data(data)

        # Обновляем горизонт (оценка roll/pitch)
        roll_deg, pitch_deg = self.estimate_attitude(data)
        if hasattr(self, 'horizon'):
            self.horizon.set_attitude(roll_deg, pitch_deg)

    def append_data(self, data):
        # Добавляем данные
        self.gx_data.append(data['gx'])
        self.gy_data.append(data['gy'])
        self.gz_data.append(data['gz'])
        self.ax_data.append(data['ax'])
        self.ay_data.append(data['ay'])
        self.az_data.append(data['az'])

        # Ограничиваем буфер
        if len(self.gx_data) > self.max_points:
            self.gx_data.pop(0)
            self.gy_data.pop(0)
            self.gz_data.pop(0)
            self.ax_data.pop(0)
            self.ay_data.pop(0)
            self.az_data.pop(0)

    def update_plots(self):
        now = time.time()
        if now - self.last_update_time > self.autoscale_interval:
            self.autoscale_charts()
            self.last_update_time = now

        # Обновляем данные только если есть данные
        if not self.gx_data:
            return

        # Обновляем данные
        x = list(range(len(self.gx_data)))

        self.series_gx.clear()
        self.series_gy.clear()
        self.series_gz.clear()
        self.series_ax.clear()
        self.series_ay.clear()
        self.series_az.clear()

        for i, val in enumerate(x):
            self.series_gx.append(i, self.gx_data[i])
            self.series_gy.append(i, self.gy_data[i])
            self.series_gz.append(i, self.gz_data[i])
            self.series_ax.append(i, self.ax_data[i])
            self.series_ay.append(i, self.ay_data[i])
            self.series_az.append(i, self.az_data[i])

    def autoscale_charts(self):
        # Масштабируем ось Y для гироскопа
        if self.gx_data:
            min_val = min(min(self.gx_data), min(self.gy_data), min(self.gz_data))
            max_val = max(max(self.gx_data), max(self.gy_data), max(self.gz_data))
            margin = (max_val - min_val) * 0.1
            self.chart_gyro.axisY().setRange(min_val - margin, max_val + margin)

        # Масштабируем ось Y для акселерометра
        if self.ax_data:
            min_val = min(min(self.ax_data), min(self.ay_data), min(self.az_data))
            max_val = max(max(self.ax_data), max(self.ay_data), max(self.az_data))
            margin = (max_val - min_val) * 0.1
            self.chart_acc.axisY().setRange(min_val - margin, max_val + margin)

    def estimate_attitude(self, data):
        """Простой комплементарный фильтр для оценки roll/pitch.
        Вход: последние gx, gy (°/с), ax, ay, az (м/с^2)
        Выход: (roll_deg, pitch_deg)
        """
        # Инициализация хранилища углов
        if not hasattr(self, '_att_roll_deg'):
            self._att_roll_deg = 0.0
            self._att_pitch_deg = 0.0
            self._last_ts = time.time()

        # Интервал времени
        now = time.time()
        dt = max(min(now - self._last_ts, 0.1), 1e-3)
        self._last_ts = now

        gx = float(data['gx'])  # deg/s
        gy = float(data['gy'])  # deg/s
        ax = float(data['ax'])
        ay = float(data['ay'])
        az = float(data['az'])

        # Оценка из акселерометра (в градусах)
        # roll_acc: atan2(ay, az), pitch_acc: atan2(-ax, sqrt(ay^2+az^2))
        from math import atan2, sqrt, degrees
        roll_acc = degrees(atan2(ay, az)) if (abs(az) + abs(ay)) > 1e-6 else 0.0
        pitch_acc = degrees(atan2(-ax, sqrt(ay*ay + az*az)))

        # Интегрирование гироскопа
        roll_gyro = self._att_roll_deg + gx * dt
        pitch_gyro = self._att_pitch_deg + gy * dt

        alpha = 0.98
        self._att_roll_deg = alpha * roll_gyro + (1 - alpha) * roll_acc
        self._att_pitch_deg = alpha * pitch_gyro + (1 - alpha) * pitch_acc

        return self._att_roll_deg, self._att_pitch_deg

    def start_reading(self):
        port = self.port_combo.currentText()
        baud = int(self.baud_combo.currentText())

        if port == "Нет портов":
            QMessageBox.warning(self, "Ошибка", "Нет доступных COM-портов!")
            return

        result = self.serial_reader.start_reading(port, baud)
        if result is not True:
            QMessageBox.critical(self, "Ошибка", f"Не удалось открыть порт:\n{result[1]}")
            return

        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.clear_btn.setEnabled(False)

        self.timer.start(50)  # Обновление каждые 50 мс (~20 FPS)

    def stop_reading(self):
        self.serial_reader.stop_reading()
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.clear_btn.setEnabled(True)
        self.timer.stop()

    def clear_data(self):
        self.gx_data.clear()
        self.gy_data.clear()
        self.gz_data.clear()
        self.ax_data.clear()
        self.ay_data.clear()
        self.az_data.clear()

        self.series_gx.clear()
        self.series_gy.clear()
        self.series_gz.clear()
        self.series_ax.clear()
        self.series_ay.clear()
        self.series_az.clear()

        self.chart_gyro.axisY().setRange(-10, 10)
        self.chart_acc.axisY().setRange(-10, 10)
        
        # Сбрасываем отображение текущих значений
        self.data_display.update_data({'gx': 0, 'gy': 0, 'gz': 0, 'ax': 0, 'ay': 0, 'az': 0})

    def save_plot(self):
        filename, _ = QFileDialog.getSaveFileName(
            self, "Сохранить график", "", "PNG Files (*.png);;All Files (*)"
        )
        if filename:
            if not filename.endswith(".png"):
                filename += ".png"
            pixmap = self.chart_view_gyro.grab()
            pixmap.save(filename)
            QMessageBox.information(self, "Успех", f"График сохранён как {filename}")

    def closeEvent(self, event):
        self.stop_reading()
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = RIM1AMonitorApp()
    window.show()
    sys.exit(app.exec_())