from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import (ExecuteProcess, RegisterEventHandler)
from launch.substitutions import FindExecutable
from launch.event_handlers import OnProcessStart
from launch.substitutions import LaunchConfiguration
from launch.actions import DeclareLaunchArgument

import os
from ament_index_python.packages import get_package_share_directory

import xacro

def generate_launch_description():
    use_sim_time = LaunchConfiguration('use_sim_time')

    # Process the URDF file
    pkg_path = os.path.join(get_package_share_directory('navi_core'))
    xacro_file = os.path.join(pkg_path,'description','robot.urdf.xacro')
    robot_description_config = xacro.process_file(xacro_file)

    node_robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[{'robot_description': robot_description_config.toxml(), 'use_sim_time': use_sim_time}]
    )

    micro_ros_agent = Node(
        package='micro_ros_agent',
        executable='micro_ros_agent',
        name='micro_ros_agent',
        arguments=["serial", "--dev", "/dev/ttyS0", "-b", "500000"]
    )

    start_firmware = ExecuteProcess(
        cmd=[[
            FindExecutable(name='openocd'),
            ' -f',
            ' interface/raspberrypi-swd.cfg',
            ' -f',
            ' target/rp2040.cfg',
            ' -c',
            ' "init; reset; exit"'
        ]],
        shell=True
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='false',
            description='Use sim time if true'),

        node_robot_state_publisher,
        micro_ros_agent,
        
        RegisterEventHandler(
            OnProcessStart(
                target_action=micro_ros_agent,
                on_start=[
                    start_firmware
                ]
            )
        )
    ])