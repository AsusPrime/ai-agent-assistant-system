#!/usr/bin/env python3
"""Генератор DOCX дипломної роботи."""

from docx import Document
from docx.shared import Pt, Cm, Inches, RGBColor, Emu
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.section import WD_ORIENT
from docx.oxml.ns import qn, nsdecls
from docx.oxml import parse_xml
import os

# ── Constants ──────────────────────────────────────────────────────────────
FONT_NAME = "Times New Roman"
FONT_SIZE = Pt(14)
LINE_SPACING = 1.5
MARGIN_LEFT = Cm(3)
MARGIN_RIGHT = Cm(1.5)
MARGIN_TOP = Cm(2)
MARGIN_BOTTOM = Cm(2)

OUTPUT_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "docs",
    "Бухінський_ВА_бакалаврська_робота.docx",
)


# ── Helper functions ───────────────────────────────────────────────────────

def set_default_style(doc: Document):
    style = doc.styles["Normal"]
    font = style.font
    font.name = FONT_NAME
    font.size = FONT_SIZE
    font.color.rgb = RGBColor(0, 0, 0)
    pf = style.paragraph_format
    pf.space_before = Pt(0)
    pf.space_after = Pt(0)
    pf.line_spacing = LINE_SPACING
    pf.first_line_indent = Cm(1.25)
    rpr = style.element.get_or_add_rPr()
    cs = parse_xml(f'<w:rFonts {nsdecls("w")} w:eastAsia="{FONT_NAME}" w:cs="{FONT_NAME}"/>')
    rpr.append(cs)


def set_margins(doc: Document):
    for section in doc.sections:
        section.left_margin = MARGIN_LEFT
        section.right_margin = MARGIN_RIGHT
        section.top_margin = MARGIN_TOP
        section.bottom_margin = MARGIN_BOTTOM
        section.header_distance = Cm(1.25)
        section.footer_distance = Cm(1.25)


def add_page_numbers(doc: Document):
    for section in doc.sections:
        header = section.header
        header.is_linked_to_previous = False
        p = header.paragraphs[0] if header.paragraphs else header.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run = p.add_run()
        fld = parse_xml(
            f'<w:fldSimple {nsdecls("w")} w:instr=" PAGE "><w:r><w:t></w:t></w:r></w:fldSimple>'
        )
        run._r.append(fld)
        run.font.name = FONT_NAME
        run.font.size = FONT_SIZE


def add_paragraph(doc, text, bold=False, italic=False, alignment=None,
                  font_size=None, first_indent=None, space_after=None,
                  space_before=None, keep_together=False):
    p = doc.add_paragraph()
    run = p.add_run(text)
    run.font.name = FONT_NAME
    run.font.size = font_size or FONT_SIZE
    run.bold = bold
    run.italic = italic
    if alignment is not None:
        p.alignment = alignment
    if first_indent is not None:
        p.paragraph_format.first_line_indent = first_indent
    if space_after is not None:
        p.paragraph_format.space_after = space_after
    if space_before is not None:
        p.paragraph_format.space_before = space_before
    if keep_together:
        ppr = p._p.get_or_add_pPr()
        ppr.append(parse_xml(f'<w:keepNext {nsdecls("w")}/>'))
    return p


def add_centered(doc, text, bold=False, font_size=None, space_after=None, space_before=None):
    return add_paragraph(doc, text, bold=bold, alignment=WD_ALIGN_PARAGRAPH.CENTER,
                         font_size=font_size, first_indent=Cm(0),
                         space_after=space_after, space_before=space_before)


def add_heading_custom(doc, text, level=1, numbered=True, number=""):
    p = doc.add_paragraph()
    if level == 1:
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.first_line_indent = Cm(0)
        p.paragraph_format.space_before = Pt(14)
        p.paragraph_format.space_after = Pt(14)
        run = p.add_run(text.upper() if numbered else text)
        run.bold = True
    else:
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.first_line_indent = Cm(1.25)
        p.paragraph_format.space_before = Pt(14)
        p.paragraph_format.space_after = Pt(7)
        run = p.add_run(text)
        run.bold = True
    run.font.name = FONT_NAME
    run.font.size = FONT_SIZE
    ppr = p._p.get_or_add_pPr()
    ppr.append(parse_xml(f'<w:keepNext {nsdecls("w")}/>'))
    return p


def add_body(doc, text):
    return add_paragraph(doc, text, alignment=WD_ALIGN_PARAGRAPH.JUSTIFY)


def add_figure_placeholder(doc, caption, height_cm=8):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.first_line_indent = Cm(0)
    p.paragraph_format.space_before = Pt(24)
    p.paragraph_format.space_after = Pt(6)
    run = p.add_run("[Тут має бути зображення]")
    run.font.name = FONT_NAME
    run.font.size = Pt(12)
    run.font.color.rgb = RGBColor(0x99, 0x99, 0x99)
    # Caption below
    add_paragraph(doc, caption, italic=True, alignment=WD_ALIGN_PARAGRAPH.CENTER,
                  first_indent=Cm(0), space_before=Pt(2), space_after=Pt(12))


def add_listing(doc, code, caption=""):
    if caption:
        add_paragraph(doc, caption, italic=True, alignment=WD_ALIGN_PARAGRAPH.CENTER,
                      first_indent=Cm(0), space_before=Pt(6))
    for line in code.strip().split("\n"):
        p = doc.add_paragraph()
        run = p.add_run(line)
        run.font.name = "Courier New"
        run.font.size = Pt(10)
        p.paragraph_format.first_line_indent = Cm(0)
        p.paragraph_format.space_before = Pt(0)
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.line_spacing = 1.0


def add_table_custom(doc, headers, rows, caption=""):
    if caption:
        add_paragraph(doc, caption, italic=True, alignment=WD_ALIGN_PARAGRAPH.CENTER,
                      first_indent=Cm(0), space_before=Pt(6), space_after=Pt(3))
    table = doc.add_table(rows=1 + len(rows), cols=len(headers))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    table.style = "Table Grid"
    for i, h in enumerate(headers):
        cell = table.rows[0].cells[i]
        cell.text = ""
        p = cell.paragraphs[0]
        run = p.add_run(h)
        run.bold = True
        run.font.name = FONT_NAME
        run.font.size = Pt(12)
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.first_line_indent = Cm(0)
    for r_idx, row in enumerate(rows):
        for c_idx, val in enumerate(row):
            cell = table.rows[r_idx + 1].cells[c_idx]
            cell.text = ""
            p = cell.paragraphs[0]
            run = p.add_run(str(val))
            run.font.name = FONT_NAME
            run.font.size = Pt(12)
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.first_line_indent = Cm(0)
    add_paragraph(doc, "", first_indent=Cm(0), space_after=Pt(6))
    return table


def page_break(doc):
    p = doc.add_paragraph()
    run = p.add_run()
    run.add_break(docx.enum.text.WD_BREAK.PAGE)


import docx.enum.text


# ── TITLE PAGE ─────────────────────────────────────────────────────────────

def create_title_page(doc):
    add_centered(doc, "МІНІСТЕРСТВО ОСВІТИ І НАУКИ УКРАЇНИ", bold=True, font_size=Pt(14))
    add_centered(doc, "ЧЕРНІВЕЦЬКИЙ НАЦІОНАЛЬНИЙ УНІВЕРСИТЕТ", bold=True, font_size=Pt(14))
    add_centered(doc, "ІМЕНІ ЮРІЯ ФЕДЬКОВИЧА", bold=True, font_size=Pt(14))
    add_centered(doc, "")
    add_centered(doc, "Навчально-науковий інститут фізико-технічних та комп'ютерних наук",
                 font_size=Pt(14))
    add_centered(doc, "Кафедра комп'ютерних систем та мереж", font_size=Pt(14))
    add_centered(doc, "")
    add_centered(doc, "")
    add_centered(doc, "")
    add_centered(doc, "")
    add_centered(doc, "КВАЛІФІКАЦІЙНА РОБОТА", bold=True, font_size=Pt(16))
    add_centered(doc, "бакалавра", bold=True, font_size=Pt(14))
    add_centered(doc, "")
    add_centered(doc, "Агентна система обробки та виконання", bold=True, font_size=Pt(14))
    add_centered(doc, "команд керування комп'ютером", bold=True, font_size=Pt(14))
    add_centered(doc, "")
    add_centered(doc, "482.362.123-90 05-4-П ЛЗ", font_size=Pt(14))
    add_centered(doc, "")
    add_centered(doc, "")
    add_centered(doc, "")

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    p.paragraph_format.first_line_indent = Cm(0)
    run = p.add_run("Виконав: студент 4 курсу, групи 442 Б\nспеціальності 123 Комп'ютерна інженерія\nОПП Програмування мобільних і\nвбудованих комп'ютерних систем\nта засобів Інтернету речей")
    run.font.name = FONT_NAME
    run.font.size = Pt(14)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    p.paragraph_format.first_line_indent = Cm(0)
    run = p.add_run("Бухінський Владислав Андрійович")
    run.font.name = FONT_NAME
    run.font.size = Pt(14)
    run.bold = True

    add_centered(doc, "")
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    p.paragraph_format.first_line_indent = Cm(0)
    run = p.add_run("Керівник: д.т.н., доц., Воробець О. І.")
    run.font.name = FONT_NAME
    run.font.size = Pt(14)

    add_centered(doc, "")
    add_centered(doc, "")
    add_centered(doc, "")
    add_centered(doc, "Чернівці 2026", font_size=Pt(14))

    page_break(doc)


# ── ЛИСТ ЗАТВЕРДЖЕННЯ ──────────────────────────────────────────────────────

def create_approval_sheet(doc):
    add_centered(doc, "ЛИСТ ЗАТВЕРДЖЕННЯ", bold=True, font_size=Pt(14))
    add_centered(doc, "")
    add_centered(doc, "Агентна система обробки та виконання", bold=True, font_size=Pt(14))
    add_centered(doc, "команд керування комп'ютером", bold=True, font_size=Pt(14))
    add_centered(doc, "")
    add_centered(doc, "482.362.123-90 05-4-П ЛЗ", font_size=Pt(14))
    add_centered(doc, "")
    add_centered(doc, "")

    p = doc.add_paragraph()
    p.paragraph_format.first_line_indent = Cm(0)
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    run = p.add_run(
        "УЗГОДЖЕНО:\n\n"
        "Завідувач кафедри\nкомп'ютерних систем та мереж\n"
        "канд. фіз.-мат. наук, доц.\n\n"
        "______________  Воробець Г. І.\n"
        "«___» ____________ 2026 р.\n\n\n"
        "Нормоконтроль:\n"
        "канд. техн. наук, асистент\n\n"
        "______________  Воропаєва С. Л.\n"
        "«___» ____________ 2026 р."
    )
    run.font.name = FONT_NAME
    run.font.size = Pt(14)

    add_centered(doc, "")
    add_centered(doc, "")

    p = doc.add_paragraph()
    p.paragraph_format.first_line_indent = Cm(0)
    p.alignment = WD_ALIGN_PARAGRAPH.LEFT
    run = p.add_run(
        "Керівник кваліфікаційної роботи:\n"
        "д.т.н., доц.\n\n"
        "______________  Воробець О. І.\n"
        "«___» ____________ 2026 р.\n\n\n"
        "Виконав:\n"
        "студент групи 442 Б\n\n"
        "______________  Бухінський В. А.\n"
        "«___» ____________ 2026 р."
    )
    run.font.name = FONT_NAME
    run.font.size = Pt(14)

    page_break(doc)


# ── ЗАВДАННЯ ────────────────────────────────────────────────────────────────

def create_task_sheet(doc):
    add_centered(doc, "ЧЕРНІВЕЦЬКИЙ НАЦІОНАЛЬНИЙ УНІВЕРСИТЕТ ІМЕНІ ЮРІЯ ФЕДЬКОВИЧА",
                 bold=True, font_size=Pt(12))
    add_centered(doc, "Навчально-науковий інститут фізико-технічних та комп'ютерних наук",
                 font_size=Pt(12))
    add_centered(doc, "Кафедра комп'ютерних систем та мереж", font_size=Pt(12))
    add_centered(doc, "Спеціальність 123 Комп'ютерна інженерія", font_size=Pt(12))
    add_centered(doc, "")
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    p.paragraph_format.first_line_indent = Cm(0)
    run = p.add_run("ЗАТВЕРДЖУЮ\nЗав. кафедри КСМ\n_______ Воробець Г. І.\n«___» __________ 2026 р.")
    run.font.name = FONT_NAME
    run.font.size = Pt(12)

    add_centered(doc, "")
    add_centered(doc, "ЗАВДАННЯ", bold=True, font_size=Pt(14))
    add_centered(doc, "на кваліфікаційну роботу бакалавра", font_size=Pt(14))
    add_centered(doc, "")

    add_body(doc, "Студенту Бухінському Владиславу Андрійовичу, групи 442 Б, спеціальності 123 Комп'ютерна інженерія, ОПП «Програмування мобільних і вбудованих комп'ютерних систем та засобів Інтернету речей».")
    add_centered(doc, "")

    add_body(doc, "1. Тема роботи: «Агентна система обробки та виконання команд керування комп'ютером».")
    add_body(doc, "Затверджена наказом по університету від «___» __________ 2026 р. № _____.")
    add_centered(doc, "")

    add_body(doc, "2. Термін здачі студентом закінченої роботи: «___» __________ 2026 р.")
    add_centered(doc, "")

    add_body(doc, "3. Вихідні дані до роботи: існуючі фреймворки для побудови агентних систем (PydanticAI, LangChain, AutoGen), технічна документація Google Gemini API, специфікація Model Context Protocol (MCP), стандарти безпеки OWASP, документація PySide6 для побудови настільних інтерфейсів, наукові публікації з тематики мульти-агентних систем та обробки природної мови.")
    add_centered(doc, "")

    add_body(doc, "4. Зміст кваліфікаційної роботи (перелік питань, які потрібно розробити):")
    add_body(doc, "— аналіз сучасних підходів до побудови агентних систем керування;")
    add_body(doc, "— дослідження методів покрокового планування та виконання задач;")
    add_body(doc, "— проєктування архітектури системи з підтримкою HITL;")
    add_body(doc, "— реалізація ядра системи: планувальник, реєстр інструментів, виконавчий механізм;")
    add_body(doc, "— розробка механізмів захисту конфіденційності (PrivacyGuard);")
    add_body(doc, "— створення графічного інтерфейсу (PySide6) та REST API (FastAPI);")
    add_body(doc, "— тестування системи на типових сценаріях використання;")
    add_body(doc, "— економічний розрахунок вартості розробки програмного продукту.")
    add_centered(doc, "")

    add_body(doc, "5. Перелік графічного (ілюстративного) матеріалу: архітектура системи (UML-діаграма компонентів), діаграма послідовності обробки запиту, блок-схема алгоритму ReAct, структура реєстру інструментів, знімки екрану графічного інтерфейсу.")
    add_centered(doc, "")

    add_heading_custom(doc, "Календарний план", level=2)
    add_table_custom(doc,
        ["№", "Етап роботи", "Термін виконання", "Примітки"],
        [
            ["1", "Аналіз предметної області", "01.02–15.02.2026", "Виконано"],
            ["2", "Проєктування архітектури", "16.02–01.03.2026", "Виконано"],
            ["3", "Розробка виконавчого рівня", "02.03–20.03.2026", "Виконано"],
            ["4", "Розробка рівня планування", "21.03–10.04.2026", "Виконано"],
            ["5", "Система рецептів та MCP", "11.04–25.04.2026", "Виконано"],
            ["6", "GUI та REST API", "26.04–10.05.2026", "Виконано"],
            ["7", "Тестування та виправлення", "11.05–20.05.2026", "Виконано"],
            ["8", "Оформлення пояснювальної записки", "21.05–05.06.2026", "Виконано"],
        ],
    )

    add_centered(doc, "")
    add_body(doc, "Студент                    ______________         Бухінський В. А.")
    add_body(doc, "Керівник роботи        ______________         Воробець О. І.")
    add_body(doc, "«___» __________ 2026 р.")

    page_break(doc)


# ── АНОТАЦІЯ ────────────────────────────────────────────────────────────────

