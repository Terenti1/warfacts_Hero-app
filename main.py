# main.py - Приложение "Герои Беларуси" (ФИНАЛ + Викторина + единый UserPreferences + 80/20)

import random
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.button import ButtonBehavior
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
from kivy.core.window import Window
from kivy.animation import Animation
from kivy.utils import get_color_from_hex
from kivy.graphics import Color, Rectangle, RoundedRectangle, Line, Ellipse
from kivy.metrics import dp
from kivy.clock import Clock

from data import FACTS_DATABASE, get_facts_count, get_fact_by_id, get_all_tags, get_facts_by_tag
from user_data import UserPreferences

try:
    from version import __version__
except Exception:
    __version__ = "1.0.0"

# updater больше не используется в этом проекте
UPDATER_AVAILABLE = False
def check_for_updates(manual=False):
    pass

# --- ЦВЕТОВАЯ ПАЛИТРА ---
COLOR_BG = get_color_from_hex('#16251B')
COLOR_BTN_BG = get_color_from_hex('#1E3024')
COLOR_GOLD = get_color_from_hex('#D4AF37')
COLOR_RED = get_color_from_hex('#8B2525')
COLOR_TEXT = (0.95, 0.95, 0.95, 1)
COLOR_ORANGE = get_color_from_hex('#E67E22')
COLOR_GREEN = get_color_from_hex('#2E7D32')


def _up():
    """Единый UserPreferences для всего приложения."""
    try:
        app = App.get_running_app()
        if app is not None and hasattr(app, 'user_prefs') and app.user_prefs is not None:
            return app.user_prefs
    except Exception:
        pass
    return UserPreferences()


def pick_recommended_fact(user_prefs):
    """Рекомендация: 80% — топ-1, 20% — случайный из топ-5. Fallback — случайный/лайкнутый."""
    viewed_facts = set(user_prefs.data["viewed_facts"])
    unviewed = [f for f in FACTS_DATABASE if f["id"] not in viewed_facts]

    if not unviewed:
        liked = user_prefs.data["liked_facts"]
        if liked:
            return get_fact_by_id(random.choice(liked))
        return random.choice(FACTS_DATABASE)

    scored = [(f, user_prefs.get_recommendation_score(f)) for f in unviewed]
    scored.sort(key=lambda x: x[1], reverse=True)
    top5 = scored[:5]

    if random.random() < 0.8:
        return top5[0][0]
    return random.choice(top5)[0]


def _fact_label(fact, length=60):
    title = fact.get("title")
    if title: return title
    text = fact.get("text", "")
    return text[:length] + "..." if len(text) > length else text


class BackButton(ButtonBehavior, AnchorLayout):
    def __init__(self, callback, **kwargs):
        super().__init__(**kwargs)
        with self.canvas.before:
            Color(*COLOR_BTN_BG)
            self.rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(6)])
            Color(*COLOR_GOLD)
            self.line = Line(rounded_rectangle=(self.x, self.y, self.width, self.height, dp(6)), width=1.5)

        self.bind(pos=self.update_graphics, size=self.update_graphics)
        self.img = Image(source='icon_arrow_left.png', size_hint=(None, None), size=(dp(24), dp(24)))
        self.img.allow_stretch = True
        self.img.keep_ratio = True
        self.add_widget(self.img)
        self.bind(on_release=callback)

    def update_graphics(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size
        self.line.rounded_rectangle = (instance.x, instance.y, instance.width, instance.height, dp(6))


def make_header(title_text, back_callback, height=dp(50)):
    header = FloatLayout(size_hint=(1, None), height=height)
    title = Label(
        text=title_text, font_size='20sp', color=COLOR_GOLD, bold=True,
        size_hint=(1, 1), pos_hint={'x': 0, 'y': 0},
        halign='center', valign='middle', text_size=(Window.width - dp(30), None)
    )
    header.add_widget(title)

    back_btn = BackButton(back_callback, size_hint=(0.15, 1), pos_hint={'x': 0, 'y': 0})
    header.add_widget(back_btn)
    return header


class IconMenuButton(ButtonBehavior, BoxLayout):
    def __init__(self, text, icon_source, orientation='vertical', **kwargs):
        super().__init__(**kwargs)
        self.orientation = orientation
        self.padding = dp(5)
        self.spacing = dp(5)

        with self.canvas.before:
            Color(*COLOR_BTN_BG)
            self.rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(8)])
            Color(*COLOR_GOLD)
            self.line = Line(rounded_rectangle=(self.x, self.y, self.width, self.height, dp(8)), width=2)

        self.bind(pos=self.update_graphics, size=self.update_graphics)

        img_hint = (1, 0.6) if orientation == 'vertical' else (0.3, 1)
        text_hint = (1, 0.4) if orientation == 'vertical' else (0.7, 1)

        self.img = Image(source=icon_source, size_hint=img_hint)
        self.img.allow_stretch = True
        self.img.keep_ratio = True
        self.add_widget(self.img)

        self.text_label = Label(text=text, font_size='16sp', color=COLOR_GOLD, bold=True, size_hint=text_hint)
        self.add_widget(self.text_label)

    def update_graphics(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size
        self.line.rounded_rectangle = (instance.x, instance.y, instance.width, instance.height, dp(8))


class IconActionButton(ButtonBehavior, BoxLayout):
    def __init__(self, icon_source, **kwargs):
        super().__init__(**kwargs)

        with self.canvas.before:
            Color(*COLOR_BTN_BG)
            self.rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(8)])
            Color(*COLOR_GOLD)
            self.line = Line(rounded_rectangle=(self.x, self.y, self.width, self.height, dp(8)), width=2)

        self.bind(pos=self.update_graphics, size=self.update_graphics)

        self.img = Image(source=icon_source, size_hint=(0.6, 0.6), pos_hint={'center_x':0.5, 'center_y':0.5})
        self.img.allow_stretch = True
        self.img.keep_ratio = True
        self.add_widget(self.img)

    def update_graphics(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size
        self.line.rounded_rectangle = (instance.x, instance.y, instance.width, instance.height, dp(8))

    def set_active(self, color):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*color)
            self.rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(8)])
            Color(*COLOR_GOLD)
            self.line = Line(rounded_rectangle=(self.x, self.y, self.width, self.height, dp(8)), width=2)
        self.bind(pos=self.update_graphics, size=self.update_graphics)


