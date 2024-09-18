from blehrm import readers
from blehrm import registry
from bleak import BleakScanner
import asyncio
from PySide6.QtCore import Qt, QPointF, QTimer
from PySide6.QtWidgets import QApplication
from PySide6.QtCharts import QChartView, QChart, QLineSeries, QValueAxis
from PySide6.QtGui import QPen
from qasync import QEventLoop
from collections import deque
import time

ADDRESS = "5BE8C8E0-8FA7-CEE7-4662-D49695040AF7"

class View(QChartView):
    def __init__(self):
        chart = QChart()
        super().__init__(chart)
        
        self.series = QLineSeries()
        pen = QPen("red")
        pen.setWidth(1)
        self.series.setPen(pen)
        self.x_axis, self.y_axis = QValueAxis(), QValueAxis()
        chart.addSeries(self.series)
        chart.addAxis(self.x_axis, Qt.AlignBottom)
        chart.addAxis(self.y_axis, Qt.AlignLeft)
        self.series.attachAxis(self.x_axis)
        self.series.attachAxis(self.y_axis)
        
        chart.setTitle("Live ECG Stream")
        chart.legend().setVisible(False)

        self.x_axis.setRange(-15, 0)
        self.y_axis.setRange(-1000, 2000)

        self.buffer = deque(maxlen=2000)
        self.start_series_update()

    def update_buffer(self, data):
        ''' Update buffer with values epoch_s, and ecg'''
        t, y = data[0], data[1]
        self.buffer.append((t, y))

    def update_series(self):
        ''' Receives ecg data and updates the chart '''
        new_series = []
        current_time = time.time_ns()/1.0e9
        for pt in self.buffer:
            new_series.append(QPointF(pt[0] - current_time, pt[1]))
            self.series.replace(new_series)
    
    def start_series_update(self):
        self.series_update_loop = QTimer()
        self.series_update_loop.timeout.connect(self.update_series)
        self.series_update_loop.setInterval(10)
        self.series_update_loop.start()

async def main(view):
    
    ble_device = await BleakScanner.find_device_by_address(ADDRESS, timeout=20.0)
    if ble_device is None:
        print(f"Device with address {ADDRESS} not found")
        return

    blehrm_reader = registry.blehrmRegistry.create_reader(ble_device)    
    await blehrm_reader.connect()
    await blehrm_reader.start_ecg_stream(view.update_buffer)

    print("Streaming ecg data. Press Ctrl+C to stop.")
    while True:
        await asyncio.sleep(100)

if __name__ == "__main__":
    
    app = QApplication()
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    view = View()
    view.setWindowTitle("BLEHRM")
    view.resize(800, 400)
    view.show()

    try:
        loop.run_until_complete(main(view))
    except KeyboardInterrupt:
        print("\nStream stopped by user.")