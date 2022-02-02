"""Stand-in for zope.interface if it is not available."""

import logging
import warnings

__all__ = [
    "Interface",
    "Attribute",
    "implementer",
    "verifyObject",
    "verifyClass",
    "describe_interface",
]

try:
    import zope.interface
    from zope.interface import Interface, Attribute, implementer
    from zope.interface.verify import verifyObject, verifyClass
except ImportError:  # pragma: nocover
    zope = None
    warnings.warn("Could not import zope.interface... using dummy stand-ins")

    Interface = object

    class Attribute(object):
        """Dummy"""

        def __init__(self, __name__, __doc__=""):
            pass

    def implementer(*interfaces):
        """Dummy"""
        return lambda cls: cls

    def verifyObject(iface, candidate):
        """Dummy"""

    def verifyClass(iface, candidate):
        """Dummy"""


if zope:
    # Provides a real "asStructuredText" replacement that produces
    # reStructuredText so I can use it in documentation like README.rst etc.

    import zope.interface.document

    if hasattr(zope.interface.document, "asReStructuredText"):
        del zope.interface.document.asReStructuredText

    if not hasattr(zope.interface.document, "asReStructuredText"):
        from zope.interface.document import _justify_and_indent, _trim_doc_string

        def _justify_and_indent_and_trim_doc_string(string, level=0, munge=0):

            # Hack to replace titles used by numpydoc...
            for indent in [" " * 4, " " * 8, " " * 12]:
                for title in ["Parameters", "Arguments"]:
                    src = "\n".join([indent + title, indent + "-" * len(title)])
                    repl = "\n".join([indent[:-2] + title + ":", ""])
                    string = string.replace(src, repl)

            return _justify_and_indent(
                _trim_doc_string(string), level=level, munge=munge
            )

        def asReStructuredText(I, munge=0):
            """Output structured text format.  Note, this will whack any existing
            'structured' format of the text.
            """

            def inline_literal(s):
                return "``%s``" % (s,)

            r = [inline_literal(I.getName())]
            # r[0] = "\n".join([r[0], "="*len(r[-1])])

            outp = r.append
            level = 1

            if I.getDoc():
                outp(_justify_and_indent_and_trim_doc_string(I.getDoc(), level))

            bases = [
                base for base in I.__bases__ if base is not zope.interface.Interface
            ]
            if bases:
                outp(_justify_and_indent("This interface extends:", level, munge))
                level += 1
                for b in bases:
                    item = "o %s" % inline_literal(b.getName())
                    outp(_justify_and_indent_and_trim_doc_string(item, level, munge))
                level -= 1

            namesAndDescriptions = sorted(I.namesAndDescriptions())

            outp(_justify_and_indent("Attributes:", level, munge))
            level += 1
            for name, desc in namesAndDescriptions:
                if not hasattr(desc, "getSignatureString"):  # ugh...
                    item = "%s -- %s" % (
                        inline_literal(desc.getName()),
                        desc.getDoc() or "no documentation",
                    )
                    outp(_justify_and_indent_and_trim_doc_string(item, level, munge))
            level -= 1

            outp(_justify_and_indent("Methods:", level, munge))
            level += 1
            for name, desc in namesAndDescriptions:
                if hasattr(desc, "getSignatureString"):  # ugh...
                    _call = "%s%s" % (desc.getName(), desc.getSignatureString())
                    item = "%s -- %s" % (
                        inline_literal(_call),
                        desc.getDoc() or "no documentation",
                    )
                    outp(_justify_and_indent_and_trim_doc_string(item, level, munge))

            return "\n\n".join(r) + "\n\n"

        logging.info(
            "Patching zope.interface.document.asReStructuredText to format code"
        )
        zope.interface.document.asReStructuredText = asReStructuredText


def describe_interface(interface, format="ipython"):
    """Return an HTML object for Jupyter notebooks that describes the
    interface.

    Parameters
    ----------
    interface : Interface
       Interface to extract documentation from.
    format : 'rst', 'html', 'ipython'
       Return format.  'rst' is raw RestructuredText, 'html' is
       packaged as HTML, and 'ipython' is packaged as an
       IPython.display.HTML() object suitable for Jupyter notebooks.

    Example
    -------
    >>> class IExample(Interface):
    ...     x = Attribute("Floating point number")
    ...     def two():
    ...         "Return two"
    >>> print(describe_interface(IExample, format='rst').strip())
    ``IExample``
    <BLANKLINE>
     Attributes:
    <BLANKLINE>
      ``x`` -- Floating point number
    <BLANKLINE>
    Methods:
    <BLANKLINE>
      ``two()`` -- Return two

    You can also get this wrapped as HTML:

    >>> print(describe_interface(IExample, format='html').strip())
    <!DOCTYPE html ...
    <p><tt class="docutils literal">IExample</tt></p>
    <blockquote>
    <p>Attributes:</p>
    <blockquote>
    <tt class="docutils literal">x</tt> -- Floating point number</blockquote>
    <p>Methods:</p>
    <blockquote>
    <tt class="docutils literal">two()</tt> -- Return two</blockquote>
    </blockquote>
    </div>

    In a Jupyter notebook, this will properly display:

    >>> describe_interface(IExample)
    <IPython.core.display.HTML object>

    Other formats are not yet supported:

    >>> describe_interface(IExample, format='WYSIWYG')
    Traceback (most recent call last):
       ...
    NotImplementedError: format WYSIWYG not supported
    """
    # Chunk of code to display interfaces.
    # See: http://code.activestate.com/recipes/
    #            193890-using-rest-restructuredtext-to-create-html-snippet/

    # Local imports since we do not depend on IPython
    from docutils import core
    from docutils.writers.html4css1 import Writer, HTMLTranslator
    import zope.interface.document

    class NoHeaderHTMLTranslator(HTMLTranslator):
        def __init__(self, document):
            HTMLTranslator.__init__(self, document)
            self.head_prefix = [""] * 5
            self.body_prefix = []
            self.body_suffix = []
            self.stylesheet = []

    writer = Writer()
    writer.translator_class = NoHeaderHTMLTranslator
    rst = zope.interface.document.asReStructuredText(interface)
    if format.lower() == "rst":
        return rst

    html = core.publish_string(rst, writer=writer).decode()
    if format.lower() == "html":
        return html

    if format.lower() in ["ipython", "jupyter"]:
        import IPython.display

        return IPython.display.HTML(html)

    raise NotImplementedError("format {} not supported".format(format))
