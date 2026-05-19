# 任务配置指南

本文档说明如何创建用于定义机器人仿真任务的 JSON 格式任务配置文件。配置文件会由 `client/layout/task_generate.py` 解析，并生成具体的任务实例。

## 目录

1. 基础结构
2. 场景原点（origin）
3. 物体配置（objects）
4. 场景配置（scene）
5. 机器人配置（robot）
6. 任务阶段（stages）
7. 其他配置
8. 完整示例
9. 快速开始
10. 常见问题
11. 动作额外参数详细说明

---

## 基础结构

任务配置文件是一个 JSON 文件，主要包含以下部分：

```json
{
    "task": "任务名称",
    "origin": { ... },           // 场景原点（可选）
    "objects": { ... },          // 物体配置（必需）
    "scene": { ... },            // 场景配置（必需）
    "robot": { ... },            // 机器人配置（可选）
    "stages": [ ... ],           // 任务阶段（必需）
    "recording_setting": { ... }, // 录制设置（可选）
    "task_description": { ... }, // 任务描述（可选）
    "task_metric": { ... }       // 任务评估指标（可选）
}
```

---

## 场景原点（origin）

`origin` 字段定义场景的全局原点位置。**所有物体和机器人的位置都会先相对于该原点进行变换**。

### 结构

```json
{
    "origin": {
        "position": [2.91, 0.76, 0.0],
        "quaternion": [1, 0, 0, 0]
    }
}
```

### 字段说明

- **position**（必需）：原点在世界坐标系中的位置 `[x, y, z]`，单位为米。
- **quaternion**（必需）：原点旋转，四元数格式为 `w, x, y, z`。

### 重要说明

- 如果配置了 `origin`，所有 workspace、物体和机器人的位置都会先相对于 `origin` 进行变换，再转换到世界坐标系。
- 如果未配置 `origin`，默认值为 `position: [0, 0, 0]` 和 `quaternion: [1, 0, 0, 0]`。
- **原点位置选择建议**：通常选择机器人前方操作空间的中心点，例如桌面中心。这样可以简化后续 workspace 和物体位置的配置。

---

## 物体配置（objects）

`objects` 字段定义场景中所有物体的配置，包含以下子字段：

### 结构

```json
{
    "objects": {
        "task_related_objects": [ ... ],  // 任务相关物体（必需）
        "scene_objects": [ ... ],         // 场景物体（可选）
        "attach_objects": [ ... ],        // 附着物体（可选）
        "fix_objects": [ ... ],           // 固定位置物体（可选）
        "constraints": null              // 约束（可选）
    }
}
```

### 1. task_related_objects（任务相关物体）

任务执行过程中涉及的主要物体。这些物体会被优先摆放。

#### 基本格式

```json
{
    "object_id": "unique_object_id",
    "data_info_dir": "objects/path/to/object",
    "workspace_id": "work_table",
    "mass": 0.05
}
```

#### 候选物体（candidate_objects）

如果同一个 `object_id` 需要从多个候选物体中随机选择，可以使用 `candidate_objects`：

```json
{
    "object_id": "geniesim_2025_storage_box_2",
    "candidate_objects": [
        {
            "data_info_dir": "objects/benchmark/storage_box/benchmark_storage_box_006/",
            "object_id": "geniesim_2025_storage_box_006_green"
        },
        {
            "data_info_dir": "objects/benchmark/storage_box/benchmark_storage_box_007/",
            "object_id": "geniesim_2025_storage_box_007_blue"
        }
    ],
    "mass": 1000,
    "workspace_id": "box_poses"
}
```

**说明**：

- 系统会从 `candidate_objects` 中随机选择一个。
- 外层字段（如 `mass`、`workspace_id`）会覆盖候选物体中的对应字段。
- 实际使用的 `object_id` 是外层定义的 `object_id`，不是候选物体内部的 `object_id`。

#### 相对 Workspace 的位置

如果物体需要相对于某个 workspace 放置：

```json
{
    "object_id": "geniesim_2025_storage_box_2",
    "workspace_id": "box_poses",
    "workspace_relative_position": [0.0, 0.0, 0.0],
    "workspace_relative_orientation": [0.5, 0.5, 0.5, 0.5]
}
```

### 2. scene_objects（场景物体）

用于增加场景复杂度的背景物体，支持采样配置。

#### 采样配置

```json
{
    "sample": {
        "min_num": 2,      // 最小采样数量
        "max_num": 7,      // 最大采样数量
        "max_repeat": 1    // 最大重复次数
    },
    "workspace_id": "work_table",
    "available_objects": [
        {
            "data_info_dir": "objects/benchmark/apple/benchmark_apple_000/",
            "object_id": "geniesim_2025_apple_000",
            "mass": 0.05
        },
        {
            "data_info_dir": "objects/benchmark/orange/benchmark_orange_001/",
            "object_id": "geniesim_2025_orange_001",
            "mass": 0.05
        }
    ]
}
```

**说明**：

