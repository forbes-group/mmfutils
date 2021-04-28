"""Tools for creating animations and movies."""
import base64
from tempfile import TemporaryDirectory

from pathlib import Path

import matplotlib as mpl
from matplotlib.animation import FuncAnimation, _log, writers
from matplotlib import pyplot as plt


encodebytes = base64.encodebytes


class MyFuncAnimation(FuncAnimation):
    """Refactoring of the FuncAnimation class to do the following:

    1. Allowing user to store video when generating HTML video.
    2. Allow clean stopping between frames in a NoInterupt context.
    """

    def __init__(self, *v, **kw):
        self.interrupted = kw.pop("interrupted", False)
        FuncAnimation.__init__(self, *v, **kw)

    def new_frame_seq(self):
        for frame in FuncAnimation.new_frame_seq(self):
            if self.interrupted:
                break
            yield frame

    def to_html5_video(self, embed_limit=None, filename=None, extra_args=None):
        """Convert the animation to an HTML5 ``<video>`` tag.

        This saves the animation as an h264 video, encoded in base64
        directly into the HTML5 video tag. This respects :obj:`animation.writer`
        and :obj:`animation.bitrate`. This also makes use of the
        ``interval`` to control the speed, and uses the ``repeat``
        parameter to decide whether to loop.

        Parameters
        ----------
        embed_limit : float, optional
            Limit, in MB, of the returned animation. No animation is created
            if the limit is exceeded.
            Defaults to :obj:`embed_limit` = 20.0.
        filename : str, optional
           *(New)* If provided, save the movie in this file and keep it,
           otherwise the movie will be stored in a temporary directory
           and deleted after.

        Returns
        -------
        video_tag : str
            An HTML5 video tag with the animation embedded as base64 encoded
            h264 video.
            If the :obj:`embed_limit` is exceeded, this returns the string
            "Video too large to embed."
        """
        VIDEO_TAG = r"""<video {size} {options}>
  <source type="video/mp4" src="data:video/mp4;base64,{video}">
  Your browser does not support the video tag.
</video>"""
        # Cache the rendering of the video as HTML
        if not hasattr(self, "_base64_video"):
            # Save embed limit, which is given in MB
            if embed_limit is None:
                embed_limit = mpl.rcParams["animation.embed_limit"]

            # Convert from MB to bytes
            embed_limit *= 1024 * 1024

            ########################################################
            # Modified code here to allow saving to filename instead

            # We create a writer manually so that we can get the
            # appropriate size for the tag
            Writer = writers[mpl.rcParams["animation.writer"]]
            writer = Writer(
                codec="h264",
                bitrate=mpl.rcParams["animation.bitrate"],
                fps=1000.0 / self._interval,
            )
            if filename is None:
                # Can't open a NamedTemporaryFile twice on Windows, so use a
                # TemporaryDirectory instead.
                with TemporaryDirectory() as tmpdir:
                    path = Path(tmpdir, "temp.m4v")
                    self.save(str(path), writer=writer)
                    # Now open and base64 encode.
                    with open(str(path), "rb") as video:
                        vid64 = encodebytes(video.read())
                    # The following works on python 3 only
                    # vid64 = encodebytes(path.read_bytes())
            else:
                path = Path(filename)
                self.save(str(path), writer=writer)
                # Now open and base64 encode.
                with open(str(path), "rb") as video:
                    vid64 = encodebytes(video.read())
                # The following works on python 3 only
                # vid64 = encodebytes(path.read_bytes())

            # End of modifications
            ########################################################
            vid_len = len(vid64)
            if vid_len >= embed_limit:
                _log.warning(
                    "Animation movie is %s bytes, exceeding the limit of %s. "
                    "If you're sure you want a large animation embedded, set "
                    "the animation.embed_limit rc parameter to a larger value "
                    "(in MB).",
                    vid_len,
                    embed_limit,
                )
            else:
                self._base64_video = vid64.decode("ascii")
                self._video_size = 'width="{}" height="{}"'.format(*writer.frame_size)

        # If we exceeded the size, this attribute won't exist
        if hasattr(self, "_base64_video"):
            # Default HTML5 options are to autoplay and display video controls
            options = ["controls", "autoplay"]

            # If we're set to repeat, make it loop
            if hasattr(self, "repeat") and self.repeat:
                options.append("loop")

            return VIDEO_TAG.format(
                video=self._base64_video,
                size=self._video_size,
                options=" ".join(options),
            )
        else:
            return "Video too large to embed."

    def _init_draw(self):
        # Initialize the drawing either using the given init_func or by
        # calling the draw function with the first item of the frame sequence.
        # For blitting, the init_func should return a sequence of modified
        # artists.
        if self._init_func is None:
            try:
                # New: ignore StopIteration.  Needed in notebooks
                # where matplotlib tries to run this again.
                self._draw_frame(next(self.new_frame_seq()))
            except StopIteration:
                pass

        else:
            self._drawn_artists = self._init_func()
            if self._blit:
                if self._drawn_artists is None:
                    raise RuntimeError(
                        "The init_func must return a " "sequence of Artist objects."
                    )
                for a in self._drawn_artists:
                    a.set_animated(self._blit)
        self._save_seq = []


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
    anim = MyFuncAnimation(fig=fig, func=func, frames=_get_frames(), **args)
    return anim
