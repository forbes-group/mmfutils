def check(q):  # pragma: nocover
    import numexpr

    q.put(numexpr.get_vml_version())
