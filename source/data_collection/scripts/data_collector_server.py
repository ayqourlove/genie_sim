# Copyright (c) 2023-2026, AgiBot Inc. All Rights Reserved.
# Author: Genie Sim Team
# License: Mozilla Public License Version 2.0

import argparse
import os
import sys


def _restart_with_clean_ros_environment():
    """Restart once without system ROS paths that can conflict with Isaac Sim's bundled ROS."""
    if os.environ.get("GENIESIM_ROS_ENV_CLEANED") == "1":
        return

    path_vars = [
        "PYTHONPATH",
        "LD_LIBRARY_PATH",
        "AMENT_PREFIX_PATH",
        "CMAKE_PREFIX_PATH",
        "COLCON_PREFIX_PATH",
        "PKG_CONFIG_PATH",
    ]
    clean_env = os.environ.copy()
    changed = False
    for name in path_vars:
        value = clean_env.get(name)
        if not value:
            continue
        parts = [part for part in value.split(os.pathsep) if part and not os.path.normpath(part).startswith("/opt/ros/")]
        new_value = os.pathsep.join(parts)
        if new_value != value:
            changed = True
            if new_value:
                clean_env[name] = new_value
            else:
                clean_env.pop(name, None)

    for name in ["ROS_VERSION", "ROS_PYTHON_VERSION", "ROS_AUTOMATIC_DISCOVERY_RANGE", "ROS_APT_SOURCE_VERSION"]:
        if name in clean_env:
            changed = True
            clean_env.pop(name, None)

    if changed:
        clean_env["GENIESIM_ROS_ENV_CLEANED"] = "1"
        sys.stderr.write(
            "Restarting data_collector_server with /opt/ros paths removed from the process environment.\n"
        )
        os.execvpe(sys.executable, [sys.executable] + sys.argv, clean_env)


_restart_with_clean_ros_environment()

root_directory = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(root_directory)

from common.base_utils.logger import logger

if os.path.exists(os.path.join(root_directory, "git_commit_info.txt")):
    with open(os.path.join(root_directory, "git_commit_info.txt"), "r") as f:
        logger.info("############GIT COMMIT INFO##########")
        logger.info(f.read())
        logger.info("############GIT COMMIT INFO##########")
else:
    logger.warning(f"git_commit_info.txt not found in {root_directory}")


def _strip_incompatible_ros_python_paths():
    """Avoid importing system ROS Python packages built for a different Python."""
    current_py_tag = f"python{sys.version_info.major}.{sys.version_info.minor}"

    def is_incompatible_ros_python_path(path):
        normalized = os.path.normpath(path)
        return (
            normalized.startswith("/opt/ros/")
            and "/lib/python" in normalized
            and current_py_tag not in normalized
        )

    pythonpath = os.environ.get("PYTHONPATH", "")
    if pythonpath:
        pythonpath_parts = pythonpath.split(os.pathsep)
        kept_paths = [path for path in pythonpath_parts if not is_incompatible_ros_python_path(path)]
        if len(kept_paths) != len(pythonpath_parts):
            os.environ["PYTHONPATH"] = os.pathsep.join(kept_paths)
            logger.warning(
                "Removed incompatible ROS Python paths from PYTHONPATH; Isaac Sim will use its Python 3.11 ROS bridge."
            )

    old_sys_path = list(sys.path)
    sys.path[:] = [path for path in sys.path if not is_incompatible_ros_python_path(path)]
    if len(sys.path) != len(old_sys_path):
        logger.warning(
            "Removed incompatible ROS Python paths from sys.path; Isaac Sim will use its Python 3.11 ROS bridge."
        )


_strip_incompatible_ros_python_paths()

