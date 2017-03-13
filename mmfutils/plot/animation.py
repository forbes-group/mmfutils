"""Tools for creating animations and movies."""
from __future__ import absolute_import, division, print_function

from matplotlib import animation
from matplotlib import pyplot as plt


class Animation(animation.Animation):
    '''
    This class wraps the creation of an animation using matplotlib. It is
    only a base class which should be subclassed to provide needed behavior.

    *fig* is the figure object that is used to get draw, resize, and any
    other needed events.

    *event_source* is a class that can run a callback when desired events
    are generated, as well as be stopped and started. Examples include timers
    (see :class:`TimedAnimation`) and file system notifications.

    *blit* is a boolean that controls whether blitting is used to optimize
    drawing.
    '''
    def __init__(self, fig, event_source=None, blit=False):
        self._fig = fig
        # Disables blitting for backends that don't support it.  This
        # allows users to request it if available, but still have a
        # fallback that works if it is not.
        self._blit = blit and fig.canvas.supports_blit

        # These are the basics of the animation.  The frame sequence represents
        # information for each frame of the animation and depends on how the
        # drawing is handled by the subclasses. The event source fires events
        # that cause the frame sequence to be iterated.
        self.frame_seq = self.new_frame_seq()
        self.event_source = event_source

        # Instead of starting the event source now, we connect to the figure's
        # draw_event, so that we only start once the figure has been drawn.
        self._first_draw_id = fig.canvas.mpl_connect('draw_event', self._start)

        # Connect to the figure's close_event so that we don't continue to
        # fire events and try to draw to a deleted figure.
        self._close_id = self._fig.canvas.mpl_connect('close_event',
                                                      self._stop)
        if self._blit:
            self._setup_blit()

    def _start(self, *args):
        '''
        Starts interactive animation. Adds the draw frame command to the GUI
        handler, calls show to start the event loop.
        '''
        # First disconnect our draw event handler
        self._fig.canvas.mpl_disconnect(self._first_draw_id)
        self._first_draw_id = None  # So we can check on save

        # Now do any initial draw
        self._init_draw()

        # Add our callback for stepping the animation and
        # actually start the event_source.
        self.event_source.add_callback(self._step)
        self.event_source.start()

    def _stop(self, *args):
        # On stop we disconnect all of our events.
        if self._blit:
            self._fig.canvas.mpl_disconnect(self._resize_id)
        self._fig.canvas.mpl_disconnect(self._close_id)
        self.event_source.remove_callback(self._step)
        self.event_source = None

    def save(self, filename, writer=None, fps=None, dpi=None, codec=None,
             bitrate=None, extra_args=None, metadata=None, extra_anim=None,
             savefig_kwargs=None):
        '''
        Saves a movie file by drawing every frame.

        *filename* is the output filename, e.g., :file:`mymovie.mp4`

        *writer* is either an instance of :class:`MovieWriter` or a string
        key that identifies a class to use, such as 'ffmpeg' or 'mencoder'.
        If nothing is passed, the value of the rcparam `animation.writer` is
        used.

        *fps* is the frames per second in the movie. Defaults to None,
        which will use the animation's specified interval to set the frames
        per second.

        *dpi* controls the dots per inch for the movie frames. This combined
        with the figure's size in inches controls the size of the movie.

        *codec* is the video codec to be used. Not all codecs are supported
        by a given :class:`MovieWriter`. If none is given, this defaults to the
        value specified by the rcparam `animation.codec`.

        *bitrate* specifies the amount of bits used per second in the
        compressed movie, in kilobits per second. A higher number means a
        higher quality movie, but at the cost of increased file size. If no
        value is given, this defaults to the value given by the rcparam
        `animation.bitrate`.

        *extra_args* is a list of extra string arguments to be passed to the
        underlying movie utiltiy. The default is None, which passes the
        additional argurments in the 'animation.extra_args' rcParam.

        *metadata* is a dictionary of keys and values for metadata to include
        in the output file. Some keys that may be of use include:
        title, artist, genre, subject, copyright, srcform, comment.

        *extra_anim* is a list of additional `Animation` objects that should
        be included in the saved movie file. These need to be from the same
        `matplotlib.Figure` instance. Also, animation frames will just be
        simply combined, so there should be a 1:1 correspondence between
        the frames from the different animations.

        *savefig_kwargs* is a dictionary containing keyword arguments to be
        passed on to the 'savefig' command which is called repeatedly to save
        the individual frames. This can be used to set tight bounding boxes,
        for example.
        '''
        if savefig_kwargs is None:
            savefig_kwargs = {}

        # FIXME: Using 'bbox_inches' doesn't currently work with
        # writers that pipe the data to the command because this
        # requires a fixed frame size (see Ryan May's reply in this
        # thread: [1]). Thus we drop the 'bbox_inches' argument if it
        # exists in savefig_kwargs.
        #
        # [1] (http://matplotlib.1069221.n5.nabble.com/
        # Animation-class-let-save-accept-kwargs-which-
        # are-passed-on-to-savefig-td39627.html)
        #
        if 'bbox_inches' in savefig_kwargs:
            if not (writer in ['ffmpeg_file', 'mencoder_file'] or
                    isinstance(writer,
                               (FFMpegFileWriter, MencoderFileWriter))):
                print("Warning: discarding the 'bbox_inches' argument in "
                      "'savefig_kwargs' as it is only currently supported "
                      "with the writers 'ffmpeg_file' and 'mencoder_file' "
                      "(writer used: "
                      "'{0}').".format(
                          writer if isinstance(writer, six.string_types)
                          else writer.__class__.__name__))
                savefig_kwargs.pop('bbox_inches')

        # Need to disconnect the first draw callback, since we'll be doing
        # draws. Otherwise, we'll end up starting the animation.
        if self._first_draw_id is not None:
            self._fig.canvas.mpl_disconnect(self._first_draw_id)
            reconnect_first_draw = True
        else:
            reconnect_first_draw = False

        if fps is None and hasattr(self, '_interval'):
            # Convert interval in ms to frames per second
            fps = 1000. / self._interval

        # If the writer is None, use the rc param to find the name of the one
        # to use
        if writer is None:
            writer = rcParams['animation.writer']

        # Re-use the savefig DPI for ours if none is given
        if dpi is None:
            dpi = rcParams['savefig.dpi']
            if dpi == 'figure':
                dpi = self._fig.dpi

        if codec is None:
            codec = rcParams['animation.codec']

        if bitrate is None:
            bitrate = rcParams['animation.bitrate']

        all_anim = [self]
        if extra_anim is not None:
            all_anim.extend(anim
                            for anim
                            in extra_anim if anim._fig is self._fig)

        # If we have the name of a writer, instantiate an instance of the
        # registered class.
        if is_string_like(writer):
            if writer in writers.avail:
                writer = writers[writer](fps, codec, bitrate,
                                         extra_args=extra_args,
                                         metadata=metadata)
            else:
                import warnings
                warnings.warn("MovieWriter %s unavailable" % writer)

                try:
                    writer = writers[writers.list()[0]](fps, codec, bitrate,
                                                        extra_args=extra_args,
                                                        metadata=metadata)
                except IndexError:
                    raise ValueError("Cannot save animation: no writers are "
                                     "available. Please install mencoder or "
                                     "ffmpeg to save animations.")

        verbose.report('Animation.save using %s' % type(writer),
                       level='helpful')
        # Create a new sequence of frames for saved data. This is different
        # from new_frame_seq() to give the ability to save 'live' generated
        # frame information to be saved later.
        # TODO: Right now, after closing the figure, saving a movie won't work
        # since GUI widgets are gone. Either need to remove extra code to
        # allow for this non-existant use case or find a way to make it work.
        with writer.saving(self._fig, filename, dpi):
            for anim in all_anim:
                # Clear the initial frame
                anim._init_draw()
            for data in zip(*[a.new_saved_frame_seq()
                              for a in all_anim]):
                for anim, d in zip(all_anim, data):
                    # TODO: Need to see if turning off blit is really necessary
                    anim._draw_next_frame(d, blit=False)
                writer.grab_frame(**savefig_kwargs)

        # Reconnect signal for first draw if necessary
        if reconnect_first_draw:
            self._first_draw_id = self._fig.canvas.mpl_connect('draw_event',
                                                               self._start)

    def _step(self, *args):
        '''
        Handler for getting events. By default, gets the next frame in the
        sequence and hands the data off to be drawn.
        '''
        # Returns True to indicate that the event source should continue to
        # call _step, until the frame sequence reaches the end of iteration,
        # at which point False will be returned.
        try:
            framedata = next(self.frame_seq)
            self._draw_next_frame(framedata, self._blit)
            return True
        except StopIteration:
            return False

    def new_frame_seq(self):
        'Creates a new sequence of frame information.'
        # Default implementation is just an iterator over self._framedata
        return iter(self._framedata)

    def new_saved_frame_seq(self):
        'Creates a new sequence of saved/cached frame information.'
        # Default is the same as the regular frame sequence
        return self.new_frame_seq()

    def _draw_next_frame(self, framedata, blit):
        # Breaks down the drawing of the next frame into steps of pre- and
        # post- draw, as well as the drawing of the frame itself.
        self._pre_draw(framedata, blit)
        self._draw_frame(framedata)
        self._post_draw(framedata, blit)

    def _init_draw(self):
        # Initial draw to clear the frame. Also used by the blitting code
        # when a clean base is required.
        pass

    def _pre_draw(self, framedata, blit):
        # Perform any cleaning or whatnot before the drawing of the frame.
        # This default implementation allows blit to clear the frame.
        if blit:
            self._blit_clear(self._drawn_artists, self._blit_cache)

    def _draw_frame(self, framedata):
        # Performs actual drawing of the frame.
        raise NotImplementedError('Needs to be implemented by subclasses to'
                                  ' actually make an animation.')

    def _post_draw(self, framedata, blit):
        # After the frame is rendered, this handles the actual flushing of
        # the draw, which can be a direct draw_idle() or make use of the
        # blitting.
        if blit and self._drawn_artists:
            self._blit_draw(self._drawn_artists, self._blit_cache)
        else:
            self._fig.canvas.draw_idle()

    # The rest of the code in this class is to facilitate easy blitting
    def _blit_draw(self, artists, bg_cache):
        # Handles blitted drawing, which renders only the artists given instead
        # of the entire figure.
        updated_ax = []
        for a in artists:
            # If we haven't cached the background for this axes object, do
            # so now. This might not always be reliable, but it's an attempt
            # to automate the process.
            if a.axes not in bg_cache:
                bg_cache[a.axes] = a.figure.canvas.copy_from_bbox(a.axes.bbox)
            a.axes.draw_artist(a)
            updated_ax.append(a.axes)

        # After rendering all the needed artists, blit each axes individually.
        for ax in set(updated_ax):
            ax.figure.canvas.blit(ax.bbox)

    def _blit_clear(self, artists, bg_cache):
        # Get a list of the axes that need clearing from the artists that
        # have been drawn. Grab the appropriate saved background from the
        # cache and restore.
        axes = set(a.axes for a in artists)
        for a in axes:
            a.figure.canvas.restore_region(bg_cache[a])

    def _setup_blit(self):
        # Setting up the blit requires: a cache of the background for the
        # axes
        self._blit_cache = dict()
        self._drawn_artists = []
        self._resize_id = self._fig.canvas.mpl_connect('resize_event',
                                                       self._handle_resize)
        self._post_draw(None, self._blit)

    def _handle_resize(self, *args):
        # On resize, we need to disable the resize event handling so we don't
        # get too many events. Also stop the animation events, so that
        # we're paused. Reset the cache and re-init. Set up an event handler
        # to catch once the draw has actually taken place.
        self._fig.canvas.mpl_disconnect(self._resize_id)
        self.event_source.stop()
        self._blit_cache.clear()
        self._init_draw()
        self._resize_id = self._fig.canvas.mpl_connect('draw_event',
                                                       self._end_redraw)

    def _end_redraw(self, evt):
        # Now that the redraw has happened, do the post draw flushing and
        # blit handling. Then re-enable all of the original events.
        self._post_draw(None, self._blit)
        self.event_source.start()
        self._fig.canvas.mpl_disconnect(self._resize_id)
        self._resize_id = self._fig.canvas.mpl_connect('resize_event',
                                                       self._handle_resize)

    def to_html5_video(self):
        r'''Returns animation as an HTML5 video tag.

        This saves the animation as an h264 video, encoded in base64
        directly into the HTML5 video tag. This respects the rc parameters
        for the writer as well as the bitrate. This also makes use of the
        ``interval`` to control the speed, and uses the ``repeat``
        paramter to decide whether to loop.
        '''
        VIDEO_TAG = r'''<video {size} {options}>
  <source type="video/mp4" src="data:video/mp4;base64,{video}">
  Your browser does not support the video tag.
</video>'''
        # Cache the the rendering of the video as HTML
        if not hasattr(self, '_base64_video'):
            # First write the video to a tempfile. Set delete to False
            # so we can re-open to read binary data.
            with tempfile.NamedTemporaryFile(suffix='.m4v',
                                             delete=False) as f:
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

    def _repr_html_(self):
        r'IPython display hook for rendering.'
        fmt = rcParams['animation.html']
        if fmt == 'html5':
            return self.to_html5_video()