class HeroFactCard(ButtonBehavior, BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = [dp(15), dp(10)]
        self.spacing = dp(5)

        with self.canvas.before:
            Color(*COLOR_RED)
            self.rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(10)])
            Color(*COLOR_GOLD)
            self.line = Line(rounded_rectangle=(self.x, self.y, self.width, self.height, dp(10)), width=2)

        self.bind(pos=self.update_graphics, size=self.update_graphics)

        star_img = Image(source='star_red_green_gold.png', size_hint=(1, 0.25))
        star_img.allow_stretch = True
        star_img.keep_ratio = True
        self.add_widget(star_img)

        self.add_widget(Label(text="ФАКТ ДНЯ", font_size='18sp', color=COLOR_GOLD, bold=True, size_hint=(1, 0.15)))

        bottom_box = BoxLayout(orientation='horizontal', spacing=dp(15), size_hint=(1, 0.6))

        photo_layout = FloatLayout(size_hint=(0.3, 1))
        with photo_layout.canvas:
            Color(*COLOR_BG)
            self.inner_circle = Ellipse(pos=photo_layout.pos, size=(dp(60), dp(60)))
            Color(*COLOR_GOLD)
            self.outer_circle = Line(circle=(0, 0, dp(31)), width=2)

        def update_photo(instance, value):
            cx = instance.x + instance.width / 2
            cy = instance.y + instance.height / 2
            self.inner_circle.pos = (cx - dp(30), cy - dp(30))
            self.inner_circle.size = (dp(60), dp(60))
            self.outer_circle.circle = (cx, cy, dp(31))

        photo_layout.bind(pos=update_photo, size=update_photo)
        photo_layout.add_widget(Label(text="ФОТО", font_size='10sp', color=COLOR_GOLD, pos_hint={'center_x':0.5, 'center_y':0.5}))

        text_layout = BoxLayout(orientation='vertical', size_hint=(0.7, 1))
        text_layout.add_widget(Label(
            text="Портрет героя\nи краткий подвиг",
            font_size='14sp', color=COLOR_TEXT,
            halign='left', valign='middle', text_size=(dp(200), None)
        ))

        bottom_box.add_widget(photo_layout)
        bottom_box.add_widget(text_layout)
        self.add_widget(bottom_box)

    def update_graphics(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size
        self.line.rounded_rectangle = (instance.x, instance.y, instance.width, instance.height, dp(10))


# ============================================================
#  ГЛАВНОЕ МЕНЮ
# ============================================================

class MainMenuScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.user_prefs = _up()
        self.build_ui()

    def on_enter(self, *args):
        self.clear_widgets()
        self.build_ui()

    def build_ui(self):
        layout = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))

        header = BoxLayout(orientation='vertical', size_hint=(1, None), height=dp(90))
        header.add_widget(Label(text="НИКТО НЕ ЗАБЫТ", font_size='12sp', color=COLOR_GOLD, bold=True, size_hint=(1, None), height=dp(25)))
        header.add_widget(Label(text="ГЕРОИ БЕЛАРУСИ", font_size='26sp', color=COLOR_GOLD, bold=True, size_hint=(1, None), height=dp(40)))
        header.add_widget(Label(text="Партизаны, лётчики, подпольщики", font_size='13sp', color=COLOR_TEXT, size_hint=(1, None), height=dp(25)))
        layout.add_widget(header)

        total_facts = get_facts_count()
        viewed = len(self.user_prefs.data["viewed_facts"])
        progress = self.user_prefs.get_total_progress(total_facts)
        streak = self.user_prefs.get_streak_days()

        prog_box = BoxLayout(orientation='vertical', size_hint=(1, None), height=dp(45), spacing=dp(5))

        prog_labels = BoxLayout(size_hint=(1, None), height=dp(20))
        prog_labels.add_widget(Label(text=f"Прогресс: {viewed}/{total_facts}", font_size='13sp', color=COLOR_TEXT, halign='left'))
        prog_labels.add_widget(Label(text=f"Серия: {streak} дн.", font_size='13sp', color=COLOR_ORANGE, halign='right'))

        prog_box.add_widget(prog_labels)

        pbar_layout = FloatLayout(size_hint=(1, None), height=dp(12))
        with pbar_layout.canvas:
            Color(0.2, 0.2, 0.2, 1)
            bg_rect = RoundedRectangle(pos=pbar_layout.pos, size=pbar_layout.size, radius=[dp(6)])
            Color(*COLOR_ORANGE)
            fill_rect = RoundedRectangle(pos=pbar_layout.pos, size=(pbar_layout.width * (progress/100), pbar_layout.height), radius=[dp(6)])
            Color(*COLOR_GOLD)
            line_rect = Line(rounded_rectangle=(pbar_layout.x, pbar_layout.y, pbar_layout.width, pbar_layout.height, dp(6)), width=1)

        def update_pbar(instance, value):
            bg_rect.pos = instance.pos
            bg_rect.size = instance.size
            fill_rect.pos = instance.pos
            fill_rect.size = (instance.width * (progress/100), instance.height)
            line_rect.rounded_rectangle = (instance.x, instance.y, instance.width, instance.height, dp(6))

        pbar_layout.bind(pos=update_pbar, size=update_pbar)
        prog_box.add_widget(pbar_layout)
        layout.add_widget(prog_box)

        self.fact_card = HeroFactCard(size_hint=(1, None), height=dp(160))
        self.fact_card.bind(on_release=self.go_to_fact_of_day)
        layout.add_widget(self.fact_card)

        layout.add_widget(BoxLayout(size_hint=(1, 0.05)))

        grid = GridLayout(cols=2, spacing=dp(10), size_hint=(1, None), height=dp(300))

        btn_history = IconMenuButton("История", "icon_book.png")
        btn_history.bind(on_release=self.go_to_history)
        grid.add_widget(btn_history)

        btn_notes = IconMenuButton("Заметки", "icon_notes.png")
        btn_notes.bind(on_release=self.go_to_notes)
        grid.add_widget(btn_notes)

        btn_stats = IconMenuButton("Статистика", "icon_chart_bar.png")
        btn_stats.bind(on_release=self.go_to_stats)
        grid.add_widget(btn_stats)

        btn_settings = IconMenuButton("Настройки", "icon_settings.png")
        btn_settings.bind(on_release=self.go_to_settings)
        grid.add_widget(btn_settings)

        btn_quiz = IconMenuButton("Викторина", "icon_check.png")
        btn_quiz.bind(on_release=self.go_to_quiz)
        grid.add_widget(btn_quiz)

        grid.add_widget(BoxLayout(size_hint=(1,1)))

        layout.add_widget(grid)
        layout.add_widget(BoxLayout(size_hint=(1, 0.05)))

        self.add_widget(layout)

    def go_to_fact_of_day(self, instance):
        best_fact = pick_recommended_fact(self.user_prefs)
        self.manager.current = 'fact_screen'
        self.manager.get_screen('fact_screen').show_fact(best_fact)

    def go_to_history(self, instance): self.manager.current = 'history_screen'
    def go_to_notes(self, instance): self.manager.current = 'notes_screen'
    def go_to_stats(self, instance): self.manager.current = 'stats_screen'
    def go_to_settings(self, instance): self.manager.current = 'settings_screen'
    def go_to_quiz(self, instance): self.manager.current = 'quiz_screen'


