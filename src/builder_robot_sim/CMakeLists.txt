cmake_minimum_required(VERSION 3.16)
project(builder_robot_sim)

find_package(ament_cmake REQUIRED)

install(
  DIRECTORY urdf models worlds config launch rviz maps
  DESTINATION share/${PROJECT_NAME}
)

ament_package()
