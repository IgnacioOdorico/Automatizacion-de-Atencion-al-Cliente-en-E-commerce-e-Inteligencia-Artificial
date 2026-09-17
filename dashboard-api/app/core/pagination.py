PAGE_SIZE = 20


def paginated(items: list[dict], total: int, page: int) -> dict:
    total_pages = (total + PAGE_SIZE - 1) // PAGE_SIZE if total else 0
    return {
        "items": items,
        "page": page,
        "page_size": PAGE_SIZE,
        "total": total,
        "total_pages": total_pages,
    }