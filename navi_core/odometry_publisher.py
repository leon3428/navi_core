import rclpy
from rclpy.node import Node

from sensor_msgs.msg import JointState
import numpy as np
from math import sin, cos

from geometry_msgs.msg import TransformStamped, Quaternion
from nav_msgs.msg import Odometry
from tf2_ros import TransformBroadcaster

import tf_transformations

import ctypes

L = 0.215

class OdometryPublisher(Node):

    def __init__(self):
        super().__init__('odometry_publisher')
        self.subscription = self.create_subscription(
            JointState,
            'joint_states',
            self.joint_state_callback,
            10)
        self.subscription  # prevent unused variable warning
        self.publisher = self.create_publisher(Odometry, 'odom', 10)
        self.last_time = 0
        self.pos = np.zeros((2,1))
        self.theta = 0
        self.broadcaster = TransformBroadcaster(self)


    def joint_state_callback(self, msg):
        right_vel = 0
        left_vel = 0

        for i in range(len(msg.name)):
            if(msg.name[i] == 'left_wheel_joint'):
                left_vel = msg.velocity[i]
            if(msg.name[i] == 'right_wheel_joint'):
                right_vel = msg.velocity[i]

        delta_t = (msg.header.stamp.nanosec - self.last_time)
        if delta_t < 0:
            delta_t += 1e9
        delta_t /= 1e9
        self.last_time = msg.header.stamp.nanosec

        omega = (right_vel - left_vel) / L
        v = 0.5 * (right_vel + left_vel)

        if(right_vel - left_vel == 0):
            self.pos += np.array([[v * delta_t * cos(self.theta)], [-v * delta_t * sin(self.theta)]])
        else:
            r = 0.5 * L * (left_vel + right_vel) / (right_vel - left_vel)
            icc = self.pos + np.array([[-r * sin(self.theta)], [r * cos(self.theta)]])
            delta_theta = omega * delta_t
            rot = np.array([[cos(delta_theta), -sin(delta_theta)], [sin(delta_theta), cos(delta_theta)]])

            self.pos = rot @ (self.pos - icc) + icc
            self.theta += delta_theta


        current_time = self.get_clock().now().to_msg()
        t = TransformStamped()

        t.header.stamp = current_time
        t.header.frame_id = 'odom'
        t.child_frame_id = 'base_link'

        t.transform.translation.x = self.pos[0][0]
        t.transform.translation.y = self.pos[1][0]
        t.transform.translation.z = 0.0

        q = tf_transformations.quaternion_from_euler(0, 0, self.theta)
        t.transform.rotation.x = q[0]
        t.transform.rotation.y = q[1]
        t.transform.rotation.z = q[2]
        t.transform.rotation.w = q[3]

        # Send the transformation
        self.broadcaster.sendTransform(t)

        msg = Odometry()
        msg.header.stamp = current_time
        msg.header.frame_id = 'odom'
        msg.child_frame_id = 'base_link'

        msg.pose.pose.position.x = self.pos[0][0]
        msg.pose.pose.position.y = self.pos[1][0]
        msg.pose.pose.position.z = 0.0
        msg.pose.pose.orientation.x = q[0]
        msg.pose.pose.orientation.y = q[1]
        msg.pose.pose.orientation.z = q[2]
        msg.pose.pose.orientation.w = q[3]
        #set the velocity
        msg.twist.twist.linear.x = v
        msg.twist.twist.linear.y = 0.0
        msg.twist.twist.angular.z = omega

        self.publisher.publish(msg)



def main(args=None):
    rclpy.init(args=args)

    odometry_publisher = OdometryPublisher()

    rclpy.spin(odometry_publisher)

    rclpy.shutdown()


if __name__ == '__main__':
    main()