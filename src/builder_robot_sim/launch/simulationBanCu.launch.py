import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node
import xacro

def generate_launch_description():
    pkg_share = get_package_share_directory('builder_robot_simulation')
    
    # Xử lý URDF
    xacro_file = os.path.join(pkg_share, 'urdf', 'builder_robot.urdf.xacro')
    robot_description_raw = xacro.process_file(xacro_file).toxml()

    # Robot State Publisher
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[{'robot_description': robot_description_raw, 'use_sim_time': True}]
    )

    # Gazebo Sim (New Ignition/Modern Gazebo) Launch
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([
            os.path.join(get_package_share_directory('ros_gz_sim'), 'launch', 'gz_sim.launch.py')
        ]),
        launch_arguments={
            # '-r' flags Gazebo to auto-run on start instead of starting paused
            'gz_args': ['-r ', os.path.join(pkg_share, 'worlds', 'arena.world')]
        }.items()
    )

    # Spawn Robot using ros_gz_sim 'create' executable
    spawn_entity = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=[
            '-topic', 'robot_description', 
            '-name', 'builder_robot', # Replaced '-entity' with '-name'
            '-x', '0.0', 
            '-y', '0.0', 
            '-z', '0.2'
        ],
        output='screen'
    )

    return LaunchDescription([
        gazebo,
        robot_state_publisher,
        spawn_entity
    ])
    
import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    RegisterEventHandler,
)
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():

    package_name = 'builder_robot_sim'

    pkg_share = get_package_share_directory(package_name)

    world_file = os.path.join(
        pkg_share,
        'worlds',
        'builder_arena.sdf'
    )

    robot_description_file = os.path.join(
        pkg_share,
        'urdf',
        'builder_robot.urdf.xacro'
    )

    mecanum_controller_file = os.path.join(
        pkg_share,
        'config',
        'mecanum_controller.yaml'
    )

    # ---------------------------------------------------------
    # Simulation time
    # ---------------------------------------------------------

    use_sim_time = LaunchConfiguration('use_sim_time')

    declare_use_sim_time = DeclareLaunchArgument(
        'use_sim_time',
        default_value='true',
        description='Use Gazebo simulation time'
    )

    # ---------------------------------------------------------
    # Robot description
    # ---------------------------------------------------------

    robot_description = {
        'robot_description': Command([
            'xacro ',
            robot_description_file
        ])
    }

    # ---------------------------------------------------------
    # Gazebo Jetty
    # ---------------------------------------------------------

    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(
                get_package_share_directory('ros_gz_sim'),
                'launch',
                'gz_sim.launch.py'
            )
        ),
        launch_arguments={
            'gz_args': f'-r -v 4 {world_file}'
        }.items()
    )

    # ---------------------------------------------------------
    # Robot State Publisher
    # ---------------------------------------------------------

    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        name='robot_state_publisher',
        output='screen',
        parameters=[
            robot_description,
            {
                'use_sim_time': use_sim_time
            }
        ]
    )

    # ---------------------------------------------------------
    # Spawn robot into Gazebo
    # ---------------------------------------------------------

    spawn_robot = Node(
        package='ros_gz_sim',
        executable='create',
        name='spawn_builder_robot',
        arguments=[
            '-topic',
            'robot_description',
            '-name',
            'builder_robot',
            '-x',
            '0.0',
            '-y',
            '0.0',
            '-z',
            '0.15',
        ],
        output='screen'
    )

    # ---------------------------------------------------------
    # Joint State Broadcaster
    #
    # controller_manager comes from gz_ros2_control.
    # ---------------------------------------------------------

    spawn_joint_state_broadcaster = Node(
        package='controller_manager',
        executable='spawner',
        name='spawner_joint_state_broadcaster',
        arguments=[
            'joint_state_broadcaster',
            '--controller-manager',
            '/controller_manager',
            '--controller-manager-timeout',
            '60',
        ],
        output='screen'
    )

    # ---------------------------------------------------------
    # Mecanum Controller
    #
    # IMPORTANT:
    # Pass mecanum_controller.yaml directly to the spawner.
    # ---------------------------------------------------------

    spawn_mecanum_controller = Node(
        package='controller_manager',
        executable='spawner',
        name='spawner_mecanum_controller',
        arguments=[
            'mecanum_controller',
            '--controller-manager',
            '/controller_manager',
            '--param-file',
            mecanum_controller_file,
            '--controller-manager-timeout',
            '60',
        ],
        output='screen'
    )

    # ---------------------------------------------------------
    # Launch sequence
    # ---------------------------------------------------------

    return LaunchDescription([

        declare_use_sim_time,

        # 1. Start Gazebo
        gazebo,

        # 2. Start robot_state_publisher
        robot_state_publisher,

        # 3. Spawn robot
        spawn_robot,

        # 4. After robot is spawned:
        #    load joint_state_broadcaster
        RegisterEventHandler(
            OnProcessExit(
                target_action=spawn_robot,
                on_exit=[
                    spawn_joint_state_broadcaster
                ]
            )
        ),

        # 5. After joint_state_broadcaster:
        #    load mecanum_controller
        RegisterEventHandler(
            OnProcessExit(
                target_action=spawn_joint_state_broadcaster,
                on_exit=[
                    spawn_mecanum_controller
                ]
            )
        ),
    ])
