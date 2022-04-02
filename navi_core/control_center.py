import rclpy
from rclpy.node import Node
from ament_index_python.packages import get_package_share_directory
from geometry_msgs.msg import Twist
from sensor_msgs.msg import BatteryState
from navi_interfaces.msg import SystemState, ColorRGB

import threading

from flask import Flask, render_template, request, jsonify
import json

class ControlCenter(Node):
    def __init__(self):
        super().__init__('control_center')
        self.publisher = self.create_publisher(Twist, 'cmd_vel', 10)
        self.battery_subscription = self.create_subscription(BatteryState, 'battery_state', self.battery_callback, 1)
        self.battery_percentage = 1

        self.system_state_subscription = self.create_subscription(SystemState, 'system_state', self.system_state_callback, 1)
        self.system_state = SystemState()

    def battery_callback(self, msg):
        self.battery_percentage = msg.percentage

    def system_state_callback(self, msg):
        self.system_state = msg

control_center = None

package_share_directory = get_package_share_directory('navi_core')
app = Flask(__name__, template_folder = package_share_directory + '/web', static_folder=package_share_directory + '/web')

@app.route("/")
def index():
    return render_template('index.html')

@app.route("/cmd_vel", methods = ['POST'])
def publish_cmd_vel():
    v = request.form.get("v")
    omega = request.form.get("omega")

    msg = Twist()
    msg.linear.x = float(v)
    msg.angular.z = float(omega)
    
    control_center.publisher.publish(msg)
    
    return jsonify(status="success")

@app.route('/battery_percentage', methods=['GET'])
def bat_callback():
    return str(control_center.battery_percentage)

@app.route('/state', methods=['GET'])
def state_callback():
    r = control_center.system_state.color.r
    g = control_center.system_state.color.g
    b = control_center.system_state.color.b
    msg = {
        "code": control_center.system_state.code,
        "color": {"r" : r, "g" : g,"b" : b},
        "msg": control_center.system_state.msg
    }
    return json.dumps(msg)

def main(args=None):
    global control_center

    rclpy.init(args=args)

    control_center = ControlCenter()

    threading.Thread(target=lambda: rclpy.spin(control_center)).start()

    app.run(host="0.0.0.0", port=3000)

if __name__ == '__main__':
    main()