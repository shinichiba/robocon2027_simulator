import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    ExecuteProcess,
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
        'robocon2027_arena.sdf '#robocon2027_arena.sdf builder_arena.sdf
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
    bridge_config_file = os.path.join(
        pkg_share,
        'config',
        'bridge.yaml'
    )

    # =========================================================
    # Arguments
    # =========================================================

    use_sim_time = LaunchConfiguration('use_sim_time')

    declare_use_sim_time = DeclareLaunchArgument(
        'use_sim_time',
        default_value='true'
    )

    # =========================================================
    # Robot description
    # =========================================================

    robot_description = {
        'robot_description': Command([
            'xacro ',
            robot_description_file
        ])
    }

    # =========================================================
    # Gazebo
    # =========================================================

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

    # =========================================================
    # Robot State Publisher
    # =========================================================

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
    # =========================================================
    # Gazebo <-> ROS 2 Bridge
    # =========================================================

    ros_gz_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        name='ros_gz_bridge',
        output='screen',
        parameters=[
            {
                'config_file': bridge_config_file
            }
        ]
    )
    # =========================================================
    # Spawn robot
    # =========================================================

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
            '4.0',
            '-y',
            '4.0',
            '-z',
            '0.15',
        ],
        output='screen'
    )

    # =========================================================
    # Wait for controller_manager
    # =========================================================

    wait_controller_manager = ExecuteProcess(
        cmd=[
            'bash',
            '-c',
            '''
            echo "[builder_robot] Waiting for /controller_manager..."

            until ros2 service type \
                /controller_manager/list_controllers \
                >/dev/null 2>&1
            do
                sleep 1
            done

            echo "[builder_robot] /controller_manager is READY."
            '''
        ],
        output='screen'
    )

    # =========================================================
    # Spawn Joint State Broadcaster
    # =========================================================

    spawn_joint_state_broadcaster = ExecuteProcess(
        cmd=[
            'ros2',
            'run',
            'controller_manager',
            'spawner',
            'joint_state_broadcaster',
            '--controller-manager',
            '/controller_manager',
            '--controller-manager-timeout',
            '60'
        ],
        output='screen'
    )

    # =========================================================
    # Wait for Joint State Broadcaster ACTIVE
    # =========================================================

    wait_joint_state_broadcaster = ExecuteProcess(
        cmd=[
            'bash',
            '-c',
            '''
            echo "[builder_robot] Waiting for joint_state_broadcaster..."

            until ros2 control list_controllers 2>/dev/null |
                grep -qE \
                '^joint_state_broadcaster[[:space:]].*[[:space:]]active'
            do
                sleep 1
            done

            echo "[builder_robot] joint_state_broadcaster is ACTIVE."
            '''
        ],
        output='screen'
    )

    # =========================================================
    # Spawn Mecanum Controller
    # =========================================================

    spawn_mecanum_controller = ExecuteProcess(
        cmd=[
            'ros2', 'run', 'controller_manager', 'spawner',
            'mecanum_controller',
            '--controller-manager', '/controller_manager',
            '--param-file', mecanum_controller_file,
            '--controller-ros-args',
            '--ros-args --remap /mecanum_controller/tf_odometry:=/tf',
            '--controller-manager-timeout', '60'
        ],
        output='screen'
    )

    # =========================================================
    # Wait for Mecanum Controller ACTIVE
    # =========================================================

    wait_mecanum_controller = ExecuteProcess(
        cmd=[
            'bash',
            '-c',
            '''
            echo "[builder_robot] Waiting for mecanum_controller..."

            until ros2 control list_controllers 2>/dev/null |
                grep -qE \
                '^mecanum_controller[[:space:]].*[[:space:]]active'
            do
                sleep 1
            done

            echo ""
            echo "=============================================="
            echo " builder_robot controllers are READY"
            echo "=============================================="
            echo " joint_state_broadcaster : ACTIVE"
            echo " mecanum_controller      : ACTIVE"
            echo "=============================================="
            '''
        ],
        output='screen'
    )

    # =========================================================
    # EVENT CHAIN
    # =========================================================

    # Robot spawned
    #
    #       ↓
    #
    # Wait for controller_manager
    robot_spawned_event = RegisterEventHandler(
        OnProcessExit(
            target_action=spawn_robot,
            on_exit=[
                wait_controller_manager
            ]
        )
    )

    # controller_manager ready
    #
    #       ↓
    #
    # Spawn joint_state_broadcaster
    controller_manager_ready_event = RegisterEventHandler(
        OnProcessExit(
            target_action=wait_controller_manager,
            on_exit=[
                spawn_joint_state_broadcaster
            ]
        )
    )

    # joint_state_broadcaster spawned
    #
    #       ↓
    #
    # Wait until it is ACTIVE
    joint_state_spawned_event = RegisterEventHandler(
        OnProcessExit(
            target_action=spawn_joint_state_broadcaster,
            on_exit=[
                wait_joint_state_broadcaster
            ]
        )
    )

    # joint_state_broadcaster ACTIVE
    #
    #       ↓
    #
    # Spawn mecanum_controller
    joint_state_ready_event = RegisterEventHandler(
        OnProcessExit(
            target_action=wait_joint_state_broadcaster,
            on_exit=[
                spawn_mecanum_controller
            ]
        )
    )

    # mecanum_controller spawned
    #
    #       ↓
    #
    # Wait until ACTIVE
    mecanum_spawned_event = RegisterEventHandler(
        OnProcessExit(
            target_action=spawn_mecanum_controller,
            on_exit=[
                wait_mecanum_controller
            ]
        )
    )
    # =========================================================
    # Launch description
    # =========================================================

    return LaunchDescription([

        declare_use_sim_time,

        gazebo,

        robot_state_publisher,
        # Gazebo <-> ROS 2 bridge
        ros_gz_bridge,

        spawn_robot,

        robot_spawned_event,

        controller_manager_ready_event,

        joint_state_spawned_event,

        joint_state_ready_event,

        mecanum_spawned_event,
    ])