parser = argparse.ArgumentParser()
parser.add_argument(
    "--headless",
    action="store_true",
    default=False,
)
parser.add_argument(
    "--debug",
    action="store_true",
    default=False,
)
parser.add_argument("--enable_physics", action="store_true", default=False)
parser.add_argument(
    "--enable_curobo",
    action="store_true",
    default=False,
)
parser.add_argument("--publish_ros", action="store_true", default=False)
parser.add_argument(
    "--livestream",
    action="store_true",
    default=False,
    help="Run Isaac Sim with the WebRTC livestream experience.",
)
parser.add_argument(
    "--livestream_public_ip",
    type=str,
    default=None,
    help="Public IP/address passed to /app/livestream/publicEndpointAddress.",
)
parser.add_argument(
    "--livestream_port",
    type=int,
    default=49100,
    help="TCP signaling port used by Isaac Sim WebRTC livestream.",
)
parser.add_argument(
    "--livestream_quit_on_disconnect",
    action="store_true",
    default=False,
    help="Quit Isaac Sim when the livestream client disconnects.",
)
parser.add_argument(
    "--physics_step",
    type=int,
    default=60,
)

args = parser.parse_args()

from isaacsim import SimulationApp

extra_args = [
    "--/persistent/rtx/modes/rt2/enabled=true",
]
if args.livestream:
    extra_args.extend(
        [
            "--enable",
            "omni.services.livestream.nvcf",
            "--/app/livestream/allowResize=true",
            f"--/app/livestream/port={args.livestream_port}",
            f"--/app/livestream/nvcf/quitOnSessionEnded={str(args.livestream_quit_on_disconnect).lower()}",
        ]
    )
    if args.livestream_public_ip:
        extra_args.append(f"--/app/livestream/publicEndpointAddress={args.livestream_public_ip}")

simulation_app = SimulationApp(
    {
        "headless": args.headless or args.livestream,
        "hide_ui": False if args.livestream else None,
        "renderer": "RealTimePathTracing",
        "extra_args": extra_args,
    }
)
simulation_app._carb_settings.set("/physics/cooking/ujitsoCollisionCooking", False)
simulation_app._carb_settings.set("/omni/replicator/asyncRendering", False)
simulation_app._carb_settings.set("/app/asyncRendering", False)
from isaacsim.core.api import World
from isaacsim.core.utils import extensions

extensions.enable_extension("isaacsim.ros2.bridge")
import omni

from server.command_controller import CommandController
from server.grpc_server import GrpcServer
from server.ui_builder import UIBuilder

physics_dt = (float)(1 / args.physics_step)
rendering_dt = (float)(1 / 30)
world = World(
    stage_units_in_meters=1,
    physics_dt=physics_dt,
    rendering_dt=rendering_dt,
    device="cpu",
)
physx_interface = omni.physx.get_physx_interface()
# Override CPU setting to use GPU
# physx_interface.overwrite_gpu_setting(1)

# world._physics_context.enable_gpu_dynamics(flag=True)
ui_builder = UIBuilder(world=world, debug=args.debug)
server_function = CommandController(
    ui_builder=ui_builder,
    enable_physics=args.enable_physics,
    enable_curobo=args.enable_curobo,
    publish_ros=args.publish_ros,
    rendering_step=int(1 / rendering_dt),
    debug=args.debug,
)
rpc_server = GrpcServer(server_function=server_function)
rpc_server.start()

step = 0
last_physics_time = 0
last_render_time = 0
while simulation_app.is_running():
    with rpc_server.server_function._timing_context("ui_builder.my_world.step"):
        ui_builder.my_world.step(render=False)
        current_time = ui_builder.my_world.current_time
        need_render = False
        if last_render_time == 0 or current_time - last_render_time >= rendering_dt:
            need_render = True
            last_render_time = current_time
        if need_render:
            ui_builder.my_world.render()
    if rpc_server:
        rpc_server.server_function.on_physics_step()
        if rpc_server.server_function.exit:
            break
    if not ui_builder.my_world.is_playing():
        if step % 100 == 0:
            logger.info("**** simulation paused ****")
        step += 1
        continue
rpc_server.server_function.print_timing_stats()
simulation_app.close()
