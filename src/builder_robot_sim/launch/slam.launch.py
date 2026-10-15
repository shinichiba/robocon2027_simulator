from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.substitutions import PathJoinSubstitution
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    slam_launch = PathJoinSubstitution([
        FindPackageShare("slam_toolbox"),
        "launch",
        "online_sync_launch.py"
    ])

    params = PathJoinSubstitution([
        FindPackageShare("builder_robot_sim"),
        "config",
        "slam.yaml"
    ])

    return LaunchDescription([
        IncludeLaunchDescription(
            slam_launch,
            launch_arguments={
                "slam_params_file": params,
                "use_sim_time": "true"
            }.items()
        )
    ])
