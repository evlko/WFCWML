import base64
import zlib
from typing import Tuple

import numpy as np

from project.wfc.wobj import WeightedObject


class Utils:
    @staticmethod
    def weighted_choice(
        objects: list[WeightedObject], seed: int = None
    ) -> WeightedObject:
        """Select a weighted object based on its weight."""
        random_gen = np.random.RandomState(seed)

        weights = np.array([obj.weight for obj in objects])
        probabilities = weights / np.sum(weights)

        return random_gen.choice(objects, p=probabilities)

    @staticmethod
    def encode_np_array(arr: np.ndarray) -> str:
        compressed_data = zlib.compress(arr.tobytes())
        return base64.b64encode(compressed_data).decode("utf-8")

    @staticmethod
    def decode_np_array(
        encoded_str: str, shape: Tuple[int, ...], dtype: np.dtype = int
    ) -> np.ndarray:
        compressed_data = base64.b64decode(encoded_str)
        byte_data = zlib.decompress(compressed_data)
        return np.frombuffer(byte_data, dtype=dtype).reshape(shape)