# ============================================================
#  ЭКРАН ФАКТА
# ============================================================

class FactScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_fact = None
        self.showing_extended = False
        self.user_prefs = _up()
        self.build_ui()

    def build_ui(self):
        main_layout = BoxLayout(orientation='vertical', padding=[dp(15), dp(10)], spacing=dp(10))

        top_panel = BoxLayout(size_hint=(1, None), height=dp(45), spacing=dp(8))

        back_btn = BackButton(self.go_back, size_hint=(0.15, 1))
        top_panel.add_widget(back_btn)

        self.ext_btn = IconMenuButton("Подробнее", "icon_bookmark.png", orientation='horizontal')
        self.ext_btn.size_hint = (0.85, 1)
        self.ext_btn.bind(on_release=self.toggle_extended)
        top_panel.add_widget(self.ext_btn)
        main_layout.add_widget(top_panel)

        self.scroll = ScrollView(size_hint=(1, 1), bar_width=dp(3))
        content_box = BoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(15))
        content_box.bind(minimum_height=content_box.setter('height'))

        photo_container = FloatLayout(size_hint=(1, None), height=dp(150))
        with photo_container.canvas:
            Color(*COLOR_GOLD)
            self.outer_ellipse = Line(circle=(0, 0, dp(65)), width=2)
            Color(*COLOR_BG)
            self.inner_ellipse = Ellipse(pos=(0, 0), size=(dp(126), dp(126)))

        def draw_circle(instance, value):
            cx = instance.x + instance.width / 2
            cy = instance.y + instance.height / 2
            self.outer_ellipse.circle = (cx, cy, dp(65))
            self.inner_ellipse.pos = (cx - dp(63), cy - dp(63))
            self.inner_ellipse.size = (dp(126), dp(126))

        photo_container.bind(pos=draw_circle, size=draw_circle)

        self.photo_text = Label(text="ФОТО", font_size='16sp', color=COLOR_GOLD, pos_hint={'center_x':0.5, 'center_y':0.5})
        photo_container.add_widget(self.photo_text)
        content_box.add_widget(photo_container)

        self.fact_text = Label(text="", font_size='22sp', color=COLOR_TEXT, bold=True, halign='center', valign='top', size_hint_y=None)
        self.fact_text.bind(width=lambda instance, value: setattr(instance, 'text_size', (value, None)))
        self.fact_text.bind(texture_size=lambda instance, value: setattr(instance, 'height', value[1]))
        content_box.add_widget(self.fact_text)

        self.ext_text = Label(text="", font_size='16sp', color=(0.85, 0.85, 0.85, 1), halign='center', valign='top', size_hint_y=None)
        self.ext_text.bind(width=lambda instance, value: setattr(instance, 'text_size', (value, None)))
        self.ext_text.bind(texture_size=lambda instance, value: setattr(instance, 'height', value[1]))
        self.ext_text.opacity = 0
        content_box.add_widget(self.ext_text)

        self.tags_label = Label(text="", font_size='14sp', color=COLOR_GOLD, size_hint_y=None, height=dp(30), halign='center')
        content_box.add_widget(self.tags_label)

        content_box.add_widget(BoxLayout(size_hint=(1, None), height=dp(20)))

        self.scroll.add_widget(content_box)
        main_layout.add_widget(self.scroll)

        bottom_panel = BoxLayout(orientation='vertical', size_hint=(1, None), height=dp(100), spacing=dp(10))

        action_row = BoxLayout(size_hint=(1, None), height=dp(60), spacing=dp(10))

        self.like_btn = IconActionButton("icon_heart.png")
        self.like_btn.bind(on_release=self.toggle_like)

        self.dislike_btn = IconActionButton("icon_bookmark.png")
        self.dislike_btn.bind(on_release=self.toggle_dislike)

        self.note_btn = IconActionButton("icon_pencil.png")
        self.note_btn.bind(on_release=self.open_note_popup)

        next_btn = IconActionButton("icon_refresh.png")
        next_btn.bind(on_release=self.next_fact)

        action_row.add_widget(self.like_btn)
        action_row.add_widget(self.dislike_btn)
        action_row.add_widget(self.note_btn)
        action_row.add_widget(next_btn)
        bottom_panel.add_widget(action_row)

        self.status_label = Label(text="", font_size='12sp', color=(0.5, 0.5, 0.5, 1), size_hint_y=None, height=dp(20), halign='center')
        bottom_panel.add_widget(self.status_label)

        main_layout.add_widget(bottom_panel)
        self.add_widget(main_layout)

    def show_fact(self, fact):
        self.current_fact = fact
        self.showing_extended = False
        self.ext_text.opacity = 0
        self.ext_btn.text_label.text = "Подробнее"

        self.scroll.scroll_y = 1

        self.photo_text.text = f"ФОТО\n{fact.get('title', '')}"
        self.fact_text.text = fact["text"]
        self.fact_text.text_size = (self.fact_text.width, None)

        if "extended" in fact and fact["extended"]:
            self.ext_text.text = fact["extended"]
            self.has_extended = True
        else:
            self.ext_text.text = "Нет дополнительной информации"
            self.has_extended = False

        self.tags_label.text = "  ".join([f"#{tag}" for tag in fact["tags"]])

        status = self.user_prefs.get_fact_status(fact["id"])
        self.update_buttons(status)

        if self.user_prefs.has_note(fact["id"]):
            self.note_btn.set_active((0.2, 0.8, 0.2, 0.2))
        else:
            self.note_btn.set_active(COLOR_BTN_BG)

        if fact["id"] not in self.user_prefs.data["viewed_facts"]:
            self.user_prefs.add_view(fact["id"], fact["tags"])

        stats = self.user_prefs.get_user_stats()
        self.status_label.text = f"Просмотрено: {stats['unique_facts_viewed']} | [+]: {stats['liked_count']} | Заметок: {len(self.user_prefs.get_all_notes())}"

    def toggle_extended(self, instance):
        if not self.has_extended: return
        self.showing_extended = not self.showing_extended
        if self.showing_extended:
            self.ext_text.opacity = 1
            self.ext_btn.text_label.text = "Скрыть"
            self.ext_text.text_size = (self.ext_text.width, None)
            Animation(opacity=1, duration=0.3).start(self.ext_text)
        else:
            Animation(opacity=0, duration=0.3).start(self.ext_text)
            self.ext_btn.text_label.text = "Подробнее"

    def open_note_popup(self, instance):
        if not self.current_fact: return
        fact_id = self.current_fact["id"]
        existing_note = self.user_prefs.get_note(fact_id)

        content = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(8))
        content.add_widget(Label(text="ЗАМЕТКА", font_size='18sp', color=COLOR_GOLD, bold=True))
        text_input = TextInput(text=existing_note, hint_text="Введите текст...", multiline=True,
                               background_color=COLOR_BTN_BG, foreground_color=COLOR_TEXT)
        content.add_widget(text_input)

        btn_row = BoxLayout(size_hint=(1, None), height=dp(40), spacing=dp(8))
        cancel_btn = Button(text="Отмена", background_color=(0.3, 0.3, 0.3, 0.8), color=COLOR_TEXT)
        save_btn = Button(text="Сохранить", background_color=COLOR_RED, color=COLOR_GOLD)

        btn_row.add_widget(cancel_btn)
        btn_row.add_widget(save_btn)
        content.add_widget(btn_row)

        popup = Popup(title="", content=content, size_hint=(0.9, 0.6), background_color=(0, 0, 0, 0.9))

        def save_note(instance):
            self.user_prefs.add_note(fact_id, text_input.text)
            popup.dismiss()
            self.show_fact(self.current_fact)

        save_btn.bind(on_release=save_note)
        cancel_btn.bind(on_release=popup.dismiss)
        popup.open()

    def update_buttons(self, status):
        self.like_btn.set_active(COLOR_BTN_BG)
        self.dislike_btn.set_active(COLOR_BTN_BG)

        if status == "liked":
            self.like_btn.set_active(COLOR_GOLD)
        elif status == "disliked":
            self.dislike_btn.set_active(COLOR_RED)

    def toggle_like(self, instance):
        if not self.current_fact: return
        fact_id = self.current_fact["id"]
        tags = self.current_fact["tags"]
        status = self.user_prefs.get_fact_status(fact_id)
        if status == "liked": self.user_prefs.remove_like(fact_id, tags)
        else:
            if status == "disliked": self.user_prefs.remove_dislike(fact_id, tags)
            self.user_prefs.add_like(fact_id, tags)
        self.show_fact(self.current_fact)

    def toggle_dislike(self, instance):
        if not self.current_fact: return
        fact_id = self.current_fact["id"]
        tags = self.current_fact["tags"]
        status = self.user_prefs.get_fact_status(fact_id)
        if status == "disliked": self.user_prefs.remove_dislike(fact_id, tags)
        else:
            if status == "liked": self.user_prefs.remove_like(fact_id, tags)
            self.user_prefs.add_dislike(fact_id, tags)
        self.show_fact(self.current_fact)

    def next_fact(self, instance):
        viewed_facts = set(self.user_prefs.data["viewed_facts"])
        unviewed_facts = [f for f in FACTS_DATABASE if f["id"] not in viewed_facts]
        if unviewed_facts:
            self.show_fact(pick_recommended_fact(self.user_prefs))
        else:
            self.status_label.text = "Вы изучили все факты!"
            self.show_fact(random.choice(FACTS_DATABASE))

    def go_back(self, instance):
        self.manager.current = 'main_menu'


