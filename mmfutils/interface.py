"""Stand-in for zope.interface if it is not available."""

__all__ = ['Interface', 'Attribute', 'implements',
           'verifyObject', 'verifyClass']

import logging
import warnings

try:
    import zope.interface
    from zope.interface import (Interface, Attribute, implements)
    from zope.interface.verify import (verifyObject, verifyClass)
except ImportError:             # pragma: nocover
    zope = None
    warnings.warn("Could not import zope.interface... using dummy stand-ins")

    Interface = object

    class Attribute(object):
        """Dummy"""
        def __init__(self, __name__, __doc__=''):
            pass

    def implements(*interfaces):
        """Dummy"""

    def verifyObject(iface, candidate):
        """Dummy"""

    def verifyClass(iface, candidate):
        """Dummy"""

if zope:
    # Provides a real "asStructuredText" replacement that produces
    # reStructuredText so I can use it in documentation like README.rst etc.

    import zope.interface.document
    from zope.interface.document import (_justify_and_indent, _trim_doc_string)

    def asStructuredText(I, munge=0):
        """ Output structured text format.  Note, this will whack any existing
        'structured' format of the text.  """

        r = ["``%s``" % (I.getName(),)]
        outp = r.append
        level = 1

        if I.getDoc():
            outp(_justify_and_indent(_trim_doc_string(I.getDoc()), level))

        bases = [base
                 for base in I.__bases__
                 if base is not zope.interface.Interface
                 ]
        if bases:
            outp(_justify_and_indent("This interface extends:", level, munge))
            level += 1
            for b in bases:
                item = "o ``%s``" % b.getName()
                outp(_justify_and_indent(_trim_doc_string(item), level, munge))
            level -= 1

        attributes = []
        methods = []
        for name, desc in sorted(I.namesAndDescriptions()):
            if hasattr(desc, 'getSignatureString'):  # ugh...
                methods.append((name, desc))
            else:
                attributes.append((name, desc))

        if attributes:
            outp(_justify_and_indent("Attributes:", level, munge))
            level += 1
            for name, desc in attributes:
                item = "``%s`` -- %s" % (desc.getName(),
                                         desc.getDoc() or 'no documentation')
                outp(_justify_and_indent(_trim_doc_string(item), level, munge))
            level -= 1

        if methods:
            outp(_justify_and_indent("Methods:", level, munge))
            level += 1
            for name, desc in methods:
                item = "``%s%s`` -- %s" % (desc.getName(),
                                           desc.getSignatureString(),
                                           desc.getDoc() or 'no documentation')
                outp(_justify_and_indent(_trim_doc_string(item), level, munge))
            level -= 1
        return "\n\n".join(r) + "\n\n"

    logging.info(
        "Patching zope.interface.document.asStructuredText to format code")
    zope.interface.document.asStructuredText = asStructuredText