class TimedAnimation(Animation):
    '''
    :class:`Animation` subclass that supports time-based animation, drawing
    a new frame every *interval* milliseconds.

    *repeat* controls whether the animation should repeat when the sequence
    of frames is completed.

    *repeat_delay* optionally adds a delay in milliseconds before repeating
    the animation.
    '''
    def __init__(self, fig, interval=200, repeat_delay=None, repeat=True,
                 event_source=None, *args, **kwargs):
        # Store the timing information
        self._interval = interval
        self._repeat_delay = repeat_delay
        self.repeat = repeat

        # If we're not given an event source, create a new timer. This permits
        # sharing timers between animation objects for syncing animations.
        if event_source is None:
            event_source = fig.canvas.new_timer()
            event_source.interval = self._interval

        Animation.__init__(self, fig, event_source=event_source,
                           *args, **kwargs)

    def _step(self, *args):
        '''
        Handler for getting events.
        '''
        # Extends the _step() method for the Animation class.  If
        # Animation._step signals that it reached the end and we want to
        # repeat, we refresh the frame sequence and return True. If
        # _repeat_delay is set, change the event_source's interval to our loop
        # delay and set the callback to one which will then set the interval
        # back.
        still_going = Animation._step(self, *args)
        if not still_going and self.repeat:
            self._init_draw()
            self.frame_seq = self.new_frame_seq()
            if self._repeat_delay:
                self.event_source.remove_callback(self._step)
                self.event_source.add_callback(self._loop_delay)
                self.event_source.interval = self._repeat_delay
                return True
            else:
                return Animation._step(self, *args)
        else:
            return still_going

    def _stop(self, *args):
        # If we stop in the middle of a loop delay (which is relatively likely
        # given the potential pause here, remove the loop_delay callback as
        # well.
        self.event_source.remove_callback(self._loop_delay)
        Animation._stop(self)

    def _loop_delay(self, *args):
        # Reset the interval and change callbacks after the delay.
        self.event_source.remove_callback(self._loop_delay)
        self.event_source.interval = self._interval
        self.event_source.add_callback(self._step)
        Animation._step(self)