- `sample` 定义采样规则。
- `available_objects` 是候选物体列表。
- 系统会从 `available_objects` 中随机采样 `min_num` 到 `max_num` 个物体。
- 支持嵌套采样，`available_objects` 中也可以包含带有 `sample` 的物体组。

### 3. attach_objects（附着物体）

附着到其他物体上的物体，例如放在盒子里的物品。

```json
{
    "sample": {
        "min_num": 1,
        "max_num": 2,
        "max_repeat": 2
    },
    "anchor_info": {
        "anchor_object": "geniesim_2025_target_storage_box",  // 锚定物体 ID
        "position": [0, 0.07, 0.04],                          // 相对位置
        "quaternion": [1, 0, 0, 0],                            // 相对旋转（可选）
        "random_range": [0.04, 0.0, 0.04]                     // 随机范围（可选）
    },
    "workspace_id": "work_table",
    "available_objects": [ ... ]
}
```

**说明**：

- `anchor_object` 指定要附着到的物体 ID。
- `position` 和 `quaternion` 定义相对于锚定物体的位姿。
- `random_range` 允许在指定范围内添加随机偏移。

### 4. fix_objects（固定位置物体）

固定位置物体。格式与 `task_related_objects` 相同，但位置直接由配置指定。

### 字段说明

所有物体类型都支持以下字段：

- **object_id**（必需）：物体的唯一标识。
- **data_info_dir**（必需）：物体数据目录路径，相对于 `$SIM_ASSETS` 环境变量。
- **workspace_id**（可选）：workspace ID，用于指定物体放置在哪个 workspace。
- **mass**（可选）：物体质量，单位 kg。
- **workspace_relative_position**（可选）：相对于 workspace 的位置 `[x, y, z]`。
- **workspace_relative_orientation**（可选）：相对于 workspace 的旋转，四元数格式为 `w, x, y, z`。
- **chinese_semantic_name**（可选）：中文语义名称，可以是列表，系统会随机选择。
- **english_semantic_name**（可选）：英文语义名称，可以是列表，系统会随机选择。
- **allow_duplicate**（可选）：是否允许重复，默认值为 `false`。

---

## 场景配置（scene）

`scene` 字段定义场景的基本信息和 workspace。

### 结构

```json
{
    "scene": {
        "scene_id": "background/home_b/",
        "scene_info_dir": "background/home_b/",
        "scene_usd": "background/home_b/home_b_00.usda",  // 也可以是列表
        "function_space_objects": { ... }
    }
}
```

### 字段说明

- **scene_id**（必需）：场景 ID，用于匹配机器人初始位姿。
- **scene_info_dir**（必需）：场景信息目录路径。
- **scene_usd**（必需）：USD 场景文件路径，可以是字符串，也可以是列表；当为列表时会随机选择。
- **function_space_objects**（可选）：workspace 定义。

### function_space_objects（Workspace）

定义用于物体摆放的 workspace 区域。根据配置方式不同，系统会使用两种不同的布局生成器（参考 `GeneratorType.SPACE` 和 `GeneratorType.SAMPLE`）。

#### 1. Workspace 区域模式（SPACE）

当 workspace **不包含** `poses` 字段时，系统使用 `GeneratorType.SPACE` 模式：

```json
{
    "work_table": {
        "position": [0.0, 0.01, 0.9],
        "quaternion": [1, 0, 0, 0],
        "size": [0.5, 0.8, 0.2]
    }
}
```

**特点**：

- 多个物体会在该区域内**同时排布**。
- 系统使用 2D 布局求解器（`LayoutSolver2D`）自动计算位置。
- 位置会在区域内选择，并以**避免碰撞**为原则。
- 适用于多个物体需要随机分布在同一区域内的场景，例如待抓取水果放在桌面上，并可在区域内随机排列。

**字段说明**：

- `position`：workspace 区域中心位置 `[x, y, z]`。
- `quaternion`：workspace 区域旋转，四元数格式为 `w, x, y, z`。
- `size`：workspace 区域尺寸 `[x, y, z]`，单位为米。
- `blocked_zone`（可选）：禁止摆放区域。

#### 2. 候选位置模式（SAMPLE）

当 workspace **包含** `poses` 字段时，系统使用 `GeneratorType.SAMPLE` 模式：

```json
{
    "box_poses": {
        "poses": [
            {
                "position": [0.11, 0.09, 0.9],
                "quaternion": [1, 0, 0, 0],
                "random": {
                    "delta_position": [0.03, 0.0, 0]
                }
            },
            {
                "position": [0.11, -0.1, 0.9],
                "quaternion": [1, 0, 0, 0],
                "random": {
                    "delta_position": [0.03, 0.0, 0]
                }
            }
        ]
    }
}
```

**特点**：

- 多个物体会从 `poses` 列表中的候选位置中**采样位置**。
- **不同物体不会被放到同一个位置**，每个 pose 最多分配给一个物体。
- 如果物体数量超过 poses 数量，系统会报错。
- 每个物体从候选位置中随机选择一个，并且只能通过 `random.delta_position` 在该点附近做小范围随机偏移。
- 适用于物体需要放在指定位置点的场景，例如多个盒子需要放在桌面左右两侧，并从两个位置中采样摆放点。

