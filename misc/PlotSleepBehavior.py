#!/usr/bin/env python
# from http://stackoverflow.com/a/30672412
import sys
import platform
import numpy as np
import matplotlib
from matplotlib import pyplot as plt

matplotlib.use("MacOSX")

import time
from datetime import datetime


# based on some psychopy calls.
# See https://github.com/psychopy/psychopy/blob/dae85517020cb1da2e5bebc9d804f0fa9465a71c/psychopy/platform_specific/darwin.py

import ctypes, ctypes.util
import sys
import time
import logging
import numpy as np

cocoa = ctypes.cdll.LoadLibrary(ctypes.util.find_library("Cocoa"))


### constants
#############

# see thread_policy.h (Darwin)
THREAD_STANDARD_POLICY = ctypes.c_int(1)
THREAD_STANDARD_POLICY_COUNT = ctypes.c_int(0)
THREAD_TIME_CONSTRAINT_POLICY = ctypes.c_int(2)
THREAD_TIME_CONSTRAINT_POLICY_COUNT = ctypes.c_int(4)
KERN_SUCCESS = 0


class timeConstraintThreadPolicy(ctypes.Structure):
    _fields_ = [
        ("period", ctypes.c_uint),
        ("computation", ctypes.c_uint),
        ("constrain", ctypes.c_uint),
        ("preemptible", ctypes.c_int),
    ]


def getCpuFreq():
    """Frequency of cpu (HZ var in Mach kernel)"""

    CTL_HW = ctypes.c_int(
        6
    )  # see  http://stackoverflow.com/questions/8147796/iphone-getting-cpu-frequency-not-run
    HW_BUS_FREQ = ctypes.c_int(14)

    mib = (ctypes.c_int * 2)(CTL_HW, HW_BUS_FREQ)
    val = ctypes.c_int(0)
    intSize = ctypes.c_int(ctypes.sizeof(val))
    cocoa.sysctl(ctypes.byref(mib), 2, ctypes.byref(val), ctypes.byref(intSize), 0, 0)
    return val.value


def setRealtime(doRealtime=True):
    """doRealtime: raise priority to realtime.  False: lower to normal"""
    HZ = getCpuFreq()

    if doRealtime:
        extendedPolicy = timeConstraintThreadPolicy()
        extendedPolicy.period = (
            HZ // 100
        )  # abstime units, length of one bus cycle: this means run every 10 ms
        extendedPolicy.computation = (
            extendedPolicy.period // 4
        )  # give up to this time to execute
        extendedPolicy.constrain = (
            extendedPolicy.period
        )  # and allow cpu cycles to be distributed anywhere in period
        extendedPolicy.preemptible = 1
        extendedPolicy = getThreadPolicy(
            getDefault=True, flavour=THREAD_TIME_CONSTRAINT_POLICY
        )
        err = cocoa.thread_policy_set(
            cocoa.mach_thread_self(),
            THREAD_TIME_CONSTRAINT_POLICY,
            ctypes.byref(extendedPolicy),  # send the address of the struct
            THREAD_TIME_CONSTRAINT_POLICY_COUNT,
        )
        if err != KERN_SUCCESS:
            raise RuntimeError(
                "Failed to set darwin thread policy, with thread_policy_set"
            )
        else:
            pMs = (
                np.array(
                    [
                        extendedPolicy.period,
                        extendedPolicy.computation,
                        extendedPolicy.constrain,
                    ]
                )
                / 1000.0
            )
            logging.info(
                "Successfully set darwin thread to realtime (per comp constrain: %d %d %d)".format(
                    x[1] for x in enumerate(pMs)
                )
            )

    else:
        # revert to default policy
        extendedPolicy = getThreadPolicy(
            getDefault=True, flavour=THREAD_STANDARD_POLICY
        )
        err = cocoa.thread_policy_set(
            cocoa.mach_thread_self(),
            THREAD_STANDARD_POLICY,
            ctypes.byref(extendedPolicy),  # send the address of the struct
            THREAD_STANDARD_POLICY_COUNT,
        )
    return True


def getThreadPolicy(getDefault, flavour):
    """Retrieve the current (or default) thread policy.

    getDefault should be True or False
    flavour should be 1 (standard) or 2 (realtime)

    Returns a ctypes struct with fields:
    .period
    .computation
    .constrain
    .preemptible

    See http://docs.huihoo.com/darwin/kernel-programming-guide/scheduler/chapter_8_section_4.html
    """

    extendedPolicy = timeConstraintThreadPolicy()
    getDefault = ctypes.c_int(
        getDefault
    )  # we want to retrieve actual policy or the default
    err = cocoa.thread_policy_get(
        cocoa.mach_thread_self(),
        THREAD_TIME_CONSTRAINT_POLICY,
        ctypes.byref(extendedPolicy),  # send the address of the policy struct
        ctypes.byref(THREAD_TIME_CONSTRAINT_POLICY_COUNT),
        ctypes.byref(getDefault),
    )
    return extendedPolicy


# setRealtime()


def measure(sleep=time.sleep):
    rng = np.random.default_rng(seed=2)

    max_sleep_time = 0.01

    req_sleep = []
    act_sleep = []

    for samp in range(1000):
        sleep_time = rng.random() * max_sleep_time
        req_sleep.append(sleep_time * 1000.0)

        start = datetime.now()
        sleep(sleep_time)
        end = datetime.now()

        act_sleep.append((end - start).total_seconds() * 1000.0)

    return req_sleep, act_sleep, max_sleep_time


import mmfutils.contexts

req_sleep, act_sleep, max_sleep_time = measure(
    # sleep=time.sleep
    sleep=mmfutils.contexts.sleep
)

platform_id = platform.platform()
version = sys.version.split(" ")[0]

plt.grid(True)
fig, ax = plt.subplots()
ax.plot(req_sleep, act_sleep, "r+")
ax.plot([0, max_sleep_time * 1000], [0, max_sleep_time * 1000.0], "k-")
ax.plot([0, 0.8 * max_sleep_time * 1000], [0, max_sleep_time * 1000.0], "k--")
ax.set(
    xlabel="Requested Sleep Time ($t_r$; ms)",
    ylabel="Actual Sleep Time ($t_s$; ms)",
    xlim=(0, max_sleep_time * 1000.0),
    ylim=(0, max_sleep_time * 1000.0),
    title="\n".join([f"Sleep behavior of {platform_id}", version]),
)

ax.annotate(
    r"$t_s \approx \frac{5}{4} t_r$",
    xy=(4, 5),
    xytext=(0.3, 0.7),
    textcoords="axes fraction",
    arrowprops=dict(arrowstyle="->", connectionstyle="angle3,angleA=-90,angleB=-45"),
    fontsize=14,
    bbox=dict(fc="w", ec="k", boxstyle="round"),
    ha="center",
)

plt.savefig(f"sleeptest{platform_id}.{version}.png")