# ============================================================
#  ВИКТОРИНА
# ============================================================

class QuizScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.user_prefs = _up()
        self.current_fact = None
        self.current_q = None
        self.option_buttons = []
        self.build_ui()

    def on_enter(self, *args):
        self.start_new_round()

    def build_ui(self):
        layout = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(10))
        layout.add_widget(make_header("Проверка знаний", self.go_back))

        q_stats = self.user_prefs.get_quiz_stats()
        self.score_label = Label(
            text=f"Счёт: {q_stats['score']}  |  Правильно: {q_stats['correct']} из {q_stats['attempts']}",
            font_size='16sp', color=COLOR_ORANGE, bold=True, size_hint=(1, None), height=dp(30)
        )
        layout.add_widget(self.score_label)

        self.question_label = Label(
            text="", font_size='20sp', color=COLOR_TEXT, bold=True,
            halign='center', valign='middle', size_hint=(1, 0.3)
        )
        self.question_label.bind(width=lambda i, v: setattr(i, 'text_size', (v, None)))
        layout.add_widget(self.question_label)

        self.options_grid = GridLayout(cols=2, spacing=dp(10), size_hint=(1, 0.5))
        layout.add_widget(self.options_grid)

        self.add_widget(layout)

    def _studied_with_quiz(self):
        viewed = set(self.user_prefs.data["viewed_facts"])
        return [f for f in FACTS_DATABASE if f["id"] in viewed and f.get("quiz")]

    def start_new_round(self):
        self.options_grid.clear_widgets()
        self.option_buttons = []

        pool = self._studied_with_quiz()
        if len(pool) < 4:
            self.current_fact = None
            self.current_q = None
            self.question_label.text = (
                "Викторина открывается после изучения минимум 4 фактов.\n"
                f"Сейчас изучено: {len(pool)}."
            )
            return

        self.current_fact = random.choice(pool)
        self.current_q = random.choice(self.current_fact["quiz"])
        self.question_label.text = self.current_q["q"]

        options = [self.current_q["correct"]] + list(self.current_q["wrong"])
        random.shuffle(options)

        for option in options:
            btn = Button(
                text=option, font_size='16sp',
                background_color=COLOR_BTN_BG, color=COLOR_GOLD, bold=True
            )
            btn.bind(on_release=lambda b, opt=option: self.check_answer(b, opt))
            self.options_grid.add_widget(btn)
            self.option_buttons.append(btn)

    def check_answer(self, btn, selected_option):
        if not self.current_q:
            return
        for b in self.option_buttons:
            b.disabled = True

        is_correct = (selected_option == self.current_q["correct"])
        self.user_prefs.add_quiz_result(is_correct)

        q_stats = self.user_prefs.get_quiz_stats()
        self.score_label.text = f"Счёт: {q_stats['score']}  |  Правильно: {q_stats['correct']} из {q_stats['attempts']}"

        if is_correct:
            btn.background_color = COLOR_GREEN
            btn.color = (1, 1, 1, 1)
        else:
            btn.background_color = COLOR_RED
            btn.color = (1, 1, 1, 1)
            for b in self.option_buttons:
                if b.text == self.current_q["correct"]:
                    b.background_color = COLOR_GREEN
                    b.color = (1, 1, 1, 1)

        Clock.schedule_once(lambda dt: self.start_new_round(), 1.5)

    def go_back(self, instance):
        self.manager.current = 'main_menu'


