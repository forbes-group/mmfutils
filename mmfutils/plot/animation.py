"""Tools for creating animations and movies."""
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import itertools
import os
import tempfile

from matplotlib import animation

try:
    from matplotlib.cbook import iterable
except ImportError:
    from matplotlib.animation import iterable
    
from matplotlib.animation import (TimedAnimation, FuncAnimation, encodebytes,
                                  writers, rcParams, six)
from matplotlib import pyplot as plt


class MyFuncAnimation(FuncAnimation):
    """Refactoring of the FuncAnimation class to do the following:

    1. Allow running to the end of `frames()` generator if save_count ==
       None.
    2. Allowing user to store video when generating HTML video.
    """
    def __init__(self, fig, func, frames=None, init_func=None, fargs=None,
                 save_count=None, **kwargs):
        if fargs:
            self._args = fargs
        else:
            self._args = ()
        self._func = func

        # Amount of framedata to keep around for saving movies. This is only
        # used if we don't know how many frames there will be: in the case
        # of no generator or in the case of a callable.
        self.save_count = save_count

        # Set up a function that creates a new iterable when needed. If nothing
        # is passed in for frames, just use itertools.count, which will just
        # keep counting from 0. A callable passed in for frames is assumed to
        # be a generator. An iterable will be used as is, and anything else
        # will be treated as a number of frames.
        if frames is None:
            self._iter_gen = itertools.count
        elif six.callable(frames):
            self._iter_gen = frames
        elif iterable(frames):
            self._iter_gen = lambda: iter(frames)
            if hasattr(frames, '__len__'):
                self.save_count = len(frames)
        else:
            self._iter_gen = lambda: range(frames).__iter__()
            self.save_count = frames

        self._init_func = init_func

        # Needs to be initialized so the draw functions work without checking
        self._save_seq = []

        TimedAnimation.__init__(self, fig, **kwargs)

        # Need to reset the saved seq, since right now it will contain data
        # for a single frame from init, which is not what we want.
        self._save_seq = []

    def _init_draw(self):
        # Initialize the drawing either using the given init_func or by
        # calling the draw function with the first item of the frame sequence.
        # For blitting, the init_func should return a sequence of modified
        # artists.
        if self._init_func is None:
            try:
                self._draw_frame(next(self.new_frame_seq()))
            except StopIteration:
                pass

        else:
            self._drawn_artists = self._init_func()
        self._save_seq = []

    def _draw_frame(self, framedata):
        # Save the data for potential saving of movies.
        self._save_seq.append(framedata)

        # Make sure to respect save_count (keep only the last save_count
        # around)
        if self.save_count is not None:
            self._save_seq = self._save_seq[-self.save_count:]

        # Call the func with framedata and args. If blitting is desired,
        # func needs to return a sequence of any artists that were modified.
        self._drawn_artists = self._func(framedata, *self._args)

    def to_html5_video(self, filename=None):
        r'''Returns animation as an HTML5 video tag.

        This saves the animation as an h264 video, encoded in base64
        directly into the HTML5 video tag. This respects the rc parameters
        for the writer as well as the bitrate. This also makes use of the
        ``interval`` to control the speed, and uses the ``repeat``
        parameter to decide whether to loop.
        '''
        VIDEO_TAG = r'''<video {size} {options}>
  <source type="video/mp4" src="data:video/mp4;base64,{video}">
  Your browser does not support the video tag.
</video>'''
        # Cache the the rendering of the video as HTML
        if not hasattr(self, '_base64_video'):
            if filename is None:
                file_ = tempfile.NamedTemporaryFile(suffix='.m4v',
                                                    delete=False)
            else:
                file_ = open(filename, 'wb')

            with file_ as f:
                # We create a writer manually so that we can get the
                # appropriate size for the tag
                Writer = writers[rcParams['animation.writer']]
                writer = Writer(codec='h264',
                                bitrate=rcParams['animation.bitrate'],
                                fps=1000. / self._interval)
                self.save(f.name, writer=writer)

            # Now open and base64 encode
            with open(f.name, 'rb') as video:
                vid64 = encodebytes(video.read())
                self._base64_video = vid64.decode('ascii')
                self._video_size = 'width="{0}" height="{1}"'.format(
                    *writer.frame_size)

            if filename is None:
                # Now we can remove
                os.remove(f.name)

        # Default HTML5 options are to autoplay and to display video controls
        options = ['controls', 'autoplay']

        # If we're set to repeat, make it loop
        if self.repeat:
            options.append('loop')
        return VIDEO_TAG.format(video=self._base64_video,
                                size=self._video_size,
                                options=' '.join(options))


def animate(get_frames, fig=None, display=False, **kw):
    """Make a movie of the frames as returned by get_frames()."""
    if display:
        from IPython.display import display, clear_output

    if fig is None:
        fig = plt.gcf()

    def _get_frames():

        nframe = 0
        for frame in get_frames():
            if nframe == 0:
                # Initial frame used to setup figure.  This is not recorded in
                # the movie.
                yield frame

            if display:
                display(fig)
                clear_output(wait=True)

            yield frame
            nframe += 1
        if display:
            clear_output(wait=False)

    def func(frame):
        return frame

    args = dict(interval=10, repeat=True)
    args.update(kw)
    anim = MyFuncAnimation(fig=fig, func=func, frames=_get_frames(),
                           **args)
    return anim
