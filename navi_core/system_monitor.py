import rclpy
from rclpy.node import Node

from navi_interfaces.msg import SystemState, ColorRGB
from sensor_msgs.msg import BatteryState
from geometry_msgs.msg import Twist
from rcl_interfaces.msg import ParameterDescriptor

import os
import time
import dbus
import psutil

class SystemMonitor(Node):

    def __init__(self):
        super().__init__('system_monitor')
        self.__publisher = self.create_publisher(SystemState, 'system_state', 10)
        timer_period = 5  # seconds
        self.__timer = self.create_timer(timer_period, self.__timer_callback)

        self.__battery_state_subscription = self.create_subscription(BatteryState, 'battery_state', self.__battery_state_callback, 10)
        self.__battery_percentage = 1

        self.__cmd_vel_publisher = self.create_publisher(Twist, 'cmd_vel', 10)

        self.declare_parameter('critical_nodes', ['system_monitor'])
        self.declare_parameter('application_nodes', ['system_monitor'])

    def __stop_motors(self):
        msg = Twist()
        msg.linear.x = 0.0
        msg.angular.z = 0.0

        for i in range(5):
            self.__cmd_vel_publisher.publish(msg)
            time.sleep(0.5)


    def __shutdown(self):
        self.get_logger().info('The system is shutting down!')
        self.__stop_motors()
        
        time.sleep(5)

        sys_bus = dbus.SystemBus()
        ck_srv = sys_bus.get_object('org.freedesktop.login1',
                                    '/org/freedesktop/login1')
        ck_iface = dbus.Interface(ck_srv, 'org.freedesktop.login1.Manager')
        ck_iface.get_dbus_method("PowerOff")(False)

        time.sleep(100)

    def __battery_state_callback(self, msg):
        self.__battery_percentage = msg.percentage
        if(self.__battery_percentage <= 0):
            self.__shutdown()
            

    def __timer_callback(self):
        msg = SystemState()
        msg.color = ColorRGB()

        # Find out if a critical node has failed
        node_list = self.get_node_names()
        critical_nodes = self.get_parameter('critical_nodes')
        missing_critical_node_name = ""

        critical_node_flag = False
        for node_name in critical_nodes.value:
            if not (node_name in node_list):
                critical_node_flag = True
                missing_critical_node_name = node_name

        # Find out if an application node has failed
        application_nodes = self.get_parameter('application_nodes')

        application_node_flag = False
        missing_application_node_name = ""
        for node_name in application_nodes.value:
            if not (node_name in node_list):
                application_node_flag = True
                missing_application_node_name = node_name

        # CPU temperature
        temp = psutil.sensors_temperatures()['cpu_thermal'][0].current

        if(self.__battery_percentage < 0.05):
            msg.code = msg.STATE_LOW_BATTERY
            msg.color.r = 255
            msg.color.g = 0
            msg.color.b = 0
            msg.msg = "The battery is below 5%. System will shutdown soon."

        elif temp > 90:
            msg.code = msg.STATE_OVERHEAT
            msg.color.r = 255
            msg.color.g = 0
            msg.color.b = 255
            msg.msg = "CPU temperature is higher than 90°C"

        elif critical_node_flag:
            msg.code = msg.STATE_CRITICAL_NODE_FAILURE
            msg.color.r = 255
            msg.color.g = 125
            msg.color.b = 0
            msg.msg = 'Critical node ' + missing_critical_node_name + ' is not active'
        elif application_node_flag:
            msg.code = msg.STATE_NODE_FAILURE
            msg.color.r = 255
            msg.color.g = 255
            msg.color.b = 0
            msg.msg = 'Node ' + missing_application_node_name + ' is not active'
        else:
            msg.code = msg.STATE_OK
            msg.color.r = 0
            msg.color.g = 255
            msg.color.b = 0
            msg.msg = "The system is up and running"

        self.__publisher.publish(msg)


def main(args=None):
    rclpy.init(args=args)

    system_monitor = SystemMonitor()

    rclpy.spin(system_monitor)

    system_monitor.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()