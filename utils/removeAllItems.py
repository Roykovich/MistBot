def remove_all_items(view):
    for item in view.children:
        view.remove_item(item)