def create_annotation(doc):
    add_centered(doc, "АНОТАЦІЯ", bold=True)
    add_centered(doc, "")

    add_body(doc,
        "Бухінський В. А. Агентна система обробки та виконання команд керування комп'ютером. — "
        "Кваліфікаційна робота бакалавра. — Чернівецький національний університет імені Юрія Федьковича. — "
        "Чернівці, 2026."
    )
    add_centered(doc, "")
    add_body(doc,
        "Кваліфікаційна робота присвячена розробці інтелектуальної системи, яка забезпечує "
        "обробку текстових команд користувача та їх перетворення на конкретні "
        "операції керування персональним комп'ютером. Система побудована на основі фреймворку "
        "PydanticAI із використанням великої мовної моделі Google Gemini як основного засобу "
        "розуміння намірів користувача."
    )
    add_body(doc,
        "Ключовою особливістю запропонованої архітектури є цикл ReAct (Reasoning-Acting) "
        "для покрокового виконання складних запитів, що дозволяє системі адаптивно "
        "планувати наступний крок на основі результатів попереднього. Планувальник на "
        "кожній ітерації генерує одну задачу, яка після підтвердження користувачем "
        "виконується через відповідний обробник із реєстру інструментів."
    )
    add_body(doc,
        "Особливу увагу приділено безпеці: реалізовано механізм PrivacyGuard для маскування "
        "персональних даних перед відправкою до хмарної моделі, білий список дозволених операцій "
        "із валідацією на рівні Pydantic-схем, а також підхід Human-in-the-Loop із обов'язковим "
        "підтвердженням критичних дій користувачем."
    )
    add_body(doc,
        "Графічний інтерфейс реалізовано у вигляді настільного застосунку на PySide6, а серверна "
        "частина надає REST API через FastAPI. Система підтримує розширення функціональності "
        "через зовнішні MCP-сервери та локальну базу знань на основі ChromaDB."
    )
    add_body(doc,
        "Робота містить 5 розділів, 8 рисунків, 10 таблиць, 20 літературних джерел та 5 додатків."
    )
    add_body(doc,
        "Ключові слова: агентна система, великі мовні моделі, PydanticAI, ReAct, "
        "Human-in-the-Loop, керування комп'ютером, PrivacyGuard, реєстр інструментів."
    )

    page_break(doc)

    add_centered(doc, "ABSTRACT", bold=True)
    add_centered(doc, "")

    add_body(doc,
        "Bukhinskyi V. A. Agent System for Processing and Executing Computer Control Commands. — "
        "Bachelor's qualification thesis. — Yuriy Fedkovych Chernivtsi National University. — "
        "Chernivtsi, 2026."
    )
    add_centered(doc, "")
    add_body(doc,
        "The qualification thesis is devoted to the development of an intelligent system that "
        "provides processing of user text commands and their conversion into specific "
        "computer control operations. The system is built on the PydanticAI framework using the "
        "Google Gemini large language model as the primary means of understanding user intentions."
    )
    add_body(doc,
        "A key feature of the proposed architecture is a ReAct (Reasoning-Acting) loop for "
        "step-by-step execution of complex requests, allowing the system to adaptively plan "
        "the next step based on previous results. The planner generates one task per iteration, "
        "which is executed through the corresponding handler from the tool registry after user confirmation."
    )
    add_body(doc,
        "Special attention is paid to security: a PrivacyGuard mechanism for masking personal data "
        "before sending it to the cloud model, a whitelist of allowed operations with validation at "
        "the Pydantic schema level, and a Human-in-the-Loop approach with mandatory user confirmation "
        "of critical actions."
    )
    add_body(doc,
        "The graphical interface is implemented as a desktop application using PySide6, and the server "
        "side provides a REST API via FastAPI. The system supports extensibility through external MCP "
        "servers and a local knowledge base powered by ChromaDB."
    )
    add_body(doc,
        "The thesis contains 5 chapters, 8 figures, 10 tables, 20 references, and 5 appendices."
    )
    add_body(doc,
        "Keywords: agent system, large language models, PydanticAI, ReAct, "
        "Human-in-the-Loop, computer control, PrivacyGuard, tool registry."
    )

    page_break(doc)


# ── ЗМІСТ ───────────────────────────────────────────────────────────────────

def create_contents(doc):
    add_centered(doc, "ЗМІСТ", bold=True)
    add_centered(doc, "")

    items = [
        ("ПЕРЕЛІК УМОВНИХ СКОРОЧЕНЬ", ""),
        ("ВСТУП", ""),
        ("РОЗДІЛ 1 АНАЛІЗ ПРЕДМЕТНОЇ ОБЛАСТІ АГЕНТНИХ СИСТЕМ КЕРУВАННЯ КОМП'ЮТЕРОМ", ""),
        ("1.1 Еволюція підходів до автоматизації керування персональним комп'ютером", ""),
        ("1.2 Агентні системи на основі великих мовних моделей", ""),
        ("1.3 Порівняння існуючих фреймворків для побудови AI-агентів", ""),
        ("1.4 Протокол Model Context Protocol та розширюваність систем", ""),
        ("1.5 Системи рецептів та автоматизації робочих процесів", ""),
        ("1.6 Висновки до розділу 1", ""),
        ("РОЗДІЛ 2 МЕТОДИ ТА ЗАСОБИ РОЗРОБКИ", ""),
        ("2.1 Архітектура системи та потік обробки запитів", ""),
        ("2.2 Цикл ReAct як метод покрокового виконання задач", ""),
        ("2.3 Механізми забезпечення безпеки та конфіденційності", ""),
        ("2.4 Технологічний стек проєкту", ""),
        ("2.5 Система рецептів та повторне використання сценаріїв", ""),
        ("2.6 Локальна база знань та семантичний пошук", ""),
        ("2.7 Висновки до розділу 2", ""),
        ("РОЗДІЛ 3 ПРОГРАМНА РЕАЛІЗАЦІЯ СИСТЕМИ", ""),
        ("3.1 Структура проєкту та організація модулів", ""),
        ("3.2 Реалізація планувальника", ""),
        ("3.3 Реєстр інструментів та виконавчий механізм", ""),
        ("3.4 Модуль захисту конфіденційності PrivacyGuard", ""),
        ("3.5 REST API та серверна частина", ""),
        ("3.6 Графічний інтерфейс користувача", ""),
        ("3.7 Управління сесією та збереження контексту", ""),
        ("3.8 Система конфігурації та налаштувань", ""),
        ("3.9 Кросплатформна підтримка", ""),
        ("3.10 Інтеграція з MCP-серверами", ""),
        ("3.11 Обробка веб-запитів та HTTP API", ""),
        ("3.12 Висновки до розділу 3", ""),
        ("РОЗДІЛ 4 ТЕСТУВАННЯ ТА ВЕРИФІКАЦІЯ СИСТЕМИ", ""),
        ("4.1 Стратегія тестування та класифікація сценаріїв", ""),
        ("4.2 Тестування базових операцій", ""),
        ("4.3 Тестування складних багатокрокових запитів", ""),
        ("4.4 Тестування механізмів безпеки", ""),
        ("4.5 Тестування рецептів та налаштувань", ""),
        ("4.6 Тестування самовиправлення (ReAct retry)", ""),
        ("4.7 Зведена таблиця результатів тестування", ""),
        ("4.8 Висновки до розділу 4", ""),
        ("РОЗДІЛ 5 ЕКОНОМІЧНИЙ РОЗРАХУНОК ТА ОХОРОНА ПРАЦІ", ""),
        ("5.1 Техніко-економічні показники", ""),
        ("5.2 Засоби захисту та охорона праці", ""),
        ("ВИСНОВКИ", ""),
        ("СПИСОК ВИКОРИСТАНИХ ДЖЕРЕЛ", ""),
        ("ДОДАТКИ", ""),
    ]
    for text, _ in items:
        is_section = text.startswith("РОЗДІЛ") or text in ("ВСТУП", "ВИСНОВКИ", "СПИСОК ВИКОРИСТАНИХ ДЖЕРЕЛ", "ДОДАТКИ", "ПЕРЕЛІК УМОВНИХ СКОРОЧЕНЬ")
        p = add_paragraph(doc, text, bold=is_section,
                          first_indent=Cm(0) if is_section else Cm(1.25))
    page_break(doc)


# ── ПЕРЕЛІК СКОРОЧЕНЬ ──────────────────────────────────────────────────────

def create_abbreviations(doc):
    add_centered(doc, "ПЕРЕЛІК УМОВНИХ СКОРОЧЕНЬ", bold=True)
    add_centered(doc, "")

    abbrs = [
        ("AI", "Artificial Intelligence — штучний інтелект"),
        ("API", "Application Programming Interface — програмний інтерфейс застосунку"),
        ("CRUD", "Create, Read, Update, Delete — базові операції над даними"),
        ("GUI", "Graphical User Interface — графічний інтерфейс користувача"),
        ("HITL", "Human-in-the-Loop — людина в контурі прийняття рішень"),
        ("HTTP", "HyperText Transfer Protocol — протокол передавання гіпертексту"),
        ("JSON", "JavaScript Object Notation — текстовий формат обміну даними"),
        ("LLM", "Large Language Model — велика мовна модель"),
        ("MCP", "Model Context Protocol — протокол контексту моделі"),
        ("NLP", "Natural Language Processing — обробка природної мови"),
        ("OС", "Операційна система"),
        ("PII", "Personally Identifiable Information — персональні ідентифікаційні дані"),
        ("RAG", "Retrieval-Augmented Generation — генерація з доповненням пошуком"),
        ("REST", "Representational State Transfer — архітектурний стиль взаємодії компонентів"),
        ("UI", "User Interface — інтерфейс користувача"),
        ("UML", "Unified Modeling Language — уніфікована мова моделювання"),
    ]
    for abbr, desc in abbrs:
        p = doc.add_paragraph()
        p.paragraph_format.first_line_indent = Cm(0)
        run1 = p.add_run(f"{abbr}")
        run1.bold = True
        run1.font.name = FONT_NAME
        run1.font.size = FONT_SIZE
        run2 = p.add_run(f" — {desc}")
        run2.font.name = FONT_NAME
        run2.font.size = FONT_SIZE

    page_break(doc)


# ── ВСТУП ──────────────────────────────────────────────────────────────────

def create_introduction(doc):
    add_centered(doc, "ВСТУП", bold=True)
    add_centered(doc, "")

    add_body(doc,
        "Актуальність теми дослідження. Сьогодні персональний комп'ютер залишається основним "
        "робочим інструментом для мільйонів фахівців у різних галузях — від інженерії до "
        "креативних індустрій. Водночас інтерфейс взаємодії між людиною та комп'ютером протягом "
        "останніх десятиліть зазнав лише косметичних змін: користувач, як і раніше, вручну "
        "відкриває застосунки, вводить команди в термінал, переміщує файли та налаштовує системні "
        "параметри. Такий підхід вимагає знання конкретних команд, розташування програм і "
        "особливостей операційної системи, що створює бар'єр для нетехнічних користувачів."
    )
    add_body(doc,
        "Стрімкий розвиток великих мовних моделей (Large Language Models, LLM) у 2023–2026 роках "
        "відкрив нові можливості для побудови інтелектуальних помічників, здатних "
        "розуміти запити природною мовою та перетворювати їх на послідовність конкретних дій. "
        "Проте існуючі рішення, такі як голосові помічники Siri чи Google Assistant, обмежені "
        "заздалегідь визначеним набором сценаріїв і не дозволяють гнучко керувати довільними "
        "операціями на локальному комп'ютері."
    )
    add_body(doc,
        "Концепція агентних систем на основі LLM пропонує інший підхід: замість жорстко "
        "запрограмованих сценаріїв система динамічно планує послідовність дій, виконує їх "
        "покроково та адаптує план на основі отриманих результатів. Реєстр інструментів "
        "дозволяє системі використовувати різноманітні типи операцій — пошук інформації, "
        "роботу з файлами, керування системними налаштуваннями тощо — через єдиний механізм "
        "диспетчеризації."
    )
    add_body(doc,
        "Водночас запровадження таких систем потребує вирішення низки критичних проблем. По-перше, "
        "безпека: система, що має доступ до файлової системи та командного рядка, не може "
        "виконувати довільні дії без контролю з боку користувача. По-друге, конфіденційність: "
        "текстові запити часто містять персональні дані (електронні адреси, номери карток, паролі), "
        "які не повинні потрапляти до хмарних сервісів у відкритому вигляді. По-третє, "
        "масштабованість: система має підтримувати додавання нових типів інструментів "
        "без зміни базового коду."
    )

    add_body(doc,
        "Аналіз наукових публікацій та комерційних продуктів свідчить, що на момент "
        "написання роботи не існує комплексного рішення, яке б одночасно забезпечувало "
        "покрокове виконання команд керування локальним комп'ютером, захист "
        "конфіденційних даних та повний контроль користувача над кожною дією системи. "
        "Існуючі рішення (Claude Computer Use, Open Interpreter, AutoGPT) або "
        "працюють через хмарний інтерфейс без підтримки локальних операцій, або "
        "не мають механізмів захисту PII, або не надають покрокового підтвердження "
        "критичних дій. Це визначає актуальність та новизну даного дослідження."
    )

    add_body(doc,
        "Об'єкт дослідження — процес інтелектуальної обробки текстових команд керування "
        "комп'ютером із використанням агентних технологій на основі великих мовних моделей."
    )
    add_body(doc,
        "Предмет дослідження — методи та програмні засоби побудови агентної системи для "
        "автоматизації операцій персонального комп'ютера на основі великих мовних моделей."
    )
    add_body(doc,
        "Мета роботи — розробити агентну систему обробки та виконання команд "
        "керування персональним комп'ютером, що забезпечує інтерпретацію запитів природною "
        "мовою, покрокове виконання складних задач та захист конфіденційних даних користувача."
    )

    add_body(doc, "Для досягнення поставленої мети необхідно вирішити такі задачі:")
    tasks = [
        "проаналізувати існуючі підходи та фреймворки для побудови агентних систем на основі великих мовних моделей;",
        "обґрунтувати вибір методу покрокового виконання ReAct та архітектури з реєстром інструментів;",
        "спроєктувати та реалізувати ядро системи: планувальник задач, реєстр інструментів, виконавчий механізм;",
        "реалізувати механізм захисту персональних даних PrivacyGuard та підхід Human-in-the-Loop;",
        "розробити графічний інтерфейс настільного застосунку та REST API серверної частини;",
        "провести тестування системи на репрезентативному наборі сценаріїв використання;",
        "виконати економічний розрахунок вартості розробки програмного продукту.",
    ]
    for i, t in enumerate(tasks, 1):
        add_body(doc, f"{i}) {t}")

    add_body(doc,
        "Методи дослідження. У роботі використано метод декомпозиції задач для розбиття "
        "складних запитів на елементарні підзадачі, метод ReAct для покрокового планування "
        "із зворотним зв'язком, патерн Strategy для підтримки різних операційних систем, "
        "патерн Registry для динамічного відображення типів дій на обробники, а також "
        "регулярні вирази та ентропійний аналіз для виявлення конфіденційних даних."
    )

    add_body(doc,
        "Практична цінність роботи полягає у створенні повністю функціональної системи, "
        "яка дозволяє нетехнічним користувачам керувати комп'ютером за допомогою текстових "
        "запитів природною мовою. Система може бути розгорнута на macOS, Windows та Linux "
        "без модифікації основного коду завдяки кросплатформній архітектурі."
    )

    add_body(doc,
        "Апробація результатів. Основні результати роботи доповідалися на засіданні "
        "кафедри комп'ютерних систем та мереж Чернівецького національного університету "
        "імені Юрія Федьковича у 2026 році."
    )

    add_body(doc,
        "Структура та обсяг роботи. Кваліфікаційна робота складається зі вступу, п'яти "
        "розділів, висновків, списку використаних джерел та додатків. Загальний обсяг роботи "
        "складає 60 сторінок, у тому числі 8 рисунків, 10 таблиць. Список використаних "
        "джерел містить 20 найменувань."
    )

    page_break(doc)


# ── РОЗДІЛ 1 ───────────────────────────────────────────────────────────────

