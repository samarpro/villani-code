from app.pager import page_after

def test_resume_from_saved_cursor_keeps_next_item():
    page1 = page_after([1,2,3,4,5], None, 2)
    assert page1.items == [1,2]
    page2 = page_after([1,2,3,4,5], page1.next_cursor, 2)
    assert page2.items == [3,4]

def test_first_page_unchanged():
    page1 = page_after([1,2,3], None, 2)
    assert page1.items == [1,2]
    assert page1.next_cursor == 1
