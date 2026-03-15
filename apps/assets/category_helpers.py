from .models import Category

def get_category_tree():
    """Return a list of root categories with their children prefetched."""
    return Category.objects.filter(parent__isnull=True).prefetch_related('children')

def get_all_descendants(category):
    """Return a queryset of all descendant categories (including self)."""
    descendants = [category]
    for child in category.children.all():
        descendants.extend(get_all_descendants(child))
    return descendants

def build_category_hierarchy(categories=None, level=0):
    """
    Build a nested dictionary representation of category hierarchy.
    Useful for rendering in templates.
    """
    if categories is None:
        categories = Category.objects.filter(parent__isnull=True).prefetch_related('children')

    hierarchy = []
    for cat in categories:
        node = {
            'id': cat.id,
            'name': cat.name,
            'children': build_category_hierarchy(cat.children.all(), level+1)
        }
        hierarchy.append(node)
    return hierarchy