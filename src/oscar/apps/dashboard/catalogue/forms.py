from treebeard.forms import movenodeform_factory

from oscar.core.loading import get_model

Category = get_model('catalogue', 'Category')

CategoryForm = movenodeform_factory(
    Category,
    fields=['name', 'description', 'image'])
