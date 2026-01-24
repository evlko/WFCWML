import pickle
from copy import copy

import numpy as np
from sklearn.base import BaseEstimator

from project.machine_learning.model import Model
from project.wfc.judge import Judge


class TrainedJudge(Model, Judge):
    def __init__(self):
        pass