# ============================================================
#  ОСТАЛЬНЫЕ ЭКРАНЫ
# ============================================================

class HistoryScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.user_prefs = _up()
        self.build_ui()

    def on_enter(self, *args):
        self.clear_widgets()
        self.build_ui()

    def build_ui(self):
        layout = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(6))
        layout.add_widget(make_header("История", self.go_back))

        scroll = ScrollView(size_hint=(1, 0.9))
        content = BoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(10))
        content.bind(minimum_height=content.setter('height'))

        liked = self.user_prefs.data["liked_facts"]
        viewed = self.user_prefs.data["viewed_facts"]
        not_liked = [fid for fid in viewed if fid not in liked]

        content.add_widget(Label(text=f"★ ПОНРАВИВШИЕСЯ ({len(liked)})", font_size='16sp', color=COLOR_GOLD, size_hint=(1, None), height=dp(40)))
        for fact_id in reversed(liked):
            fact = get_fact_by_id(fact_id)
            if fact:
                btn = IconMenuButton(_fact_label(fact, 40), "icon_heart.png", orientation='horizontal')
                btn.size_hint = (1, None)
                btn.height = dp(50)
                btn.bind(on_release=lambda x, f=fact: self.view_fact(f))
                content.add_widget(btn)

        content.add_widget(Label(text="", size_hint=(1, None), height=dp(10)))
        content.add_widget(Label(text=f"▸ ИЗУЧЕННЫЕ ({len(not_liked)})", font_size='16sp', color=COLOR_TEXT, size_hint=(1, None), height=dp(40)))
        for fact_id in reversed(not_liked):
            fact = get_fact_by_id(fact_id)
            if fact:
                btn = IconMenuButton(_fact_label(fact, 40), "icon_book.png", orientation='horizontal')
                btn.size_hint = (1, None)
                btn.height = dp(50)
                btn.bind(on_release=lambda x, f=fact: self.view_fact(f))
                content.add_widget(btn)

        scroll.add_widget(content)
        layout.add_widget(scroll)
        self.add_widget(layout)

    def view_fact(self, fact):
        self.manager.current = 'fact_screen'
        self.manager.get_screen('fact_screen').show_fact(fact)
    def go_back(self, instance): self.manager.current = 'main_menu'


class NotesScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.user_prefs = _up()
        self.build_ui()

    def on_enter(self, *args):
        self.clear_widgets()
        self.build_ui()

    def build_ui(self):
        layout = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(6))
        layout.add_widget(make_header("Мои заметки", self.go_back))

        scroll = ScrollView(size_hint=(1, 0.9))
        notes_box = BoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(8))
        notes_box.bind(minimum_height=notes_box.setter('height'))

        all_notes = self.user_prefs.get_all_notes()
        if all_notes:
            for fact_id_str, text in all_notes.items():
                fact = get_fact_by_id(int(fact_id_str))
                if fact:
                    btn = IconMenuButton(f"{_fact_label(fact, 30)}\n\n{text[:80]}...", "icon_pencil.png", orientation='horizontal')
                    btn.size_hint = (1, None)
                    btn.height = dp(100)
                    btn.bind(on_release=lambda x, f=fact: self.view_fact(f))
                    notes_box.add_widget(btn)
        else:
            notes_box.add_widget(Label(text="У вас пока нет заметок", color=COLOR_TEXT, font_size='16sp'))

        scroll.add_widget(notes_box)
        layout.add_widget(scroll)
        self.add_widget(layout)

    def view_fact(self, fact):
        self.manager.current = 'fact_screen'
        self.manager.get_screen('fact_screen').show_fact(fact)
    def go_back(self, instance): self.manager.current = 'main_menu'


class StatsScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.user_prefs = _up()
        self.build_ui()

    def on_enter(self, *args):
        self.clear_widgets()
        self.build_ui()

    def build_ui(self):
        layout = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(6))
        layout.add_widget(make_header("Статистика", self.go_back))

        scroll = ScrollView(size_hint=(1, 0.9))
        content = BoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(10))
        content.bind(minimum_height=content.setter('height'))

        stats = self.user_prefs.get_user_stats()
        q_stats = self.user_prefs.get_quiz_stats()
        total_facts = get_facts_count()
        progress = self.user_prefs.get_total_progress(total_facts)

        content.add_widget(Label(text="[ ОБЩИЙ ПРОГРЕСС ]", font_size='18sp', color=COLOR_GOLD, size_hint=(1, None), height=dp(40)))
        content.add_widget(Label(text=f"Изучено: {stats['unique_facts_viewed']} / {total_facts}", font_size='15sp', color=COLOR_TEXT, size_hint=(1, None), height=dp(30)))
        content.add_widget(Label(text=f"Прогресс: {progress}%", font_size='15sp', color=COLOR_TEXT, size_hint=(1, None), height=dp(30)))

        content.add_widget(Label(text="[ ВИКТОРИНА ]", font_size='18sp', color=COLOR_GOLD, size_hint=(1, None), height=dp(40)))
        content.add_widget(Label(text=f"Счёт: {q_stats['score']} очков", font_size='15sp', color=COLOR_TEXT, size_hint=(1, None), height=dp(30)))
        content.add_widget(Label(text=f"Правильных ответов: {q_stats['correct']} из {q_stats['attempts']}", font_size='15sp', color=COLOR_TEXT, size_hint=(1, None), height=dp(30)))

        content.add_widget(Label(text="[ ДОСТИЖЕНИЯ ]", font_size='18sp', color=COLOR_GOLD, size_hint=(1, None), height=dp(40)))
        achievements = self.user_prefs.get_achievement_progress()
        if achievements:
            for ach in achievements:
                content.add_widget(Label(text=f"[+] {ach['name']} — {ach['desc']}", font_size='14sp', color=COLOR_TEXT, size_hint=(1, None), height=dp(30)))
        else:
            content.add_widget(Label(text="Читайте факты, чтобы получать достижения!", font_size='14sp', color=(0.5, 0.5, 0.5, 1)))

        scroll.add_widget(content)
        layout.add_widget(scroll)
        self.add_widget(layout)

    def go_back(self, instance): self.manager.current = 'main_menu'


class SettingsScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.user_prefs = _up()
        self.build_ui()

    def on_enter(self, *args):
        self.clear_widgets()
        self.build_ui()

    def build_ui(self):
        layout = BoxLayout(orientation='vertical', padding=dp(15), spacing=dp(15))
        layout.add_widget(make_header("Настройки", self.go_back))

        layout.add_widget(Label(text=f"Версия: {__version__}", font_size='15sp', color=COLOR_TEXT))

        btn_clear = IconMenuButton("Очистить историю", "icon_refresh.png", orientation='horizontal')
        btn_clear.size_hint = (1, None)
        btn_clear.height = dp(50)
        btn_clear.bind(on_release=self.confirm_clear_history)
        layout.add_widget(btn_clear)

        btn_reset = IconMenuButton("Сбросить всё", "icon_chart_bar.png", orientation='horizontal')
        btn_reset.size_hint = (1, None)
        btn_reset.height = dp(50)
        btn_reset.bind(on_release=self.confirm_reset_all)
        layout.add_widget(btn_reset)

        layout.add_widget(BoxLayout(size_hint=(1, 1)))
        self.add_widget(layout)

    def confirm_clear_history(self, instance):
        content = BoxLayout(orientation='vertical', padding=dp(15), spacing=dp(15))
        lbl = Label(text="Вы уверены, что хотите очистить историю просмотров?\nЭто действие нельзя отменить.",
                    font_size='16sp', color=COLOR_TEXT, halign='center', valign='middle')
        lbl.bind(width=lambda i, v: setattr(i, 'text_size', (v, None)))
        content.add_widget(lbl)

        btn_row = BoxLayout(size_hint=(1, None), height=dp(45), spacing=dp(10))
        cancel_btn = Button(text="Отмена", background_color=(0.3, 0.3, 0.3, 1), color=COLOR_TEXT, font_size='16sp')
        confirm_btn = Button(text="Очистить", background_color=COLOR_RED, color=COLOR_GOLD, font_size='16sp', bold=True)

        btn_row.add_widget(cancel_btn)
        btn_row.add_widget(confirm_btn)
        content.add_widget(btn_row)

        popup = Popup(title="", content=content, size_hint=(0.85, 0.35), background_color=COLOR_BTN_BG)

        def do_clear(inst):
            self.user_prefs.clear_history()
            popup.dismiss()
            self.clear_widgets()
            self.build_ui()

        confirm_btn.bind(on_release=do_clear)
        cancel_btn.bind(on_release=popup.dismiss)
        popup.open()

    def confirm_reset_all(self, instance):
        content = BoxLayout(orientation='vertical', padding=dp(15), spacing=dp(15))
        lbl = Label(text="ВНИМАНИЕ!\nВы действительно хотите удалить ВСЕ данные?\n(Историю, лайки, заметки, викторину и прогресс)",
                    font_size='15sp', color=COLOR_TEXT, halign='center', valign='middle')
        lbl.bind(width=lambda i, v: setattr(i, 'text_size', (v, None)))
        content.add_widget(lbl)

        btn_row = BoxLayout(size_hint=(1, None), height=dp(45), spacing=dp(10))
        cancel_btn = Button(text="Отмена", background_color=(0.3, 0.3, 0.3, 1), color=COLOR_TEXT, font_size='16sp')
        confirm_btn = Button(text="Удалить всё", background_color=COLOR_RED, color=COLOR_GOLD, font_size='16sp', bold=True)

        btn_row.add_widget(cancel_btn)
        btn_row.add_widget(confirm_btn)
        content.add_widget(btn_row)

        popup = Popup(title="", content=content, size_hint=(0.85, 0.4), background_color=COLOR_BTN_BG)

        def do_reset(inst):
            self.user_prefs.reset_data()
            popup.dismiss()
            self.clear_widgets()
            self.build_ui()

        confirm_btn.bind(on_release=do_reset)
        cancel_btn.bind(on_release=popup.dismiss)
        popup.open()

    def go_back(self, instance): self.manager.current = 'main_menu'


class TagScreen(Screen):
    pass


# ============================================================
#  ПРИЛОЖЕНИЕ
# ============================================================

class WarFactApp(App):
    def build(self):
        Window.clearcolor = COLOR_BG
        # Единый UserPreferences на всё приложение
        self.user_prefs = UserPreferences()

        sm = ScreenManager()
        sm.add_widget(MainMenuScreen(name='main_menu'))
        sm.add_widget(FactScreen(name='fact_screen'))
        sm.add_widget(HistoryScreen(name='history_screen'))
        sm.add_widget(NotesScreen(name='notes_screen'))
        sm.add_widget(StatsScreen(name='stats_screen'))
        sm.add_widget(SettingsScreen(name='settings_screen'))
        sm.add_widget(QuizScreen(name='quiz_screen'))
        return sm


if __name__ == '__main__':
    WarFactApp().run()