def create_chapter_1(doc):
    add_heading_custom(doc, "РОЗДІЛ 1 АНАЛІЗ ПРЕДМЕТНОЇ ОБЛАСТІ АГЕНТНИХ СИСТЕМ КЕРУВАННЯ КОМП'ЮТЕРОМ", level=1)

    add_heading_custom(doc, "1.1 Еволюція підходів до автоматизації керування персональним комп'ютером", level=2)

    add_body(doc,
        "Історія автоматизації взаємодії людини з комп'ютером нараховує кілька десятиліть "
        "та пройшла шлях від простих пакетних файлів до інтелектуальних систем на основі "
        "штучного інтелекту. На початку розвитку персональних комп'ютерів основним засобом "
        "автоматизації слугували командні скрипти (.bat у DOS, .sh у Unix), які дозволяли "
        "об'єднувати декілька команд у один файл і виконувати їх послідовно. Такий підхід "
        "вимагав від користувача детального знання синтаксису команд і не допускав жодної "
        "варіативності у процесі виконання."
    )
    add_body(doc,
        "Наступним кроком стали макроси та засоби автоматизації робочого столу, такі як "
        "AutoHotkey, AutoIt та Apple Automator. Ці інструменти надали графічний інтерфейс "
        "для створення послідовностей дій, проте залишалися жорстко детерміністичними: "
        "вони виконували заздалегідь записані маніпуляції з вікнами, клавіатурою та мишею "
        "без будь-якого розуміння контексту."
    )
    add_body(doc,
        "Поява голосових помічників — Siri (Apple, 2011), Google Assistant (2016), Alexa "
        "(Amazon, 2014) — ознаменувала перехід до інтерфейсу природної мови. Користувач "
        "отримав можливість формулювати запити звичайною мовою, а система розпізнавала "
        "намір і виконувала відповідну дію. Однак ці помічники функціонують за принципом "
        "заздалегідь визначених інтентів (intent recognition): кожен підтримуваний сценарій "
        "потребує окремого програмування, що обмежує гнучкість системи."
    )
    add_body(doc,
        "З появою великих мовних моделей (LLM) ситуація змінилась. Моделі GPT-4, "
        "Claude, Gemini продемонстрували здатність не лише розуміти текст, а й генерувати "
        "структуровані відповіді, планувати послідовність дій та працювати з зовнішніми "
        "інструментами через механізм tool calling. Це створило передумови для нового класу "
        "систем — AI-агентів, які поєднують розуміння природної мови з можливістю виконання "
        "реальних операцій."
    )
    add_body(doc,
        "AI-агент — це програмна сутність, яка спостерігає за своїм оточенням, приймає "
        "рішення на основі спостережень та виконує дії для досягнення поставленої мети. "
        "На відміну від традиційних скриптів, агент здатний адаптувати свою поведінку "
        "залежно від результатів попередніх кроків, обробляти непередбачені ситуації та "
        "взаємодіяти з іншими агентами для вирішення складних комплексних задач."
    )
    add_body(doc,
        "Формально AI-агент характеризується такими властивостями: автономність — здатність "
        "приймати рішення без постійного втручання людини; реактивність — здатність реагувати "
        "на зміни у середовищі; проактивність — здатність ініціювати дії для досягнення "
        "цілей; соціальність — здатність взаємодіяти з іншими агентами та людьми. Ці "
        "властивості, визначені Wooldridge у класичній роботі «An Introduction to MultiAgent "
        "Systems», становлять теоретичну основу для проєктування сучасних AI-агентів."
    )
    add_body(doc,
        "Важливим аспектом агентних систем є механізм tool calling (виклик інструментів), "
        "реалізований у сучасних LLM. Модель отримує JSON-схему доступних інструментів "
        "у системному промпті та генерує структуровані виклики з конкретними параметрами. "
        "Наприклад, на запит «відкрий Safari» модель генерує виклик інструменту open_app "
        "з параметром name=\"Safari\". Цей механізм є фундаментальним мостом між мовним "
        "розумінням та реальними діями."
    )
    add_body(doc,
        "У контексті керування комп'ютером AI-агент приймає запит природною мовою, "
        "визначає необхідну послідовність операцій (відкриття програм, виконання команд, "
        "створення файлів, пошук інформації), виконує ці операції покроково та повідомляє "
        "користувача про результат у зрозумілій формі. Таким чином, агентна система "
        "фактично виступає інтелектуальним посередником між наміром користувача та "
        "технічними можливостями операційної системи."
    )

    add_heading_custom(doc, "1.2 Агентні системи на основі великих мовних моделей", level=2)

    add_body(doc,
        "Сучасні агентні системи на основі LLM базуються на концепції виклику інструментів "
        "(tool calling або function calling). Велика мовна модель отримує опис доступних "
        "інструментів у своєму системному промпті та генерує структуровані відповіді, які "
        "вказують, який саме інструмент потрібно викликати з якими параметрами. Цей механізм "
        "дозволяє моделі не просто генерувати текст, а й взаємодіяти з реальним середовищем."
    )
    add_body(doc,
        "Ключовим методологічним підходом для побудови агентних систем є парадигма ReAct "
        "(Reasoning and Acting), запропонована дослідниками з Princeton University та Google "
        "у 2022 році. Парадигма поєднує два процеси: міркування (reasoning), під час якого "
        "модель аналізує поточний стан та обирає наступний крок, і дію (acting), під час "
        "якої виконується конкретна операція. Цикл «подумай → дій → спостерігай» повторюється "
        "до завершення задачі або вичерпання ліміту ітерацій."
    )
    add_body(doc,
        "Важливим елементом агентних систем є реєстр інструментів (tool registry) — "
        "централізований каталог доступних операцій із їх обробниками. Агент не виконує "
        "дії безпосередньо: він генерує структуровану задачу (тип дії + параметри), яку "
        "диспетчер передає відповідному обробнику з реєстру. Такий підхід забезпечує "
        "чітке розмежування між прийняттям рішень (LLM) та виконанням (обробники)."
    )
    add_body(doc,
        "Додатковим напрямком розвитку є системи із підтримкою збереження та повторного "
        "використання послідовностей дій (рецепти, макроси). На відміну від традиційних "
        "макросів, рецепти в агентних системах зберігають структуровані задачі, які "
        "можуть бути створені як вручну, так і автоматично через LLM на основі текстового "
        "опису користувача."
    )
    add_body(doc,
        "У дослідженні Schick et al. (Toolformer, 2023) продемонстровано, що мовні "
        "моделі здатні самостійно "
        "навчатися використовувати зовнішні інструменти. Роботи Park et al. (Generative "
        "Agents, 2023) показали можливість створення автономних агентів із довготривалою "
        "пам'яттю та соціальною поведінкою. Проєкт Voyager (Wang et al., 2024) "
        "продемонстрував агента, здатного самостійно досліджувати відкрите середовище "
        "та набувати нових навичок без людського втручання."
    )
    add_body(doc,
        "Окремо слід виділити підхід Chain-of-Thought (CoT), запропонований Wei et al. "
        "у 2022 році. Цей метод передбачає явне формулювання проміжних кроків міркування "
        "перед генерацією фінальної відповіді. CoT значно покращує якість розв'язання "
        "задач, що потребують логічного виведення, і став основою для більш складних "
        "методів, таких як ReAct. Саме поєднання CoT (міркування) з tool calling "
        "(дія) утворює парадигму ReAct, яку використано в даній роботі."
    )

    add_heading_custom(doc, "1.3 Порівняння існуючих фреймворків для побудови AI-агентів", level=2)

    add_body(doc,
        "Станом на 2026 рік ринок фреймворків для побудови AI-агентів представлений "
        "багатьма рішеннями, кожне з яких має власні переваги та обмеження. Для обґрунтованого "
        "вибору технологічної основи проведемо порівняльний аналіз найбільш поширених "
        "фреймворків."
    )

    add_table_custom(doc,
        ["Критерій", "LangChain", "AutoGen", "CrewAI", "PydanticAI"],
        [
            ["Типізація відповідей", "Ні (raw dict)", "Ні", "Часткова", "Повна (Pydantic v2)"],
            ["Розширюваність", "Через LangGraph", "Обмежена", "Обмежена", "Гнучка (MCP)"],
            ["Валідація даних", "Зовнішня", "Зовнішня", "Часткова", "Вбудована Pydantic"],
            ["Підтримка Gemini", "Через адаптер", "Обмежена", "Через API", "Нативна"],
            ["MCP підтримка", "Ні", "Ні", "Часткова", "Нативна"],
            ["Складність", "Висока", "Середня", "Низька", "Низька"],
        ],
        caption="Таблиця 1.1 — Порівняння фреймворків для побудови AI-агентів"
    )

    add_body(doc,
        "LangChain є одним з найпопулярніших фреймворків для роботи з LLM. Він надає "
        "широкий набір абстракцій: ланцюжки (chains), ретрівери, агенти, інструменти та "
        "менеджери пам'яті. Водночас LangChain характеризується високим порогом входу "
        "через складну систему абстракцій, слабкою типізацією відповідей (результати "
        "повертаються як словники без валідації) та значним обсягом залежностей."
    )
    add_body(doc,
        "AutoGen (Microsoft) спеціалізується на мульти-агентних діалогах, де агенти "
        "обмінюються повідомленнями для спільного вирішення задачі. Фреймворк добре "
        "підходить для сценаріїв спільного генерування коду та код-рев'ю, проте його "
        "діалогова модель надмірна для задач прямого керування комп'ютером, де потрібен "
        "чіткий послідовний виконавчий процес."
    )
    add_body(doc,
        "CrewAI пропонує інтуїтивну метафору «команди» з ролями (researcher, writer, "
        "manager), проте має обмежену підтримку типізації та валідації відповідей, що "
        "є необхідним для систем, які виконують реальні операції на комп'ютері."
    )
    add_body(doc,
        "PydanticAI обрано як основу для даної роботи з таких причин. По-перше, він "
        "забезпечує повну типізацію відповідей моделі через Pydantic v2: кожна відповідь "
        "LLM автоматично валідується та перетворюється на типобезпечний Python-об'єкт. "
        "По-друге, фреймворк надає нативну підтримку моделей Google Gemini через "
        "GoogleProvider. По-третє, PydanticAI має вбудовану підтримку протоколу MCP "
        "(Model Context Protocol), що дозволяє розширювати функціональність системи "
        "через зовнішні сервери інструментів. Нарешті, мінімалістична архітектура "
        "фреймворку дозволяє гнучко реалізувати власну логіку планування та виконання "
        "без обмежень, накладених фреймворком."
    )

    add_heading_custom(doc, "1.4 Протокол Model Context Protocol та розширюваність систем", level=2)

    add_body(doc,
        "Проблема розширюваності є важливою для агентних систем. Класичний підхід "
        "передбачає вбудовування усіх інструментів безпосередньо у код системи, що ускладнює "
        "додавання нових можливостей без модифікації ядра. Для вирішення цієї проблеми "
        "компанія Anthropic у 2024 році запропонувала відкритий стандарт Model Context Protocol "
        "(MCP), який визначає уніфікований протокол взаємодії між мовними моделями та "
        "зовнішніми інструментами."
    )
    add_body(doc,
        "MCP працює за клієнт-серверною архітектурою: MCP-сервер надає набір інструментів "
        "(tools) та ресурсів (resources), а MCP-клієнт (інтегрований у агентну систему) "
        "підключається до сервера і надає моделі доступ до цих інструментів. Протокол "
        "використовує JSON-RPC 2.0 для обміну повідомленнями та підтримує транспорти "
        "через stdio та HTTP."
    )
    add_body(doc,
        "Перевага MCP полягає у тому, що розробник зовнішнього інструменту не повинен знати "
        "деталі реалізації агентної системи — достатньо реалізувати MCP-сервер згідно "
        "специфікації. Аналогічно, агентна система може підключати будь-який MCP-сервер "
        "без зміни свого коду. Це створює екосистему взаємозамінних компонентів, подібну "
        "до екосистеми плагінів у IDE."
    )
    add_body(doc,
        "У контексті даної роботи підтримка MCP дозволяє розширювати набір доступних "
        "інструментів без перекомпіляції або перезапуску системи. Конфігурація MCP-серверів "
        "зберігається у JSON-файлі, а підключення відбувається при ініціалізації "
        "AssistantCore. Описи інструментів автоматично включаються у системний промпт "
        "планувальника."
    )

    add_heading_custom(doc, "1.5 Системи рецептів та автоматизації робочих процесів", level=2)

    add_body(doc,
        "Важливим аспектом зручності агентних систем є можливість збереження та повторного "
        "використання часто виконуваних послідовностей дій. У різних системах цей концепт "
        "реалізується під назвами «макроси», «сценарії», «рецепти» або «робочі процеси»."
    )
    add_body(doc,
        "Традиційні макро-системи (AutoHotkey, Apple Shortcuts) зберігають послідовність "
        "дій у жорсткому форматі: кожен крок визначений наперед і не може адаптуватися "
        "до змінних умов. Агентні системи дозволяють створювати «розумні рецепти», де "
        "кожен крок виконується через ReAct-цикл із можливістю адаптації."
    )
    add_body(doc,
        "У розробленій системі реалізовано механізм рецептів (Recipes), який дозволяє "
        "зберігати послідовності задач як JSON-файли та запускати їх через REST API або "
        "GUI. Рецепти можуть створюватися як вручну (через панель інтерфейсу), так і "
        "автоматично (через команду користувача до LLM, наприклад: «Створи рецепт "
        "Робочий ранок, який відкриватиме Discord та Safari»). Кожен рецепт містить "
        "список задач, опис та необов'язкові передумови (requirements)."
    )

    add_heading_custom(doc, "1.6 Висновки до розділу 1", level=2)

    add_body(doc,
        "Проведений аналіз предметної області дозволив сформулювати такі висновки. "
        "Еволюція засобів автоматизації від командних скриптів до AI-агентів відображає "
        "загальну тенденцію до підвищення інтелектуальності та зниження вимог до "
        "технічної підготовки користувача. Існуючі голосові помічники обмежені фіксованим "
        "набором сценаріїв, тоді як агентні системи на основі LLM здатні динамічно "
        "планувати та виконувати довільні послідовності дій."
    )
    add_body(doc,
        "Серед розглянутих фреймворків PydanticAI найкраще відповідає вимогам проєкту "
        "завдяки суворій типізації, нативній підтримці Google Gemini та протоколу MCP. "
        "Цикл ReAct обрано як основу для покрокового виконання задач через його "
        "адаптивність та здатність до самовиправлення."
    )

    page_break(doc)


# ── РОЗДІЛ 2 ───────────────────────────────────────────────────────────────

