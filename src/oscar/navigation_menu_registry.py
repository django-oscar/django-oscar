from collections import defaultdict
from importlib import import_module

from django.apps import apps
from django.conf import settings
from django.utils.module_loading import module_has_submodule

__all__ = [
    "get_dashboard_navigation_menu",
    "Menu",
    "get_legacy_parent_menu",
    "register_dashboard_menu",
    "unregister_dashboard_menu",
]


def _get_app_submodules(submodule_name):
    """
    Searches each app module for the specified submodule yields tuples of (app_name, module)
    """
    for app in apps.get_app_configs():
        if module_has_submodule(app.module, submodule_name):
            yield app.name, import_module(f"{app.name}.{submodule_name}")


class Menu:
    def __init__(self, label, url_name=None, icon=None, identifier=None, position=None, **kwargs):
        self.label = label
        self.url_name = url_name
        self.icon = icon
        self.identifier = identifier or label.lower().replace(" ", "_")
        self.position = position
        self._children = []
        if "children" in kwargs:
            raise ValueError("Children can be added to menu using `.add_child(...)` or `.add_children(...)` method")
        self._kwargs = kwargs
        self._auto_positioned = False

    def __lt__(self, other):
        if self.position is None:
            return other.position is not None
        elif other.position is None:
            return True
        elif self.position == other.position:
            return other.is_auto_positioned
        return self.position < other.position

    def __eq__(self, other):
        return self.identifier == other.identifier

    def __repr__(self):
        return f"Menu(id={self.identifier}, label={self.label})"

    def __hash__(self):
        return hash(self.identifier)

    def merge(self, other):
        """Assumes `other` should be overriding `self` hence it's given higher precedence"""
        if self != other:
            raise ValueError("Cannot merge menus with different identifiers")

        if self.children != other.children:
            other.add_children(self._children)

        if other.position is None:
            other.position = self.position
            if self.is_auto_positioned:
                other._auto_positioned = True
        return other

    __add__ = merge

    @classmethod
    def placeholder(cls, identifier):
        return cls(identifier=identifier, label="", url_name="", icon="")

    def auto_position_if_applicable(self, seed: int):
        if self.position is not None:
            return
        self.position = (seed + 1) * settings.OSCAR_DEFAULT_NAVIGATION_MENU_POSITION_INCREMENTER
        self._auto_positioned = True

    @property
    def is_auto_positioned(self):
        return self._auto_positioned

    @property
    def is_placeholder(self):
        return self.label == "" and self.url_name == "" and self.icon == ""

    @classmethod
    def from_dict(cls, _dict):
        """Should help ease migration process from menus declared through `settings.OSCAR_DASHBOARD_NAVIGATION`"""
        children = []
        for index, child_dict in enumerate(_dict.pop("children", [])):
            menu = cls.from_dict(child_dict)
            menu.auto_position_if_applicable(index)
            children.append(menu)
        menu = cls(**_dict)
        menu._children += children
        return menu

    @property
    def children(self):
        return sorted(self._children)

    def add_child(self, menu):
        """
        Add child to `self` with the extra advantage of:
         1. preserving the order of addition.
         2. merging `menu` to existing menu (with same identity).
        """
        for index, child in enumerate(self._children):
            if child == menu:
                self._children[index] = child + menu
                break
        else:
            menu.auto_position_if_applicable(len(self._children))
            self._children.append(menu)
        return self

    def add_children(self, children):
        for child in children:
            self.add_child(child)
        return self

    def remove_child(self, identifier):
        try:
            self._children.remove(self.placeholder(identifier))
        except ValueError:
            raise ValueError(f"Child menu with ID '{identifier}' not found for parent with ID '{self.identifier}'")
        return self

    def as_navigation_dict(self):
        return {
            "label": self.label,
            "url_name": self.url_name,
            "icon": self.icon,
            "children": [menu.as_navigation_dict() for menu in self.children],
            **self._kwargs,
        }


_dashboard_navigation_menu = defaultdict(Menu)
_marked_for_deregistration = set()


def get_legacy_parent_menu(lookup_label_or_index):
    """Should help ease migration process from menus declared through `settings.OSCAR_DASHBOARD_NAVIGATION`"""
    is_lookup_by_position = isinstance(lookup_label_or_index, int)
    if is_lookup_by_position:
        return settings.OSCAR_DASHBOARD_NAVIGATION[lookup_label_or_index]

    # parent menu is to be identified by label
    for index, parent_menu in enumerate(settings.OSCAR_DASHBOARD_NAVIGATION):
        if parent_menu["label"] == lookup_label_or_index:
            return parent_menu
    raise ValueError(
        f"Parent with {'position' if is_lookup_by_position else 'label'} '{lookup_label_or_index}' not found"
    )


def register_dashboard_menu(menu_or_function=None, parent_id=None):
    if menu_or_function is None:
        def decorator(decorated_function):
            register_dashboard_menu(decorated_function, parent_id)
            return decorated_function

        return decorator

    menu = menu_or_function() if callable(menu_or_function) else menu_or_function
    if menu is None:
        return

    if isinstance(menu, dict):
        menu = Menu.from_dict(menu)

    if parent_id is None:
        try:
            _dashboard_navigation_menu[menu.identifier] += menu
        except TypeError:
            # `defaultdict` tried to instantiate a default Menu object but could not because
            # 'label' positional argument is required
            menu.auto_position_if_applicable(len(_dashboard_navigation_menu))
            _dashboard_navigation_menu[menu.identifier] = menu
    else:
        # Placeholder instance will be used temporarily if child (menu) was registered ahead of
        # its parent. It will be replaced (merged) into the actual parent once it's registered.
        _dashboard_navigation_menu.setdefault(parent_id, Menu.placeholder(parent_id)).add_child(
            menu).auto_position_if_applicable(len(_dashboard_navigation_menu))


def unregister_dashboard_menu(parent_id, child_id=None):
    _marked_for_deregistration.add((parent_id, child_id))


_search_for_dashboard_navigation_menu = False


def get_dashboard_navigation_menu():
    global _search_for_dashboard_navigation_menu
    if not _search_for_dashboard_navigation_menu:
        list(_get_app_submodules("navigation_menu"))
        _search_for_dashboard_navigation_menu = True

    for parent_id, child_id in _marked_for_deregistration:
        if child_id is not None:
            parent_menu = _dashboard_navigation_menu.get(parent_id)
            if parent_menu:
                _dashboard_navigation_menu[parent_id] = parent_menu.remove_child(child_id)
            else:
                raise ValueError(f"Parent menu with the ID '{parent_id}' does not exist")
        else:
            del _dashboard_navigation_menu[parent_id]

    navigation_menu, placeholder_menu = [], set()
    for menu in sorted(_dashboard_navigation_menu.values()):
        if menu.is_placeholder:
            placeholder_menu.add(menu)
        else:
            navigation_menu.append(menu.as_navigation_dict())

    if placeholder_menu:
        raise ReferenceError("Pending placeholder menus detected", placeholder_menu)

    return navigation_menu
