def paginate(items, page_size):
    return [items[i:i+page_size] for i in range(0, len(items), page_size)]
