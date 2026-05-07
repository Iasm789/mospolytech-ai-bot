from handlers.navigation import BACK_TEXT, get_main_menu_keyboard, get_student_menu_keyboard


def test_main_menu_keyboard_has_three_rows():
    keyboard = get_main_menu_keyboard()
    assert len(keyboard.keyboard) == 3


def test_student_menu_contains_back_button():
    keyboard = get_student_menu_keyboard()
    flat_labels = [button.text for row in keyboard.keyboard for button in row]
    assert BACK_TEXT in flat_labels
