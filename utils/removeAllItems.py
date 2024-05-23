def remove_all_items(view):
    if view is not None:
        for item in view.children:
            view.remove_item(item)