"""
load_tests/locustfile_staged.py
--------------------------------
Entrypoint for the staged ramp load test.
Imports all user classes from locustfile.py and defines StagedRampShape
in the same module so Locust 2.x auto-discovers it.

Run:
    uv run locust \
        -f load_tests/locustfile_staged.py \
        --headless \
        --host=http://localhost:8000 \
        --html=load_tests/results/staged_report.html
"""

# Re-export all user classes so Locust picks them up
from load_tests.locustfile import (
    ShopkeeperUser,
    WarehouseManagerUser,
    RiderUser,
    AdminUser,
)

from locust import LoadTestShape


class StagedRampShape(LoadTestShape):
    """
    Phase schedule:
      0:00 –  2:00  Warm-up  :  20 users at  5/s
      2:00 –  7:00  Ramp     : 100 users at 10/s
      7:00 – 15:00  Peak     : 200 users at 20/s  ← resume numbers come from here
    """

    stages = [
        (120,  20,   5),
        (420,  100,  10),
        (900,  200,  20),
    ]

    def tick(self):
        run_time = self.get_run_time()
        for time_limit, users, spawn_rate in self.stages:
            if run_time < time_limit:
                return (users, spawn_rate)
        return None