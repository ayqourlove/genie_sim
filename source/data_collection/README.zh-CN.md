# 数据采集

这是一个面向机器人仿真任务的数据采集系统，基于 Isaac Sim 和 cuRobo 构建。

## 目录

- [前置条件](#前置条件)
- [快速开始](#快速开始)
  - [方案 1：Docker 容器（推荐）](#方案-1docker-容器推荐)
    - [构建 Docker 镜像](#构建-docker-镜像)
    - [一键数据采集（推荐）](#一键数据采集推荐)
    - [交互模式](#交互模式)
  - [方案 2：本地部署](#方案-2本地部署)
- [使用示例](#使用示例)
  - [Docker - 自动化数据采集](#docker---自动化数据采集)
  - [Docker - 交互式开发](#docker---交互式开发)
  - [本地 - 完全控制](#本地---完全控制)
- [任务配置指南](#任务配置指南)

## 前置条件

- Docker（用于容器化部署）
- 支持 CUDA 的 NVIDIA GPU（推荐 40 系列 GPU；50 系列 GPU（SM_120）可能无法安装 cuRobo，需要等待 cuRobo 团队进行兼容性更新）
- Python 3.11
- Conda（用于本地部署）

## 快速开始

**注意：** 运行前请确保已设置 `SIM_ASSETS` 环境变量：

```bash
export SIM_ASSETS={YOUR_ASSETS_PATH}
```

### 方案 1：Docker 容器（推荐）

#### 构建 Docker 镜像

首先构建 Docker 镜像。

假设 benchmark 镜像 `registry.agibot.com/genie-sim/open_source:latest` 已经构建完成，运行：

```bash
docker build -f ./dockerfile -t registry.agibot.com/genie-sim/open_source-data-collection:latest .
```

**注意：** 对于 cuRobo 安装，Dockerfile 默认按照 RTX 4090D 配置。如果你使用的是其他 GPU 型号，需要修改 Dockerfile 中的 `TORCH_CUDA_ARCH_LIST` 环境变量。50 系列 GPU（SM_120）可能无法安装 cuRobo，需要 cuRobo 团队进行兼容性更新。

#### 一键数据采集（推荐）

使用 `scripts/run_data_collection.sh` 可以通过一条命令启动数据采集。

**用法：**

```bash
./scripts/run_data_collection.sh [OPTIONS]
```

**选项：**

- `--headless`：以 headless 模式运行，默认值为 `false`。
- `--no-record`：禁用录制，默认启用录制。
- `--task TASK_PATH`：任务模板路径，例如 `tasks/geniesim_2025/sort_fruit/g2/sort_the_fruit_into_the_box_apple_g2.json`。
- `--standalone`：以 standalone 模式运行，只保存日志，不在终端输出，默认值为 `false`。
- `--container-name NAME`：容器名称，默认值为 `data_collection_open_source`。
- `--help, -h`：显示帮助信息。

**环境变量：**

- `SIM_ASSETS`：Isaac Sim 资产路径，必需。

**示例：**

```bash
# 使用默认任务，以 GUI 模式运行
./scripts/run_data_collection.sh

# 使用自定义任务，以 headless 模式运行
./scripts/run_data_collection.sh --headless --task tasks/geniesim_2025/sort_fruit/g2/sort_the_fruit_into_the_box_apple_g2.json

# 以 standalone + headless 模式运行（只保存日志，不输出到终端）
./scripts/run_data_collection.sh --standalone --headless

# 不录制数据
./scripts/run_data_collection.sh --no-record
```

**日志：**

日志会保存到 `logs/{TASK_NAME}/` 目录：

- `run_data_collection_sh.log`：脚本输出。
- `container.log`：容器日志。
- `data_collector_server.log`：数据采集服务器日志（如果可用）。
- `run_data_collection.log`：数据采集应用日志（如果可用）。

**输出：**

输出会保存到 `recording_data/[{TASK_NAME}_{INDEX}]/` 目录。

#### 交互模式

使用 `scripts/start_gui.sh` 可以启动交互式容器，用于调试或开发。

**用法：**

```bash
./scripts/start_gui.sh [ACTION] [CONTAINER_NAME]
```

**动作：**

- `run`（默认）：创建并运行一个新容器。
- `exec`：进入已有容器。
- `start`：启动已停止的容器。
- `restart`：重启容器。

**参数：**

- `ACTION`：可选值为 `exec`、`start`、`restart`、`run`，默认值为 `run`。
- `CONTAINER_NAME`：容器名称，默认值为 `data_collection_open_source`。

**示例：**

```bash
# 创建并运行新容器（默认）
./scripts/start_gui.sh run my_container

# 进入已有容器
./scripts/start_gui.sh exec my_container

# 启动已停止的容器
./scripts/start_gui.sh start my_container

# 重启容器
./scripts/start_gui.sh restart my_container
```

**在容器内运行服务：**

使用 `exec` 进入容器后，需要在两个不同终端中启动两个服务。

**终端 1 - 启动容器并运行数据采集服务器：**

```bash
# 进入容器
./scripts/start_gui.sh exec my_container

# 在容器内启动数据采集服务器
python scripts/data_collector_server.py --enable_physics --enable_curobo --publish_ros
```

**终端 2 - 进入同一个容器并运行数据采集应用：**

```bash
# 在新终端中进入同一个容器
./scripts/start_gui.sh exec my_container

# 在容器内运行数据采集应用
python scripts/run_data_collection.py --task_template tasks/geniesim_2025/sort_fruit/g2/sort_the_fruit_into_the_box_apple_g2.json --use_recording
```

**注意：** 两个终端都需要 `exec` 进入同一个容器。执行这些命令前，请确保容器正在运行。

### 方案 2：本地部署

#### 1. 创建 Conda 环境

```bash
conda create -n data_collect python=3.11
conda activate data_collect
```

#### 2. 安装依赖

```bash
pip install -r requirements.txt
pip install "isaacsim[all,extscache]==5.1.0" --extra-index-url https://pypi.nvidia.com
```

#### 3. 安装 cuRobo

克隆 [cuRobo](https://github.com/NVlabs/curobo) 并安装：

```bash
# 将 CUROBO_DIR 设置为你的 cuRobo 安装目录
export CUROBO_DIR=/path/to/cuRobo

# 复制机器人资产和配置
cp -r ${SIM_ASSETS}/robot/curobo_robot/assets/robot ${CUROBO_DIR}/src/curobo/content/assets
cp -r config/curobo/configs ${CUROBO_DIR}/src/curobo/content/

# 安装 cuRobo
cd ${CUROBO_DIR} && pip install -e ".[isaacsim]" --no-build-isolation
```

**注意：** 安装 cuRobo 前，请根据你的 GPU 架构设置 `TORCH_CUDA_ARCH_LIST`。对于 RTX 4090D，使用：

```bash
export TORCH_CUDA_ARCH_LIST="8.9"
```

#### 4. 设置 ROS2

在本机安装 ROS2，安装位置应为 `/opt/ros/humble/` 或 `/opt/ros/jazzy/`。

然后设置环境变量，也可以将这些环境变量写入 `~/.bashrc`：

```bash
export ROS_DISTRO=jazzy # 或 humble
export ROS_CMD_DISTRO=${ROS_DISTRO}
export CONDA_SITE_PACKAGES=YOUR_CONDA_ENV_SITE_PACKAGES_PATH # 例如 ~/anaconda3/envs/data_collect/lib/python3.11/site-packages/
export LD_LIBRARY_PATH=${LD_LIBRARY_PATH}:${CONDA_SITE_PACKAGES}/isaacsim/exts/isaacsim.ros2.bridge/${ROS_DISTRO}/lib
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
```

#### 5. 启动服务

你需要在两个独立终端中运行两个服务。

**终端 1 - 数据采集服务器：**

```bash
python scripts/data_collector_server.py [OPTIONS]
```

**`data_collector_server.py` 的选项：**

- `--headless`：以 headless 模式运行。
- `--enable_physics`：启用物理仿真。
- `--enable_curobo`：启用 cuRobo 运动规划。
- `--publish_ros`：发布 ROS 消息。如果需要录制数据，必须设置该选项。

**终端 2 - 数据采集应用：**

```bash
python scripts/run_data_collection.py [OPTIONS]
```

**`run_data_collection.py` 的选项：**

- `--use_recording`：使用录制模式。如果需要录制数据，必须设置该选项。
- `--task_template`：任务模板 JSON 文件路径。

**示例：**

```bash
# 终端 1
python scripts/data_collector_server.py --enable_physics --enable_curobo --publish_ros
python scripts/data_collector_server.py \
  --enable_physics \
  --enable_curobo \
  --publish_ros \
  --livestream
# 终端 2
python scripts/run_data_collection.py --task_template tasks/geniesim_2025/sort_fruit/g2/sort_the_fruit_into_the_box_apple_g2.json --use_recording
```

## 使用示例

### Docker - 自动化数据采集

```bash
# 设置资产路径
export SIM_ASSETS=~/assets

# 使用自定义任务运行数据采集
./scripts/run_data_collection.sh \
  --headless \
  --task tasks/geniesim_2025/sort_fruit/g2/sort_the_fruit_into_the_box_apple_g2.json
```

### Docker - 交互式开发

```bash
# 设置资产路径
export SIM_ASSETS=~/assets

# 启动交互式容器
./scripts/start_gui.sh run my_container

# 终端 1：进入容器并启动数据采集服务器
./scripts/start_gui.sh exec my_container
# 在容器内：
python scripts/data_collector_server.py --enable_physics --enable_curobo --publish_ros

# 终端 2：进入同一个容器并运行数据采集应用
./scripts/start_gui.sh exec my_container
# 在容器内：
python scripts/run_data_collection.py --task_template tasks/geniesim_2025/sort_fruit/g2/sort_the_fruit_into_the_box_apple_g2.json --use_recording
```

### 本地 - 完全控制

```bash
# 终端 1：启动带物理仿真和 cuRobo 的服务器
python scripts/data_collector_server.py --enable_physics --enable_curobo --publish_ros

# 终端 2：运行数据采集
python scripts/run_data_collection.py \
  --task_template tasks/geniesim_2025/sort_fruit/g2/sort_the_fruit_into_the_box_apple_g2.json \
  --use_recording
```

## 任务配置指南

要创建和配置数据采集任务，请参考 [任务配置指南](TASK_CONFIG_GUIDE.zh-CN.md)。该完整指南涵盖：

- 从零创建任务配置文件。
- 配置场景、机器人和物体。
- 设置任务阶段（pick、place、insert、rotate、reset）。
- 配置运行时检查器和数据过滤规则。
- 理解动作参数和 workspace 类型。
- 完整示例和最佳实践。

该指南为所有配置选项提供了详细说明和示例，便于你根据自己的数据采集需求创建自定义任务。