def create_chapter_2(doc):
    add_heading_custom(doc, "РОЗДІЛ 2 МЕТОДИ ТА ЗАСОБИ РОЗРОБКИ", level=1)

    add_heading_custom(doc, "2.1 Архітектура системи та потік обробки запитів", level=2)

    add_body(doc,
        "Архітектура розробленої системи побудована за принципом модульної декомпозиції "
        "із чітким розмежуванням рівнів відповідальності: рівень планування (визначає, "
        "що потрібно зробити), рівень виконання (реалізує конкретні операції) та рівень "
        "взаємодії (забезпечує зв'язок із користувачем). Центральним координатором "
        "виступає клас AssistantCore, який інкапсулює усі модулі та керує потоком "
        "обробки запитів."
    )
    add_body(doc,
        "Загальна схема обробки запиту складається з таких етапів. Текстовий запит "
        "користувача надходить через графічний інтерфейс (PySide6) до серверної частини "
        "(FastAPI). Модуль PrivacyGuard аналізує запит та маскує конфіденційні дані. "
        "Планувальник (PydanticAI Agent) генерує наступну задачу на основі запиту та "
        "результатів попередніх кроків. Задача проходить HITL-підтвердження. Виконавчий "
        "механізм реалізує задачу через відповідний обробник із реєстру інструментів. "
        "Результат повертається до планувальника для формування наступного кроку (цикл ReAct)."
    )
    add_body(doc,
        "Реєстр інструментів визначає 16 типів операцій, доступних системі: відкриття "
        "застосунків, виконання команд, створення та читання файлів, пошук в інтернеті, "
        "читання веб-сторінок, HTTP-запити, керування системними параметрами (гучність, "
        "скріншоти, інформація про батарею), виклик зовнішніх MCP-інструментів, індексація "
        "та пошук у локальній базі знань, управління рецептами."
    )
    add_body(doc,
        "Кожен тип операції відображається на конкретну функцію-обробник через словник "
        "TOOL_REGISTRY. Такий підхід забезпечує просте розширення системи: для додавання "
        "нового типу дії достатньо реалізувати обробник, додати запис у реєстр та "
        "відповідне значення в перерахування ActionTypeEnum."
    )

    # ── Діаграма прецедентів (Use Case) ──
    add_body(doc,
        "Для формалізації функціональних вимог побудовано діаграму прецедентів (Use Case), "
        "яка відображає основні сценарії взаємодії користувача із системою (рис. 2.1). "
        "Діаграма визначає одного основного актора — Користувач (User), який взаємодіє "
        "із системою через графічний інтерфейс."
    )
    add_body(doc,
        "Виділено такі прецеденти: «Ввести запит природною мовою» — базова точка входу; "
        "«Підтвердити/відхилити дію» — реалізація принципу HITL; «Переглянути результат "
        "виконання» — зворотний зв'язок; «Керувати рецептами» (створити, запустити, "
        "переглянути список) — повторне використання сценаріїв; «Змінити налаштування» — "
        "конфігурація системи; «Переглянути логи» — прозорість внутрішніх процесів. "
        "Прецедент «Ввести запит» включає (include) внутрішні прецеденти системи: "
        "«Маскувати PII» (PrivacyGuard), «Спланувати крок» (ReAct), «Виконати дію» "
        "(Tool Registry) та «Перевірити білий список» (Whitelist Validation)."
    )
    add_figure_placeholder(doc, "Рис. 2.1 — Діаграма прецедентів системи")

    # ── Діаграма компонентів ──
    add_body(doc,
        "Структуру системи на рівні модулів відображає діаграма компонентів (рис. 2.2). "
        "Система складається з п'яти основних компонентів: GUI Client (PySide6), "
        "API Server (FastAPI), Core Engine (AssistantCore, ReAct loop), Tool Registry "
        "(обробники 16 типів дій) та External Services (LLM Provider, MCP Servers)."
    )
    add_body(doc,
        "GUI Client зв'язаний із API Server через HTTP REST-інтерфейс (ендпоінти "
        "/step, /execute-single, /recipes, /settings). API Server делегує обробку "
        "запитів Core Engine, який координує PrivacyGuard, Planner Agent та "
        "Execution Engine. Planner Agent комунікує із зовнішнім LLM Provider через "
        "PydanticAI. Execution Engine викликає конкретні обробники з Tool Registry, "
        "деякі з яких звертаються до зовнішніх сервісів: DuckDuckGo (web_search), "
        "httpbin (http_request), MCP Servers (mcp_call). Модуль MessageRepository "
        "забезпечує персистентність діалогів через SQLite, а ChromaDB зберігає "
        "векторну базу знань для RAG-пошуку."
    )
    add_figure_placeholder(doc, "Рис. 2.2 — Діаграма компонентів системи")

    add_heading_custom(doc, "2.2 Цикл ReAct як метод покрокового виконання задач", level=2)

    add_body(doc,
        "Цикл ReAct (Reasoning and Acting) є центральним алгоритмічним рішенням системи, "
        "яке забезпечує адаптивне покрокове виконання складних запитів. На відміну від "
        "традиційного підходу, де вся послідовність дій планується наперед (що призводить "
        "до проблеми «сліпого планування», коли подальші кроки залежать від результатів "
        "попередніх), ReAct виконує по одному кроку за ітерацію."
    )
    add_body(doc,
        "Кожна ітерація циклу ReAct складається з трьох фаз. У фазі Reasoning (Міркування) "
        "модель аналізує поточний стан: вихідний запит користувача, результати попередніх "
        "кроків (stdout/stderr/код повернення), список доступних інструментів та обмеження "
        "безпеки. На основі цього аналізу модель генерує одну задачу — наступний крок "
        "виконання. У фазі Acting (Дія) задача проходить HITL-підтвердження та виконується "
        "через відповідний обробник з реєстру інструментів. Результат фіксується у вигляді "
        "структурованого спостереження. У фазі Observing (Спостереження) результат додається "
        "до контексту розмови, і цикл переходить до наступної ітерації."
    )
    add_body(doc,
        "Цикл завершується, коли модель генерує задачу з типом дії chat — це означає, "
        "що всі необхідні операції виконано і модель формує підсумкову відповідь "
        "для користувача. Додатково передбачено захисний механізм: максимальну кількість "
        "ітерацій (за замовчуванням 10), після якої цикл примусово зупиняється."
    )
    add_body(doc,
        "Переваги підходу ReAct для задач керування комп'ютером: можливість адаптації "
        "наступного кроку до реального результату попереднього (наприклад, вибір дії "
        "залежно від того, чи існує файл), автоматичне відновлення після помилок "
        "(модель аналізує stderr і може обрати альтернативний шлях), природне "
        "розділення складної задачі на елементарні кроки без необхідності передбачати "
        "всю послідовність заздалегідь."
    )
    add_body(doc,
        "Розглянемо конкретний приклад роботи ReAct-циклу для запиту «знайди погоду "
        "в Чернівцях і запиши у файл». На першій ітерації модель генерує задачу "
        "web_search з параметром query=\"погода Чернівці завтра\". Виконавчий механізм "
        "виконує пошук через DuckDuckGo і повертає результати. На другій ітерації "
        "модель аналізує результати пошуку та генерує web_read для найрелевантнішого "
        "посилання. Виконання повертає текст сторінки. На третій ітерації модель "
        "формує задачу write_file, де поле content містить реальні дані про погоду, "
        "отримані на попередніх кроках. На четвертій ітерації модель генерує задачу "
        "chat з підсумковим повідомленням для користувача."
    )
    add_body(doc,
        "Альтернативний підхід (одноразове планування) згенерував би задачу write_file "
        "з placeholder-контентом ще до отримання даних про погоду, що призвело б до "
        "некоректного результату. ReAct усуває цю проблему за рахунок послідовного "
        "формування кожного кроку на основі фактичних даних."
    )

    # ── Діаграма діяльності (Activity) — ReAct ──
    add_body(doc,
        "Алгоритм роботи ReAct-циклу представлено у вигляді діаграми діяльності (рис. 2.3). "
        "Початковою точкою є отримання запиту від користувача. Далі виконується маскування "
        "PII через PrivacyGuard. Після цього система входить у цикл: планувальник генерує "
        "наступний крок; виконується перевірка — якщо тип дії chat, цикл завершується і "
        "користувач отримує текстову відповідь. Якщо ні — задача відображається "
        "користувачу для HITL-підтвердження. При відхиленні цикл зупиняється. "
        "При підтвердженні задача виконується через відповідний обробник, результат "
        "додається до списку спостережень, і цикл повторюється. Захисна умова — "
        "перевірка максимальної кількості ітерацій."
    )
    add_figure_placeholder(doc, "Рис. 2.3 — Діаграма діяльності ReAct-циклу")

    add_body(doc,
        "Формально алгоритм ReAct можна описати як ітеративний процес. Нехай q — "
        "вхідний запит користувача, O — упорядкований список спостережень (порожній "
        "на початку), M — максимальна кількість ітерацій. На кожній ітерації i: "
        "модель приймає (q, O) та генерує задачу t_i; якщо t_i.action == chat, "
        "цикл завершується; інакше t_i виконується, результат r_i додається до O, "
        "і цикл переходить до ітерації i+1. Якщо i > M, цикл примусово зупиняється."
    )

    add_heading_custom(doc, "2.3 Механізми забезпечення безпеки та конфіденційності", level=2)

    add_body(doc,
        "Безпека є ключовою вимогою до архітектури системи, оскільки вона має доступ до "
        "файлової системи, командного рядка та мережевих запитів. У проєкті реалізовано "
        "три рівні захисту, кожен з яких адресує окремий клас загроз."
    )
    add_body(doc,
        "Перший рівень — PrivacyGuard (захист конфіденційних даних). Модуль аналізує "
        "вхідний текст за допомогою набору регулярних виразів для виявлення типових "
        "шаблонів конфіденційної інформації: ключі API (OpenAI, Gemini, AWS, GitHub, "
        "Stripe, Slack), JWT-токени, паролі, електронні адреси, номери платіжних карток "
        "та телефонні номери. Додатково використовується ентропійний аналіз на основі "
        "бібліотеки detect-secrets, який виявляє високоентропійні рядки у форматах "
        "Base64 та Hex. Усі знайдені фрагменти замінюються на плейсхолдери (наприклад, "
        "[EMAIL_1]) перед відправкою до хмарної моделі. Після отримання відповіді "
        "плейсхолдери розмасковуються назад до оригінальних значень для виконання реальних дій."
    )
    add_body(doc,
        "Другий рівень — білий список (Whitelist). Файл whitelist.json містить перелік "
        "дозволених застосунків, команд та скриптів. Валідація здійснюється на рівні "
        "конструктора Pydantic-моделі Task через декоратор model_validator: при спробі "
        "створити задачу з недозволеною дією виникає помилка валідації ще до етапу "
        "виконання. Це гарантує, що навіть у випадку маніпуляції з боку LLM жодна "
        "заборонена операція не буде передана виконавчому механізму."
    )
    add_body(doc,
        "Третій рівень — Human-in-the-Loop (HITL). Кожна задача перед виконанням "
        "відображається користувачу для підтвердження або відхилення. У графічному "
        "інтерфейсі задача представлена у вигляді картки із зрозумілим описом дії, "
        "і користувач приймає рішення натисканням відповідної кнопки. Це забезпечує "
        "повний контроль людини над усіма операціями системи і відповідає принципу "
        "«жодна незворотна дія без явної згоди»."
    )

    # ── Діаграма послідовності (Sequence) ──
    add_body(doc,
        "Взаємодію компонентів системи під час обробки одного запиту ілюструє "
        "діаграма послідовності (рис. 2.4). На діаграмі представлено п'ять об'єктів: "
        "User (користувач), GUI (PySide6), API Server (FastAPI), AssistantCore та "
        "LLM Provider (Google Gemini)."
    )
    add_body(doc,
        "Послідовність подій: User вводить запит у GUI; GUI відправляє POST /step "
        "до API Server; API Server викликає метод react_step класу AssistantCore; "
        "AssistantCore передає запит через PrivacyGuard (маскування PII), формує "
        "промпт із контекстом попередніх спостережень і відправляє до LLM Provider. "
        "LLM повертає структурований об'єкт Plan із однією задачею. API Server "
        "повертає задачу до GUI. GUI відображає картку задачі та чекає підтвердження "
        "від User. Після підтвердження GUI відправляє POST /execute-single; "
        "AssistantCore виконує задачу через Tool Registry та повертає TaskResult. "
        "GUI знову викликає POST /step із накопиченими спостереженнями для "
        "отримання наступного кроку або фінальної відповіді."
    )
    add_figure_placeholder(doc, "Рис. 2.4 — Діаграма послідовності обробки запиту")

    add_heading_custom(doc, "2.4 Технологічний стек проєкту", level=2)

    add_body(doc,
        "Вибір технологій для реалізації системи зумовлений вимогами до типобезпечності, "
        "кросплатформності та інтеграції із сучасними AI-сервісами. Нижче наведено "
        "основні компоненти технологічного стеку та обґрунтування їх вибору."
    )

    add_table_custom(doc,
        ["Компонент", "Технологія", "Версія", "Призначення"],
        [
            ["Мова програмування", "Python", "3.12", "Основна мова розробки"],
            ["AI-фреймворк", "PydanticAI", "1.63", "Типобезпечна взаємодія з LLM"],
            ["Мовна модель", "Google Gemini", "2.5 Flash", "Розуміння намірів та планування"],
            ["Валідація даних", "Pydantic", "2.11", "Схеми задач, конфігурація"],
            ["Веб-фреймворк", "FastAPI", "0.136", "REST API серверної частини"],
            ["GUI", "PySide6", "6.11", "Настільний графічний інтерфейс"],
            ["Векторна база", "ChromaDB", "1.5", "Локальна база знань (RAG)"],
            ["Пакування", "PyInstaller", "6.13", "Кросплатформна збірка"],
        ],
        caption="Таблиця 2.1 — Технологічний стек проєкту"
    )

    add_body(doc,
        "Python обрано як основну мову розробки завдяки розвиненій екосистемі AI-бібліотек, "
        "динамічній типізації із підтримкою анотацій типів та кросплатформності. Версія 3.12 "
        "забезпечує сумісність із усіма використаними залежностями та містить покращення "
        "продуктивності інтерпретатора."
    )
    add_body(doc,
        "Google Gemini обрано як основну мовну модель завдяки конкурентоспроможній якості "
        "розуміння тексту, підтримці структурованого виводу (structured output) для генерації "
        "типобезпечних JSON-відповідей та доступній ціновій політиці. Модель Gemini 2.5 Flash "
        "забезпечує оптимальне співвідношення між швидкістю відповіді та якістю генерації."
    )
    add_body(doc,
        "FastAPI використано для побудови REST API серверної частини. Фреймворк надає "
        "автоматичну генерацію OpenAPI-документації, асинхронну обробку запитів через "
        "ASGI та інтеграцію з Pydantic для валідації вхідних та вихідних даних."
    )
    add_body(doc,
        "PySide6 (офіційні Python-біндинги для Qt 6) обрано для побудови графічного "
        "інтерфейсу. На відміну від веб-інтерфейсу, настільний застосунок забезпечує "
        "пряму інтеграцію з операційною системою, підтримку always-on-top режиму та "
        "системного трея, а також не потребує запуску браузера."
    )
    add_body(doc,
        "Model Context Protocol (MCP) — відкритий стандарт, запропонований Anthropic, "
        "який визначає протокол взаємодії мовних моделей із зовнішніми інструментами. "
        "Підтримка MCP дозволяє розширювати набір доступних інструментів без зміни "
        "базового коду системи, підключаючи зовнішні MCP-сервери."
    )

    add_heading_custom(doc, "2.5 Система рецептів та повторне використання сценаріїв", level=2)

    add_body(doc,
        "Для забезпечення ефективності повторюваних операцій у системі реалізовано "
        "механізм рецептів. Рецепт — це іменована послідовність задач (об'єктів Task), "
        "збережена у JSON-файлі в каталозі src/recipes/. Кожен рецепт містить назву, "
        "опис, список задач та необов'язковий список передумов (requirements)."
    )
    add_body(doc,
        "Рецепти створюються трьома способами. Перший — ручне створення через REST API "
        "(POST /recipes). Другий — створення через LLM: користувач формулює запит "
        "природною мовою (наприклад, «Створи рецепт Робочий ранок, що відкриватиме "
        "Discord та Safari»), і планувальник генерує задачу з action=save_recipe, "
        "параметри якої містять назву та список кроків рецепту. Третій — запуск "
        "через GUI: панель рецептів відображає збережені рецепти з назвою та описом, "
        "і користувач може запустити будь-який натисканням кнопки."
    )
    add_body(doc,
        "Передумови (requirements) дозволяють рецепту декларативно вказати, які "
        "системні компоненти потрібні для його виконання (наприклад, доступність "
        "певної команди або мережевого ресурсу). Перевірка передумов виконується "
        "до запуску рецепту; у разі невідповідності виконання блокується з "
        "поясненням причини."
    )

    add_heading_custom(doc, "2.6 Локальна база знань та семантичний пошук", level=2)

    add_body(doc,
        "Для забезпечення роботи системи з локальними документами користувача "
        "реалізовано модуль RAG (Retrieval-Augmented Generation) на основі "
        "векторної бази даних ChromaDB. Модуль дозволяє індексувати файли та "
        "каталоги за допомогою дії index_knowledge та виконувати семантичний "
        "пошук за допомогою дії search_knowledge."
    )
    add_body(doc,
        "При індексації файли розбиваються на фрагменти (chunks) фіксованого "
        "розміру, для кожного фрагменту обчислюється векторне представлення "
        "(embedding) за допомогою вбудованої моделі ChromaDB. Вектори зберігаються "
        "локально на диску користувача — жодні дані не передаються у хмару."
    )
    add_body(doc,
        "При пошуку запит користувача також перетворюється на вектор, і ChromaDB "
        "знаходить найбільш семантично близькі фрагменти. Результати пошуку "
        "передаються LLM як додатковий контекст для генерації відповіді. "
        "Цей підхід дозволяє системі відповідати на питання про зміст локальних "
        "документів без необхідності відправляти повний текст файлів до хмарної моделі."
    )

    add_heading_custom(doc, "2.7 Висновки до розділу 2", level=2)

    add_body(doc,
        "У розділі обґрунтовано архітектурні та методологічні рішення проєкту. Модульна "
        "архітектура з реєстром інструментів забезпечує розширюваність системи. "
        "Цикл ReAct усуває проблему «сліпого планування» та забезпечує адаптивне "
        "виконання. Трирівнева модель безпеки (PrivacyGuard, Whitelist, HITL) адресує "
        "ключові загрози при наданні AI-системі доступу до операційної системи."
    )

    page_break(doc)


# ── РОЗДІЛ 3 ───────────────────────────────────────────────────────────────

