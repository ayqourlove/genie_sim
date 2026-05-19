# Copyright (c) 2023-2026, AgiBot Inc. All Rights Reserved.
# Author: Genie Sim Team
# License: Mozilla Public License Version 2.0

import sys

import numpy as np

from common.base_utils.logger import logger


try:
    from cv_bridge import CvBridge as CvBridge  # noqa: F401
except ModuleNotFoundError:

    class CvBridge:
        """Small cv_bridge fallback for publishing numpy images as ROS Image messages."""

        _CHANNELS_BY_ENCODING = {
            "mono8": 1,
            "rgb8": 3,
            "bgr8": 3,
            "rgba8": 4,
            "bgra8": 4,
        }

        def __init__(self):
            logger.warning(
                "cv_bridge is not available for this Python runtime; using a limited numpy-to-Image fallback."
            )

        def cv2_to_imgmsg(self, cvim, encoding="passthrough"):
            from sensor_msgs.msg import Image

            array = np.ascontiguousarray(cvim)
            if array.dtype != np.uint8:
                raise TypeError(f"Only uint8 images are supported by the fallback CvBridge, got {array.dtype}")

            msg = Image()
            msg.height = int(array.shape[0])
            msg.width = int(array.shape[1])
            msg.encoding = encoding
            msg.is_bigendian = sys.byteorder == "big"

            channels = self._get_channel_count(array, encoding)
            msg.step = int(msg.width * channels * array.itemsize)
            msg.data = array.tobytes()
            return msg

        def _get_channel_count(self, array, encoding):
            if encoding == "passthrough":
                return int(array.shape[2]) if array.ndim == 3 else 1
            if encoding not in self._CHANNELS_BY_ENCODING:
                raise ValueError(f"Unsupported image encoding for fallback CvBridge: {encoding}")
            channels = self._CHANNELS_BY_ENCODING[encoding]
            if channels == 1 and array.ndim != 2:
                raise ValueError(f"Encoding {encoding} expects a 2D image, got shape {array.shape}")
            if channels > 1 and (array.ndim != 3 or array.shape[2] != channels):
                raise ValueError(f"Encoding {encoding} expects {channels} channels, got shape {array.shape}")
            return channels
