from setuptools import setup
from glob import glob
import os

package_name = 'navi_core'

setup(
    name=package_name,
    version='0.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob(os.path.join('launch', '*.launch.py'))),
        (os.path.join('share', package_name, 'description'), glob('description/*.xacro')),
        (os.path.join('share', package_name, 'description/meshes'), glob('description/meshes/*')),
        (os.path.join('share', package_name, 'web'), glob('web/*')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='ubuntu',
    maintainer_email='leon.stjepan@gmail.com',
    description='Core tools for an autonomous mobile robot Navi',
    license='TODO: License declaration',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'odometry_publisher = navi_core.odometry_publisher:main',
            'control_center = navi_core.control_center:main',
            'system_monitor = navi_core.system_monitor:main',
        ],
    },
)