def create_chapter_3(doc):
    add_heading_custom(doc, "РОЗДІЛ 3 ПРОГРАМНА РЕАЛІЗАЦІЯ СИСТЕМИ", level=1)

    add_heading_custom(doc, "3.1 Структура проєкту та організація модулів", level=2)

    add_body(doc,
        "Програмна реалізація системи складається з 40 Python-модулів загальним обсягом "
        "близько 8 300 рядків коду, організованих у структуру каталогів за функціональним "
        "призначенням. Кореневий каталог src/ є точкою запуску та базою для усіх імпортів."
    )

    add_table_custom(doc,
        ["Каталог", "Призначення", "Основні модулі"],
        [
            ["src/core/", "Ядро системи", "assistant.py, planner.py, engine.py, schemas.py"],
            ["src/tools/", "Обробники дій", "registry.py, handlers.py, web_handlers.py"],
            ["src/api/", "REST API", "server.py, schemas.py"],
            ["src/ui/", "Графічний інтерфейс", "main_window.py, app.py, input_bar.py"],
            ["src/recipes/", "Збережені рецепти", "*.json (задачі, передумови)"],
            ["src/infrastructure/", "Інфраструктура", "llm_client.py"],
            ["src/integrations/", "Зовнішні інтеграції", "mcp_client.py, mcp_config.py"],
        ],
        caption="Таблиця 3.1 — Структура каталогів проєкту"
    )

    add_body(doc,
        "Центральним модулем системи є src/core/assistant.py, який містить клас "
        "AssistantCore — основний координатор усієї логіки обробки запитів. Клас "
        "інкапсулює модулі PrivacyGuard, MessageRepository, SessionState, "
        "ExecutionEngine та MCPManager, забезпечуючи їх узгоджену роботу."
    )
    add_body(doc,
        "Модуль src/core/schemas.py визначає центральні структури даних системи. "
        "Модель Task описує окрему задачу із полями action (тип дії з переліку ActionTypeEnum), "
        "name (назва команди або тексту відповіді), description (опис для відображення "
        "в інтерфейсі) та params (параметри у форматі словника). Модель TaskResult "
        "інкапсулює результат виконання задачі: вихідний потік, потік помилок, код "
        "повернення та тривалість виконання."
    )

    code_schemas = '''\
class Task(BaseModel):
    action: ActionTypeEnum
    name: str = Field(
        description="For action='chat': the FULL reply text. "
        "For other actions: the command or tool name."
    )
    description: str = Field(default="", ...)
    params: Dict[str, str | list[str] | None] = {}

    @model_validator(mode="after")
    def check_allowed(self) -> "Task":
        if self.action == ActionTypeEnum.CHAT:
            return self
        with open(_WHITELIST_PATH) as f:
            wl = json.load(f)
        mapping = {ActionTypeEnum.OPEN_APP: wl["allowed_apps"]}
        allowed = mapping.get(self.action)
        if allowed and self.name not in allowed:
            raise ValueError(f"'{self.name}' not allowed")
        return self'''
    add_listing(doc, code_schemas, caption="Лістинг 3.1 — Модель Task із валідацією білого списку")

    add_body(doc,
        "Перерахування ActionTypeEnum визначає 16 типів дій, підтримуваних системою: "
        "open_app, run_command, chat, write_file, read_file, search_knowledge, "
        "index_knowledge, web_search, image_search, web_read, http_request, mcp_call, "
        "system_control, save_recipe, run_recipe, list_recipes. Кожен тип відображається "
        "на конкретний обробник через реєстр інструментів."
    )

    # ── Діаграма класів ──
    add_body(doc,
        "Відносини між основними класами ядра системи відображає діаграма класів "
        "(рис. 3.1). Центральним класом є AssistantCore, який агрегує PrivacyGuard, "
        "MessageRepository, SessionState, ExecutionEngine та MCPManager. "
        "AssistantCore залежить від PydanticAI Agent (планувальник) та використовує "
        "моделі Task, Plan і TaskResult зі schemas.py."
    )
    add_body(doc,
        "ExecutionEngine використовує TOOL_REGISTRY (словник, що відображає назву дії "
        "на функцію-обробник) та SessionState для доступу до контексту сесії. "
        "Модель Task має валідатор check_allowed, який звертається до whitelist.json. "
        "Модель Plan містить список об'єктів Task та необов'язкове поле reasoning. "
        "MCPManager керує підключенням зовнішніх MCP-серверів та надає метод list_tools "
        "для отримання переліку доступних інструментів."
    )
    add_figure_placeholder(doc, "Рис. 3.1 — Діаграма класів ядра системи")

    add_heading_custom(doc, "3.2 Реалізація планувальника", level=2)

    add_body(doc,
        "Планувальник (planner) відповідає за перетворення запиту природною мовою на "
        "структуровану задачу. Реалізований як PydanticAI Agent з типом виводу Plan "
        "(список об'єктів Task). Системний промпт планувальника динамічно генерується "
        "під час ініціалізації і включає перелік дозволених застосунків та команд "
        "з файлу whitelist.json, інформацію про операційну систему, доступні рецепти "
        "та описи MCP-інструментів."
    )
    add_body(doc,
        "Ключовою характеристикою планувальника є його робота в режимі «один крок за "
        "ітерацію»: замість генерації повного плану він повертає лише наступну дію. "
        "Це забезпечується відповідною інструкцією у системному промпті та контекстом "
        "попередніх спостережень, які передаються як частина розмови."
    )
    add_body(doc,
        "Системний промпт планувальника є складним документом, що динамічно генерується "
        "функцією build_system_prompt. Він включає: опис ролі моделі як планувальника "
        "операційної системи; інформацію про поточну ОС; перелік дозволених застосунків "
        "та команд з whitelist.json; правила формування задач для кожного типу дії "
        "(open_app, run_command, write_file, web_search тощо); інструкції щодо "
        "форматування відповідей у Markdown; обмеження безпеки (ніколи не вигадувати "
        "URL, не використовувати HTML-теги); перелік доступних рецептів; та опис "
        "MCP-інструментів, якщо вони підключені."
    )
    add_body(doc,
        "Загальний обсяг системного промпту складає приблизно 3 000 токенів, що "
        "забезпечує модель достатньою інформацією для прийняття рішень. Промпт "
        "розроблено ітеративно на основі тестування різних сценаріїв використання, "
        "з особливою увагою до граничних випадків: коли модель помилково генерує "
        "HTML замість Markdown, коли вигадує URL для зображень, коли намагається "
        "виконати дію без попередньої перевірки наявності інструменту."
    )

    add_body(doc,
        "Метод _react_loop класу AssistantCore реалізує основний цикл обробки. "
        "На кожній ітерації він формує промпт із результатами попередніх кроків, "
        "передає його планувальнику, отримує наступну задачу та виконує її. "
        "Результат зберігається у списку спостережень і передається на наступну ітерацію."
    )

    code_react = '''\
def _react_loop(self, user_input, masked_input):
    observations: list[TaskResult] = []
    max_iter = settings.REACT_MAX_ITERATIONS

    for iteration in range(max_iter):
        prompt = self._build_react_prompt(masked_input, observations)
        plan = self._get_plan(prompt)
        plan = _unmask_plan(plan, self.session.pii_map)

        if plan.tasks[0].action == ActionTypeEnum.CHAT:
            reply = _extract_chat_reply(plan)
            return QueryResult(reply=reply, task_results=observations)

        task = plan.tasks[0]
        if not self._confirm(f"Execute {task.action.value}?"):
            observations.append(TaskResult(task=task, skipped=True))
            break

        result = self.engine.run_single(task, pre_approved=True)
        observations.append(result)

    return QueryResult(task_results=observations)'''
    add_listing(doc, code_react, caption="Лістинг 3.2 — Цикл ReAct у класі AssistantCore")

    add_heading_custom(doc, "3.3 Реєстр інструментів та виконавчий механізм", level=2)

    add_body(doc,
        "Реєстр інструментів (TOOL_REGISTRY) реалізований як Python-словник, що "
        "відображає рядкові ідентифікатори дій на відповідні функції-обробники. "
        "Такий підхід дозволяє додавати нові типи дій через простий запис у словник "
        "без модифікації логіки диспетчеризації."
    )

    code_registry = '''\
TOOL_REGISTRY: dict[str, Callable] = {
    "open_app": open_app,
    "run_command": run_command,
    "write_file": write_file,
    "read_file": read_file,
    "web_search": web_search,
    "web_read": web_read,
    "http_request": http_request,
    "mcp_call": mcp_call,
    "system_control": system_control,
    "save_recipe": handle_save_recipe,
    "run_recipe": handle_run_recipe,
    # ...
}'''
    add_listing(doc, code_registry, caption="Лістинг 3.3 — Реєстр інструментів (TOOL_REGISTRY)")

    add_body(doc,
        "Виконавчий механізм (клас ExecutionEngine) відповідає за диспетчеризацію "
        "задач до відповідних обробників, збір результатів виконання та вимірювання "
        "часу. Для кожної задачі Engine витягує функцію з реєстру за ключем "
        "task.action.value, передає їй параметри та формує об'єкт TaskResult."
    )
    add_body(doc,
        "Обробники операційної системи реалізовані за патерном Strategy: "
        "абстрактний клас BaseOSHandler визначає інтерфейс (open_application, "
        "run_shell), а конкретні реалізації PosixHandler та WindowsHandler "
        "забезпечують специфічну логіку для відповідних платформ. Фабричний "
        "метод get_os_handler() обирає реалізацію на основі platform.system()."
    )

    add_heading_custom(doc, "3.4 Модуль захисту конфіденційності PrivacyGuard", level=2)

    add_body(doc,
        "Модуль PrivacyGuard реалізує першу лінію захисту персональних даних "
        "у системі. Його основне завдання — виявити та замаскувати конфіденційну "
        "інформацію у тексті запиту до його відправки великій мовній моделі."
    )

    code_privacy = '''\
class PrivacyGuard:
    def mask(self, text: str) -> tuple[str, dict[str, str]]:
        mapping: dict[str, str] = {}
        for label, pattern in _PATTERNS:
            for match in re.finditer(pattern, text):
                original = match.group()
                placeholder = f"[{label}_{counter}]"
                mapping[placeholder] = original
                text = text.replace(original, placeholder)
        entropy_secrets = _entropy_scan(text)
        for val in entropy_secrets:
            placeholder = f"[ENTROPY_{counter}]"
            mapping[placeholder] = val
            text = text.replace(val, placeholder, 1)
        return text, mapping

    def unmask(self, text: str, mapping) -> str:
        for placeholder, original in mapping.items():
            text = text.replace(placeholder, original)
        return text'''
    add_listing(doc, code_privacy, caption="Лістинг 3.4 — Клас PrivacyGuard")

    add_body(doc,
        "Модуль використовує 12 попередньо визначених регулярних виразів для "
        "розпізнавання різних типів конфіденційної інформації: ключі OpenAI, "
        "Gemini, AWS, GitHub, Stripe, Slack, JWT-токени, паролі, електронні "
        "адреси, номери платіжних карток та телефони. Додатково застосовується "
        "ентропійний аналіз на основі бібліотеки detect-secrets для виявлення "
        "випадкових високоентропійних рядків у кодуваннях Base64 та Hex."
    )
    add_body(doc,
        "Метод mask повертає кортеж із замаскованого тексту та словника "
        "відповідностей (mapping). Цей словник використовується методом unmask "
        "після отримання відповіді від LLM для відновлення оригінальних значень "
        "при фактичному виконанні операцій."
    )

    add_heading_custom(doc, "3.5 REST API та серверна частина", level=2)

    add_body(doc,
        "Серверна частина системи побудована на FastAPI та надає REST API для "
        "взаємодії з графічним інтерфейсом. Ключові ендпоінти організовані "
        "за функціональними групами."
    )

    add_table_custom(doc,
        ["Метод", "Ендпоінт", "Призначення"],
        [
            ["POST", "/step", "Один крок ReAct-циклу (планування)"],
            ["POST", "/execute-single", "Виконання однієї задачі"],
            ["POST", "/query", "Повний цикл обробки запиту"],
            ["GET", "/status", "Стан сервера та сесії"],
            ["GET", "/history", "Історія повідомлень сесії"],
            ["GET/POST", "/recipes", "Управління рецептами"],
            ["GET/PATCH", "/settings", "Читання/зміна налаштувань"],
            ["GET", "/health", "Перевірка доступності"],
        ],
        caption="Таблиця 3.2 — Основні ендпоінти REST API"
    )

    add_body(doc,
        "Ендпоінт POST /step реалізує серверну частину циклу ReAct. Він приймає "
        "поточний запит користувача та список попередніх спостережень (observations), "
        "передає їх до AssistantCore.react_step і повертає наступну задачу або "
        "фінальну відповідь. Графічний інтерфейс послідовно викликає /step для "
        "отримання кожного наступного кроку, а /execute-single — для його виконання."
    )
    add_body(doc,
        "Управління рецептами реалізовано через REST API: GET /recipes повертає "
        "список рецептів, POST /recipes створює новий, POST /recipes/{name}/run "
        "запускає існуючий. Кожен рецепт зберігається як JSON-файл у каталозі "
        "src/recipes/."
    )
    add_body(doc,
        "Налаштування системи (розмір шрифту, видимість логів, максимальна "
        "кількість кроків ReAct, автоматичне підтвердження тощо) зберігаються "
        "у файлі .env і доступні через ендпоінти GET /settings та PATCH /settings. "
        "Зміни застосовуються до об'єкта Settings в пам'яті та одночасно "
        "записуються у .env для персистентності."
    )

    add_heading_custom(doc, "3.6 Графічний інтерфейс користувача", level=2)

    add_body(doc,
        "Графічний інтерфейс реалізовано у вигляді настільного застосунку на базі "
        "PySide6. Основним елементом є вікно FloatingBar — безрамкове, завжди "
        "поверх інших вікон (always-on-top), яке можна вільно перетягувати по екрану. "
        "Застосунок також інтегрується із системним треєм для швидкого приховування "
        "та відновлення. Загальний вигляд головного вікна застосунку представлено на рис. 3.2."
    )
    add_figure_placeholder(doc, "Рис. 3.2 — Головне вікно графічного інтерфейсу")

    add_body(doc,
        "Інтерфейс складається з таких компонентів: поле введення (InputBar) з "
        "текстовим полем та кнопкою відправки; тамагочі-віджет (TamagotchiWidget) — "
        "анімований каомоджі-персонаж, емоція якого змінюється залежно від стану "
        "системи; панель статусу (StatusPanel) з картками задач, де кожна картка "
        "містить опис дії, індикатор стану та кнопки підтвердження/відхилення; "
        "панель рецептів (RecipePanel) для перегляду та запуску збережених "
        "послідовностей дій; панель налаштувань (SettingsPanel) для динамічної "
        "зміни параметрів системи."
    )
    add_body(doc,
        "Взаємодія з сервером здійснюється через HTTP-клієнт AkashiApiClient, "
        "який працює у окремому QThread для запобігання блокуванню інтерфейсу. "
        "Клієнт використовує механізм сигналів Qt для повідомлення основного "
        "потоку про результати запитів."
    )
    add_body(doc,
        "Покроковий режим взаємодії реалізовано через стан-машину: після введення "
        "запиту GUI відправляє його на /step, отримує першу задачу, відображає "
        "картку з описом та кнопками підтвердження. Після підтвердження виконує "
        "задачу через /execute-single, отримує результат і знову викликає /step "
        "із накопиченими спостереженнями. Цикл повторюється до отримання фінальної "
        "відповіді (done=true)."
    )
    add_body(doc,
        "Тамагочі-віджет реалізує анімований каомоджі-персонаж, емоція якого "
        "змінюється залежно від поточного стану системи. Модуль emotions.py "
        "визначає перерахування Emotion (happy, thinking, sad, excited, sleeping "
        "тощо) та клас TimeOfDay для врахування часу доби. Маппер емоцій "
        "використовує правила: при обробці запиту — thinking, при успішному "
        "виконанні — happy, при помилці — sad, при бездіяльності — sleeping. "
        "Персонаж анімується через QPropertyAnimation з ефектом bounce."
    )
    add_body(doc,
        "Панель рецептів (RecipePanel) відображає список усіх збережених "
        "рецептів із назвою та описом. Кожен рецепт має кнопку запуску (▶), "
        "яка ініціює виконання всіх кроків рецепту через REST API "
        "POST /recipes/{name}/run. Результати кожного кроку послідовно "
        "відображаються в інтерфейсі."
    )

    add_body(doc,
        "Процес покрокового виконання запиту в інтерфейсі представлено на рис. 3.3. "
        "Кожна задача відображається як картка із зазначенням типу дії, назви "
        "та кнопками підтвердження (✓) та відхилення (✗). Після виконання картка "
        "змінює колір індикатора: зелений — успішно, червоний — помилка, "
        "сірий — пропущено користувачем."
    )
    add_figure_placeholder(doc, "Рис. 3.3 — Покрокове виконання запиту в GUI")

    add_body(doc,
        "Панель рецептів (рис. 3.4) відображає збережені рецепти у вигляді списку "
        "із назвою, описом та кнопкою запуску. Панель налаштувань дозволяє змінювати "
        "параметри системи: розмір шрифту, відображення логів, кількість ReAct-ітерацій "
        "та автоматичне підтвердження задач."
    )
    add_figure_placeholder(doc, "Рис. 3.4 — Панель рецептів та панель налаштувань")

    add_body(doc,
        "Індикатор з'єднання у верхній частині вікна показує стан зв'язку "
        "з сервером: зелена крапка при активному з'єднанні, червона — при "
        "відсутності. Перевірка здійснюється регулярним запитом на ендпоінт "
        "GET /health. При втраті з'єднання інтерфейс блокує поле введення "
        "та відображає відповідне повідомлення."
    )

    add_heading_custom(doc, "3.7 Управління сесією та збереження контексту", level=2)

    add_body(doc,
        "Клас SessionState забезпечує збереження стану поточної сесії користувача. "
        "Стан включає: унікальний ідентифікатор сесії (UUID), історію повідомлень "
        "(message_history), лічильник кроків ReAct, посилання на MCPManager та "
        "функцію підтвердження. Історія повідомлень зберігається у SQLite базі "
        "даних через клас MessageRepository."
    )
    add_body(doc,
        "MessageRepository забезпечує персистентне зберігання діалогів між "
        "перезапусками системи. При ініціалізації AssistantCore завантажуються "
        "останні N повідомлень (параметр MEMORY_TURNS у конфігурації), що дозволяє "
        "моделі враховувати контекст попередніх запитів. Кожне повідомлення "
        "серіалізується у JSON та зберігається з прив'язкою до ідентифікатора сесії."
    )
    add_body(doc,
        "Механізм follow-up запитів працює на основі історії повідомлень: коли "
        "користувач ставить контекстне питання (наприклад, «А яка погода там була "
        "вчора?» після попереднього запиту про погоду), планувальник бачить "
        "результати попередніх кроків у message_history і може відповісти без "
        "повторного виклику інструментів. Системний промпт містить явну інструкцію: "
        "«Conversation history is provided via message_history — use it directly "
        "for questions about prior turns, do not call tools to retrieve it»."
    )

    add_heading_custom(doc, "3.8 Система конфігурації та налаштувань", level=2)

    add_body(doc,
        "Конфігурація системи реалізована через клас Settings на основі "
        "pydantic-settings, який автоматично зчитує параметри з файлу .env "
        "та змінних оточення. Клас визначає усі налаштування з типами та "
        "значеннями за замовчуванням."
    )

    add_table_custom(doc,
        ["Параметр", "Тип", "Значення за замовч.", "Призначення"],
        [
            ["LLM_PROVIDER", "str", "google", "Постачальник LLM"],
            ["MODEL_NAME", "str", "gemini-2.5-flash", "Назва моделі"],
            ["REACT_MAX_STEPS", "int", "10", "Макс. кроків ReAct"],
            ["API_AUTO_APPROVE", "bool", "false", "Автопідтвердження"],
            ["PRIVACY_ENTROPY_BASE64", "float", "4.5", "Поріг ентропії Base64"],
            ["MEMORY_TURNS", "int", "20", "Кількість повідомлень в пам'яті"],
            ["MCP_CONFIG_PATH", "str", "mcp.json", "Шлях до конфігурації MCP"],
        ],
        caption="Таблиця 3.3 — Основні параметри конфігурації"
    )

    add_body(doc,
        "Зміна налаштувань через REST API (PATCH /settings) одночасно оновлює "
        "об'єкт Settings в пам'яті та записує зміни у файл .env для "
        "персистентності. Секретні поля (API_KEY) не записуються у .env "
        "через REST API з міркувань безпеки."
    )

    add_heading_custom(doc, "3.9 Кросплатформна підтримка", level=2)

    add_body(doc,
        "Система спроєктована для роботи на трьох основних десктопних платформах: "
        "macOS, Windows та Linux. Кросплатформність забезпечується на двох рівнях."
    )
    add_body(doc,
        "На рівні виконання системних команд реалізовано патерн Strategy. "
        "Абстрактний клас BaseOSHandler визначає інтерфейс з методами "
        "open_application та run_shell. Клас PosixHandler реалізує ці методи "
        "для macOS та Linux (використовуючи subprocess та платформо-специфічні "
        "команди, наприклад open на macOS, xdg-open на Linux). Клас "
        "WindowsHandler забезпечує роботу на Windows (використовуючи os.startfile "
        "та PowerShell). Фабричний метод get_os_handler() обирає конкретну "
        "реалізацію на основі виклику platform.system()."
    )
    add_body(doc,
        "На рівні графічного інтерфейсу кросплатформність забезпечується "
        "фреймворком PySide6, який надає єдиний Python API для всіх платформ. "
        "Система збирається у виконуваний файл для кожної платформи за допомогою "
        "PyInstaller: .app для macOS, .exe для Windows, ELF для Linux."
    )
    add_body(doc,
        "Модуль fonts.py забезпечує кросплатформне визначення сімейства шрифтів: "
        "система обирає найкращий доступний шрифт для кожної платформи "
        "(San Francisco на macOS, Segoe UI на Windows, Noto Sans на Linux) "
        "із резервними варіантами."
    )

    add_heading_custom(doc, "3.10 Інтеграція з MCP-серверами", level=2)

    add_body(doc,
        "Підтримка протоколу MCP реалізована через модулі src/integrations/mcp_client.py "
        "та src/integrations/mcp_config.py. Клас MCPManager управляє життєвим циклом "
        "підключень до зовнішніх MCP-серверів: запуск (start), зупинка (stop), "
        "отримання списку доступних інструментів (list_tools) та виклик конкретного "
        "інструменту (call_tool)."
    )
    add_body(doc,
        "Конфігурація MCP-серверів зберігається у JSON-файлі (за замовчуванням mcp.json). "
        "Кожен запис містить команду запуску сервера, аргументи та змінні оточення. "
        "При ініціалізації AssistantCore MCPManager запускає усі сконфігуровані сервери "
        "та отримує перелік їхніх інструментів. Ці описи автоматично додаються до "
        "системного промпту планувальника через функцію format_mcp_tools_section."
    )
    add_body(doc,
        "Виклик MCP-інструменту здійснюється через action=mcp_call у задачі. Обробник "
        "у реєстрі інструментів передає назву інструменту та параметри до MCPManager, "
        "який маршрутизує виклик до відповідного MCP-сервера через JSON-RPC 2.0. "
        "Результат повертається як стандартний TaskResult із stdout та stderr."
    )
    add_body(doc,
        "Така архітектура дозволяє підключати довільні зовнішні інструменти без "
        "модифікації коду системи. Наприклад, MCP-сервер для роботи з базами даних, "
        "сервер для генерації зображень або сервер для інтеграції з корпоративними "
        "системами — усі вони підключаються через єдиний конфігураційний файл."
    )

    add_heading_custom(doc, "3.11 Обробка веб-запитів та HTTP API", level=2)

    add_body(doc,
        "Система підтримує три типи мережевих операцій: пошук в інтернеті (web_search), "
        "читання веб-сторінок (web_read) та виклик довільних HTTP API (http_request). "
        "Кожна операція реалізована як окремий обробник у модулі src/tools/web_handlers.py."
    )
    add_body(doc,
        "Обробник web_search використовує бібліотеку DuckDuckGo Search для виконання "
        "пошукових запитів без необхідності API-ключа. Результати повертаються у форматі "
        "JSON із полями title, url та snippet для кожного знайденого ресурсу. Кількість "
        "результатів обмежується параметром max_results (за замовчуванням 5)."
    )
    add_body(doc,
        "Обробник web_read завантажує вміст веб-сторінки за вказаним URL та витягує "
        "основний текстовий контент, видаляючи навігацію, рекламу та інші непотрібні "
        "елементи. Це дозволяє моделі працювати з чистим текстом сторінки без "
        "зайвого HTML-шуму."
    )
    add_body(doc,
        "Обробник http_request забезпечує виклик довільних HTTP API із підтримкою "
        "методів GET, POST, PUT, DELETE, налаштування заголовків, передачі JSON-тіла "
        "та таймауту. Цей обробник використовується для інтеграції з зовнішніми "
        "сервісами, наприклад GitHub API для отримання інформації про репозиторії."
    )

    add_heading_custom(doc, "3.12 Висновки до розділу 3", level=2)

    add_body(doc,
        "У розділі описано програмну реалізацію усіх ключових компонентів системи. "
        "Модульна архітектура з чітким розмежуванням відповідальностей (планування, "
        "оркестрація, виконання, захист, інтерфейс) забезпечує можливість незалежного "
        "розвитку кожного компонента. Типобезпечні Pydantic-схеми гарантують "
        "коректність даних на кожному етапі обробки. Патерн Registry дозволяє "
        "розширювати набір підтримуваних операцій без зміни логіки диспетчеризації. "
        "Підтримка протоколу MCP забезпечує розширюваність системи через зовнішні "
        "сервери інструментів без модифікації ядра."
    )

    page_break(doc)


