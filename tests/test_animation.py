import os
import tempfile

import numpy as np
from matplotlib import pyplot as plt

import pytest

from mmfutils.plot import animation
from mmfutils.contexts import coroutine


class TestAnimation(object):
    @staticmethod
    def get_data():
        x = np.linspace(0, 1, 10)
        t = 0
        y = 0 * x
        while t < 5:
            y = np.sin(2 * np.pi * t * x)
            yield t, x, y
            t += 0.1

    @staticmethod
    @coroutine
    def get_plot_data(fig=None):
        if fig is None:
            # I can specify a custom size here if needed
            fig = plt.gcf()
        plt.clf()

        (line,) = plt.plot([], [])  # Here we do the initial plot, set the axes,
        plt.axis([0, 1, -1, 1])  # and save line and text to update later
        title = plt.title("")
        while True:
            t, x, y = yield fig  # Arguments passed from the yield statement
            line.set_data(x, y)  # Updating the data is faster than redrawing
            title.set_text("t={:.1f}".format(t))

    def get_frames(self):
        with self.get_plot_data() as plot_data:
            for data in self.get_data():
                yield plot_data(data)

    def test_animation1(self):
        fig = plt.figure()
        with tempfile.NamedTemporaryFile(suffix=".mp4") as f:
            with self.get_plot_data(fig=fig) as plot_data:
                anim = animation.MyFuncAnimation(fig, plot_data, self.get_data())
                anim.save(f.name, fps=20)

    def test_animate(self):
        anim = animation.animate(self.get_frames)
        html = anim.to_html5_video()
        return html


pytest.mark.slow(TestAnimation)
