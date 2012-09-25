URL
===
URL parsing for humans.

Chaining
========
Many of the methods on the `URL` class can be chained to produce a number of
effects in sequence:

    import url

    # Create a url object
    myurl = url.URL.parse('http://www.FOO.com/bar?utm_source=foo#what')
    # Remove some parameters and the fragment, spit out utf-8
    print myurl.defrag().lower().deparam(['utm_source']).utf8()