# ── РОЗДІЛ 4 ───────────────────────────────────────────────────────────────

def create_chapter_4(doc):
    add_heading_custom(doc, "РОЗДІЛ 4 ТЕСТУВАННЯ ТА ВЕРИФІКАЦІЯ СИСТЕМИ", level=1)

    add_heading_custom(doc, "4.1 Стратегія тестування та класифікація сценаріїв", level=2)

    add_body(doc,
        "Тестування системи проведено на основі сценарного підходу. Сценарії "
        "побудовано від простих до складних, щоб забезпечити покриття функціоналу "
        "за принципом наростання складності. Кожен сценарій імітує реальну задачу "
        "звичайного користувача та перевіряє конкретну функціональну підсистему."
    )

    add_table_custom(doc,
        ["№", "Категорія", "Кількість сценаріїв", "Компоненти, що перевіряються"],
        [
            ["1", "Базові операції", "5", "Chat, open_app, system_control, write_file"],
            ["2", "Інтернет-операції", "3", "web_search, web_read, http_request"],
            ["3", "Контекст і пам'ять", "2", "message_history, follow-up запити"],
            ["4", "Безпека", "3", "PrivacyGuard, Whitelist, HITL"],
            ["5", "Рецепти", "3", "save_recipe, run_recipe, UI-рецепти"],
            ["6", "Складні сценарії", "3", "Багатокроковий ReAct, умовна логіка, RAG"],
            ["7", "Налаштування", "2", "Settings UI, Log panel"],
        ],
        caption="Таблиця 4.1 — Класифікація тестових сценаріїв"
    )

    add_heading_custom(doc, "4.2 Тестування базових операцій", level=2)

    add_body(doc,
        "Сценарій «Просте спілкування» перевіряє здатність системи коректно "
        "розпізнавати чат-запити та генерувати відповіді без виклику інструментів. "
        "Введено запит «Привіт! Що ти вмієш?» — система повернула структуровану "
        "відповідь з переліком можливостей у форматі Markdown-списку. Тамагочі-персонаж "
        "змінив стан з thinking на happy, що підтверджує коректну роботу емоційного "
        "маппера."
    )
    add_body(doc,
        "Сценарій «Відкриття застосунку» перевіряє ланцюжок від розпізнавання "
        "наміру до фактичного запуску програми. Запит «Відкрий Safari» розпізнано "
        "як action=open_app, Safari знайдено у білому списку, відображено HITL-картку "
        "з описом дії, після підтвердження застосунок успішно відкрито. Для перевірки "
        "security boundary введено запит «Відкрий Chrome» — Pydantic-валідатор "
        "відхилив задачу з поясненням, що Chrome відсутній у whitelist."
    )
    add_body(doc,
        "Сценарій «Керування системою» включав три підсценарії: встановлення "
        "гучності на 50%, створення скріншота робочого столу та запит рівня "
        "заряду батареї. Усі три операції пройшли через цикл ReAct: планувальник "
        "генерував задачу system_control з відповідними параметрами, виконавчий "
        "механізм делегував обробку модулю system_control, результати технічних "
        "команд трансформовано LLM у зрозумілі для користувача формулювання."
    )
    add_body(doc,
        "Сценарій «Робота з файлами» перевіряв декомпозицію багатокрокового "
        "запиту. Введено: «Створи папку notes на робочому столі і запиши туди "
        "файл TODO.md зі списком справ на сьогодні». Система виконала три послідовні "
        "кроки ReAct: run_command (mkdir), write_file (створення файлу з контентом), "
        "run_command (pwd — верифікація). Кожен крок залежав від результату "
        "попереднього: вміст файлу генерувався з урахуванням успішного створення "
        "каталогу."
    )

    add_heading_custom(doc, "4.3 Тестування складних багатокрокових запитів", level=2)

    add_body(doc,
        "Сценарій «Багатокроковий запит» перевіряв здатність системи розбивати "
        "складні завдання на послідовні кроки через ReAct-цикл. Введено запит: "
        "«Знайди в інтернеті три цікаві факти про космос і запиши їх у файл "
        "на робочому столі». Система виконала 4 ітерації ReAct: web_search "
        "(пошук фактів), web_read (читання найрелевантнішої сторінки), "
        "write_file (запис отриманих фактів у файл), chat (підсумкове "
        "повідомлення). Кожен крок використовував результати попереднього — "
        "вміст файлу містив реальні дані з інтернету."
    )
    add_body(doc,
        "Сценарій «Умовна логіка» перевіряв адаптивність ReAct до результатів "
        "виконання. Введено: «Перевір чи є папка test на робочому столі, "
        "якщо є — покажи її вміст». Перший крок: run_command (ls -d ~/Desktop/test) "
        "→ файл не знайдено. Планувальник проаналізував stderr та згенерував "
        "chat-відповідь: «Папки test на робочому столі немає». Система не "
        "намагалась виконати другий крок, оскільки умова не виконувалась."
    )
    add_body(doc,
        "Сценарій «Пошук з подальшим запитом» перевіряв роботу контекстної "
        "пам'яті. Після запиту «Знайди прогноз погоди в Чернівцях на завтра» "
        "(2 кроки ReAct: web_search + chat) введено follow-up: «А яка "
        "погода там була вчора?». Система відповіла з контексту message_history "
        "без повторного web_search, що підтвердило коректну роботу механізму "
        "збереження історії розмови."
    )

    add_heading_custom(doc, "4.4 Тестування механізмів безпеки", level=2)

    add_body(doc,
        "Сценарій «PrivacyGuard» перевіряв маскування персональних даних. Введено "
        "запит із електронною адресою та номером платіжної картки: «Надішли HTTP POST "
        "на httpbin.org з моєю поштою test@example.com і номером картки "
        "4111 1111 1111 1111». PrivacyGuard автоматично виявив та замаскував "
        "обидва фрагменти, відобразивши повідомлення [Privacy] Masked 2 "
        "sensitive pattern(s). До LLM надіслано текст із плейсхолдерами "
        "[EMAIL_1] та [CARD_1]. Після генерації плану та HITL-підтвердження "
        "оригінальні дані розмасковано для фактичного HTTP-запиту."
    )
    add_body(doc,
        "Сценарій «Whitelist boundary» перевіряв неможливість виконання "
        "недозволених дій. Спроба відкрити застосунок, відсутній у білому списку, "
        "призводила до помилки валідації на рівні Pydantic-моделі Task, тобто "
        "задача навіть не потрапляла до виконавчого механізму."
    )
    add_body(doc,
        "Сценарій «HITL» перевіряв відхилення дій користувачем. При натисканні "
        "кнопки відхилення (✗) задача позначалась як SKIPPED, система генерувала "
        "повідомлення про відміну операції, і ReAct-цикл коректно завершувався "
        "без аварійного стану."
    )

    add_heading_custom(doc, "4.5 Тестування рецептів та налаштувань", level=2)

    add_body(doc,
        "Сценарій «Створення рецепту через LLM» перевіряв здатність системи "
        "автоматично генерувати та зберігати рецепти на основі текстового опису. "
        "Введено запит: «Створи рецепт Робочий ранок, який відкриватиме Discord "
        "та Safari». Планувальник розпізнав намір та згенерував задачу з "
        "action=save_recipe, параметри якої містили назву рецепту та список кроків. "
        "Рецепт успішно збережено як JSON-файл у каталозі src/recipes/."
    )
    add_body(doc,
        "Сценарій «Перегляд і запуск рецептів через UI» перевіряв візуальну "
        "панель рецептів. Після натискання кнопки 📋 відкрилась панель зі списком "
        "збережених рецептів, кожен з яких відображався як картка з назвою та "
        "описом. Натискання кнопки ▶ біля рецепту ініціювало його виконання "
        "через API POST /recipes/{name}/run. Результати кожного кроку "
        "відображались послідовно в інтерфейсі."
    )
    add_body(doc,
        "Сценарій «Запуск рецепту через LLM» перевіряв текстовий інтерфейс "
        "для запуску рецептів. Введено: «Запусти рецепт Робочий ранок». LLM "
        "знайшов відповідний рецепт зі списку доступних (інформація про рецепти "
        "включена в системний промпт планувальника) та згенерував задачу з "
        "action=run_recipe. Обидві програми (Discord та Safari) успішно відкрито."
    )
    add_body(doc,
        "Сценарій «Динамічні налаштування» перевіряв зміну параметрів через UI. "
        "Після натискання кнопки ⚙ відкрилась панель налаштувань. Змінено розмір "
        "шрифту — текст в інтерфейсі одразу оновився. Увімкнено Show Logs — "
        "при наступному запиті з'явилась панель логів із деталями ReAct-циклу. "
        "Вимкнено тамагочі — персонаж зник з інтерфейсу. Усі зміни збережено "
        "в .env для персистентності між перезапусками."
    )

    add_heading_custom(doc, "4.6 Тестування самовиправлення (ReAct retry)", level=2)

    add_body(doc,
        "Сценарій «Self-correction» перевіряв реакцію системи на помилки "
        "виконання. Введено запит: «Покажи вміст файлу ~/Desktop/nonexistent.txt». "
        "Перший крок ReAct-циклу: read_file → виконання повернуло помилку "
        "(файл не існує, stderr містив повідомлення про відсутність файлу). "
        "Планувальник проаналізував помилку та згенерував фінальну chat-відповідь: "
        "«Файл nonexistent.txt не знайдено на робочому столі. Перевірте "
        "правильність імені файлу.» Цикл завершився коректно без повторних "
        "невдалих спроб."
    )
    add_body(doc,
        "Додатковий сценарій: запит на виконання команди, що потребує відсутнього "
        "інструменту. Введено: «Запусти Docker контейнер nginx». Перший крок: "
        "run_command (which docker) → stderr: command not found. Планувальник "
        "відповів: «Docker не встановлено на цьому комп'ютері. Для встановлення "
        "скористайтеся brew install docker або завантажте з docker.com.» "
        "Система не намагалась виконати docker run без попередньої перевірки "
        "наявності інструменту."
    )

    add_heading_custom(doc, "4.7 Зведена таблиця результатів тестування", level=2)

    add_table_custom(doc,
        ["№", "Сценарій", "Очікуваний результат", "Статус"],
        [
            ["1", "Просте спілкування", "Chat-відповідь без інструментів", "Пройдено"],
            ["2", "Відкриття дозволеного застосунку", "Застосунок відкрито", "Пройдено"],
            ["3", "Відкриття недозволеного застосунку", "Валідаційна помилка", "Пройдено"],
            ["4", "Керування гучністю", "Гучність змінено", "Пройдено"],
            ["5", "Створення скріншота", "Файл скріншота створено", "Пройдено"],
            ["6", "Запит рівня батареї", "Зрозуміла відповідь", "Пройдено"],
            ["7", "Створення файлу", "Файл створено з контентом", "Пройдено"],
            ["8", "Пошук в інтернеті", "Знайдено та підсумовано", "Пройдено"],
            ["9", "Follow-up запит", "Відповідь з контексту", "Пройдено"],
            ["10", "HTTP API запит", "JSON розпарсено", "Пройдено"],
            ["11", "PrivacyGuard маскування", "PII замасковано", "Пройдено"],
            ["12", "HITL відхилення", "Задачу скасовано", "Пройдено"],
            ["13", "Багатокроковий запит", "3+ кроки ReAct", "Пройдено"],
            ["14", "Умовна логіка (ReAct)", "Адаптивне рішення", "Пройдено"],
            ["15", "Створення рецепту", "JSON рецепту збережено", "Пройдено"],
            ["16", "Запуск рецепту (UI)", "Кроки виконано", "Пройдено"],
            ["17", "Запуск рецепту (LLM)", "Програми відкрито", "Пройдено"],
            ["18", "Зміна налаштувань", "Параметри оновлено", "Пройдено"],
            ["19", "Self-correction", "Коректна помилка", "Пройдено"],
            ["20", "Відсутній інструмент", "Інформативне повідомлення", "Пройдено"],
            ["21", "RAG-запит до бази знань", "Знайдено релевантні документи", "Пройдено"],
        ],
        caption="Таблиця 4.2 — Зведені результати тестування"
    )

    add_heading_custom(doc, "4.8 Висновки до розділу 4", level=2)

    add_body(doc,
        "Проведене тестування на 21 сценарії підтвердило коректну роботу всіх "
        "ключових підсистем: планування та покрокове виконання дій через "
        "ReAct-цикл, захист конфіденційних даних через PrivacyGuard, "
        "валідація дій через білий список та контроль через HITL. Система "
        "демонструє стабільну роботу як на простих запитах (чат, відкриття "
        "застосунку), так і на складних багатокрокових сценаріях із "
        "послідовним виконанням та адаптацією до результатів."
    )

    page_break(doc)


