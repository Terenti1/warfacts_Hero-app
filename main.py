# main.py - Приложение "Герои Беларуси"

import random
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.button import ButtonBehavior
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.floatlayout import FloatLayout
from kivy.core.window import Window
from kivy.animation import Animation
from kivy.utils import get_color_from_hex
from kivy.graphics import Color, Rectangle, Line, Ellipse
from kivy.metrics import dp

from data import FACTS_DATABASE, get_facts_count, get_fact_by_id, get_all_tags, get_facts_by_tag
from user_data import UserPreferences

try:
    from version import __version__
except Exception:
    __version__ = "1.0.0"

try:
    from updater import check_for_updates, UPDATER_AVAILABLE
except Exception:
    UPDATER_AVAILABLE = False
    def check_for_updates(manual=False): pass

# Цветовая палитра
COLOR_BG = get_color_from_hex('#16251B')      # Темно-зеленый фон
COLOR_GOLD = get_color_from_hex('#D4AF37')    # Золотой
COLOR_RED = get_color_from_hex('#8B2525')     # Темно-красный
COLOR_TEXT = (0.9, 0.9, 0.9, 1)               # Светлый текст
COLOR_ORANGE = get_color_from_hex('#E67E22')  # Оранжевый

Window.clearcolor = COLOR_BG


def _fact_label(fact, length=60):
    title = fact.get("title")
    if title: return title
    text = fact.get("text", "")
    return text[:length] + "..." if len(text) > length else text


def make_header(title_text, back_callback, height=dp(50)):
    """Хедер с центрированным заголовком и кнопкой назад слева."""
    header = FloatLayout(size_hint=(1, None), height=height)

    title = Label(
        text=title_text, font_size='20sp', color=COLOR_GOLD, bold=True,
        size_hint=(1, 1), pos_hint={'x': 0, 'y': 0},
        halign='center', valign='middle', text_size=(Window.width - 30, None)
    )
    header.add_widget(title)

    back_btn = Button(
        text="<--", size_hint=(0.15, 1), pos_hint={'x': 0, 'y': 0},
        background_color=(0.2, 0.2, 0.2, 0.5), color=COLOR_GOLD, font_size='16sp'
    )
    back_btn.bind(on_release=back_callback)
    header.add_widget(back_btn)

    return header