**字段说明**：

- `poses`：候选位置列表，每个元素包含：
  - `position`：位置 `[x, y, z]`。
  - `quaternion`：旋转，四元数格式为 `w, x, y, z`。
  - `random`（可选）：随机偏移配置。
    - `delta_position`：位置随机范围 `[x, y, z]`。
    - `delta_angle`：角度随机范围，单位为弧度。
  - `chinese_position_semantic`（可选）：中文位置语义名称。
  - `english_position_semantic`（可选）：英文位置语义名称。

**两种模式对比**：

| 特性 | SPACE（Workspace 区域） | SAMPLE（候选位置） |
|---|---|---|
| 配置方式 | 包含 `size`，不包含 `poses` | 包含 `poses` 数组 |
| 物体摆放 | 在区域内同时排布，可在区域内随机 | 从候选位置中采样，只能在点附近随机 |
| 位置计算 | 由 2D 布局求解器自动计算 | 从预定义位置中选择 |
| 碰撞检测 | 自动避免碰撞 | 不重复使用同一位置 |
| 使用场景 | 待抓取水果放在桌上，可在区域内随机排列 | 多个盒子需要放在桌面左右两侧，从两个位置中采样摆放点 |

---

## 机器人配置（robot）

`robot` 字段定义机器人配置和初始状态。

### 结构

```json
{
    "robot": {
        "arm": "dual",              // "left", "right", "dual"
        "robot_id": "G2",           // "G1", "G2"
        "robot_cfg": "G2_omnipicker_fixed_dual.json",
        "robot_init_pose": { ... },
        "init_arm_pose": { ... },
        "init_arm_pose_noise": { ... }
    }
}
```

### robot_init_pose（机器人初始位姿）

```json
{
    "robot_init_pose": {
        "position": [-0.66, 0.0, 0.0],
        "quaternion": [1, 0, 0, 0],
        "random": {
            "delta_position": [0.06, 0.06, 0]
        }
    }
}
```

**说明**：

- `position` 和 `quaternion` 定义机器人底座的初始位姿。
- `random.delta_position` 允许在指定范围内添加随机位置偏移。

### init_arm_pose（手臂初始关节角）

定义机器人各关节的初始角度，单位为弧度：

```json
{
    "init_arm_pose": {
        "idx21_arm_l_joint1": 0.739033,
        "idx22_arm_l_joint2": -0.717023,
        "idx61_arm_r_joint1": -0.739033,
        "idx62_arm_r_joint2": -0.717023,
        // ... 其他关节
        "idx41_gripper_l_outer_joint1": 0.85,
        "idx81_gripper_r_outer_joint1": 0.85
    }
}
```

### init_arm_pose_noise（关节角噪声）

为关节角添加随机噪声：

```json
{
    "init_arm_pose_noise": {
        ".*_arm_.*": {
            "noise_type": "uniform",
            "low": -0.05,
            "high": 0.05
        }
    }
}
```

**说明**：

- 键是用于匹配关节名称的正则表达式。
- `noise_type` 可以为 `"uniform"`，表示均匀分布。
- `low` 和 `high` 定义噪声范围。

---

## 任务阶段（stages）

`stages` 是一个数组，用于定义任务执行过程中的各个阶段。

### 基本结构

```json
{
    "stages": [
        {
            "action": "pick",           // 动作类型
            "action_description": { ... },
            "active": { ... },          // 主动物体
            "passive": { ... },         // 被动物体
            "extra_params": { ... },    // 额外参数
            "checker": [ ... ]          // 检查器（可选）
        }
    ]
}
```

### 动作类型

- **pick**：抓取物体。
- **place**：放置物体。
- **rotate**：旋转物体。
- **insert**：插入物体。
- **reset**：手臂复位。

### active 和 passive

```json
{
    "active": {
        "object_id": "gripper",     // 也可以是具体物体 ID
        "primitive": null           // 抓取 primitive（可选）
    },
    "passive": {
        "object_id": "geniesim_2025_target_grasp_object",
        "primitive": null
    }
}
```

**说明**：

- `active` 是执行动作的物体，通常是 `"gripper"`。
- `passive` 是被操作的物体。
- `object_id` 可以是字符串、列表或字典；当为字典时，会根据 `arm` 选择。

### extra_params（额外参数）

不同动作类型拥有不同参数。详细参数说明请参考“动作额外参数详细说明”章节。

#### pick 动作

```json
{
    "extra_params": {
        "arm": "auto",                    // "left", "right", "auto"
        "disable_upside_down": true,      // 禁用倒置抓取
        "flip_grasp": true,               // 翻转抓取
        "grasp_offset": 0.01,             // 抓取偏移
        "pick_up_distance": 0.1,          // 抬升距离
        "grasp_upper_percentile": 75      // 抓取上分位数
    }
}
```

#### place 动作

```json
{
    "extra_params": {
        "arm": "auto",
        "place_with_origin_orientation": true
    }
}
```

#### insert 动作

```json
{
    "extra_params": {
        "arm": "auto",
        "pre_insert_offset": 0.1,
        "gripper_state": "open"
    }
}
```

