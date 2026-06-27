"""Generate a PPTX presentation for the diploma defense (6-7 min).

Requirements based on university guidelines:
- Light background, dark text (avoid reverse contrast for large areas)
- Max 50 words per slide, 6-8 lines, 6-8 words per line
- Font >= 16pt, sans-serif (Arial)
- Max 3 colors per slide (background, headings, text)
- Slide numbers bottom-right
- No decorative elements (logos, background images = spam)
- Structure: title → motivation → object/subject/goal → content → conclusions
"""

import os
from pptx import Presentation
from pptx.util import Pt, Emu, Cm
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

OUTPUT_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "docs",
    "Бухінський_ВА_презентація.pptx",
)
DIAGRAMS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "docs", "diagrams",
)

BG_WHITE = RGBColor(0xFF, 0xFF, 0xFF)
TEXT_DARK = RGBColor(0x22, 0x22, 0x22)
HEADING_RED = RGBColor(0xC0, 0x00, 0x00)
GRAY_SUB = RGBColor(0x55, 0x55, 0x55)
CARD_BG = RGBColor(0xF2, 0xF4, 0xF8)

SLIDE_W = Emu(12192000)
SLIDE_H = Emu(6858000)


def set_slide_bg(slide, color=BG_WHITE):
    bg = slide.background
    fill = bg.fill
    fill.solid()
    fill.fore_color.rgb = color


def add_text_box(slide, left, top, width, height, text, font_size=18,
                 bold=False, color=TEXT_DARK, alignment=PP_ALIGN.LEFT,
                 font_name="Arial", line_spacing=1.3):
    txBox = slide.shapes.add_textbox(left, top, width, height)
    tf = txBox.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = text
    p.font.size = Pt(font_size)
    p.font.bold = bold
    p.font.color.rgb = color
    p.font.name = font_name
    p.alignment = alignment
    p.line_spacing = line_spacing
    return txBox


def add_multiline(slide, left, top, width, height, lines, font_size=18,
                  color=TEXT_DARK, bullet=False, line_spacing=1.5,
                  font_name="Arial", bold=False, alignment=PP_ALIGN.LEFT):
    txBox = slide.shapes.add_textbox(left, top, width, height)
    tf = txBox.text_frame
    tf.word_wrap = True
    for i, line in enumerate(lines):
        if i == 0:
            p = tf.paragraphs[0]
        else:
            p = tf.add_paragraph()
        p.text = ("• " + line) if bullet else line
        p.font.size = Pt(font_size)
        p.font.color.rgb = color
        p.font.name = font_name
        p.font.bold = bold
        p.alignment = alignment
        p.line_spacing = line_spacing
        p.space_after = Pt(4)
    return txBox


def add_rich_paragraph(slide, left, top, width, height, segments,
                       font_size=18, font_name="Arial", line_spacing=1.3,
                       alignment=PP_ALIGN.LEFT):
    txBox = slide.shapes.add_textbox(left, top, width, height)
    tf = txBox.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.alignment = alignment
    p.line_spacing = line_spacing
    for text, bold, color in segments:
        run = p.add_run()
        run.text = text
        run.font.size = Pt(font_size)
        run.font.bold = bold
        run.font.name = font_name
        run.font.color.rgb = color
    return txBox


def add_slide_number(slide, number):
    add_text_box(slide, Cm(23), Cm(17.2), Cm(2), Cm(0.8),
                 str(number), font_size=14, color=GRAY_SUB,
                 alignment=PP_ALIGN.RIGHT)


def add_card(slide, left, top, width, height, title, body_lines,
             title_color=HEADING_RED, body_color=TEXT_DARK):
    shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,
                                   left, top, width, height)
    shape.fill.solid()
    shape.fill.fore_color.rgb = CARD_BG
    shape.line.fill.background()
    shape.shadow.inherit = False

    add_text_box(slide, left + Cm(0.6), top + Cm(0.4),
                 width - Cm(1.2), Cm(1),
                 title, font_size=16, bold=True, color=title_color)
    add_multiline(slide, left + Cm(0.6), top + Cm(1.5),
                  width - Cm(1.2), height - Cm(2),
                  body_lines, font_size=14, color=body_color,
                  line_spacing=1.3)


