from handlers import question_handler


def test_find_answer_prefers_best_keyword_match():
    question_handler.faq_data = {
        "faq": [
            {
                "id": 1,
                "question": "Как получить стипендию?",
                "answer": "Ответ про стипендию",
                "keywords": ["стипендия", "социальная стипендия"],
            },
            {
                "id": 2,
                "question": "Как получить общежитие?",
                "answer": "Ответ про общежитие",
                "keywords": ["общежитие", "заселение"],
            },
        ]
    }

    result = question_handler.find_answer("Как оформить социальную стипендию?")

    assert result is not None
    assert result["id"] == 1


def test_find_answer_handles_typo_with_fuzzy_scoring():
    question_handler.faq_data = {
        "faq": [
            {
                "id": 10,
                "question": "Где посмотреть расписание занятий?",
                "answer": "Ответ про расписание",
                "keywords": ["расписание", "пары"],
            }
        ]
    }

    result = question_handler.find_answer("где пасматреть расписание занатий")

    assert result is not None
    assert result["id"] == 10


def test_find_answer_returns_none_when_nothing_relevant():
    question_handler.faq_data = {
        "faq": [
            {
                "id": 20,
                "question": "Как получить справку?",
                "answer": "Ответ про справку",
                "keywords": ["справка", "документы"],
            }
        ]
    }

    result = question_handler.find_answer("какая сегодня погода в москве")

    assert result is None


def test_find_answer_handles_colloquial_synonyms():
    question_handler.faq_data = {
        "faq": [
            {
                "id": 30,
                "question": "Как получить место в общежитии?",
                "answer": "Ответ про общежитие",
                "keywords": ["общежитие", "заселение"],
            }
        ]
    }

    result = question_handler.find_answer("как попасть в общагу первокурснику")

    assert result is not None
    assert result["id"] == 30


def test_find_answer_handles_word_forms():
    question_handler.faq_data = {
        "faq": [
            {
                "id": 40,
                "question": "Социальная стипендия: условия получения",
                "answer": "Ответ про социальную стипендию",
                "keywords": ["стипендия", "социальная стипендия"],
            }
        ]
    }

    result = question_handler.find_answer("как получить стипу в этом семестре")

    assert result is not None
    assert result["id"] == 40


def test_find_answer_avoids_wrong_topic_match():
    question_handler.faq_data = {
        "faq": [
            {
                "id": 50,
                "question": "Какие факультеты и институты есть в вузе?",
                "answer": "Ответ про структуру вуза",
                "keywords": ["факультет", "институт", "вуз"],
            },
            {
                "id": 51,
                "question": "Как заселиться в общежитие?",
                "answer": "Ответ про заселение в общежитие",
                "keywords": ["общежитие", "заселение"],
            },
        ]
    }

    result = question_handler.find_answer("Как заселиться в общежитие?")

    assert result is not None
    assert result["id"] == 51


def test_find_answer_returns_none_on_cross_domain_only():
    question_handler.faq_data = {
        "faq": [
            {
                "id": 60,
                "question": "Какие факультеты и институты есть в вузе?",
                "answer": "Ответ про структуру вуза",
                "keywords": ["факультет", "институт", "вуз"],
            }
        ]
    }

    result = question_handler.find_answer("Как заселиться в общежитие?")

    assert result is None


def test_find_answer_returns_none_for_math_question():
    question_handler.faq_data = {
        "faq": [
            {
                "id": 70,
                "question": "Когда студенты начинают работать над проектами от компаний?",
                "answer": "С первого курса идет погружение, со второго - работа с компаниями.",
                "keywords": ["проекты", "2 курс", "компании"],
            }
        ]
    }

    result = question_handler.find_answer("2+2 сколько будет?")

    assert result is None


def test_is_obvious_offtopic_detects_math_and_weather():
    assert question_handler.is_obvious_offtopic("2+2")
    assert question_handler.is_obvious_offtopic("Какая погода завтра?")


def test_is_obvious_offtopic_ignores_domain_question():
    assert not question_handler.is_obvious_offtopic("Как получить социальную стипендию?")


def test_is_obvious_offtopic_allows_edu_math_context():
    assert not question_handler.is_obvious_offtopic("Сколько нужно баллов ЕГЭ на бюджет?")
    assert not question_handler.is_obvious_offtopic("Проходной балл: 240+10, хватит для поступления?")


def test_medical_question_not_covered_by_financial_aid_faq():
    answer_item = {
        "question": "Как оформить материальную помощь через профсоюз?",
        "answer": "Члены профсоюза могут получать выплаты при подаче заявления.",
        "keywords": ["профсоюз", "материальная помощь", "выплаты"],
    }
    assert not question_handler.is_faq_answer_covered(
        "Расскажи про медицинскую помощь студентам",
        answer_item,
    )
