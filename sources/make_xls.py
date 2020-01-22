import pandas as pd
import numpy as np


def set_to_nan(array, n_nans):
    array = array[:]
    n = array.shape[0]
    nan_indices = np.random.choice(np.arange(n), size=n_nans, replace=False)
    array[nan_indices] = np.nan
    return array


n_timesteps = 10000
x = np.linspace(0, 20, n_timesteps)

observable_1 = 10 * np.sin(2 * np.pi * x) + 20
observable_1 += 2 * np.cos(np.pi * x)
observable_1 += 2 * np.cos(1.3 * np.pi * x)
observable_1 += 1.2 * x

observable_2 = 9.2 * np.sin(2.2 * np.pi * x) + 24
observable_2 += 2.1 * np.cos(0.9 * np.pi * x)
observable_2 += 1.9 * np.cos(1.4 * np.pi * x)
observable_2 += 1.1 * x

target = 0.83 * observable_1 + 1.2 * observable_2

n_to_nan = int(n_timesteps * 0.05)
n_to_nan2 = int(n_timesteps * 0.08)
observable_1 = set_to_nan(observable_1, n_to_nan)
observable_2 = set_to_nan(observable_2, n_to_nan2)
data = np.zeros((n_timesteps, 3))
data[:, 0] = target
data[:, 1] = observable_1
data[:, 2] = observable_2

time = pd.date_range(start="1/1/2008", end="1/1/2015", periods=n_timesteps)
dataframe = pd.DataFrame(
        data,
        columns=["Total consumption", "A1 consumption", "A2 consumption"],
        index=time
        )
dataframe.to_excel("example.xls", na_rep="NA")