class GoldButton(Button):
    """Кнопка с золотой рамкой."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = ''
        self.background_color = (0, 0, 0, 0) # Прозрачный фон для отрисовки
        self.color = COLOR_GOLD
        self.bold = True
        self.font_size = '16sp'
        
        with self.canvas.before:
            Color(0.1, 0.15, 0.12, 1) # Темный фон кнопки
            self.rect = Rectangle(pos=self.pos, size=self.size)
            Color(*COLOR_GOLD)
            self.line = Line(rectangle=(self.x, self.y, self.width, self.height), width=1.5)
            
        self.bind(pos=self.update_graphics, size=self.update_graphics)
        
    def update_graphics(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size
        self.line.rectangle = (instance.x, instance.y, instance.width, instance.height)


class FactCard(ButtonBehavior, BoxLayout):
    """Красная карточка 'Факт дня'."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = dp(10)
        self.spacing = dp(5)
        
        with self.canvas.before:
            Color(*COLOR_RED)
            self.rect = Rectangle(pos=self.pos, size=self.size)
            Color(*COLOR_GOLD)
            self.line = Line(rectangle=(self.x, self.y, self.width, self.height), width=2)
            
        self.bind(pos=self.update_graphics, size=self.update_graphics)

        # Содержимое
        self.add_widget(Label(text="★", font_size='28sp', color=COLOR_GOLD, size_hint=(1, 0.15)))
        self.add_widget(Label(text="ФАКТ ДНЯ", font_size='18sp', color=COLOR_GOLD, bold=True, size_hint=(1, 0.15)))
        
        # Место под фото (Круг)
        photo_layout = FloatLayout(size_hint=(1, 0.45))
        with photo_layout.canvas:
            Color(*COLOR_BG) # Черный фон внутри круга
            self.ellipse = Ellipse(pos=(Window.width/2 - dp(30), photo_layout.y + dp(10)), size=(dp(60), dp(60)))
            Color(*COLOR_GOLD)
            self.ellipse_border = Line(circle=(Window.width/2, photo_layout.y + dp(40), dp(30)), width=1.5)
            
        self.photo_text = Label(text="ФОТО", font_size='12sp', color=COLOR_GOLD, pos_hint={'center_x':0.5, 'center_y':0.5})
        photo_layout.add_widget(self.photo_text)
        self.add_widget(photo_layout)
        
        self.subtitle = Label(
            text="Портрет героя\nи краткий подвиг", font_size='13sp', color=COLOR_TEXT,
            halign='center', size_hint=(1, 0.25)
        )
        self.add_widget(self.subtitle)

    def update_graphics(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size
        self.line.rectangle = (instance.x, instance.y, instance.width, instance.height)


class CustomProgressBar(BoxLayout):
    """Тонкий прогресс-бар."""
    def __init__(self, progress=0, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (1, None)
        self.height = dp(20)
        self.progress = progress
        
        self.label = Label(text=f"{progress}%", font_size='10sp', color=COLOR_TEXT)
        self.add_widget(self.label)
        
        self.bind(pos=self.update_graphics, size=self.update_graphics)

    def update_graphics(self, instance, value):
        self.canvas.before.clear()
        with self.canvas.before:
            # Фон
            Color(0.2, 0.2, 0.2, 1)
            Rectangle(pos=instance.pos, size=instance.size)
            # Заливка
            if self.progress > 0:
                Color(*COLOR_ORANGE)
                width = instance.width * (self.progress / 100)
                Rectangle(pos=instance.pos, size=(width, instance.height))
            # Рамка
            Color(*COLOR_GOLD)
            Line(rectangle=(instance.x, instance.y, instance.width, instance.height), width=1)


# ============================================================
#  ГЛАВНОЕ МЕНЮ
# ============================================================

class MainMenuScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.user_prefs = UserPreferences()
        self._built_once = False
        self.build_ui()

    def on_enter(self, *args):
        if self._built_once:
            self.clear_widgets()
            self.user_prefs = UserPreferences()
            self.build_ui()
        else:
            self._built_once = True

    def build_ui(self):
        layout = BoxLayout(orientation='vertical', padding=dp(15), spacing=dp(10))

        # 1. Шапка
        header = BoxLayout(orientation='vertical', size_hint=(1, None), height=dp(90))
        header.add_widget(Label(text="НИКТО НЕ ЗАБЫТ", font_size='12sp', color=COLOR_GOLD, bold=True))
        header.add_widget(Label(text="ГЕРОИ БЕЛАРУСИ", font_size='26sp', color=COLOR_GOLD, bold=True))
        header.add_widget(Label(text="Партизаны, лётчики, подпольщики", font_size='13sp', color=COLOR_TEXT))
        layout.add_widget(header)

        # 2. Прогресс
        total_facts = get_facts_count()
        viewed = len(self.user_prefs.data["viewed_facts"])
        progress = self.user_prefs.get_total_progress(total_facts)
        streak = self.user_prefs.get_streak_days()

        prog_box = BoxLayout(orientation='vertical', size_hint=(1, None), height=dp(45), spacing=dp(2))
        
        prog_labels = BoxLayout(size_hint=(1, None), height=dp(20))
        prog_labels.add_widget(Label(text=f"Прогресс: {viewed}/{total_facts}", font_size='13sp', color=COLOR_TEXT, halign='left'))
        prog_labels.add_widget(Label(text=f"Серия: {streak} дн.", font_size='13sp', color=COLOR_ORANGE, halign='right'))
        
        prog_box.add_widget(prog_labels)
        prog_box.add_widget(CustomProgressBar(progress))
        layout.add_widget(prog_box)

        # 3. Карточка "Факт дня"
        self.fact_card = FactCard(size_hint=(1, None), height=dp(200))
        self.fact_card.bind(on_release=self.go_to_fact_of_day)
        layout.add_widget(self.fact_card)

        # 4. Сетка кнопок
        grid = GridLayout(cols=2, spacing=dp(10), size_hint=(1, None), height=dp(150))
        
        btn_history = GoldButton(text="[ История ]")
        btn_history.bind(on_release=self.go_to_history)
        grid.add_widget(btn_history)

        btn_notes = GoldButton(text="[ Заметки ]")
        btn_notes.bind(on_release=self.go_to_notes)
        grid.add_widget(btn_notes)

        btn_stats = GoldButton(text="[ Статистика ]")
        btn_stats.bind(on_release=self.go_to_stats)
        grid.add_widget(btn_stats)

        btn_settings = GoldButton(text="[ Настройки ]")
        btn_settings.bind(on_release=self.go_to_settings)
        grid.add_widget(btn_settings)

        layout.add_widget(grid)
        
        # Пустое место снизу, чтобы все прижалось к верху
        layout.add_widget(BoxLayout(size_hint=(1, 1)))

        self.add_widget(layout)

    def go_to_fact_of_day(self, instance):
        viewed_facts = set(self.user_prefs.data["viewed_facts"])
        unviewed_facts = [f for f in FACTS_DATABASE if f["id"] not in viewed_facts]

        if unviewed_facts:
            scored_facts = [(f, self.user_prefs.get_recommendation_score(f)) for f in unviewed_facts]
            scored_facts.sort(key=lambda x: x[1], reverse=True)
            best_fact = scored_facts[0][0] if scored_facts else random.choice(unviewed_facts)
        else:
            liked = self.user_prefs.data["liked_facts"]
            best_fact = get_fact_by_id(random.choice(liked)) if liked else random.choice(FACTS_DATABASE)

        self.manager.current = 'fact_screen'
        self.manager.get_screen('fact_screen').show_fact(best_fact)

    def go_to_history(self, instance): self.manager.current = 'history_screen'
    def go_to_notes(self, instance): self.manager.current = 'notes_screen'
    def go_to_stats(self, instance): self.manager.current = 'stats_screen'
    def go_to_settings(self, instance): self.manager.current = 'settings_screen'


# ============================================================
#  ЭКРАН ФАКТА
# ============================================================

class FactScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_fact = None
        self.showing_extended = False
        self.user_prefs = UserPreferences()
        self.build_ui()

    def build_ui(self):
        layout = BoxLayout(orientation='vertical', padding=dp(15), spacing=dp(10))

        # Верхняя панель
        top_panel = BoxLayout(size_hint=(1, None), height=dp(40), spacing=dp(8))
        back_btn = Button(text="<--", size_hint=(0.15, 1), background_color=(0.2, 0.2, 0.2, 0.5), color=COLOR_GOLD)
        back_btn.bind(on_release=self.go_back)
        top_panel.add_widget(back_btn)

        self.ext_btn = GoldButton(text="[i] Подробнее", size_hint=(0.85, 1))
        self.ext_btn.bind(on_release=self.toggle_extended)
        top_panel.add_widget(self.ext_btn)
        layout.add_widget(top_panel)

        # Круглая заглушка для фото
        photo_container = FloatLayout(size_hint=(1, None), height=dp(140))
        with photo_container.canvas:
            Color(*COLOR_GOLD)
            self.ellipse = Ellipse(pos=(Window.width/2 - dp(60), dp(10)), size=(dp(120), dp(120)))
            Color(*COLOR_BG)
            self.inner_ellipse = Ellipse(pos=(Window.width/2 - dp(57), dp(13)), size=(dp(114), dp(114)))
            
        self.photo_text = Label(text="ФОТО", font_size='16sp', color=COLOR_GOLD, pos_hint={'center_x':0.5, 'center_y':0.5})
        photo_container.add_widget(self.photo_text)
        layout.add_widget(photo_container)

        # Текст факта
        self.text_scroll = ScrollView(size_hint=(1, 0.3))
        self.fact_text = Label(
            text="", font_size='18sp', color=COLOR_TEXT,
            halign='left', valign='top', size_hint=(1, None), text_size=(Window.width - dp(30), None)
        )
        self.fact_text.bind(texture_size=self.fact_text.setter('size'))
        self.text_scroll.add_widget(self.fact_text)
        layout.add_widget(self.text_scroll)

        # Расширенная информация
        self.ext_scroll = ScrollView(size_hint=(1, 0.25))
        self.ext_text = Label(
            text="", font_size='14sp', color=(0.8, 0.8, 0.8, 1),
            halign='left', valign='top', size_hint=(1, None), text_size=(Window.width - dp(30), None)
        )
        self.ext_text.bind(texture_size=self.ext_text.setter('size'))
        self.ext_scroll.add_widget(self.ext_text)
        self.ext_scroll.opacity = 0
        self.ext_scroll.disabled = True
        layout.add_widget(self.ext_scroll)

        # Теги
        self.tags_label = Label(text="", font_size='12sp', color=COLOR_GOLD, size_hint=(1, None), height=dp(25), halign='center')
        layout.add_widget(self.tags_label)

        # Кнопки действий
        action_row = BoxLayout(size_hint=(1, None), height=dp(50), spacing=dp(8))

        self.like_btn = GoldButton(text="[+]", font_size='20sp')
        self.like_btn.bind(on_release=self.toggle_like)
        
        self.dislike_btn = GoldButton(text="[-]", font_size='20sp')
        self.dislike_btn.bind(on_release=self.toggle_dislike)
        
        self.note_btn = GoldButton(text="[N]", font_size='20sp')
        self.note_btn.bind(on_release=self.open_note_popup)
        
        next_btn = GoldButton(text="[>]", font_size='20sp')
        next_btn.background_color = (0,0,0,0) # Оставим прозрачным, цвет задается в canvas
        next_btn.bind(on_release=self.next_fact)

        action_row.add_widget(self.like_btn)
        action_row.add_widget(self.dislike_btn)
        action_row.add_widget(self.note_btn)
        action_row.add_widget(next_btn)
        layout.add_widget(action_row)

        self.status_label = Label(text="", font_size='11sp', color=(0.5, 0.5, 0.5, 1), size_hint=(1, None), height=dp(20))
        layout.add_widget(self.status_label)
        
        layout.add_widget(BoxLayout(size_hint=(1, 1))) # Отступ снизу
        self.add_widget(layout)

    def show_fact(self, fact):
        self.current_fact = fact
        self.showing_extended = False
        self.ext_scroll.opacity = 0
        self.ext_scroll.disabled = True
        self.ext_btn.text = "[i] Подробнее"

        self.photo_text.text = f"ПОРТРЕТ\n{fact.get('title', '')}"
        self.fact_text.text = fact["text"]
        self.fact_text.text_size = (self.width - dp(30), None)

        if "extended" in fact and fact["extended"]:
            self.ext_text.text = fact["extended"]
            self.ext_text.text_size = (self.width - dp(30), None)
            self.has_extended = True
        else:
            self.ext_text.text = "Нет дополнительной информации"
            self.has_extended = False

        self.tags_label.text = "  ".join([f"#{tag}" for tag in fact["tags"]])

        status = self.user_prefs.get_fact_status(fact["id"])
        self.update_buttons(status)

        if self.user_prefs.has_note(fact["id"]):
            self.note_btn.text = "[N*]"
            self.note_btn.color = (0.2, 0.8, 0.2, 1)
        else:
            self.note_btn.text = "[N]"
            self.note_btn.color = COLOR_GOLD

        if fact["id"] not in self.user_prefs.data["viewed_facts"]:
            self.user_prefs.add_view(fact["id"], fact["tags"])

        stats = self.user_prefs.get_user_stats()
        self.status_label.text = f"Просмотрено: {stats['unique_facts_viewed']} | [+]: {stats['liked_count']} | Заметок: {len(self.user_prefs.get_all_notes())}"

    def toggle_extended(self, instance):
        if not self.has_extended: return
        self.showing_extended = not self.showing_extended
        if self.showing_extended:
            self.ext_scroll.opacity = 1
            self.ext_scroll.disabled = False
            self.ext_btn.text = "[i] Скрыть"
            Animation(opacity=1, duration=0.3).start(self.ext_scroll)
        else:
            anim = Animation(opacity=0, duration=0.3)
            anim.bind(on_complete=lambda *args: setattr(self.ext_scroll, 'disabled', True))
            anim.start(self.ext_scroll)
            self.ext_btn.text = "[i] Подробнее"

    def open_note_popup(self, instance):
        if not self.current_fact: return
        fact_id = self.current_fact["id"]
        existing_note = self.user_prefs.get_note(fact_id)

        content = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(8))
        content.add_widget(Label(text="ЗАМЕТКА", font_size='18sp', color=COLOR_GOLD, bold=True))
        text_input = TextInput(text=existing_note, hint_text="Введите текст...", multiline=True,
                               background_color=(0.1, 0.15, 0.12, 1), foreground_color=COLOR_TEXT)
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
        self.like_btn.color = COLOR_GOLD
        self.dislike_btn.color = COLOR_GOLD
        self.like_btn.text = "[+]"
        self.dislike_btn.text = "[-]"

        if status == "liked":
            self.like_btn.color = (0.2, 0.8, 0.2, 1)
            self.like_btn.text = "[★]"
        elif status == "disliked":
            self.dislike_btn.color = (0.8, 0.2, 0.2, 1)
            self.dislike_btn.text = "[✖]"

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
            scored_facts = [(f, self.user_prefs.get_recommendation_score(f)) for f in unviewed_facts]
            scored_facts.sort(key=lambda x: x[1], reverse=True)
            self.show_fact(scored_facts[0][0])
        else:
            self.status_label.text = "Вы изучили все факты!"
            self.show_fact(random.choice(FACTS_DATABASE))

    def go_back(self, instance):
        self.manager.current = 'main_menu'


# ============================================================
#  ОСТАЛЬНЫЕ ЭКРАНЫ
# ============================================================

class HistoryScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.user_prefs = UserPreferences()
        self._built_once = False
        self.build_ui()

    def on_enter(self, *args):
        if self._built_once:
            self.clear_widgets(); self.user_prefs = UserPreferences(); self.build_ui()
        else: self._built_once = True

    def build_ui(self):
        layout = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(6))
        layout.add_widget(make_header("История", self.go_back))

        scroll = ScrollView(size_hint=(1, 0.9))
        content = BoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(10))
        content.bind(minimum_height=content.setter('height'))

        liked = self.user_prefs.data["liked_facts"]
        viewed = self.user_prefs.data["viewed_facts"]
        not_liked = [fid for fid in viewed if fid not in liked]

        content.add_widget(Label(text=f"★ ПОНРАВИВШИЕСЯ ({len(liked)})", font_size='15sp', color=COLOR_GOLD, size_hint=(1, None), height=dp(40)))
        for fact_id in reversed(liked):
            fact = get_fact_by_id(fact_id)
            if fact:
                btn = GoldButton(text=f"[★] {_fact_label(fact, 40)}")
                btn.size_hint = (1, None)
                btn.height = dp(50)
                btn.bind(on_release=lambda x, f=fact: self.view_fact(f))
                content.add_widget(btn)

        content.add_widget(Label(text="", size_hint=(1, None), height=dp(10)))
        content.add_widget(Label(text=f"▸ ИЗУЧЕННЫЕ ({len(not_liked)})", font_size='15sp', color=COLOR_TEXT, size_hint=(1, None), height=dp(40)))
        for fact_id in reversed(not_liked):
            fact = get_fact_by_id(fact_id)
            if fact:
                btn = GoldButton(text=f"[i] {_fact_label(fact, 40)}")
                btn.color = COLOR_TEXT # Для изученных текст белый
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
        self.user_prefs = UserPreferences()
        self._built_once = False
        self.build_ui()

    def on_enter(self, *args):
        if self._built_once:
            self.clear_widgets(); self.user_prefs = UserPreferences(); self.build_ui()
        else: self._built_once = True

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
                    btn = GoldButton(text=f"[N] {_fact_label(fact, 30)}\n\n{text[:80]}...")
                    btn.size_hint = (1, None)
                    btn.height = dp(90)
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
        self.user_prefs = UserPreferences()
        self._built_once = False
        self.build_ui()

    def on_enter(self, *args):
        if self._built_once:
            self.clear_widgets(); self.user_prefs = UserPreferences(); self.build_ui()
        else: self._built_once = True

    def build_ui(self):
        layout = BoxLayout(orientation='vertical', padding=dp(10), spacing=dp(6))
        layout.add_widget(make_header("Статистика", self.go_back))

        scroll = ScrollView(size_hint=(1, 0.9))
        content = BoxLayout(orientation='vertical', size_hint_y=None, spacing=dp(10))
        content.bind(minimum_height=content.setter('height'))

        stats = self.user_prefs.get_user_stats()
        total_facts = get_facts_count()
        progress = self.user_prefs.get_total_progress(total_facts)

        content.add_widget(Label(text="[ ОБЩИЙ ПРОГРЕСС ]", font_size='16sp', color=COLOR_GOLD, size_hint=(1, None), height=dp(40)))
        content.add_widget(Label(text=f"Изучено: {stats['unique_facts_viewed']} / {total_facts}", font_size='14sp', color=COLOR_TEXT, size_hint=(1, None), height=dp(30)))
        content.add_widget(Label(text=f"Прогресс: {progress}%", font_size='14sp', color=COLOR_TEXT, size_hint=(1, None), height=dp(30)))

        content.add_widget(Label(text="[ ДОСТИЖЕНИЯ ]", font_size='16sp', color=COLOR_GOLD, size_hint=(1, None), height=dp(40)))
        achievements = self.user_prefs.get_achievement_progress()
        if achievements:
            for ach in achievements:
                content.add_widget(Label(text=f"[+] {ach['name']} — {ach['desc']}", font_size='13sp', color=COLOR_TEXT, size_hint=(1, None), height=dp(30)))
        else:
            content.add_widget(Label(text="Читайте факты, чтобы получать достижения!", font_size='14sp', color=(0.5, 0.5, 0.5, 1)))

        scroll.add_widget(content)
        layout.add_widget(scroll)
        self.add_widget(layout)

    def go_back(self, instance): self.manager.current = 'main_menu'


class SettingsScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.user_prefs = UserPreferences()
        self._built_once = False
        self.build_ui()

    def on_enter(self, *args):
        if self._built_once:
            self.clear_widgets(); self.user_prefs = UserPreferences(); self.build_ui()
        else: self._built_once = True

    def build_ui(self):
        layout = BoxLayout(orientation='vertical', padding=dp(15), spacing=dp(15))
        layout.add_widget(make_header("Настройки", self.go_back))

        layout.add_widget(Label(text=f"Версия: {__version__}", font_size='14sp', color=COLOR_TEXT))

        btn_clear = GoldButton(text="ОЧИСТИТЬ ИСТОРИЮ")
        btn_clear.background_color = (0.6, 0.2, 0.2, 0.9)
        btn_clear.size_hint = (1, None)
        btn_clear.height = dp(50)
        btn_clear.bind(on_release=self.clear_history)
        layout.add_widget(btn_clear)

        btn_reset = GoldButton(text="СБРОСИТЬ ВСЁ")
        btn_reset.background_color = (0.4, 0.1, 0.1, 0.8)
        btn_reset.size_hint = (1, None)
        btn_reset.height = dp(50)
        btn_reset.bind(on_release=self.reset_all)
        layout.add_widget(btn_reset)

        if UPDATER_AVAILABLE:
            btn_update = GoldButton(text="ПРОВЕРИТЬ ОБНОВЛЕНИЯ")
            btn_update.size_hint = (1, None)
            btn_update.height = dp(50)
            btn_update.bind(on_release=lambda x: check_for_updates(manual=True))
            layout.add_widget(btn_update)

        layout.add_widget(BoxLayout(size_hint=(1, 1))) # Отступ снизу
        self.add_widget(layout)

    def clear_history(self, instance):
        self.user_prefs.clear_history(); self.build_ui()
    def reset_all(self, instance):
        self.user_prefs.reset_data(); self.build_ui()
    def go_back(self, instance): self.manager.current = 'main_menu'


class TagScreen(Screen):
    pass


# ============================================================
#  ПРИЛОЖЕНИЕ
# ============================================================

class WarFactApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(MainMenuScreen(name='main_menu'))
        sm.add_widget(FactScreen(name='fact_screen'))
        sm.add_widget(HistoryScreen(name='history_screen'))
        sm.add_widget(NotesScreen(name='notes_screen'))
        sm.add_widget(StatsScreen(name='stats_screen'))
        sm.add_widget(SettingsScreen(name='settings_screen'))
        return sm


if __name__ == '__main__':
    WarFactApp().run()