#### rotate 动作

```json
{
    "extra_params": {
        "arm": "auto",
        "place_up_axis": "y",
        "pick_up_distance": 0.05
    }
}
```

#### reset 动作

```json
{
    "extra_params": {
        "arm": "auto",
        "plan_type": "AvoidObs"           // "Simple", "AvoidObs"
    }
}
```

**注意**：每类动作完整的参数列表和说明请参考“动作额外参数详细说明”章节。

### action_description（动作描述）

用于生成任务描述文本：

```json
{
    "action_description": {
        "action_text": "{左/右}臂拿起桌面上的苹果",
        "english_action_text": "{Left/Right} arm picks up the apple on the table"
    }
}
```

**占位符**：

- `{左/右}`、`{Left/Right}` 或 `{left/right}`：会根据实际使用的手臂自动替换。
- `{object:object_id}`：替换为物体的中文或英文语义名称。
- `{position:object_id}`：替换为物体的位置语义名称。

### checker（检查器）

用于验证某个阶段是否成功完成。详细检查器参数说明请参考 [Runtime Checker Description](./common/data_filter/README.md#runtime-checker-runtime-checker)。

**基本结构**：

```json
{
    "checker": [
        {
            "checker_name": "distance_to_target",
            "params": {
                "object_id": "geniesim_2025_target_grasp_object",
                "target_id": "gripper",
                "rule": "lessThan",
                "value": 0.08
            }
        }
    ]
}
```

**可用检查器**：

- `distance_to_target`：检查物体和目标之间的距离。
- `local_axis_angle`：检查物体局部轴与目标向量之间的夹角。

详细参数说明和示例请参考 [Runtime Checker Description](./common/data_filter/README.md#runtime-checker-runtime-checker)。

---

## 其他配置

### recording_setting（录制设置）

```json
{
    "recording_setting": {
        "camera_list": [
            "/G2/head_link3/head_front_Camera",
            "/G2/gripper_r_base_link/Right_Camera"
        ],
        "fps": 30,
        "num_of_episode": 8,
        "noised_probability": 0.1
    }
}
```

### task_description（任务描述）

```json
{
    "task_description": {
        "task_name": "将苹果放入对应的收纳盒中",
        "english_task_name": "sort the apple into the corresponding storage box",
        "init_scene_text": "机器人在桌面前，桌面上放着一个水果和两个盛有不同水果的收纳盒"
    }
}
```

支持占位符，规则与 `action_description` 相同。

### task_metric（任务评估指标）

定义数据过滤规则，用于在数据采集后验证采集数据是否满足质量要求。详细过滤规则说明请参考 [Data Filter Rules Description](./common/data_filter/README.md#data-filter-rules-filter-rules)。

**基本结构**：

```json
{
    "task_metric": {
        "filter_rules": [
            {
                "rule_name": "is_gripper_in_view",
                "params": {
                    "camera": "head",
                    "gripper": "right",
                    "out_view_allow_time": 0.2
                },
                "result_code": 4
            },
            {
                "rule_name": "is_object_relative_position_in_target",
                "params": {
                    "objects": ["geniesim_2025_target_grasp_object"],
                    "target": "geniesim_2025_target_storage_box",
                    "relative_position_range": [[-0.06, 0.06], [-0.05, 0.05], [-0.12, 0.12]]
                },
                "result_code": 1
            }
        ]
    }
}
```

**可用过滤规则**：

- `is_object_reach_target`：检查物体是否到达目标区域。
- `is_object_pose_similar2start`：检查物体位姿是否与初始位姿相近。
- `is_object_in_view`：检查物体是否在图像边界内。
- `is_gripper_in_view`：检查夹爪是否在相机视野内。
- `is_object_end_pose_up`：检查物体最终位姿是否竖直向上。
- `is_object_end_higher_than_start`：检查物体最终位置是否高于初始位置。
- `is_objects_distance_greater_than`：检查物体之间的距离。
- `is_object_end_in_region`：检查物体最终位置是否在指定区域内。
- `is_object_grasped_by_gripper`：检查物体是否被夹爪抓住。
- `is_object_relative_position_in_target`：检查物体相对于目标物体的位置。

详细参数说明和示例请参考 [Data Filter Rules Description](./common/data_filter/README.md#data-filter-rules-filter-rules)。

---

## 完整示例

完整任务配置示例可参考 `tasks/geniesim_2025/` 目录下的配置文件，例如：

- `tasks/geniesim_2025/sort_fruit/g2/sort_the_fruit_into_the_box_apple_g2.json`：水果分类任务。
- 其他任务配置文件。

---

## 快速开始

### 从零创建任务配置

本节以 `tasks/geniesim_2025/sort_fruit/g2/sort_the_fruit_into_the_box_apple_g2.json` 为例，详细说明如何从零创建一个任务配置。

#### 1. 配置场景和原点（origin）

**设计思路**：首先需要选择场景文件，并确定场景原点。原点通常选择机器人前方操作空间的中心点，例如桌面中心。这样可以简化后续 workspace 和物体位置的配置。

```json
{
    "origin": {
        "position": [2.91, 0.76, 0.0],
        "quaternion": [1, 0, 0, 0]
    },
    "scene": {
        "scene_id": "background/home_b/",
        "scene_info_dir": "background/home_b/",
        "scene_usd": ["background/home_b/home_b_00.usda"],
        "function_space_objects": {
            "work_table": {
                "position": [-0.15, 0.01, 0.9],
                "quaternion": [1, 0, 0, 0],
                "size": [0.24, 0.8, 0.2]
            },
            "box_poses": {
                "poses": [
                    {
                        "position": [0.11, 0.09, 0.9],
                        "quaternion": [1, 0, 0, 0],
                        "random": {
                            "delta_position": [0.03, 0.0, 0]
                        }
                    },
                    {
                        "position": [0.11, -0.1, 0.9],
                        "quaternion": [1, 0, 0, 0],
                        "random": {
                            "delta_position": [0.03, 0.0, 0]
                        }
                    }
                ]
            }
        }
    }
}
```

**说明**：

- `work_table` 使用 SPACE 模式（包含 `size`），用于放置待抓取水果，可在区域内随机排列。
- `box_poses` 使用 SAMPLE 模式（包含 `poses`），用于放置两个收纳盒，会从两个候选位置中采样。

#### 2. 配置机器人

```json
{
    "robot": {
        "arm": "dual",
        "robot_id": "G2",
        "robot_cfg": "G2_omnipicker_fixed_dual.json",
        "robot_init_pose": {
            "position": [-0.66, 0.0, 0.0],
            "quaternion": [1, 0, 0, 0],
            "random": {
                "delta_position": [0.06, 0.06, 0]
            }
        },
        "init_arm_pose": {
            "idx21_arm_l_joint1": 0.739033,
            "idx22_arm_l_joint2": -0.717023,
            // ... 其他关节
        },
        "init_arm_pose_noise": {
            ".*_arm_.*": {
                "noise_type": "uniform",
                "low": -0.05,
                "high": 0.05
            }
        }
    }
}
```

#### 3. 配置任务相关物体（task_related_objects）

**设计思路**：该任务需要抓取一个苹果，并将其放入对应的收纳盒。因此需要配置：

- 目标抓取物体：从多个苹果资产中随机选择一个。
- 两个收纳盒：从多个收纳盒资产中随机选择，并使用 SAMPLE 模式从两个候选位置中采样摆放点。

```json
{
    "objects": {
        "task_related_objects": [
            {
                "object_id": "geniesim_2025_target_grasp_object",
                "candidate_objects": [
                    {
                        "data_info_dir": "objects/benchmark/apple/benchmark_apple_000/",
                        "object_id": "geniesim_2025_apple_000"
                    },
                    {
                        "data_info_dir": "objects/benchmark/apple/benchmark_apple_001/",
                        "object_id": "geniesim_2025_apple_001"
                    },
                    {
                        "data_info_dir": "objects/benchmark/apple/benchmark_apple_002/",
                        "object_id": "geniesim_2025_apple_002"
                    },
                    {
                        "data_info_dir": "objects/benchmark/apple/benchmark_apple_003/",
                        "object_id": "geniesim_2025_apple_003"
                    }
                ],
                "mass": 0.05,
                "workspace_id": "work_table"
            },
            {
                "object_id": "geniesim_2025_target_storage_box",
                "candidate_objects": [
                    {
                        "data_info_dir": "objects/benchmark/storage_box/benchmark_storage_box_006/",
                        "object_id": "geniesim_2025_storage_box_006_green"
                    },
                    {
                        "data_info_dir": "objects/benchmark/storage_box/benchmark_storage_box_007/",
                        "object_id": "geniesim_2025_storage_box_007_blue"
                    },
                    {
                        "data_info_dir": "objects/benchmark/storage_box/benchmark_storage_box_008/",
                        "object_id": "geniesim_2025_storage_box_008_white"
                    },
                    {
                        "data_info_dir": "objects/benchmark/storage_box/benchmark_storage_box_009/",
                        "object_id": "geniesim_2025_storage_box_009_red"
                    },
                    {
                        "data_info_dir": "objects/benchmark/storage_box/benchmark_storage_box_010/",
                        "object_id": "geniesim_2025_storage_box_010_grey"
                    },
                    {
                        "data_info_dir": "objects/benchmark/storage_box/benchmark_storage_box_011/",
                        "object_id": "geniesim_2025_storage_box_011_black"
                    }
                ],
                "mass": 1000,
                "workspace_id": "box_poses",
                "workspace_relative_position": [0.0, 0.0, 0.0],
                "workspace_relative_orientation": [0.5, 0.5, 0.5, 0.5]
            },
            {
                "object_id": "geniesim_2025_storage_box_2",
                "candidate_objects": [
                    {
                        "data_info_dir": "objects/benchmark/storage_box/benchmark_storage_box_006/",
                        "object_id": "geniesim_2025_storage_box_006_green"
                    },
                    // ... 其他收纳盒选项
                ],
                "mass": 1000,
                "workspace_id": "box_poses",
                "workspace_relative_position": [0.0, 0.0, 0.0],
                "workspace_relative_orientation": [0.5, 0.5, 0.5, 0.5]
            }
        ]
    }
}
```

#### 4. 配置附着物体（attach_objects）

**设计思路**：为了增加场景真实感和复杂度，需要在目标收纳盒中放置 1 到 2 个苹果，并在另一个收纳盒中放置 1 到 2 个其他类型水果（桃子、橙子、柠檬、石榴等）。这里展示了嵌套采样：外层从多个水果组中采样，内层从每个水果组的多个资产中采样。

```json
{
    "objects": {
        "attach_objects": [
            {
                "sample": {
                    "min_num": 1,
                    "max_num": 2,
                    "max_repeat": 2
                },
                "anchor_info": {
                    "anchor_object": "geniesim_2025_target_storage_box",
                    "position": [0, 0.07, 0.04],
                    "quaternion": [1, 0, 0, 0],
                    "random_range": [0.04, 0.0, 0.04]
                },
                "workspace_id": "work_table",
                "available_objects": [
                    {
                        "data_info_dir": "objects/benchmark/apple/benchmark_apple_000/",
                        "object_id": "geniesim_2025_apple_000"
                    },
                    {
                        "data_info_dir": "objects/benchmark/apple/benchmark_apple_001/",
                        "object_id": "geniesim_2025_apple_001"
                    },
                    {
                        "data_info_dir": "objects/benchmark/apple/benchmark_apple_002/",
                        "object_id": "geniesim_2025_apple_002"
                    },
                    {
                        "data_info_dir": "objects/benchmark/apple/benchmark_apple_003/",
                        "object_id": "geniesim_2025_apple_003"
                    }
                ]
            },
            {
                "sample": {
                    "min_num": 1,
                    "max_num": 1,
                    "max_repeat": 1
                },
                "workspace_id": "work_table",
                "anchor_info": {
                    "anchor_object": "geniesim_2025_storage_box_2",
                    "position": [0, 0.12, 0],
                    "quaternion": [1, 0, 0, 0],
                    "random_range": [0.04, 0.0, 0.04]
                },
                "available_objects": [
                    {
                        "sample": {
                            "min_num": 1,
                            "max_num": 2,
                            "max_repeat": 2
                        },
                        "workspace_id": "work_table",
                        "available_objects": [
                            {
                                "data_info_dir": "objects/benchmark/peach/benchmark_peach_000/",
                                "object_id": "geniesim_2025_peach_000"
                            },
                            {
                                "data_info_dir": "objects/benchmark/peach/benchmark_peach_019/",
                                "object_id": "geniesim_2025_peach_019"
                            },
                            {
                                "data_info_dir": "objects/benchmark/peach/benchmark_peach_020/",
                                "object_id": "geniesim_2025_peach_020"
                            },
                            {
                                "data_info_dir": "objects/benchmark/peach/benchmark_peach_021/",
                                "object_id": "geniesim_2025_peach_021"
                            }
                        ]
                    },
                    {
                        "sample": {
                            "min_num": 1,
                            "max_num": 2,
                            "max_repeat": 2
                        },
                        "workspace_id": "work_table",
                        "available_objects": [
                            {
                                "data_info_dir": "objects/benchmark/orange/benchmark_orange_001/",
                                "object_id": "geniesim_2025_orange_001"
                            },
                            {
                                "data_info_dir": "objects/benchmark/orange/benchmark_orange_002/",
                                "object_id": "geniesim_2025_orange_002"
                            },
                            {
                                "data_info_dir": "objects/benchmark/orange/benchmark_orange_004/",
                                "object_id": "geniesim_2025_orange_004"
                            }
                        ]
                    },
                    {
                        "sample": {
                            "min_num": 1,
                            "max_num": 2,
                            "max_repeat": 2
                        },
                        "workspace_id": "work_table",
                        "available_objects": [
                            {
                                "data_info_dir": "objects/benchmark/lemon/benchmark_lemon_027/",
                                "object_id": "geniesim_2025_lemon_027"
                            },
                            {
                                "data_info_dir": "objects/benchmark/lemon/benchmark_lemon_028/",
                                "object_id": "geniesim_2025_lemon_028"
                            },
                            {
                                "data_info_dir": "objects/benchmark/lemon/benchmark_lemon_029/",
                                "object_id": "geniesim_2025_lemon_029"
                            },
                            {
                                "data_info_dir": "objects/benchmark/lemon/benchmark_lemon_030/",
                                "object_id": "geniesim_2025_lemon_030"
                            }
                        ]
                    }
                ]
            }
        ]
    }
}
```

#### 5. 配置任务阶段（stages）

**设计思路**：该任务由三个阶段组成：抓取苹果、放入目标收纳盒、手臂复位。每个阶段都需要配置动作类型、动作描述、检查器等。

```json
{
    "stages": [
        {
            "action": "pick",
            "action_description": {
                "action_text": "{左/右}臂拿起桌面上的苹果",
                "english_action_text": "{Left/Right} arm picks up the apple on the table"
            },
            "active": {
                "object_id": "gripper",
                "primitive": null
            },
            "passive": {
                "object_id": "geniesim_2025_target_grasp_object",
                "primitive": null
            },
            "extra_params": {
                "arm": "auto",
                "disable_upside_down": true,
                "flip_grasp": true,
                "grasp_offset": 0.01,
                "pick_up_distance": 0.1,
                "grasp_upper_percentile": 75
            },
            "checker": [
                {
                    "checker_name": "distance_to_target",
                    "params": {
                        "object_id": "geniesim_2025_target_grasp_object",
                        "target_id": "gripper",
                        "rule": "lessThan",
                        "value": 0.08
                    }
                }
            ]
        },
        {
            "action": "place",
            "action_description": {
                "action_text": "将拿着的苹果归类到桌面上对应的收纳筐中",
                "english_action_text": "Place the apple into the corresponding storage bin"
            },
            "active": {
                "object_id": "geniesim_2025_target_grasp_object",
                "primitive": null
            },
            "passive": {
                "object_id": "geniesim_2025_target_storage_box",
                "primitive": null
            },
            "extra_params": {
                "arm": "auto",
                "place_with_origin_orientation": true
            },
            "checker": [
                {
                    "checker_name": "distance_to_target",
                    "params": {
                        "object_id": "geniesim_2025_target_grasp_object",
                        "target_id": "geniesim_2025_target_storage_box",
                        "target_offset": {
                            "frame": "world",
                            "position": [0, 0, 0.02]
                        },
                        "rule": "lessThan",
                        "value": 0.12
                    }
                }
            ]
        },
        {
            "action": "reset",
            "action_description": {
                "action_text": "{左/右}臂复位",
                "english_action_text": "{Left/Right} arm resets"
            },
            "active": {
                "object_id": "gripper",
                "primitive": null
            },
            "passive": {
                "object_id": "gripper",
                "primitive": null
            },
            "extra_params": {
                "arm": "auto"
            }
        }
    ]
}
```

#### 6. 配置任务评估指标（task_metric）

**设计思路**：数据采集完成后，需要检查采集数据的质量，例如检查夹爪是否在视野内、物体是否成功放到目标位置等。

```json
{
    "task_metric": {
        "filter_rules": [
            {
                "rule_name": "is_gripper_in_view",
                "params": {
                    "camera": "head",
                    "gripper": "right",
                    "out_view_allow_time": 0.2
                },
                "result_code": 4
            },
            {
                "rule_name": "is_gripper_in_view",
                "params": {
                    "camera": "head",
                    "gripper": "left",
                    "out_view_allow_time": 0.1
                },
                "result_code": 4
            },
            {
                "rule_name": "is_object_relative_position_in_target",
                "params": {
                    "objects": ["geniesim_2025_target_grasp_object"],
                    "target": "geniesim_2025_target_storage_box",
                    "relative_position_range": [[-0.06, 0.06], [-0.05, 0.05], [-0.12, 0.12]]
                },
                "result_code": 1
            }
        ]
    }
}
```

#### 7. 配置其他设置

```json
{
    "task": "sort_the_fruit_into_the_box_apple_g2",
    "task_description": {
        "task_name": "将苹果放入对应的收纳盒中",
        "english_task_name": "sort the apple into the corresponding storage box",
        "init_scene_text": "机器人在桌面前，桌面上放着一个水果和两个盛有不同水果的收纳盒"
    },
    "recording_setting": {
        "camera_list": [
            "/G2/head_link3/head_front_Camera",
            "/G2/gripper_r_base_link/Right_Camera",
            "/G2/gripper_l_base_link/Left_Camera",
            "/G2/head_link3/head_right_Camera",
            "/G2/head_link3/head_left_Camera"
        ],
        "fps": 30,
        "num_of_episode": 8,
        "noised_probability": 0.1
    }
}
```

### 修改已有配置

如果已经有类似的任务配置，可以在 `tasks/geniesim_2025/` 目录中找一个相似任务作为模板，再根据需求修改相应配置项。

---

## 常见问题

### Q：如何实现物体随机选择？

A：使用 `candidate_objects` 字段，系统会从候选物体中随机选择一个。

### Q：如何将物体附着到其他物体上？

A：使用 `attach_objects`，并通过 `anchor_info` 指定锚定物体和相对位置。

### Q：如何定义多个可选位置？

A：在 workspace 配置中使用 `poses` 数组。注意：包含 `poses` 的 workspace 使用 SAMPLE 模式，多个物体会从候选位置中采样，且不同物体不会放在同一个位置。如果需要多个物体在同一区域内排布，请使用包含 `size` 的 workspace 区域模式（SPACE）。

### Q：如何实现多个物体采样？

A：在 `scene_objects` 或 `attach_objects` 中使用 `sample` 配置，并指定 `min_num` 和 `max_num`。

### Q：如何指定物体路径？

A：`data_info_dir` 是相对于 `$SIM_ASSETS` 环境变量的路径，例如 `"objects/benchmark/apple/benchmark_apple_000/"`。

---

## 动作额外参数详细说明

动作额外参数定义在 `stages` 的 `extra_params` 字段中，用于控制动作的具体行为。

### pick 动作

**参数**：

- `arm`（str，可选）：使用的手臂，可为 `"left"`、`"right"` 或 `"auto"`，默认值为 `"right"`。
- `grasp_offset`（float，可选）：抓取偏移，单位为米，默认值为 `0.03`。
- `pre_grasp_offset`（float，可选）：预抓取偏移，单位为米，默认值为 `0.0`。
- `grasp_lower_percentile`（float，可选）：抓取下分位数，范围为 0 到 100，默认值为 `0`。
- `grasp_upper_percentile`（float，可选）：抓取上分位数，范围为 0 到 100，默认值为 `100`。
- `disable_upside_down`（bool，可选）：禁用倒置抓取，默认值为 `false`。
- `flip_grasp`（bool，可选）：翻转抓取，即绕 z 轴旋转 180 度，默认值为 `false`。
- `pick_up_distance`（float，可选）：抬升距离，单位为米，默认值为 `0.12`。
- `pick_up_type`（str，可选）：抬升类型，可为 `"Simple"` 或 `"AvoidObs"`，默认值为 `"Simple"`。
- `use_near_point`（bool，可选）：是否使用近邻点，默认值为 `false`。
- `error_data`（dict，可选）：错误数据配置。
  - `type`（str）：错误类型，例如 `"RandomPerturbations"`、`"MissGrasp"`、`"WrongTarget"`、`"KeepClose"`。
  - `params`（dict）：错误参数。

**示例**：

```json
{
    "extra_params": {
        "arm": "auto",
        "disable_upside_down": true,
        "flip_grasp": true,
        "grasp_offset": 0.01,
        "pick_up_distance": 0.1,
        "grasp_upper_percentile": 75
    }
}
```

### place 动作

**参数**：

- `arm`（str，可选）：使用的手臂，可为 `"left"`、`"right"` 或 `"auto"`，默认值为 `"right"`。
- `place_with_origin_orientation`（bool，可选）：放置时是否使用原始朝向，默认值为 `true`。
- `disable_upside_down`（bool，可选）：禁用倒置放置，默认值为 `false`。
- `use_pre_place`（bool，可选）：是否使用预放置，默认值为 `false`。
- `pre_place_offset`（float，可选）：预放置偏移，单位为米，默认值为 `0.12`。
- `pre_place_direction`（str，可选）：预放置方向，默认值为 `"z"`。
- `pre_pose_noise`（dict，可选）：预位姿噪声配置。
  - `position_noise`（float）：位置噪声。
  - `rotation_noise`（float）：旋转噪声。
- `gripper_state`（str | None，可选）：夹爪状态，可为 `"open"`、`"close"` 或 `None`，默认值为 `"open"`。
- `post_place_action`（list[dict]，可选）：放置后的动作列表。
  - `gripper_cmd`（str，可选）：夹爪命令。
  - `distance`（float，可选）：移动距离，单位为米，默认值为 `0.02`。
  - `direction`（list[float]，可选）：移动方向，在被动物体局部坐标系下表示，默认值为 `[0, 0, 1]`。
- `use_near_point`（bool，可选）：是否使用近邻点，默认值为 `false`。
- `error_data`（dict，可选）：错误数据配置，格式与 pick 相同。

**示例**：

```json
{
    "extra_params": {
        "arm": "auto",
        "place_with_origin_orientation": true,
        "use_pre_place": true,
        "pre_place_offset": 0.12
    }
}
```

### insert 动作

继承自 `place` 动作，所有参数与 `place` 动作相同。

**示例**：

```json
{
    "extra_params": {
        "arm": "auto",
        "use_pre_place": true,
        "pre_place_offset": 0.1,
        "gripper_state": "open"
    }
}
```

### rotate 动作

**参数**：

- `arm`（str，可选）：使用的手臂，可为 `"left"`、`"right"` 或 `"auto"`，默认值为 `"right"`。
- `place_up_axis`（str，可选）：放置时朝上的轴，可为 `"x"`、`"y"` 或 `"z"`，默认值为 `"y"`。
- `pick_up_distance`（float，可选）：抬升距离，单位为米，默认值为 `0.0`。
- `pick_up_direction`（str，可选）：抬升方向，可为 `"x"`、`"y"` 或 `"z"`，默认值为 `"z"`。
- `place_origin_position`（bool，可选）：是否放回原位置，默认值为 `true`。

**示例**：

```json
{
    "extra_params": {
        "arm": "auto",
        "place_up_axis": "y",
        "pick_up_distance": 0.05
    }
}
```

### reset 动作

**参数**：

- `arm`（str，可选）：使用的手臂，可为 `"left"`、`"right"` 或 `"auto"`，默认值为 `"right"`。
- `plan_type`（str，可选）：规划类型，可为 `"Simple"` 或 `"AvoidObs"`，默认值为 `"AvoidObs"`。

**示例**：

```json
{
    "extra_params": {
        "arm": "auto",
        "plan_type": "AvoidObs"
    }
}
```