class FuncAnimation(TimedAnimation):
    '''
    Makes an animation by repeatedly calling a function *func*, passing in
    (optional) arguments in *fargs*.

    *frames* can be a generator, an iterable, or a number of frames.

    *init_func* is a function used to draw a clear frame. If not given, the
    results of drawing from the first item in the frames sequence will be
    used. This function will be called once before the first frame.

    If blit=True, *func* and *init_func* should return an iterable of
    drawables to clear.

    *kwargs* include *repeat*, *repeat_delay*, and *interval*:
    *interval* draws a new frame every *interval* milliseconds.
    *repeat* controls whether the animation should repeat when the sequence
    of frames is completed.
    *repeat_delay* optionally adds a delay in milliseconds before repeating
    the animation.
    '''
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
            self._iter_gen = lambda: xrange(frames).__iter__()
            self.save_count = frames

        # If we're passed in and using the default, set it to 100.
        if self.save_count is None:
            self.save_count = 100

        self._init_func = init_func

        # Needs to be initialized so the draw functions work without checking
        self._save_seq = []

        TimedAnimation.__init__(self, fig, **kwargs)

        # Need to reset the saved seq, since right now it will contain data
        # for a single frame from init, which is not what we want.
        self._save_seq = []

    def new_frame_seq(self):
        # Use the generating function to generate a new frame sequence
        return self._iter_gen()

    def new_saved_frame_seq(self):
        # Generate an iterator for the sequence of saved data. If there are
        # no saved frames, generate a new frame sequence and take the first
        # save_count entries in it.
        if self._save_seq:
            # While iterating we are going to update _save_seq
            # so make a copy to safely iterate over
            self._old_saved_seq = list(self._save_seq)
            return iter(self._old_saved_seq)
        else:
            return itertools.islice(self.new_frame_seq(), self.save_count)

    def _init_draw(self):
        # Initialize the drawing either using the given init_func or by
        # calling the draw function with the first item of the frame sequence.
        # For blitting, the init_func should return a sequence of modified
        # artists.
        if self._init_func is None:
            self._draw_frame(next(self.new_frame_seq()))

        else:
            self._drawn_artists = self._init_func()
            if self._blit:
                for a in self._drawn_artists:
                    a.set_animated(self._blit)
        self._save_seq = []

    def _draw_frame(self, framedata):
        # Save the data for potential saving of movies.
        self._save_seq.append(framedata)

        # Make sure to respect save_count (keep only the last save_count
        # around)
        self._save_seq = self._save_seq[-self.save_count:]

        # Call the func with framedata and args. If blitting is desired,
        # func needs to return a sequence of any artists that were modified.
        self._drawn_artists = self._func(framedata, *self._args)
        if self._blit:
            for a in self._drawn_artists:
                a.set_animated(self._blit)


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
    anim = animation.FuncAnimation(fig=fig, func=func, frames=_get_frames(),
                                   **args)
    return anim
