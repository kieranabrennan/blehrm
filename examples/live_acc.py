from blehrm import blehrm
from bleak import BleakScanner, BLEDevice
import asyncio
import sys
import numpy as np
from PySide6.QtWidgets import QApplication, QMainWindow
import pyqtgraph.opengl as gl
from qasync import QEventLoop
from scipy.spatial.transform import Rotation
import argparse

ADDRESS = "5BE8C8E0-8FA7-CEE7-4662-D49695040AF7" # Polar H10

class DiceGroup(gl.GLGraphicsItem.GLGraphicsItem):
    def __init__(self):
        gl.GLGraphicsItem.GLGraphicsItem.__init__(self)
        self.items = []

    def addItem(self, item):
        self.items.append(item)
        item.setParentItem(self)

class DiceVisualizer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("3D Dice Visualization")
        self.resize(800, 600)

        self.plot_widget = gl.GLViewWidget()
        self.setCentralWidget(self.plot_widget)

        # Create a dice
        self.dice_group = DiceGroup()
        self.create_dice()
        self.plot_widget.addItem(self.dice_group)

        # Set up the camera
        self.plot_widget.setCameraPosition(distance=7, elevation=20, azimuth=45)

        # Initialize the previous acceleration vector
        self.prev_acc = np.array([0, 0, 1])

    def create_dice(self):
        # Create individual faces for the cube
        face_color = (0.9, 0.9, 0.9, 1.0)
        edge_color = (0, 0, 0, 1)
        
        # Define vertices for a 2x2x2 cube centered at the origin
        verts = [
            [1, 1, 1], [-1, 1, 1], [-1, -1, 1], [1, -1, 1],
            [1, 1, -1], [-1, 1, -1], [-1, -1, -1], [1, -1, -1]
        ]

        # Define faces using vertex indices
        faces = [
            [0, 1, 2, 3],  # Front
            [4, 5, 6, 7],  # Back
            [0, 4, 7, 3],  # Right
            [1, 5, 6, 2],  # Left
            [0, 1, 5, 4],  # Top
            [3, 2, 6, 7]   # Bottom
        ]

        for face in faces:
            face_verts = [verts[i] for i in face]
            face_mesh = gl.GLMeshItem(
                vertexes=np.array(face_verts),
                faces=np.array([[0, 1, 2], [0, 2, 3]]),
                smooth=False,
                drawEdges=True,
                edgeColor=edge_color,
                color=face_color
            )
            self.dice_group.addItem(face_mesh)

        # Add pips (dots) to the faces
        self.create_pips()

    def create_pips(self):
        pip_radius = 0.08
        pip_color = (0, 0, 0, 1)  # Black color

        # Define pip positions for each face
        pip_positions = {
            1: [(0, 0, 1.01)],  # Front face (1)
            2: [(-0.5, 0.5, -1.01), (0.5, -0.5, -1.01)],  # Back face (2)
            3: [(1.01, -0.5, 0.5), (1.01, 0, 0), (1.01, 0.5, -0.5)],  # Right face (3)
            4: [(-1.01, -0.5, -0.5), (-1.01, -0.5, 0.5), (-1.01, 0.5, -0.5), (-1.01, 0.5, 0.5)],  # Left face (4)
            5: [(-0.5, 1.01, -0.5), (-0.5, 1.01, 0.5), (0, 1.01, 0), (0.5, 1.01, -0.5), (0.5, 1.01, 0.5)],  # Top face (5)
            6: [(-0.5, -1.01, -0.5), (-0.5, -1.01, 0), (-0.5, -1.01, 0.5),
                (0.5, -1.01, -0.5), (0.5, -1.01, 0), (0.5, -1.01, 0.5)]  # Bottom face (6)
        }

        for positions in pip_positions.values():
            for pos in positions:
                pip = gl.GLMeshItem(
                    meshdata=gl.MeshData.sphere(rows=20, cols=20, radius=pip_radius),
                    smooth=True,
                    color=pip_color,
                    glOptions='opaque'
                )
                pip.translate(pos[0], pos[1], pos[2])
                self.dice_group.addItem(pip)

    def update_dice_orientation(self, data):
        _, x, y, z = data
        # Normalize the acceleration vector
        acc_vector = np.array([x, y, z])
        acc_vector = acc_vector / np.linalg.norm(acc_vector)

        # Calculate rotation from previous acceleration to current acceleration
        rotation = Rotation.align_vectors([acc_vector], [self.prev_acc])[0]
        
        # Convert rotation to Euler angles
        angles = rotation.as_euler('xyz', degrees=True)

        # Apply rotation to the dice group
        self.dice_group.rotate(angles[0], 1, 0, 0)
        self.dice_group.rotate(angles[1], 0, 1, 0)
        self.dice_group.rotate(angles[2], 0, 0, 1)

        # Update previous acceleration
        self.prev_acc = acc_vector

async def main(view, use_mock = False):
    if use_mock:
        ble_device = BLEDevice(address="Mock", name="Mock", details=None, rssi=0)    
    else:
        ble_device = await BleakScanner.find_device_by_address(ADDRESS, timeout=20.0)
        if ble_device is None:
            print(f"Device with address {ADDRESS} not found")
            return

    blehrm_client = blehrm.create_client(ble_device)    
    print(blehrm_client)
    await blehrm_client.connect()
    await blehrm_client.start_acc_stream(view.update_dice_orientation)

    print("Streaming acc data. Press Ctrl+C to stop.")
    while True:
        await asyncio.sleep(0.1)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Print heart rate data")
    parser.add_argument("--use-mock", action="store_true", help="Use mock hr data")
    args = parser.parse_args()

    app = QApplication(sys.argv)
    window = DiceVisualizer()

    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    window.setWindowTitle("3D Dice Visualization")
    window.resize(800, 600)
    window.show()

    try:
        loop.run_until_complete(main(window, use_mock=args.use_mock))
    except KeyboardInterrupt:
        print("\nStream stopped by user.")
    finally:
        loop.close()

    sys.exit(app.exec())