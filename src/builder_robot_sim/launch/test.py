import os

from ament_index_python.packages import get_package_share_directory

from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    IncludeLaunchDescription,
    ExecuteProcess,
    RegisterEventHandler,
    SetEnvironmentVariable,
)
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():

    package_name = 'builder_robot_sim'

    pkg_share = get_package_share_directory(package_name)

    # ĐÃ SỬA: Xóa khoảng trắng thừa ở cuối chuỗi 'robocon2027_arena.sdf'
    world_file = os.path.join(
        pkg_share,
        'worlds',
        'robocon2027_arena.sdf' # Xóa dấu cách thừa ở đây
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
    # set_env_action
    # =========================================================
    # Tối ưu: Thêm cả pkg_share và pkg_share/models để Gazebo quét tìm mô hình chuẩn nhất
    models_path = os.path.join(pkg_share, 'models')
    
    current_gz_path = os.environ.get('GZ_SIM_RESOURCE_PATH', '')
    
    # Gộp các đường dẫn lại với nhau ngăn cách bởi dấu :
    gz_paths = [models_path, pkg_share]
    if current_gz_path:
        gz_paths.append(current_gz_path)
        
    full_gz_path = ":".join(gz_paths)

    # Tạo hành động cấu hình biến môi trường cho Gazebo
    set_env_action = SetEnvironmentVariable(
        name='GZ_SIM_RESOURCE_PATH', 
        value=full_gz_path
    )
    # =========================================================
    # Arguments
    # =========================================================
    check_env_node = ExecuteProcess(
        cmd=['echo "==> GZ_SIM_RESOURCE_PATH THỰC TẾ TRONG LAUNCH: $GZ_SIM_RESOURCE_PATH"'],
        output='screen',
        shell=True # Bắt buộc phải có shell=True để nhận diện ký tự $
    )
    # =========================================================
    # Launch description
    # =========================================================

    return LaunchDescription([
        set_env_action,
        check_env_node,
    ])