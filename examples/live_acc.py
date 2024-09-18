from blehrm import readers
from blehrm import registry
from bleak import BleakScanner
import asyncio
import sys
import numpy as np
from PySide6.QtWidgets import QApplication, QMainWindow
import pyqtgraph.opengl as gl
from qasync import QEventLoop

# ADDRESS = "CF7582F0-5AA4-7279-63A3-5850A4B6F780" # CL800
ADDRESS = "5BE8C8E0-8FA7-CEE7-4662-D49695040AF7" # Polar H10

class AccelerometerVisualizer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("3D Accelerometer Visualization")
        self.resize(800, 600)

        self.plot_widget = gl.GLViewWidget()
        self.setCentralWidget(self.plot_widget)

        grid = gl.GLGridItem()
        self.plot_widget.addItem(grid)

        axis_length = 2
        x_axis = gl.GLLinePlotItem(pos=np.array([[0, 0, 0], [axis_length, 0, 0]]), color=(1, 0, 0, 1), width=2)
        y_axis = gl.GLLinePlotItem(pos=np.array([[0, 0, 0], [0, axis_length, 0]]), color=(0, 1, 0, 1), width=2)
        z_axis = gl.GLLinePlotItem(pos=np.array([[0, 0, 0], [0, 0, axis_length]]), color=(0, 0, 1, 1), width=2)
        self.plot_widget.addItem(x_axis)
        self.plot_widget.addItem(y_axis)
        self.plot_widget.addItem(z_axis)

        self.vector = gl.GLLinePlotItem(pos=np.array([[0, 0, 0], [1, 1, 1]]), color=(1, 1, 0, 1), width=3)
        self.plot_widget.addItem(self.vector)

        self.trail = gl.GLLinePlotItem(pos=np.array([[0, 0, 0]]), color=(1, 1, 0, 0.5), width=2)
        self.plot_widget.addItem(self.trail)
        self.trail_data = np.array([[0, 0, 0]])

    def update_acc_vector(self, data):
        t, x, y, z = data
        new_pos = np.array([[0, 0, 0], [x, y, z]])
        self.vector.setData(pos=new_pos)

        self.trail_data = np.vstack([self.trail_data, [x, y, z]])
        if len(self.trail_data) > 100:
            self.trail_data = self.trail_data[-100:]
        self.trail.setData(pos=self.trail_data)

async def main(view):
    
    ble_device = await BleakScanner.find_device_by_address(ADDRESS, timeout=20.0)
    if ble_device is None:
        print(f"Device with address {ADDRESS} not found")
        return

    blehrm_reader = registry.blehrmRegistry.create_reader(ble_device)    
    await blehrm_reader.connect()
    await blehrm_reader.start_acc_stream(view.update_acc_vector)

    print("Streaming ecg data. Press Ctrl+C to stop.")
    while True:
        await asyncio.sleep(1)

if __name__ == '__main__':
    
    app = QApplication(sys.argv)
    window = AccelerometerVisualizer()

    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    window.setWindowTitle("BLEHRM")
    window.resize(800, 400)
    window.show()

    try:
        loop.run_until_complete(main(window))
    except KeyboardInterrupt:
        print("\nStream stopped by user.")

    sys.exit(app.exec())