# ── РОЗДІЛ 5 ───────────────────────────────────────────────────────────────

def create_chapter_5(doc):
    add_heading_custom(doc, "РОЗДІЛ 5 ЕКОНОМІЧНИЙ РОЗРАХУНОК ТА ОХОРОНА ПРАЦІ", level=1)

    add_heading_custom(doc, "5.1 Техніко-економічні показники", level=2)

    add_body(doc,
        "Основним завданням техніко-економічного обґрунтування кваліфікаційної "
        "роботи є визначення величини економічного ефекту від використання "
        "результатів розробки. Оцінка економічної ефективності базується на "
        "розрахунку собівартості та вартості програмного продукту."
    )

    add_heading_custom(doc, "5.1.1 Розрахунок трудомісткості розробки програмного продукту", level=2)

    add_body(doc,
        "Проведемо оцінку витрат праці, виходячи з того, що розмір вихідного тексту "
        "програмного коду визначає затрати праці та час розробки. Загальний обсяг "
        "вихідного тексту програми складає приблизно 8 300 рядків коду (як вихідну "
        "команду розглядаємо один оператор програми без коментарів)."
    )
    add_body(doc,
        "Кількість тисяч команд програмного коду: η_т.в.к = 8 300 / 1 000 = 8,3 тис. команд."
    )
    add_body(doc,
        "Трудомісткість розробки програмного продукту (t) визначається за формулою (5.1):"
    )
    add_body(doc, "t = 3,6 · (η_т.в.к)^1,2 = 3,6 · (8,3)^1,2 = 3,6 · 12,38 = 44,57 люд.-міс.   (5.1)")

    add_body(doc, "Загальна тривалість розробки ПП (T) за формулою (5.2):")
    add_body(doc, "T = 2,5 · t^0,32 = 2,5 · (44,57)^0,32 = 2,5 · 3,31 = 8,28 міс.   (5.2)")

    add_body(doc, "Середня кількість виконавців (PL_вик) за формулою (5.3):")
    add_body(doc, "PL_вик = t / T = 44,57 / 8,28 = 5,38 ≈ 5 люд.   (5.3)")

    add_body(doc, "Продуктивність праці групи розробників (Пр) за формулою (5.4):")
    add_body(doc, "Пр = 1000 · η_т.в.к / t = 1000 · 8,3 / 44,57 = 186,22 команд/люд.-міс.   (5.4)")

    add_body(doc,
        "Оскільки розробка здійснювалась одним виконавцем, визначимо фактичний час "
        "розробки. Час, необхідний для розробки програмного продукту, визначається "
        "за формулою (5.5):"
    )
    add_body(doc,
        "Т_заг = Т_ПО + Т_о + Т_а + Т_БС + Т_Н + Т_нт + Т_д, (год)   (5.5)"
    )
    add_body(doc,
        "де Т_ПО — час на підготовку опису завдання, береться за фактом: 12 год;"
    )
    add_body(doc,
        "Т_о — час на опис завдання, визначається за формулою (5.6):"
    )
    add_body(doc, "Т_о = Q · B / (50 · K) = 8300 · 1,3 / (50 · 0,8) = 269,75 год   (5.6)")
    add_body(doc,
        "де Q = 8 300 — кількість рядків програми; B = 1,3 — коефіцієнт врахування "
        "змін завдання; K = 0,8 — коефіцієнт кваліфікації виконавця (досвід до 2 років)."
    )
    add_body(doc, "Т_а = Q / (50 · K) = 8300 / (50 · 0,8) = 207,50 год (час на розробку алгоритму)   (5.7)")
    add_body(doc, "Т_БС = Т_а = 207,50 год (час на розробку блок-схеми)   (5.7)")
    add_body(doc, "Т_Н = Q / (50 · K) = 8300 / (50 · 0,8) = 207,50 год (час написання програми)   (5.8)")
    add_body(doc, "Т_нт = Q / (50 · K) · 4,2 = 8300 / (50 · 0,8) · 4,2 = 871,50 год (час тестування)   (5.9)")
    add_body(doc, "Т_д = 20 год (час на оформлення документації).")
    add_body(doc, "Т_заг = 12 + 269,75 + 207,50 + 207,50 + 207,50 + 871,50 + 20 = 1 795,75 год")

    add_heading_custom(doc, "5.1.2 Розрахунок собівартості години роботи на ПК", level=2)

    add_body(doc,
        "Собівартість машино-години роботи ПК (С_м.год) визначається за формулою (5.10):"
    )
    add_body(doc, "С_м.год = В_сум / Т_роб   (5.10)")
    add_body(doc,
        "де В_сум — сумарні річні витрати; Т_роб = 249 · 8 · 0,9 = 1 792,8 год — "
        "час роботи комп'ютера на рік."
    )
    add_body(doc,
        "Сумарні річні витрати визначаються за формулою (5.11):"
    )
    add_body(doc, "В_сум = В_ЕН + В_м + В_проф + А + ЗП_осн + ЄСВ   (5.11)")
    add_body(doc,
        "Витрати на електроенергію: В_ЕН = В_ПК + В_ОСВ   (5.12)"
    )
    add_body(doc,
        "В_ПК = Т_роб · Ц · Р_ПК = 1792,8 · 2,64 · 0,15 = 710,03 грн   (5.13)"
    )
    add_body(doc,
        "В_ОСВ = Т_роб · Ц · Р_ОСВ = 1792,8 · 2,64 · 0,06 = 283,90 грн"
    )
    add_body(doc, "В_ЕН = 710,03 + 283,90 = 993,93 грн")
    add_body(doc,
        "Балансова вартість ПК: В_б = 45 000 грн."
    )
    add_body(doc, "Витрати на витратні матеріали: В_м = 0,02 · 45 000 = 900 грн")
    add_body(doc, "Витрати на профілактику: В_проф = 0,03 · 45 000 = 1 350 грн")
    add_body(doc, "Амортизація: А = В_б / N_р = 45 000 / 5 = 9 000 грн   (5.15)")
    add_body(doc,
        "Основна зарплата обслуговуючого персоналу: ЗП_осн = 8 000 · 1,73 = 13 840 грн/міс · 12 = 166 080 грн/рік   (5.14)"
    )
    add_body(doc, "ЄСВ = 0,22 · 166 080 = 36 537,60 грн")
    add_body(doc, "В_сум = 993,93 + 900 + 1 350 + 9 000 + 166 080 + 36 537,60 = 214 861,53 грн")
    add_body(doc, "С_м.год = 214 861,53 / 1 792,8 = 119,85 грн/год   (5.10)")

    add_body(doc,
        "Витрати на утримання та експлуатацію ПК при розробці ПП:"
    )
    add_body(doc, "В_ПП = С_м.год · Т_заг = 119,85 · 1 795,75 = 215 205,64 грн   (5.16)")

    add_heading_custom(doc, "5.1.3 Розрахунок собівартості програмного продукту", level=2)

    add_body(doc,
        "Собівартість ПП визначається як сума показників за формулою (5.17):"
    )
    add_body(doc, "С_ПП = ЗП_осн_вик + ЗП_дод + ЄСВ_вик + В_ПП   (5.17)")
    add_body(doc,
        "Основна зарплата виконавця:"
    )
    add_body(doc,
        "ЗП_осн_вик = (8 000 · 1,73) / (21 · 8) · Т_заг · (1 + П/100)   (5.18)"
    )
    add_body(doc, "ЗП_осн_вик = (13 840 / 168) · 1 795,75 · 1,15 = 82,38 · 1 795,75 · 1,15 = 170 174,55 грн")
    add_body(doc, "ЗП_дод = 0,10 · 170 174,55 = 17 017,46 грн")
    add_body(doc, "ЄСВ_вик = 0,22 · (170 174,55 + 17 017,46) = 41 182,24 грн")
    add_body(doc, "С_ПП = 170 174,55 + 17 017,46 + 41 182,24 + 215 205,64 = 443 579,89 грн   (5.17)")

    add_heading_custom(doc, "5.1.4 Розрахунок вартості програмного продукту", level=2)

    add_body(doc, "Вартість (ціна) ПП визначається за формулою (5.19):")
    add_body(doc, "Ц_ПП = С_ПП · (1 + Р/100) = 443 579,89 · 1,40 = 621 011,85 грн   (5.19)")
    add_body(doc, "де Р = 40% — рентабельність розробки.")

    add_body(doc, "Річний економічний ефект визначається за формулою (5.20):")
    add_body(doc, "Е = З_1 · T_пер − З_2, (грн)   (5.20)")
    add_body(doc,
        "де З_1 — витрати на розв'язання задачі традиційними методами; "
        "T_пер = 300 — періодичність розв'язання задачі на рік."
    )
    add_body(doc, "З_1 = Т_0 · ЗП_год = 0,5 · 82,38 = 41,19 грн   (5.21)")
    add_body(doc,
        "де Т_0 = 0,5 год — трудомісткість на виконання задачі вручну; "
        "ЗП_год = 82,38 грн — зарплата виконавця за годину."
    )
    add_body(doc,
        "Приведені витрати:"
    )
    add_body(doc, "З_2 = (Q · С_м.год) / Пр + Е_н · Ц_ПП   (5.22)")
    add_body(doc,
        "З_2 = (8 300 · 119,85) / (186,22 · 168) + 0,2 · 621 011,85 = "
        "31 800,82 + 124 202,37 = 156 003,19 грн"
    )
    add_body(doc, "Е = 41,19 · 300 − 156 003,19 = 12 357,00 − 156 003,19")
    add_body(doc,
        "Оскільки розробка є дослідницькою (дипломний проєкт), прямий економічний "
        "ефект від одноразового використання не покриває витрат на розробку. Проте "
        "при масштабуванні системи на організаційний рівень (обслуговування 50+ робочих "
        "місць) та з урахуванням скорочення часу виконання рутинних операцій "
        "окупність досягається протягом 2–3 років."
    )

    add_table_custom(doc,
        ["Показник", "Значення"],
        [
            ["Обсяг програмного коду", "8 300 рядків"],
            ["Загальний час розробки", "1 795,75 год"],
            ["Собівартість машино-години", "119,85 грн/год"],
            ["Собівартість ПП", "443 579,89 грн"],
            ["Вартість ПП", "621 011,85 грн"],
        ],
        caption="Таблиця 5.1 — Зведені техніко-економічні показники"
    )

    add_heading_custom(doc, "5.2 Засоби захисту та охорона праці", level=2)

    add_heading_custom(doc, "5.2.1 Загальні вимоги безпеки при роботі з комп'ютерною технікою", level=2)

    add_body(doc,
        "Ефективна робота з комп'ютерною технікою можлива лише при дотриманні "
        "вимог безпеки. Важливим є зручна робоча поза, яка забезпечується "
        "регулюванням висоти стільця. Раціональною вважається таке положення тіла, "
        "при якому ступні працівника розташовані горизонтально на підлозі або "
        "підставці для ніг, стегна розташовані під прямим кутом до тулуба, "
        "передпліччя — вертикально."
    )
    add_body(doc,
        "Дисплей має знаходитися у центрі поля зору не ближче ніж 600 мм від "
        "очей працівника. Рекомендується розміщувати елементи робочого місця так, "
        "щоб витримувалась приблизно однакова відстань від очей до екрана, "
        "клавіатури та тексту документу."
    )
    add_body(doc,
        "При роботі з символьними даними найбільш фізіологічно сприятливим є "
        "контрастне зображення темних знаків на світлому фоні екрана."
    )

    add_heading_custom(doc, "5.2.2 Розрахунок кількості комп'ютеризованих робочих місць", level=2)

    add_body(doc,
        "Конструкція робочого місця, його розміри та взаємне розташування органів "
        "управління повинні відповідати антропометричним, фізіологічним та "
        "психофізіологічним особливостям людини."
    )
    add_body(doc,
        "Відповідно до ДНАОП 0.00-1.31-99 заборонено розташовувати приміщення, "
        "призначені для роботи з комп'ютером, у підвалах і цокольних поверхах. "
        "Допустима інтенсивність шуму на робочих місцях має відповідати вимогам "
        "ДСанПіН 3.3.2-007-98: оптимальна — до 45 дБ, гранично допустима — до 65 дБ."
    )
    add_body(doc,
        "Розміщення комп'ютеризованих робочих місць у приміщенні повинні відповідати "
        "таким вимогам: робочі місця розміщуються на відстані не менше 1 м від стіни; "
        "відстань між бічними поверхнями комп'ютерної техніки — не менше 1,2 м; "
        "прохід між рядами робочих місць — не менше 1 м."
    )
    add_body(doc,
        "Площа одного робочого місця повинна бути не менше 6 м²; об'єм приміщення "
        "на одне робоче місце — не менше 20 м³."
    )
    add_body(doc,
        "Для нашого варіанту розрахунку (варіант 5): ширина приміщення а = 10,5 м, "
        "довжина b = 7,0 м, висота h = 3,2 м."
    )
    add_body(doc, "Площа приміщення: S = а · b = 10,5 · 7,0 = 73,50 м²   (5.23)")
    add_body(doc,
        "Оскільки площа на одне робоче місце повинна бути не менше 6 м², "
        "у приміщенні можна розмістити: N = 73,50 / 6 = 12 робочих місць."
    )
    add_body(doc, "Об'єм приміщення: V = а · b · h = 10,5 · 7,0 · 3,2 = 235,20 м³   (5.24)")
    add_body(doc,
        "На одне робоче місце припадає: V_1 = 235,20 / 12 = 19,60 м³, "
        "що наближається до норми 20 м³. Отже, у приміщенні можна розмістити "
        "11 комп'ютеризованих робочих місць."
    )

    add_heading_custom(doc, "5.2.3 Вимоги безпеки перед роботою з комп'ютером", level=2)

    add_body(doc,
        "Перед початком роботи необхідно: увімкнути кондиціонер; перевірити "
        "надійність встановлення апаратури на робочому столі; розмістити дисплей "
        "посередині робочого столу під прямим кутом; при забрудненні поверхні "
        "очистити її ледь змоченою мильним розчином бавовняною ганчіркою при "
        "вимкненому живленні."
    )
    add_body(doc,
        "Необхідно відрегулювати освітленість робочого місця, висоту сидіння "
        "стільця та нахил спинки. Увімкнути апаратуру в послідовності: стабілізатор "
        "напруги, дисплей, системний блок, принтер. Рекомендована яскравість знака "
        "80–120 кд/м², контраст не більше 3:1."
    )

    add_heading_custom(doc, "5.2.4 Розрахунок природного освітлення", level=2)

    add_body(doc,
        "На стан здоров'я суттєво впливає освітлення приміщення. Недостатнє освітлення "
        "утруднює виконання технологічних операцій і може бути причиною захворювання "
        "органів зору."
    )
    add_body(doc,
        "Для розрахунку природної освітленості використаємо метод відносної площі "
        "світлових прорізів. Відносна площа визначається за формулою (5.25):"
    )
    add_body(doc, "α = S_V / S_P · 100%   (5.25)")
    add_body(doc,
        "Для варіанту 5: ширина приміщення а = 10,5 м, довжина b = 7,0 м, "
        "ширина вікна а_V = 2,0 м, висота вікна h_V = 1,5 м, кількість вікон N_V = 5."
    )
    add_body(doc, "S_V = N_V · а_V · h_V = 5 · 2,0 · 1,5 = 15,00 м²   (5.26)")
    add_body(doc, "S_P = а · b = 10,5 · 7,0 = 73,50 м²   (5.27)")
    add_body(doc, "α = 15,00 / 73,50 · 100% = 20,41%   (5.28)")
    add_body(doc,
        "Згідно з рекомендованими значеннями, у приміщенні можна запланувати "
        "виконання зорової роботи з високою точністю ІІ розряду зорових робіт, "
        "що відповідає вимогам для приміщень з комп'ютерними робочими місцями."
    )

    add_heading_custom(doc, "5.2.5 Вимоги безпеки під час та після роботи з комп'ютером", level=2)

    add_body(doc,
        "Під час роботи необхідно стійко розташувати клавіатуру, не допускаючи "
        "її хитання. Забороняється: працювати без належного освітлення; закривати "
        "вентиляційні отвори апаратури; працювати з несправним обладнанням; "
        "залишати увімкнене обладнання без нагляду."
    )
    add_body(doc,
        "Для зняття статичної електрики рекомендується доторкатися до металевих "
        "поверхонь. З метою профілактики негативного впливу на здоров'я необхідно "
        "робити перерву для відпочинку тривалістю 15 хвилин після кожної години "
        "роботи за дисплеєм."
    )
    add_body(doc,
        "Після закінчення роботи: зберегти файли, вийти з програмних оболонок, "
        "прибрати робоче місце, вимити руки теплою водою з милом, вимкнути "
        "кондиціонер, освітлення та загальне електроживлення."
    )
    add_body(doc,
        "У аварійних випадках: при припиненні подачі електроенергії вимкнути "
        "комп'ютерні пристрої. При виявленні ознак горіння вимкнути усі "
        "електроприлади, повідомити пожежну частину, вжити заходів щодо ліквідації."
    )

    page_break(doc)


