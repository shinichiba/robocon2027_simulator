# builder_robot_sim

ROS 2 Lyrical + Gazebo Jetty simulation of a 600x600 mm mecanum mobile robot.

## Build Them tu dong bien moi truong
```bash
cd ~/builder_ws
rosdep install --from-paths src --ignore-src -r -y
colcon build --symlink-install
source install/setup.bash
```

## Run simulation
```bash
ros2 launch builder_robot_sim simulation.launch.py
```

## Run SLAM
In another terminal:
```bash
source ~/builder_ws/install/setup.bash
ros2 launch builder_robot_sim slam.launch.py
```

## Command robot
The mecanum controller subscribes to:
`/mecanum_controller/reference` as `geometry_msgs/msg/TwistStamped`.

Use:
```bash
ros2 topic pub --rate 10 /mecanum_controller/reference geometry_msgs/msg/TwistStamped "{twist: {linear: {x: 0.4, y: 0.0}, angular: {z: 0.0}}}"
```

For lateral:
```bash
ros2 topic pub --rate 10 /mecanum_controller/reference geometry_msgs/msg/TwistStamped "{twist: {linear: {x: 0.0, y: 0.4}, angular: {z: 0.0}}}"
```

Save map:
```bash
ros2 run nav2_map_server map_saver_cli -f ~/builder_ws/src/builder_robot_sim/maps/builder_map
```

Record data:
```bash
ros2 bag record /scan /imu /mecanum_controller/odometry /tf /tf_static /mecanum_controller/reference
```


## First checks

After launching, check:

```bash
ros2 control list_controllers
ros2 topic list | grep -E 'scan|imu|odom|joint|mecanum'
ros2 topic hz /scan
ros2 topic hz /imu
```

Expected controllers:
- `joint_state_broadcaster` — active
- `mecanum_controller` — active

Expected key topics:
- `/scan`
- `/imu`
- `/joint_states`
- `/mecanum_controller/odometry`
- `/tf`
- `/tf_static`
- `/clock`

### Forward command

```bash
ros2 topic pub --rate 10 /mecanum_controller/reference \
geometry_msgs/msg/TwistStamped \
"{twist: {linear: {x: 0.4, y: 0.0}, angular: {z: 0.0}}}"
```

### Lateral command

```bash
ros2 topic pub --rate 10 /mecanum_controller/reference \
geometry_msgs/msg/TwistStamped \
"{twist: {linear: {x: 0.0, y: 0.4}, angular: {z: 0.0}}}"
```

### Rotate

```bash
ros2 topic pub --rate 10 /mecanum_controller/reference \
geometry_msgs/msg/TwistStamped \
"{twist: {linear: {x: 0.0, y: 0.0}, angular: {z: 0.5}}}"
```

Stop by publishing zero:

```bash
ros2 topic pub --once /mecanum_controller/reference \
geometry_msgs/msg/TwistStamped \
"{twist: {linear: {x: 0.0, y: 0.0}, angular: {z: 0.0}}}"
```

## Important note about the Mecanum wheel model

The wheel collision uses anisotropic friction to approximate the diagonal roller effect. It is intentionally a lightweight research simulation, not a CAD-level roller model. For quantitative benchmarking against a physical robot, replace this wheel contact model with an explicit roller-wheel model or a validated custom Gazebo system.

## Ground truth

For SLAM evaluation, Gazebo's model pose can be queried from Gazebo transport / simulation interfaces. Keep the ground-truth trajectory separate from the SLAM topics so it is never fed into the estimator.

## Troubleshooting

If `gz_ros2_control` is not found:

```bash
sudo apt update
sudo apt install ros-lyrical-gz-ros2-control
```

If the mecanum controller plugin is not found:

```bash
sudo apt update
sudo apt install ros-lyrical-ros2-controllers
```

If SLAM Toolbox is not found:

```bash
sudo apt update
sudo apt install ros-lyrical-slam-toolbox
```

If Gazebo cannot load the robot from `/robot_description`, test:

```bash
ros2 topic echo /robot_description --once
```

and separately:

```bash
ros2 run xacro xacro \
  ~/builder_ws/src/builder_robot_sim/urdf/builder_robot.urdf.xacro > /tmp/builder_robot.urdf
```
