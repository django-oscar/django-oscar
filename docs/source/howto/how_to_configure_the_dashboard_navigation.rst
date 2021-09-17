=========================================
How to configure the dashboard navigation
=========================================

Oscar comes with a pre-configured dashboard navigation that gives you access
to its individual pages. If you have your own dashboard app that you would like
to show up in the dashboard navigation or want to arrange it differently,
that's very easy. All you have to do is create a ``navigation_menu.py`` file
then register the menu with optional child(ren) menu as explained below.


Add your own dashboard menu item
--------------------------------

Assuming that you just want to append a new menu item to the dashboard, all
you have to do is open up (create if not present) your
``path/to/dashboard/app/navigation_menu.py``::

    from oscar.navigation_menu_registry import Menu, register_dashboard_menu

    register_dashboard_menu(
        Menu(
            label=_("Dashboard app's menu name"),
            url_name="dashboard:url-name",
            position=1,
        ),
    )

Add your own dashboard menu item with submenus
----------------------------------------------

Let's assume you would like to add a new item "Store Manager" with a submenu
item "Stores". The way you would do that is::

    from oscar.navigation_menu_registry import Menu, register_dashboard_menu

    register_dashboard_menu(
        Menu(label=_("Store manager")).add_child(
            Menu(
                label=_("Stores"),
                url_name="your-reverse-url-lookup-name",
            )
        ),
    )

That's it. You should now have *Store manager > Stores* in you dashboard
menu.

Submenus can also be registered from other apps using their parent menu ID
(which by default is the lowercase equivalent to the parent menu's label
with spaces replaced by ``_`` e.g. ``Parent menu`` label will by default
generate ``parent_menu`` as it's ID. An alternative ID can be specified
using the ``identifier`` kwarg) as follows:

``path/to/app-with-parent-menu/navigation_menu.py``::

    from oscar.navigation_menu_registry import Menu, register_dashboard_menu

    register_dashboard_menu(Menu(label=_("Store manager")))

``path/to/another-app-with-child-menu/navigation_menu.py``::

    from oscar.navigation_menu_registry import Menu, register_dashboard_menu

    register_dashboard_menu(
        Menu(
            label=_("Stores"),
            url_name="your-reverse-url-lookup-name",
        ),
        parent_id="store_manager",
    )

If you add to the navigation non-dashboard URLconf, you need to set
``access_fn`` parameter for the current node, so that Oscar is able to
resolve permissions to the current node::

    from oscar.navigation_menu_registry import Menu, register_dashboard_menu

    register_dashboard_menu(
        Menu(
            label=_("Admin site"),
            icon="fas fa-list",
            url_name="admin:index",
            access_fn=lambda user, url_name, url_args, url_kwargs: user.is_staff,
        ),
    )

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

    from oscar.navigation_menu_registry import Menu, register_dashboard_menu

    register_dashboard_menu(
        Menu(label=_("Store manager"), icon="fas fa-map-marker").add_child(
            Menu(
                label=_("Stores"),
                url_name="your-reverse-url-lookup-name",
            )
        ),
    )

You are not restricted to use `Font Awesome`_ icons for you menu heading. Other
web fonts will work as well as long as they support the same markup::

    <i class="icon-map-marker"></i>

The class is of the ``<i>`` is defined by the *icon* setting in the
configuration of your dashboard navigation above.


.. _`Font Awesome`: http://fortawesome.github.com/Font-Awesome/
.. _`this icon list`: http://fortawesome.github.com/Font-Awesome/#all-icons

Controlling menu positioning
----------------------------

By default the menu registry will auto generate a menu position for ``Menu`` objects
starting from value of ``OSCAR_DEFAULT_NAVIGATION_MENU_POSITION_INCREMENTER`` setting.
For example, the default setting's value of (``10``), will be used as ``Menu``
object's ``position`` in the registry if it had the default value of (``None``).

Subsequently registered menus will have the setting's value times the number of menu
items already present in the registry i.e. ``10``, ``20``, ``30``... which is dependent
on the order in which the apps with ``navigation_menu.py`` modules are installed in
Django's ``INSTALLED_APPS`` setting.

To override this default positioning behaviour, you can simply register a menu item as
with an explicitly set position as follows::

    from django.utils.translation import gettext_lazy as _

    from oscar.navigation_menu_registry import Menu, register_dashboard_menu

    # Assuming:
    #   1. you only have a single `navigation_menu.py` module in your entire project.
    #   2. `settings.OSCAR_DEFAULT_NAVIGATION_MENU_POSITION_INCREMENTER` = 10
    # the `3rd menu` will have an auto-generated position value of `10` where as the
    # `4th menu` will have an auto-generated position value of `20` with the rest
    # keeping there explicitly set positions.

    register_dashboard_menu(Menu(label=_("1st menu"), position=1))
    register_dashboard_menu(Menu(label=_("3rd menu")))
    register_dashboard_menu(Menu(label=_("4th menu")))
    register_dashboard_menu(Menu(label=_("2nd menu"), position=2))

Controlling visibility per user
-------------------------------

By setting ``'access_fn'`` for a node, you can specify a function that will
get called with the current user. The node will only be displayed if that
function returns ``True``.
If no ``'access_fn'`` is specified, ``OSCAR_DASHBOARD_DEFAULT_ACCESS_FUNCTION``
is used.
