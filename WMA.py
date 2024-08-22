import pandas as pd
import numpy as np
from collections import deque

class RealTimePandasWMA:
    def __init__(self, weights, max_data_points=1000):
        self.weights = np.array(weights) / np.sum(weights)  # Normalize weights
        self.window_size = len(weights)
        self.window = deque(maxlen=self.window_size)
        self.data = pd.Series(dtype=float)
        self.prev_wma = None
        self.max_data_points = max_data_points

    def add_data_point(self, value):
        self.window.append(value)
        self.data = pd.concat([self.data, pd.Series([value])], ignore_index=True)
        
        # Limit the size of self.data
        if len(self.data) > self.max_data_points:
            self.data = self.data.iloc[-self.max_data_points:]

        if len(self.window) == self.window_size:
            rolling_window = pd.Series(self.window)
            weighted_sum = np.sum(rolling_window * self.weights)

            sentiment_change = None
            if self.prev_wma is not None:
                sentiment_change = weighted_sum - self.prev_wma

            self.prev_wma = weighted_sum
            return weighted_sum, sentiment_change
        return None, None

