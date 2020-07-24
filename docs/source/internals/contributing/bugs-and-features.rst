======================================
Reporting bugs and requesting features
======================================

Before reporting a bug or requesting a new feature, please consider these
general points:

* Check that someone hasn't already filed the bug or feature request by
  searching in the ticket tracker.

* Don't use the ticket system to ask support questions. Use the
  `django-oscar`_ mailing list for that.

* Don't use the ticket tracker for lengthy discussions, because they're
  likely to get lost. If a particular ticket is controversial, please move the
  discussion to `django-oscar`_.

All bugs are reported on our `GitHub issue tracker`_.

.. _`GitHub issue tracker`: https://github.com/django-oscar/django-oscar/issues

Reporting security issues
-------------------------

Security is paramount for e-commerce software like Oscar.  Hence, we have
adopted a policy which allows for responsible reporting and disclosure of
security related issues.

If you believe you have found something in Oscar (or one of its extensions)
which has security implications, please report is via email to
``oscar.security@tangentlabs.co.uk``.  Someone from the core team will
acknowledge your report and take appropriate action.

Reporting bugs
--------------

Well-written bug reports are *incredibly* helpful. However, there's a certain
amount of overhead involved in working with any bug tracking system so your
help in keeping our ticket tracker as useful as possible is appreciated. In
particular:

* **Do** ask on `django-oscar`_ *first* if you're not sure if
  what you're seeing is a bug.

* **Do** write complete, reproducible, specific bug reports. You must
  include a clear, concise description of the problem, and a set of
  instructions for replicating it. Add as much debug information as you can:
  code snippets, test cases, exception stack traces, screenshots, etc. A nice
  small test case is the best way to report a bug, as it gives us an easy
  way to confirm the bug quickly.

Reporting user interface bugs and features
------------------------------------------

If your bug or feature request touches on anything visual in nature, there
are a few additional guidelines to follow:

* Include screenshots in your ticket which are the visual equivalent of a
  minimal test case. Show off the issue, not the crazy customisations
  you've made to your browser.

* If you're offering a pull request which changes the look or behaviour of
  Oscar's UI, please attach before *and* after screenshots.

* Screenshots don't absolve you of other good reporting practices. Make sure
  to include URLs, code snippets, and step-by-step instructions on how to
  reproduce the behaviour visible in the screenshots.

Requesting features
-------------------

We're always trying to make Oscar better, and your feature requests are a key
part of that. Here are some tips on how to make a request most effectively:

* First request the feature on the `django-oscar`_ list, not in the
  ticket tracker. It'll get read more closely if it's on the mailing list.
  This is even more important for large-scale feature requests. We like to
  discuss any big changes to Oscar's core on the mailing list before
  actually working on them.

* Describe clearly and concisely what the missing feature is and how you'd
  like to see it implemented. Include example code (non-functional is OK)
  if possible.

* Explain *why* you'd like the feature, because sometimes it isn't obvious
  why the feature would be useful.

As with most open-source projects, code talks. If you are willing to write the
code for the feature yourself or, even better, if you've already written it,
it's much more likely to be accepted. Just fork Oscar on GitHub, create a
feature branch, and show us your work!

.. _django-oscar: http://groups.google.com/group/django-oscar