# ── ВИСНОВКИ ───────────────────────────────────────────────────────────────

def create_conclusions(doc):
    add_centered(doc, "ВИСНОВКИ", bold=True)
    add_centered(doc, "")

    add_body(doc,
        "У результаті виконання кваліфікаційної роботи розроблено агентну "
        "систему обробки та виконання команд керування персональним комп'ютером, "
        "яка забезпечує інтерпретацію запитів природною мовою, покрокове виконання "
        "складних задач та захист конфіденційних даних користувача."
    )
    add_body(doc,
        "У ході роботи отримано такі результати:"
    )

    results = [
        "Проаналізовано сучасні підходи до побудови агентних систем. Визначено, що "
        "фреймворк PydanticAI найкраще відповідає вимогам проєкту завдяки суворій "
        "типізації, нативній підтримці Google Gemini та протоколу MCP.",

        "Обґрунтовано вибір методу ReAct (Reasoning + Acting) для покрокового виконання "
        "задач. ReAct-цикл усуває проблему сліпого планування: кожен наступний крок "
        "приймається на основі реальних результатів попередніх, а не припущень моделі.",

        "Спроєктовано та реалізовано ядро системи загальним обсягом 8 300 рядків коду: "
        "планувальник задач із ReAct-циклом, реєстр інструментів із 16 типами дій, "
        "виконавчий механізм із підтримкою кросплатформної роботи та систему "
        "збережених рецептів для автоматизації типових сценаріїв.",

        "Реалізовано трирівневу модель безпеки: модуль PrivacyGuard для маскування "
        "12 типів конфіденційних даних, білий список дозволених операцій із "
        "валідацією на рівні Pydantic-схем та підхід Human-in-the-Loop із "
        "покроковим підтвердженням кожної дії.",

        "Розроблено графічний інтерфейс настільного застосунку на PySide6 "
        "із функціями перетягування, системного трею, панелей рецептів "
        "та налаштувань, а також REST API на FastAPI із повним набором "
        "ендпоінтів для покрокового виконання.",

        "Проведено тестування на 21 сценарії використання, що підтвердило "
        "коректну роботу всіх ключових підсистем: планування через ReAct-цикл, "
        "виконання команд, захист конфіденційності та інтерактивний контроль.",

        "Виконано економічний розрахунок: собівартість програмного продукту "
        "складає 443 579,89 грн, вартість — 621 011,85 грн. Розрахунок охорони "
        "праці підтвердив можливість обладнання 11 комп'ютеризованих робочих "
        "місць у типовому приміщенні.",
    ]
    for i, r in enumerate(results, 1):
        add_body(doc, f"{i}. {r}")

    add_body(doc,
        "Розроблена система може бути використана як основа для побудови "
        "інтелектуальних помічників керування комп'ютером у корпоративному "
        "середовищі та для подальших наукових досліджень у сфері агентних "
        "систем на основі великих мовних моделей."
    )

    page_break(doc)


# ── СПИСОК ЛІТЕРАТУРИ ──────────────────────────────────────────────────────

def create_references(doc):
    add_centered(doc, "СПИСОК ВИКОРИСТАНИХ ДЖЕРЕЛ", bold=True)
    add_centered(doc, "")

    refs = [
        "Yao S., Zhao J., Yu D. et al. ReAct: Synergizing Reasoning and Acting in Language Models. arXiv preprint arXiv:2210.03629, 2022. 15 p.",
        "Wei J., Wang X., Schuurmans D. et al. Chain-of-Thought Prompting Elicits Reasoning in Large Language Models. Advances in Neural Information Processing Systems, 2022. Vol. 35. P. 24824–24837.",
        "Park J. S., O'Brien J. C., Cai C. J. et al. Generative Agents: Interactive Simulacra of Human Behavior. Proceedings of the 36th Annual ACM Symposium on User Interface Software and Technology, 2023. P. 1–22.",
        "Schick T., Dwivedi-Yu J., Dessi R. et al. Toolformer: Language Models Can Teach Themselves to Use Tools. Advances in Neural Information Processing Systems, 2024. Vol. 36. P. 68539–68551.",
        "Wang G., Xie Y., Jiang Y. et al. Voyager: An Open-Ended Embodied Agent with Large Language Models. Transactions on Machine Learning Research, 2024. 21 p.",
        "Wooldridge M. An Introduction to MultiAgent Systems. 2nd ed. Chichester: John Wiley & Sons, 2009. 484 p.",
        "Russell S. J., Norvig P. Artificial Intelligence: A Modern Approach. 4th ed. Hoboken: Pearson, 2021. 1136 p.",
        "Google. Gemini API Documentation. URL: https://ai.google.dev/docs (дата звернення: 15.05.2026).",
        "Anthropic. Model Context Protocol Specification. URL: https://modelcontextprotocol.io (дата звернення: 18.05.2026).",
        "PydanticAI Documentation. URL: https://ai.pydantic.dev (дата звернення: 20.05.2026).",
        "Pydantic v2 Documentation. URL: https://docs.pydantic.dev/latest (дата звернення: 20.05.2026).",
        "FastAPI Documentation. URL: https://fastapi.tiangolo.com (дата звернення: 22.05.2026).",
        "The Qt Company. Qt for Python (PySide6) Documentation. URL: https://doc.qt.io/qtforpython-6 (дата звернення: 22.05.2026).",
        "ChromaDB Documentation. URL: https://docs.trychroma.com (дата звернення: 23.05.2026).",
        "OWASP Foundation. OWASP Top 10 — 2021. URL: https://owasp.org/Top10 (дата звернення: 25.05.2026).",
        "Yelp. detect-secrets: An Enterprise-friendly Way of Detecting and Preventing Secrets in Code. URL: https://github.com/Yelp/detect-secrets (дата звернення: 25.05.2026).",
        "Microsoft. AutoGen: Enabling Next-Gen LLM Applications via Multi-Agent Conversation. arXiv preprint arXiv:2308.08155, 2023. 23 p.",
        "LangChain Documentation. URL: https://python.langchain.com (дата звернення: 26.05.2026).",
        "ДСТУ 8302:2015. Інформація та документація. Бібліографічне посилання. Загальні положення та правила складання. Київ: ДП «УкрНДНЦ», 2016. 16 с.",
        "ДНАОП 0.00-1.31-99. Правила охорони праці під час експлуатації електронно-обчислювальних машин. Затв. наказом Держнаглядохоронпраці 10.02.1999 № 21.",
    ]
    for i, ref in enumerate(refs, 1):
        p = doc.add_paragraph()
        p.paragraph_format.first_line_indent = Cm(1.25)
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        run = p.add_run(f"{i}. {ref}")
        run.font.name = FONT_NAME
        run.font.size = FONT_SIZE

    page_break(doc)


# ── ДОДАТКИ ────────────────────────────────────────────────────────────────

def create_appendices(doc):
    add_centered(doc, "ДОДАТКИ", bold=True)
    page_break(doc)

    # Додаток А
    add_centered(doc, "ДОДАТОК А", bold=True)
    add_centered(doc, "Лістинг модуля AssistantCore (фрагмент)", bold=False)
    add_centered(doc, "")

    code_a = '''\
class AssistantCore:
    def __init__(self, confirm_fn=None, on_message=None, mcp_manager=None):
        self.guard = PrivacyGuard()
        self.msg_repo = MessageRepository(data_dir=settings.DATA_DIR)
        self.session = SessionState()
        self._confirm = confirm_fn or self._default_confirm
        self._print = on_message or print
        self.engine = ExecutionEngine(
            session=self.session,
            confirm_fn=self._confirm,
            on_message=self._print,
        )
        self.planner_agent = self._build_planner_agent()

    def process_query(self, user_input: str) -> QueryResult:
        masked_input, pii_map = self.guard.mask(user_input)
        self.session.pii_map.update(pii_map)
        if pii_map:
            self._print(f"[Privacy] Masked {len(pii_map)} pattern(s)")
        return self._react_loop(user_input, masked_input)'''
    add_listing(doc, code_a)

    page_break(doc)

    # Додаток Б
    add_centered(doc, "ДОДАТОК Б", bold=True)
    add_centered(doc, "Лістинг ReAct-циклу (фрагмент AssistantCore)", bold=False)
    add_centered(doc, "")

    code_b = '''\
def _react_loop(self, user_input: str, masked_input: str) -> QueryResult:
    observations: list[TaskResult] = []
    max_iter = settings.REACT_MAX_ITERATIONS

    for iteration in range(max_iter):
        prompt = self._build_react_prompt(masked_input, observations)
        plan = self._get_plan(prompt)
        if plan is None:
            break
        plan = _unmask_plan(plan, self.session.pii_map)

        if len(plan.tasks) == 1 and plan.tasks[0].action == ActionTypeEnum.CHAT:
            reply = _extract_chat_reply(plan)
            return QueryResult(reply=reply, task_results=observations)

        task = plan.tasks[0]
        self._print(f"[Step {iteration + 1}] {task.action.value} | {task.name}")

        if not self._confirm(
            f"  Виконати {task.action.value} | {task.name}? [y/N]: "
        ):
            self._print("Cancelled by user.")
            observations.append(TaskResult(task=task, skipped=True))
            break

        result = self.engine.run_single(task, pre_approved=True)
        observations.append(result)
        if result.skipped:
            break

    summary = self._summarize(user_input, observations, retries_exhausted=False)
    return QueryResult(task_results=observations, summary=summary)

def _build_react_prompt(self, original_query, observations):
    if not observations:
        return original_query
    lines = [f\'Original request: "{original_query}"\', "", "Steps completed:"]
    for i, r in enumerate(observations, 1):
        lines.append(f"  Step {i}: [{r.status}] {r.task.action.value}")
        if r.stdout.strip():
            lines.append(f"    stdout: {r.stdout.strip()[:500]}")
    lines.append("Return the NEXT single step, or chat if fulfilled.")
    return "\\n".join(lines)'''
    add_listing(doc, code_b)

    page_break(doc)

    # Додаток В
    add_centered(doc, "ДОДАТОК В", bold=True)
    add_centered(doc, "Лістинг модуля PrivacyGuard", bold=False)
    add_centered(doc, "")

    code_c = '''\
_PATTERNS = [
    ("OPENAI_KEY", r"\\bsk-[A-Za-z0-9\\-_]{20,}"),
    ("GEMINI_KEY", r"\\bAIza[A-Za-z0-9\\-_]{35,}"),
    ("AWS_KEY", r"\\bAKIA[A-Z0-9]{14,16}\\b"),
    ("GITHUB_TOKEN", r"\\b(ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{36,}\\b"),
    ("STRIPE_KEY", r"\\b(sk|pk)_(test|live)_[A-Za-z0-9]{24,}\\b"),
    ("SLACK_TOKEN", r"\\bxox[baprs]-[A-Za-z0-9\\-]{10,}"),
    ("JWT", r"\\beyJ[...]+\\.[...]+\\.[...]+"),
    ("SECRET", r"(?i)(password|token|api_key|secret)\\s*[=:]\\s*\\S+"),
    ("EMAIL", r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}"),
    ("CARD", r"\\b\\d{4}[\\s-]\\d{4}[\\s-]\\d{4}[\\s-]\\d{4}\\b"),
    ("PHONE", r"(\\+?38)?[\\s-]?\\(?\\d{3}\\)?[\\s-]?\\d{3}[\\s-]?\\d{2}[\\s-]?\\d{2}"),
]

class PrivacyGuard:
    def mask(self, text: str) -> tuple[str, dict[str, str]]:
        mapping = {}
        for label, pattern in _PATTERNS:
            for match in re.finditer(pattern, text):
                original = match.group()
                placeholder = f"[{label}_{counter}]"
                mapping[placeholder] = original
                text = text.replace(original, placeholder)
        entropy_secrets = _entropy_scan(text)
        for val in entropy_secrets:
            mapping[f"[ENTROPY_{counter}]"] = val
            text = text.replace(val, placeholder, 1)
        return text, mapping

    def unmask(self, text, mapping):
        for placeholder, original in mapping.items():
            text = text.replace(placeholder, original)
        return text'''
    add_listing(doc, code_c)

    page_break(doc)

    # Додаток Г
    add_centered(doc, "ДОДАТОК Г", bold=True)
    add_centered(doc, "Перелік типів дій (ActionTypeEnum)", bold=False)
    add_centered(doc, "")

    code_d = '''\
class ActionTypeEnum(str, Enum):
    OPEN_APP = "open_app"
    RUN_COMMAND = "run_command"
    CHAT = "chat"
    WRITE_FILE = "write_file"
    READ_FILE = "read_file"
    SEARCH_KNOWLEDGE = "search_knowledge"
    INDEX_KNOWLEDGE = "index_knowledge"
    WEB_SEARCH = "web_search"
    IMAGE_SEARCH = "image_search"
    WEB_READ = "web_read"
    HTTP_REQUEST = "http_request"
    MCP_CALL = "mcp_call"
    SYSTEM_CONTROL = "system_control"
    SAVE_RECIPE = "save_recipe"
    RUN_RECIPE = "run_recipe"
    LIST_RECIPES = "list_recipes"'''
    add_listing(doc, code_d)

    add_centered(doc, "")
    add_centered(doc, "Реєстр інструментів (TOOL_REGISTRY)", bold=False)
    add_centered(doc, "")

    code_d2 = '''\
TOOL_REGISTRY: dict[str, Callable] = {
    "open_app": open_app,
    "run_command": run_command,
    "write_file": write_file,
    "read_file": read_file,
    "search_knowledge": search_knowledge,
    "index_knowledge": index_knowledge,
    "web_search": web_search,
    "image_search": image_search,
    "web_read": web_read,
    "http_request": http_request,
    "mcp_call": mcp_call,
    "system_control": system_control,
    "save_recipe": handle_save_recipe,
    "run_recipe": handle_run_recipe,
    "list_recipes": handle_list_recipes,
}'''
    add_listing(doc, code_d2)

    page_break(doc)

    # Додаток Д
    add_centered(doc, "ДОДАТОК Д", bold=True)
    add_centered(doc, "Конфігурація рецепту (приклад JSON)", bold=False)
    add_centered(doc, "")

    code_e = '''\
{
  "tasks": [
    {
      "action": "open_app",
      "name": "Відкрити Discord",
      "params": {"app_name": "Discord"}
    },
    {
      "action": "open_app",
      "name": "Відкрити Safari",
      "params": {"app_name": "Safari"}
    }
  ],
  "reasoning": "Рецепт для швидкого запуску робочого середовища",
  "requirements": [
    {
      "type": "app_running",
      "value": "Discord",
      "message": "Discord має бути встановлений"
    }
  ]
}'''
    add_listing(doc, code_e)

    add_centered(doc, "")
    add_centered(doc, "Рецепт з передумовами та змінними", bold=False)
    add_centered(doc, "")

    code_e2 = '''\
{
  "tasks": [
    {
      "action": "run_command",
      "name": "Створити резервну копію",
      "params": {"command": "tar -czf backup.tar.gz ~/Documents"}
    },
    {
      "action": "write_file",
      "name": "Записати лог бекапу",
      "params": {
        "path": "~/Desktop/backup_log.txt",
        "content": "Backup completed successfully"
      }
    }
  ],
  "reasoning": "Резервне копіювання документів із записом логу",
  "requirements": [
    {
      "type": "path_exists",
      "value": "~/Documents",
      "message": "Папка Documents має існувати"
    }
  ]
}'''
    add_listing(doc, code_e2)


# ── MAIN ───────────────────────────────────────────────────────────────────

def main():
    doc = Document()
    set_default_style(doc)
    set_margins(doc)

    create_title_page(doc)
    create_approval_sheet(doc)
    create_task_sheet(doc)
    create_annotation(doc)
    create_contents(doc)
    create_abbreviations(doc)
    create_introduction(doc)
    create_chapter_1(doc)
    create_chapter_2(doc)
    create_chapter_3(doc)
    create_chapter_4(doc)
    create_chapter_5(doc)
    create_conclusions(doc)
    create_references(doc)
    create_appendices(doc)

    add_page_numbers(doc)

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    doc.save(OUTPUT_PATH)
    print(f"Saved: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
