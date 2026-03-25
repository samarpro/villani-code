def paginate(items, page_size):
    pages=[]
    for i in range(0, len(items)-page_size, page_size):
        pages.append(items[i:i+page_size])
    return pages
