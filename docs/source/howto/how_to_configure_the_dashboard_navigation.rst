=========================================
How to configure the dashboard navigation
=========================================

Oscar comes with a pre-configured dashboard navigation that gives you access
to its individual pages. If you have your own dashboard app that you would like
to show up in the dashboard navigation or want to arrange it differently,
that's very easy. All you have to do is override the
``OSCAR_DASHBOARD_NAVIGATION`` setting in you settings file.


Add your own dashboard menu item
--------------------------------

Assuming that you just want to append a new menu item to the dashboard, all
you have to do is open up your settings file and somewhere below the import
of the Oscar default settings::

    from oscar.defaults import *

add your custom dashboard configuration. Let's assume you would like to add
a new item "Store Manager" with a submenu item "Stores". The way you would
do that is::

    OSCAR_DASHBOARD_NAVIGATION += [
        {
            'label': _('Store manager'),
            'children': [
                {
                    'label': _('Stores'),
                    'url_name': 'your-reverse-url-lookup-name',
                },
             ]
        },
    ]

That's it. You should now have *Store manager > Stores* in you dashboard
menu. If you add to the navigation non-dashboard URLconf, you need to set
``access_fn`` parameter for the current node, so that Oscar is able to
resolve permissions to the current node::

    OSCAR_DASHBOARD_NAVIGATION += [
        {
            'label': _('Admin site'),
            'icon': 'fas fa-list',
            'url_name': 'admin:index',
            'access_fn': lambda user, url_name, url_args, url_kwargs: user.is_staff,
        }
    ]


Add an icon to your dashboard menu
----------------------------------

Although you have your menu in the dashboard now, it doesn't look as
nice as the other menu items that have icons displayed next to them. So
you probably want to add an icon to your heading.

Oscar uses `Font Awesome`_ for its icons which makes it very simple to add
an icon to your dashboard menu. All you need to do is find the right icon
for your menu item. Check out `the icon list`_ to find one.

.. _`the icon list`: http://fortawesome.github.com/Font-Awesome/#icons-web-app

Now that you have decided for an icon to use, all you need to do add the
icon class for the icon to your menu heading::

    OSCAR_DASHBOARD_NAVIGATION += [
        {
            'label': _('Store manager'),
            'icon': 'fas fa-map-marker',
            'children': [
                {
                    'label': _('Stores'),
                    'url_name': 'your-reverse-url-lookup-name',
                },
             ]
        },
    ]

You are not restricted to use `Font Awesome`_ icons for you menu heading. Other
web fonts will work as well as long as they support the same markup::

    <i class="icon-map-marker"></i>

The class is of the ``<i>`` is defined by the *icon* setting in the
configuration of your dashboard navigation above.


.. _`Font Awesome`: https://fontawesome.com/
.. _`this icon list`: https://fontawesome.com/icons

Controlling visibility per user
-------------------------------

By setting ``'access_fn'`` for a node, you can specify a function that will
get called with the current user. The node will only be displayed if that
function returns ``True``.
If no ``'access_fn'`` is specified, ``OSCAR_DASHBOARD_DEFAULT_ACCESS_FUNCTION``
is used.