def create_presentation():
    prs = Presentation()
    prs.slide_width = SLIDE_W
    prs.slide_height = SLIDE_H
    blank_layout = prs.slide_layouts[6]

    # ═══════════════════════════════════════════════════════════════════
    # SLIDE 1: Title
    # ═══════════════════════════════════════════════════════════════════
    slide = prs.slides.add_slide(blank_layout)
    set_slide_bg(slide)

    add_multiline(slide, Cm(2), Cm(1), Cm(22), Cm(2), [
        "Чернівецький національний університет імені Юрія Федьковича",
        "Кафедра комп'ютерних систем та мереж",
    ], font_size=16, color=TEXT_DARK, line_spacing=1.4,
       alignment=PP_ALIGN.CENTER)

    add_text_box(slide, Cm(2), Cm(4), Cm(22), Cm(1),
                 "Бакалаврська робота на тему:",
                 font_size=18, color=HEADING_RED,
                 alignment=PP_ALIGN.CENTER)

    add_text_box(slide, Cm(2), Cm(5.5), Cm(22), Cm(4),
                 "Агентна система обробки\nта виконання команд\nкерування комп'ютером",
                 font_size=32, bold=True, color=HEADING_RED,
                 alignment=PP_ALIGN.CENTER, line_spacing=1.2)

    add_multiline(slide, Cm(2), Cm(10.5), Cm(22), Cm(3), [
        "Спеціальність: Комп'ютерна інженерія",
        "ОПП: Комп'ютерна інженерія",
    ], font_size=16, color=TEXT_DARK, line_spacing=1.5,
       alignment=PP_ALIGN.CENTER)

    add_text_box(slide, Cm(2), Cm(13), Cm(22), Cm(1),
                 "Бухінський Владислав Андрійович",
                 font_size=18, bold=True, color=TEXT_DARK,
                 alignment=PP_ALIGN.CENTER)

    add_text_box(slide, Cm(2), Cm(14.5), Cm(22), Cm(1),
                 "Науковий керівник — д.т.н., доц. Воробець О. І.",
                 font_size=16, bold=True, color=HEADING_RED,
                 alignment=PP_ALIGN.CENTER)

    add_text_box(slide, Cm(2), Cm(16.2), Cm(22), Cm(1),
                 "Чернівці, 2026",
                 font_size=16, color=TEXT_DARK,
                 alignment=PP_ALIGN.CENTER)

    add_slide_number(slide, 1)

    # ═══════════════════════════════════════════════════════════════════
    # SLIDE 2: Агентні системи
    # ═══════════════════════════════════════════════════════════════════
    slide = prs.slides.add_slide(blank_layout)
    set_slide_bg(slide)

    add_text_box(slide, Cm(2), Cm(1.2), Cm(22), Cm(1.5),
                 "Агентні системи",
                 font_size=28, bold=True, color=HEADING_RED,
                 alignment=PP_ALIGN.CENTER)

    add_rich_paragraph(slide, Cm(2), Cm(3.5), Cm(22), Cm(3), [
        ("Агентна система", True, HEADING_RED),
        (" — програмний комплекс, де автономний AI-агент "
         "сприймає середовище, приймає рішення та виконує "
         "дії для досягнення заданої мети.", False, TEXT_DARK),
    ], font_size=20, line_spacing=1.4)

    add_text_box(slide, Cm(2), Cm(7), Cm(22), Cm(2),
                 "Відмінність від чат-ботів:",
                 font_size=18, bold=True, color=HEADING_RED)

    add_multiline(slide, Cm(2), Cm(8.5), Cm(22), Cm(6), [
        "Чат-бот генерує текстову відповідь",
        "AI-агент виконує реальні дії на комп'ютері",
        "Агент працює в циклі: планує → діє → спостерігає",
        "Кожен крок базується на результатах попереднього",
    ], font_size=18, color=TEXT_DARK, bullet=True, line_spacing=1.7)

    add_text_box(slide, Cm(2), Cm(14.5), Cm(22), Cm(2),
                 "Приклади: AutoGPT, LangChain Agents, Claude Computer Use",
                 font_size=16, color=GRAY_SUB,
                 alignment=PP_ALIGN.CENTER)

    add_slide_number(slide, 2)

    # ═══════════════════════════════════════════════════════════════════
    # SLIDE 3: Актуальність
    # ═══════════════════════════════════════════════════════════════════
    slide = prs.slides.add_slide(blank_layout)
    set_slide_bg(slide)

    add_text_box(slide, Cm(2), Cm(1.2), Cm(22), Cm(1.5),
                 "Актуальність теми",
                 font_size=28, bold=True, color=HEADING_RED,
                 alignment=PP_ALIGN.CENTER)

    add_text_box(slide, Cm(2), Cm(3.5), Cm(22), Cm(12),
                 "Керування комп'ютером вимагає від користувача "
                 "технічних знань: команд терміналу, роботи з API, "
                 "написання скриптів. Існуючі AI-асистенти (ChatGPT, "
                 "Google Assistant) відповідають текстом, але не "
                 "виконують реальних дій на комп'ютері користувача.\n\n"
                 "Водночас виникають ризики безпеки: витік даних "
                 "при взаємодії з хмарними LLM та відсутність "
                 "контролю над діями AI-агента.\n\n"
                 "Тому розробка агентної системи, яка виконує реальні "
                 "дії на ПК під контролем користувача із захистом "
                 "персональних даних, є актуальною задачею.",
                 font_size=18, color=TEXT_DARK,
                 alignment=PP_ALIGN.JUSTIFY, line_spacing=1.4)

    add_slide_number(slide, 3)

    # ═══════════════════════════════════════════════════════════════════
    # SLIDE 4: Об'єкт / Предмет / Мета
    # ═══════════════════════════════════════════════════════════════════
    slide = prs.slides.add_slide(blank_layout)
    set_slide_bg(slide)

    y = Cm(2)

    add_rich_paragraph(slide, Cm(2), y, Cm(22), Cm(2.5), [
        ("Об'єктом дослідження", True, HEADING_RED),
        (" є процес обробки та виконання команд "
         "керування комп'ютером засобами агентних систем "
         "на основі великих мовних моделей.", False, TEXT_DARK),
    ], font_size=20, line_spacing=1.4)

    y = Cm(5.5)
    add_rich_paragraph(slide, Cm(2), y, Cm(22), Cm(2.5), [
        ("Предметом дослідження", True, HEADING_RED),
        (" є програмна система на базі фреймворку PydanticAI "
         "для інтерпретації команд природною мовою та їх "
         "безпечного виконання на ПК.", False, TEXT_DARK),
    ], font_size=20, line_spacing=1.4)

    y = Cm(9.5)
    add_rich_paragraph(slide, Cm(2), y, Cm(22), Cm(3), [
        ("Мета роботи: ", True, HEADING_RED),
        ("розробка, програмна реалізація та тестування "
         "агентної системи обробки та виконання команд "
         "керування комп'ютером з використанням ReAct-циклу, "
         "трирівневої моделі безпеки та графічного інтерфейсу.",
         False, TEXT_DARK),
    ], font_size=20, line_spacing=1.4)

    add_slide_number(slide, 4)

    # ═══════════════════════════════════════════════════════════════════
    # SLIDE 5: Architecture — ReAct
    # ═══════════════════════════════════════════════════════════════════
    slide = prs.slides.add_slide(blank_layout)
    set_slide_bg(slide)

    add_text_box(slide, Cm(2), Cm(1.2), Cm(22), Cm(1.5),
                 "Архітектура системи: ReAct-цикл",
                 font_size=28, bold=True, color=HEADING_RED,
                 alignment=PP_ALIGN.CENTER)

    add_text_box(slide, Cm(2), Cm(3.2), Cm(22), Cm(1.5),
                 "ReAct (Reasoning + Acting) — ітеративний метод, "
                 "де LLM планує та виконує дії покроково:",
                 font_size=16, color=GRAY_SUB,
                 alignment=PP_ALIGN.CENTER)

    steps = [
        ("1. Запит", "Користувач вводить\nзавдання природною\nмовою"),
        ("2. Think", "LLM аналізує запит\nта планує один\nнаступний крок"),
        ("3. Act", "Виконання дії після\nпідтвердження\nкористувачем (HITL)"),
        ("4. Observe", "Результат → LLM\nдля вибору\nнаступного кроку"),
    ]

    positions = [Cm(1), Cm(7), Cm(13), Cm(19)]
    for (title, body), left in zip(steps, positions):
        shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,
                                       left, Cm(5.5), Cm(5.5), Cm(5))
        shape.fill.solid()
        shape.fill.fore_color.rgb = CARD_BG
        shape.line.fill.background()

        add_text_box(slide, left + Cm(0.4), Cm(6), Cm(4.7), Cm(1),
                     title, font_size=16, bold=True, color=HEADING_RED)
        add_text_box(slide, left + Cm(0.4), Cm(7.5), Cm(4.7), Cm(2.8),
                     body, font_size=14, color=TEXT_DARK, line_spacing=1.3)

    for x in [Cm(6.5), Cm(12.5), Cm(18.5)]:
        add_text_box(slide, x, Cm(7.3), Cm(1), Cm(1), "→",
                     font_size=28, color=HEADING_RED,
                     alignment=PP_ALIGN.CENTER)

    add_text_box(slide, Cm(4), Cm(11.5), Cm(18), Cm(1.5),
                 "Цикл повторюється поки завдання не виконано "
                 "або LLM не поверне фінальну відповідь",
                 font_size=16, color=GRAY_SUB, alignment=PP_ALIGN.CENTER)

    add_text_box(slide, Cm(2), Cm(13.5), Cm(22), Cm(2),
                 "Перевага: кожен крок базується на реальних "
                 "результатах попередніх, а не на припущеннях моделі",
                 font_size=16, bold=True, color=TEXT_DARK,
                 alignment=PP_ALIGN.CENTER, line_spacing=1.3)

    add_slide_number(slide, 5)

    # ═══════════════════════════════════════════════════════════════════
    # SLIDE 6: Tech Stack
    # ═══════════════════════════════════════════════════════════════════
    slide = prs.slides.add_slide(blank_layout)
    set_slide_bg(slide)

    add_text_box(slide, Cm(2), Cm(1.2), Cm(22), Cm(1.5),
                 "Технологічний стек",
                 font_size=28, bold=True, color=HEADING_RED,
                 alignment=PP_ALIGN.CENTER)

    cards = [
        (Cm(1), Cm(3.5), "Backend",
         ["Python 3.12", "FastAPI + Uvicorn",
          "PydanticAI 1.63", "Pydantic v2", "MCP SDK"]),
        (Cm(9), Cm(3.5), "Frontend",
         ["PySide6 (Qt6)", "PyInstaller",
          "SVG-іконки"]),
        (Cm(17), Cm(3.5), "Сховище даних",
         ["SQLite", "ChromaDB", "JSON-файли"]),
        (Cm(1), Cm(9.5), "AI / LLM",
         ["Google Gemini", "OpenAI", "Anthropic", "Ollama"]),
        (Cm(9), Cm(9.5), "Зовнішні сервіси",
         ["DuckDuckGo Search", "httpx", "Logfire"]),
        (Cm(17), Cm(9.5), "Обсяг проєкту",
         ["~8300 рядків Python", "16 типів дій",
          "21 тестовий сценарій"]),
    ]

    for left, top, title, lines in cards:
        add_card(slide, left, top, Cm(7.5), Cm(5.3), title, lines)

    add_slide_number(slide, 6)

    # ═══════════════════════════════════════════════════════════════════
    # SLIDE 7: Security
    # ═══════════════════════════════════════════════════════════════════
    slide = prs.slides.add_slide(blank_layout)
    set_slide_bg(slide)

    add_text_box(slide, Cm(2), Cm(1.2), Cm(22), Cm(1.5),
                 "Трирівнева модель безпеки",
                 font_size=28, bold=True, color=HEADING_RED,
                 alignment=PP_ALIGN.CENTER)

    layers = [
        ("1. PrivacyGuard",
         "Маскування персональних даних перед відправкою до LLM",
         "12 regex-патернів (email, картки, токени) + ентропійне сканування"),
        ("2. Whitelist",
         "Валідація кожної дії проти білого списку",
         "Перевірка на рівні Pydantic-моделі — заборонена дія не створюється"),
        ("3. Human-in-the-Loop",
         "Підтвердження кожного кроку користувачем",
         "Користувач бачить що буде виконано і може скасувати"),
    ]

    for title, line1, line2, top in zip(
        [l[0] for l in layers],
        [l[1] for l in layers],
        [l[2] for l in layers],
        [Cm(3.5), Cm(7.5), Cm(11.5)]
    ):
        shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,
                                       Cm(2), top, Cm(22), Cm(3.5))
        shape.fill.solid()
        shape.fill.fore_color.rgb = CARD_BG
        shape.line.fill.background()

        add_text_box(slide, Cm(3), top + Cm(0.3), Cm(20), Cm(1),
                     title, font_size=20, bold=True, color=HEADING_RED)
        add_text_box(slide, Cm(3), top + Cm(1.3), Cm(20), Cm(1),
                     line1, font_size=16, bold=True, color=TEXT_DARK)
        add_text_box(slide, Cm(3), top + Cm(2.2), Cm(20), Cm(1),
                     line2, font_size=14, color=GRAY_SUB)

    add_slide_number(slide, 7)

    # ═══════════════════════════════════════════════════════════════════
    # SLIDE 8: Features — 16 action types
    # ═══════════════════════════════════════════════════════════════════
    slide = prs.slides.add_slide(blank_layout)
    set_slide_bg(slide)

    add_text_box(slide, Cm(2), Cm(1.2), Cm(22), Cm(1.5),
                 "Реєстр інструментів: 16 типів дій",
                 font_size=28, bold=True, color=HEADING_RED,
                 alignment=PP_ALIGN.CENTER)

    col1 = [
        "open_app — відкриття застосунків",
        "run_command — термінальні команди",
        "write_file / read_file — файли",
        "web_search — пошук в інтернеті",
        "web_read — читання веб-сторінок",
        "http_request — виклик API",
        "system_control — гучність, скріншот",
        "mcp_call — зовнішні MCP-інструменти",
    ]
    col2 = [
        "save_recipe — збереження рецептів",
        "run_recipe — запуск рецептів",
        "list_recipes — перегляд рецептів",
        "search_knowledge — RAG-пошук",
        "index_knowledge — індексація",
        "image_search — пошук зображень",
        "chat — текстова відповідь",
    ]

    add_multiline(slide, Cm(1), Cm(3.5), Cm(12.5), Cm(13),
                  col1, font_size=14, color=TEXT_DARK,
                  bullet=True, line_spacing=1.6)
    add_multiline(slide, Cm(13), Cm(3.5), Cm(12.5), Cm(13),
                  col2, font_size=14, color=TEXT_DARK,
                  bullet=True, line_spacing=1.6)

    add_text_box(slide, Cm(2), Cm(15), Cm(22), Cm(1.5),
                 "Реєстр розширюється через MCP (Model Context Protocol) — "
                 "підключення зовнішніх інструментів без зміни коду",
                 font_size=15, color=GRAY_SUB,
                 alignment=PP_ALIGN.CENTER)

    add_slide_number(slide, 8)

    # ═══════════════════════════════════════════════════════════════════
    # SLIDE 9: GUI
    # ═══════════════════════════════════════════════════════════════════
    slide = prs.slides.add_slide(blank_layout)
    set_slide_bg(slide)

    add_text_box(slide, Cm(2), Cm(1.2), Cm(22), Cm(1.5),
                 "Графічний інтерфейс користувача",
                 font_size=28, bold=True, color=HEADING_RED,
                 alignment=PP_ALIGN.CENTER)

    add_multiline(slide, Cm(2), Cm(3.5), Cm(11), Cm(10), [
        "Floating always-on-top вікно",
        "Тамагочі-персонаж із емоціями",
        "Відображення зображень у чаті",
        "Markdown-рендеринг відповідей",
        "Панель рецептів та налаштувань",
        "Log-панель для діагностики",
        "System tray (hide / show / quit)",
    ], font_size=18, color=TEXT_DARK, bullet=True, line_spacing=1.7)

    add_card(slide, Cm(14), Cm(3.5), Cm(10), Cm(7),
             "Технічні деталі",
             ["PySide6 (Qt6 for Python)",
              "QThread для async-запитів",
              "Signals / Slots архітектура",
              "SVG-іконки, кастомні шрифти",
              "PyInstaller → .app / .exe / ELF"])

    add_text_box(slide, Cm(2), Cm(12.5), Cm(22), Cm(2),
                 "[Місце для скріншоту інтерфейсу]",
                 font_size=14, color=GRAY_SUB,
                 alignment=PP_ALIGN.CENTER)

    add_slide_number(slide, 9)

    # ═══════════════════════════════════════════════════════════════════
    # SLIDE 10: Recipes + RAG
    # ═══════════════════════════════════════════════════════════════════
    slide = prs.slides.add_slide(blank_layout)
    set_slide_bg(slide)

    add_text_box(slide, Cm(2), Cm(1.2), Cm(22), Cm(1.5),
                 "Рецепти та локальна база знань",
                 font_size=28, bold=True, color=HEADING_RED,
                 alignment=PP_ALIGN.CENTER)

    add_multiline(slide, Cm(2), Cm(3.5), Cm(11), Cm(6), [
        "Рецепт — збережена послідовність дій",
        "Створення через LLM або вручну",
        "JSON-формат із requirements",
        "Запуск одним кліком або голосом",
        "Валідація перед виконанням",
    ], font_size=18, color=TEXT_DARK, bullet=True, line_spacing=1.6)

    add_card(slide, Cm(14), Cm(3.5), Cm(10), Cm(5.5),
             "Приклад: «Робочий ранок»",
             ["1. open_app → Discord",
              "2. open_app → Safari",
              "3. run_command → Notion",
              "REST API: GET/POST /recipes"])

    add_text_box(slide, Cm(2), Cm(10.5), Cm(22), Cm(1),
                 "Локальна база знань (RAG)",
                 font_size=20, bold=True, color=HEADING_RED)

    add_multiline(slide, Cm(2), Cm(12), Cm(22), Cm(4), [
        "ChromaDB — векторне сховище для документів",
        "index_knowledge — індексація файлів із розбиттям на чанки",
        "search_knowledge — семантичний пошук за запитом користувача",
    ], font_size=16, color=TEXT_DARK, bullet=True, line_spacing=1.5)

    add_slide_number(slide, 10)

    # ═══════════════════════════════════════════════════════════════════
    # DIAGRAM SLIDES (11-15)
    # ═══════════════════════════════════════════════════════════════════
    diagrams = [
        ("Діаграма прецедентів", "fig_2_1_use_case.png"),
        ("Діаграма компонентів системи", "fig_2_2_components.png"),
        ("Діаграма діяльності (ReAct-цикл)", "fig_2_3_activity.png"),
        ("Діаграма інтеракцій (послідовності)", "fig_2_4_sequence.png"),
        ("Діаграма класів ядра системи", "fig_3_1_classes.png"),
    ]

    MAX_IMG_W = Cm(28)
    MAX_IMG_H = Cm(14.5)
    IMG_TOP = Cm(3.2)
    SLIDE_CENTER_X = SLIDE_W // 2

    for idx, (title, filename) in enumerate(diagrams):
        slide = prs.slides.add_slide(blank_layout)
        set_slide_bg(slide)

        add_text_box(slide, Cm(2), Cm(0.8), Cm(22), Cm(1.5),
                     title,
                     font_size=26, bold=True, color=HEADING_RED,
                     alignment=PP_ALIGN.CENTER)

        img_path = os.path.join(DIAGRAMS_DIR, filename)
        from PIL import Image as PILImage
        with PILImage.open(img_path) as im:
            iw, ih = im.size
        ratio = iw / ih

        if ratio >= 1:
            w = MAX_IMG_W
            h = int(w / ratio)
            if h > MAX_IMG_H:
                h = MAX_IMG_H
                w = int(h * ratio)
        else:
            h = MAX_IMG_H
            w = int(h * ratio)
            if w > MAX_IMG_W:
                w = MAX_IMG_W
                h = int(w / ratio)

        left = (SLIDE_W - w) // 2
        slide.shapes.add_picture(img_path, left, IMG_TOP, w, h)

        add_slide_number(slide, 11 + idx)

    # ═══════════════════════════════════════════════════════════════════
    # SLIDE 15: Testing
    # ═══════════════════════════════════════════════════════════════════
    slide = prs.slides.add_slide(blank_layout)
    set_slide_bg(slide)

    add_text_box(slide, Cm(2), Cm(1.2), Cm(22), Cm(1.5),
                 "Тестування системи",
                 font_size=28, bold=True, color=HEADING_RED,
                 alignment=PP_ALIGN.CENTER)

    add_text_box(slide, Cm(2), Cm(3.5), Cm(22), Cm(1.5),
                 "Протестовано 21 сценарій у 5 категоріях. "
                 "Усі сценарії пройдено.",
                 font_size=18, color=TEXT_DARK,
                 alignment=PP_ALIGN.CENTER)

    categories = [
        ("Керування додатками", "open_app, run_command — 4 сценарії"),
        ("Робота з файлами", "write_file, read_file — 3 сценарії"),
        ("Веб-інтеграція", "web_search, web_read, http_request — 4 сценарії"),
        ("Безпека", "PrivacyGuard, Whitelist, HITL — 5 сценаріїв"),
        ("Комплексні задачі", "ReAct-цикл із 3+ кроків — 5 сценаріїв"),
    ]

    for i, (cat, desc) in enumerate(categories):
        top = Cm(5.5) + Cm(2.2) * i
        shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,
                                       Cm(2), top, Cm(22), Cm(1.9))
        shape.fill.solid()
        shape.fill.fore_color.rgb = CARD_BG
        shape.line.fill.background()

        add_text_box(slide, Cm(3), top + Cm(0.2), Cm(9), Cm(1),
                     cat, font_size=16, bold=True, color=HEADING_RED)
        add_text_box(slide, Cm(12), top + Cm(0.2), Cm(11), Cm(1),
                     desc, font_size=15, color=TEXT_DARK)

    add_slide_number(slide, 16)

    # ═══════════════════════════════════════════════════════════════════
    # SLIDE 17: Video Demo
    # ═══════════════════════════════════════════════════════════════════
    slide = prs.slides.add_slide(blank_layout)
    set_slide_bg(slide)

    add_text_box(slide, Cm(2), Cm(1.2), Cm(22), Cm(1.5),
                 "Демонстрація роботи системи",
                 font_size=28, bold=True, color=HEADING_RED,
                 alignment=PP_ALIGN.CENTER)

    shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE,
                                   Cm(3), Cm(3.5), Cm(20), Cm(11))
    shape.fill.solid()
    shape.fill.fore_color.rgb = CARD_BG
    shape.line.fill.background()

    add_text_box(slide, Cm(3), Cm(7.5), Cm(20), Cm(3),
                 "[Місце для відео демонстрації]",
                 font_size=24, bold=True, color=GRAY_SUB,
                 alignment=PP_ALIGN.CENTER)

    add_multiline(slide, Cm(5), Cm(15), Cm(16), Cm(3), [
        "Введення запиту природною мовою",
        "Покрокове виконання через ReAct-цикл",
        "Підтвердження кожного кроку (HITL)",
    ], font_size=16, color=GRAY_SUB, bullet=True, line_spacing=1.5,
       alignment=PP_ALIGN.LEFT)

    add_slide_number(slide, 17)

    # ═══════════════════════════════════════════════════════════════════
    # SLIDE 18: Conclusions
    # ═══════════════════════════════════════════════════════════════════
    slide = prs.slides.add_slide(blank_layout)
    set_slide_bg(slide)

    add_text_box(slide, Cm(2), Cm(1.2), Cm(22), Cm(1.5),
                 "Висновки",
                 font_size=28, bold=True, color=HEADING_RED,
                 alignment=PP_ALIGN.CENTER)

    conclusions = [
        "Розроблено агентну систему керування ПК через природну мову.",
        "Реалізовано ReAct-цикл для покрокового виконання задач.",
        "Впроваджено трирівневу модель безпеки "
        "(PrivacyGuard + Whitelist + HITL).",
        "Створено реєстр із 16 типів інструментів "
        "із розширенням через MCP.",
        "Побудовано desktop GUI (PySide6) та REST API (FastAPI).",
        "Протестовано на 21 сценарії — усі пройдено.",
    ]

    for i, text in enumerate(conclusions):
        top = Cm(3.5) + Cm(1.8) * i
        add_text_box(slide, Cm(2.5), top, Cm(1.5), Cm(1),
                     f"{i + 1}.", font_size=18, bold=True, color=HEADING_RED)
        add_text_box(slide, Cm(4.2), top, Cm(19), Cm(1.5),
                     text, font_size=18, color=TEXT_DARK, line_spacing=1.3)

    add_text_box(slide, Cm(2), Cm(15), Cm(22), Cm(1.5),
                 "Перспективи: голосове керування, розподілене виконання, "
                 "адаптивне навчання",
                 font_size=16, color=GRAY_SUB,
                 alignment=PP_ALIGN.CENTER)

    add_slide_number(slide, 18)

    # ═══════════════════════════════════════════════════════════════════
    # SLIDE 19: Thank you
    # ═══════════════════════════════════════════════════════════════════
    slide = prs.slides.add_slide(blank_layout)
    set_slide_bg(slide)

    add_text_box(slide, Cm(2), Cm(6), Cm(22), Cm(3),
                 "Дякую за увагу!",
                 font_size=44, bold=True, color=HEADING_RED,
                 alignment=PP_ALIGN.CENTER)

    add_text_box(slide, Cm(2), Cm(10), Cm(22), Cm(2),
                 "Готовий відповісти на запитання",
                 font_size=22, color=GRAY_SUB, alignment=PP_ALIGN.CENTER)

    add_text_box(slide, Cm(2), Cm(14), Cm(22), Cm(2),
                 "Бухінський В. А.  •  Група 442 Б  •  2026",
                 font_size=16, color=GRAY_SUB, alignment=PP_ALIGN.CENTER)

    add_slide_number(slide, 19)

    # ═══════════════════════════════════════════════════════════════════
    # Save
    # ═══════════════════════════════════════════════════════════════════
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    prs.save(OUTPUT_PATH)
    print(f"Saved: {OUTPUT_PATH}")


if __name__ == "__main__":
    create_presentation()
