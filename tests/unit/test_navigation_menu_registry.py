import pytest

from oscar.navigation_menu_registry import Menu


class TestMenu:
    def test_passing_children_as_kwarg_raises_error(self):
        with pytest.raises(ValueError):
            Menu("Menu title", identifier="id", children=None)

    def test_extra_kwargs_passed_to_menu_are_used_as_is_in_navigation_dict(self):
        access_fn = lambda user, url_name, url_args, url_kwargs: user.is_staff
        menu = Menu("Menu title", identifier="id", access_fn=access_fn)

        assert menu.as_navigation_dict() == {
            "label": "Menu title",
            "icon": None,
            "url_name": None,
            "access_fn": access_fn,
            "children": [],
        }

    def test_is_placeholder(self):
        assert Menu.placeholder("id").is_placeholder is True
        assert Menu(label="", identifier="id").is_placeholder is False
        assert Menu(label="Not placeholder", identifier="id").is_placeholder is False
        assert Menu(label="", icon="Not placeholder", identifier="id").is_placeholder is False
        menu = Menu.placeholder("id")
        menu.label = "Makes it non-placeholder"
        assert menu.is_placeholder is False

    def test_adding_duplicate_children_merges_the_duplicates(self):
        child_d1 = Menu("D1", identifier="d1")
        child_c1 = Menu("C1", identifier="c1")
        child_c2 = Menu("C2", identifier="c2")
        menu = Menu("Parent", identifier="parent").add_child(child_d1).add_child(child_d1).add_children(
            [child_c1, child_c1, child_c2])

        assert menu.children == [child_d1, child_c1, child_c2]
        assert len(child_d1.children) == 0
        child_d1_with_children = Menu(child_d1.label, identifier=child_d1.identifier).add_child(
            Menu(f"Child of {child_d1.label}", identifier="child_of_d1"))
        assert menu.add_child(child_d1_with_children).children == [child_d1_with_children, child_c1, child_c2]

    def test_adding_duplicate_child_menu_retains_later_declared_menus_position_if_not_none(self):
        parent = Menu("Parent", identifier="parent").add_child(
            Menu("Merge this with auto-positioning", identifier="m1")).add_child(
            Menu("Merge this without auto-positioning", identifier="m2", position=20))

        assert parent.children[0].position == 10
        assert parent.children[0].is_auto_positioned
        assert parent.children[1].position == 20
        assert parent.children[1].is_auto_positioned is False

        parent.add_child(Menu("Merge M1 using auto-position", identifier="m1"))
        assert parent.children[0].position == 10
        assert parent.children[0].is_auto_positioned

        parent.add_child(Menu("Merge M1", identifier="m1", position=1)).add_child(Menu("Merge M2", identifier="m2"))
        assert parent.children[0].position == 1
        assert parent.children[0].is_auto_positioned is False
        assert parent.children[1].position == 20
        assert parent.children[1].is_auto_positioned is False  # menu being merged was not auto-positioned

    def test_adding_non_duplicate_children(self):
        menu = Menu("Catalogue", "catalogue", "catalogue:index")
        assert len(menu.children) == 0

        products_submenu = Menu(label="Products", identifier="products", url_name="catalogue:products")
        menu.add_child(products_submenu)
        assert len(menu.children) == 1

        categories_submenu = Menu(label="Categories", identifier="categories", url_name="catalogue:categories")
        attributes_submenu = Menu(label="Attributes", identifier="attributes", url_name="catalogue:attributes")
        first_position_submenu = Menu(label="First position", identifier="first_position", url_name="catalogue:first",
                                      position=1)
        menu.add_child(categories_submenu).add_child(attributes_submenu).add_child(first_position_submenu)
        assert menu.children == [
            first_position_submenu,
            products_submenu,
            categories_submenu,
            attributes_submenu,
        ]

        first_of_first_submenu = Menu(label="FFP", identifier="ffp", url_name="catalogue:ff", position=0)
        menu.add_child(first_of_first_submenu)
        assert menu.children == [
            first_of_first_submenu,
            first_position_submenu,
            products_submenu,
            categories_submenu,
            attributes_submenu,
        ]
        copy_first_position_submenu = Menu(label="CFP", identifier="cfp", url_name="catalogue:cf", position=1)
        menu.add_child(copy_first_position_submenu)
        assert menu.children == [
            first_of_first_submenu,
            first_position_submenu,
            copy_first_position_submenu,
            products_submenu,
            categories_submenu,
            attributes_submenu,
        ]

    def test_as_navigation_dict(self):
        menu = Menu("Top level", "top_level", "index")
        assert menu.as_navigation_dict() == {
            "label": "Top level",
            "url_name": "index",
            "icon": None,
            "children": [],
        }

        child_menu = Menu("Child", "child", "child").add_child(Menu("Inner child", "inner_child", "inner-child"))
        menu.add_child(child_menu)
        assert menu.as_navigation_dict() == {
            "label": "Top level",
            "url_name": "index",
            "icon": None,
            "children": [
                {
                    "label": "Child",
                    "url_name": "child",
                    "icon": None,
                    "children": [
                        {
                            "label": "Inner child",
                            "url_name": "inner-child",
                            "icon": None,
                            "children": [],
                        }
                    ],
                },
            ],
        }

    def test_auto_positioned_has_lower_precedence_over_explicitly_positioned_menu_with_same_position(self):
        parent = Menu("Menu", identifier="menu").add_children(
            [Menu("3rd", identifier="3rd"), Menu("1st", identifier="1st", position=1),
             Menu("2nd", identifier="2nd", position=10)])
        assert [(menu.label, menu.position) for menu in parent.children] == [("1st", 1), ("2nd", 10), ("3rd", 10)]

    def test_remove_child(self):
        parent_menu = Menu("Parent", "parent", "parent-url-name").add_child(Menu("Child", "child", "child-url-name"))
        assert len(parent_menu.children) == 1

        parent_menu.remove_child("child")
        assert len(parent_menu.children) == 0

        with pytest.raises(ValueError):
            parent_menu.remove_child("unexisting_child")

    def test_merging_menus_with_different_identifiers_raises_exception(self):
        with pytest.raises(ValueError):
            Menu.placeholder("m1") + Menu("Menu 2", identifier="m2")

    def test_merge_menus(self):
        menu1_child = Menu.placeholder("cm1")
        menu1 = Menu.placeholder("m1").add_child(menu1_child)
        menu2 = Menu("Menu 2", identifier=menu1.identifier)

        assert (menu1 + menu2).as_navigation_dict() == {
            "label": "Menu 2",
            "url_name": None,
            "icon": None,
            "children": [
                menu1_child.as_navigation_dict(),
            ],
        }

    def test_children_menu_from_dict_has_auto_generated_position_if_non_was_explicitly_set(self):
        menu = Menu.from_dict(
            {
                "identifier": "menu",
                "label": "Menu",
                "url_name": None,
                "children": [
                    {"label": "Child 1", "identifier": "child_1", "url_name": None},
                    {"label": "Child 2", "identifier": "child_2", "url_name": None},
                    {"label": "Child 3", "identifier": "child_3", "url_name": None, "position": None},
                    {"label": "Child 4", "identifier": "child_4", "url_name": None, "position": 5},
                ],
            },
        )
        assert menu.children[0].label == "Child 4" and menu.children[0].position == 5 and menu.children[
            0].is_auto_positioned is False
        assert menu.children[1].label == "Child 1" and menu.children[1].position == 10 and menu.children[
            1].is_auto_positioned
        assert menu.children[2].label == "Child 2" and menu.children[2].position == 20 and menu.children[
            2].is_auto_positioned
        assert menu.children[3].label == "Child 3" and menu.children[3].position == 30 and menu.children[
            3].is_auto_positioned
