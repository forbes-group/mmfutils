# ---
# jupyter:
#   jupytext:
#     formats: ipynb,py:light
#     text_representation:
#       extension: .py
#       format_name: light
#       format_version: '1.3'
#       jupytext_version: 1.0.5
#   kernelspec:
#     display_name: Python [conda env:_test3]
#     language: python
#     name: conda-env-_test3-py
# ---

# # Animation with IPython Notebooks

# Here is a simple animation of a figure in a loop using `display` and `clear_output`.  This will flicker slightly and it seems to work best if you make sure there is another cell below the output (or the browser window resizes).  By putting the `clear_output` after the display command, once the loop is done, it will only display the final plot window.  You can also see anything that is printed in the cell (but you need to specify `wait=True` or it will immediately clear the figure).
#
# Most of the flicker comes from resizing the output cell, so if you do everything in a plot window of the same size, then the flicker is reduced.  Instead of printing, I usually use `title`.

# +
# %%time
# %pylab inline --no-import-all
from IPython.display import display, clear_output

x = np.linspace(0,1,100)
fig = plt.gcf()

t = 0
while t < 5:
    plt.clf()
    plt.plot(x, np.sin(2*np.pi*t*x))
    plt.axis([0,1,-1,1])
    plt.title("t={:.1f}".format(t))
    t += 0.1
    display(fig)
    clear_output(wait=True)    
# -

# Now we do the same thing, but separating the data generation and plotting into two separate functions.  This division can be useful because the computation might be done by one set of code that knows nothing about plotting.  Another abstraction that could be useful is to have the computations done on another server or in another process (but one needs to be careful about synchronization which has not yet been considered here).

# +
# %%time
# %pylab inline --no-import-all
from IPython.display import display, clear_output

def get_data():
    x = np.linspace(0,1,100)
    t = 0
    y = 0*x
    while t < 5:
        y = np.sin(2*np.pi*t*x)
        yield t, x, y
        t += 0.1
        
def plot_data(data, fig=None):
    t, x, y = data
    if fig is None:
        # I can specify a custom size here if needed
        fig = plt.gcf()
    plt.clf()
    l = plt.plot(x, y)
    plt.axis([0,1,-1,1])
    plt.title("t={:.1f}".format(t))
    display(fig)
    clear_output(wait=True)
    return fig

for data in get_data():
    plot_data(data)
# -

# One slight downside of this approach is that the data computed is no longer in the global scope which may not be so desireable for interactive work.  (It is *much* better for development though).  To allow for the usual workflow, in the previous code I have included a line to update a local dictionary.  This functionality is also provided by a decorator in my [`mmfutils` package](https://bitbucket.org/mforbes/mmfutils-fork) (version 0.4.5 or higher).

# +
from mmfutils.debugging import debug

@debug(locals())
def get_data():
    x = np.linspace(0,1,100)
    t = 0
    y = 0*x
    while t < 10:
        y = np.sin(2*np.pi*t*x)
        yield t, x, y
        t += 0.1



# -

# ## Coroutines for Speed

# Another downside of this approach is that you must redraw the figure from scratch each time which is slow.  Better is to update the plot objects (i.e. calling `set_data()`) but this requires storing the data, usually in the global state (or a class) which is not optimal.
#
# One way to achieve this is to use a [coroutine](http://book.pythontips.com/en/latest/coroutines.html) to do the drawing.  These are a little tricky to use (they must be "primed") so we will ultimately provide a wrapper for this type of code, but the idea is that your `plot_data()` function `yields` the updated figure, and gets the results from `get_frame()` from this yield statement:

# +
# %%time 
# %pylab inline --no-import-all
import IPython.display
from IPython.display import display, clear_output

from mmfutils.contexts import coroutine

def get_data():
    x = np.linspace(0,1,100)
    t = 0
    y = 0*x
    while t < 5:
        y = np.sin(2*np.pi*t*x)
        yield t, x, y
        t += 0.1
        
@coroutine
def get_plot_data(fig=None, display=IPython.display.display):
    if fig is None:
        # I can specify a custom size here if needed
        fig = plt.gcf()
    plt.clf()
    
    line, = plt.plot([], []) # Here we do the initial plot, set the axes,
    plt.axis([0,1,-1,1])     # and save line and text to update later
    title = plt.title("")
    while True:
        t, x, y = (yield fig) # Arguments passed from the yield statement
        line.set_data(x, y)    # Updating the data is faster than redrawing
        title.set_text("t={:.1f}".format(t))
        if display:
            display(fig)
            clear_output(wait=True)

# Can use the same code.
with get_plot_data() as plot_data:
    for data in get_data():
        plot_data(data)
# -

# ## Movies

# Now we can use the `animation` module to make a movie.  Since our plotting function calls `display()`, the frames will be shown as they are drawn.

# %%time
from mmfutils.plot import animation
fig = plt.gcf()
with get_plot_data(fig=fig) as plot_data:
    anim = animation.MyFuncAnimation(fig, plot_data, get_data())
    anim.save('im.mp4', fps=20)

# %%time
from IPython.display import HTML
from mmfutils.plot import animation
fig = plt.gcf()
with get_plot_data(fig=fig) as plot_data:
    anim = animation.MyFuncAnimation(fig, plot_data, get_data(), interval=10, repeat=False)
    display(HTML(anim.to_html5_video(filename='im1.mp4')))

anim.save('im.m4v')

# The video is saved to a file and can be loaded dynamically as follows:

from IPython.display import HTML
FILE_VIDEO_TAG = """<video src="{0}" type="video/mp4" controls/>"""
# !ls -lah im.mp4
HTML(FILE_VIDEO_TAG.format('im.mp4'))

# Another option is to embed the video directly as data.  The video then gets stored in the notebook itself, making the notebook very large, but allowing it to be kept as a single file:

# +
from mmfutils.plot.animation import encodebytes
from IPython.display import HTML
EMBEDED_VIDEO_TAG = """<video controls><source type="video/mp4" src="data:video/mp4;base64,{0}">
  Your browser does not support the video tag.</video>"""
_EMBEDED_VIDEO_TAG = """<video controls><source src="data:video/x-m4v;base64,{0}" type="video/mp4">
</video>"""
with open('im.mp4', 'rb') as f:
    video = encodebytes(f.read()).decode('ascii')

HTML(EMBEDED_VIDEO_TAG.format(video))
# -

# ### Video Encoding

# The default encoding seems to work, but does not have the best quality.  It also fails to render in some browsers on some machines.  Here we play with some other options.

# +
fig = plt.gcf()
with get_plot_data(fig=fig, display=False) as plot_data:
    anim = animation.MyFuncAnimation(fig, plot_data, get_data())
    filename = 'im1.mp4' 
    anim.save(filename, fps=20, extra_args=['-vcodec', 'libx264', '-pix_fmt', 'yuv420p']);

# !ls -lah $filename
with open(filename, 'rb') as f:
    video = encodebytes(f.read()).decode('ascii')
display(HTML(FILE_VIDEO_TAG.format(filename)),
        HTML(EMBEDED_VIDEO_TAG.format(video)))
# -


