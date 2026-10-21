# main.py - Приложение "Герои Беларуси"

import random
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.floatlayout import FloatLayout
from kivy.core.window import Window
from kivy.animation import Animation
from kivy.utils import get_color_from_hex
from kivy.graphics import Color, Rectangle

from data import FACTS_DATABASE, get_facts_count, get_fact_by_id, get_all_tags, get_facts_by_tag
from user_data import UserPreferences

try:
    from version import __version__
except Exception:
    __version__ = "1.0.0"

# Цветовая палитра по макету
COLOR_BG = get_color_from_hex('#1a2b22')       # Темно-зеленый фон
COLOR_GOLD = get_color_from_hex('#c9a84c')     # Золотой
COLOR_RED = get_color_from_hex('#8b2525')      # Темно-красный
COLOR_TEXT = (0.9, 0.9, 0.9, 1)               # Светлый текст

def _fact_label(fact, length=60):
    title = fact.get("title")
    if title:
        return title
    text = fact.get("text", "")
    return text[:length] + "..." if len(text) > length else text

def make_header(title_text, back_callback, height=0.10):
    header = FloatLayout(size_hint=(1, height))
    title = Label(
        text=title_text, font_size='20sp', color=COLOR_GOLD, bold=True,
        size_hint=(1, 1), pos_hint={'x': 0, 'y': 0}, halign='center', valign='middle',
        text_size=(Window.width - 30, None)
    )
    header.add_widget(title)
    back_btn = Button(
        text="<--", size_hint=(0.15, 1), pos_hint={'x': 0, 'y': 0},
        background_color=(0.2, 0.2, 0.2, 0.8), color=COLOR_GOLD, font_size='16sp'
    )
    back_btn.bind(on_release=back_callback)
    header.add_widget(back_btn)
    return header

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
        with self.canvas.before:
            Color(*COLOR_BG)
            self.rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self.update_rect, size=self.update_rect)

        layout = BoxLayout(orientation='vertical', padding=15, spacing=10)

        # 1. Шапка
        header = BoxLayout(orientation='vertical', size_hint=(1, 0.15))
        header.add_widget(Label(text="НИКТО НЕ ЗАБЫТ", font_size='12sp', color=COLOR_GOLD, bold=True, size_hint=(1, 0.3)))
        header.add_widget(Label(text="ГЕРОИ БЕЛАРУСИ", font_size='26sp', color=COLOR_GOLD, bold=True, size_hint=(1, 0.4)))
        header.add_widget(Label(text="Партизаны, лётчики, подпольщики", font_size='12sp', color=COLOR_TEXT, size_hint=(1, 0.3)))
        layout.add_widget(header)

        # 2. Прогресс
        total_facts = get_facts_count()
        viewed = len(self.user_prefs.data["viewed_facts"])
        progress = self.user_prefs.get_total_progress(total_facts)
        streak = self.user_prefs.get_streak_days()

        progress_layout = BoxLayout(orientation='vertical', size_hint=(1, 0.08), spacing=3)
        progress_header = BoxLayout(size_hint=(1, 0.4))
        progress_header.add_widget(Label(text=f"Прогресс: {viewed}/{total_facts}", font_size='12sp', color=COLOR_TEXT, size_hint=(0.7, 1), halign='left'))
        progress_header.add_widget(Label(text=f"Серия: {streak} дн.", font_size='12sp', color=get_color_from_hex('#e67e22'), size_hint=(0.3, 1), halign='right'))
        progress_layout.add_widget(progress_header)

        progress_bar = Button(text=f"{progress}%", background_color=(0, 0, 0, 0), color=COLOR_TEXT, size_hint=(1, 0.6), font_size='10sp', disabled=True)
        progress_bar.canvas.before.clear()
        with progress_bar.canvas.before:
            Color(0.2, 0.2, 0.2, 1)
            Rectangle(pos=progress_bar.pos, size=progress_bar.size)
            if progress > 0:
                Color(0.9, 0.5, 0.1, 1)
                Rectangle(pos=progress_bar.pos, size=(progress_bar.width * progress / 100, progress_bar.height))
            Color(*COLOR_GOLD)
            Rectangle(pos=progress_bar.pos, size=progress_bar.size, outline=COLOR_GOLD)
        
        progress_bar.bind(pos=self.update_progress_bar, size=self.update_progress_bar)
        self.progress_bar = progress_bar
        self.progress_value = progress
        progress_layout.add_widget(progress_bar)
        layout.add_widget(progress_layout)

        # 3. Красный блок "Факт дня"
        fact_btn = Button(text="", background_normal='', background_color=(0,0,0,0), size_hint=(1, 0.35))
        with fact_btn.canvas.before:
            Color(*COLOR_RED)
            Rectangle(pos=fact_btn.pos, size=fact_btn.size)
            Color(*COLOR_GOLD)
            Rectangle(pos=fact_btn.pos, size=fact_btn.size, outline=COLOR_GOLD)

        fact_box = BoxLayout(orientation='vertical', spacing=5)
        fact_box.add_widget(Label(text="⭐", font_size='20sp', color=COLOR_GOLD, size_hint=(1, 0.15)))
        fact_box.add_widget(Label(text="ФАКТ ДНЯ", font_size='18sp', color=COLOR_GOLD, bold=True, size_hint=(1, 0.2)))
        
        img_layout = BoxLayout(size_hint=(1, 0.35))
        img_placeholder = Button(text="ФОТО", background_color=(0,0,0,0.3), color=COLOR_TEXT, size_hint=(0.3, 1))
        img_layout.add_widget(Label(size_hint=(0.35,1)))
        img_layout.add_widget(img_placeholder)
        img_layout.add_widget(Label(size_hint=(0.35,1)))
        fact_box.add_widget(img_layout)

        fact_box.add_widget(Label(text="Портрет героя\nи краткий подвиг", font_size='12sp', color=COLOR_TEXT, halign='center', size_hint=(1, 0.2)))
        
        fact_btn.add_widget(fact_box)
        fact_btn.bind(on_release=self.go_to_fact_of_day)
        layout.add_widget(fact_btn)

        # 4. Сетка 2х2
        grid = GridLayout(cols=2, spacing=10, size_hint=(1, 0.35))
        def make_menu_btn(text, icon, callback):
            btn = Button(text=f"{icon}\n{text}", background_normal='', background_color=(0.1, 0.15, 0.12, 1), color=COLOR_GOLD, font_size='14sp', bold=True, halign='center')
            with btn.canvas.before:
                Color(*COLOR_GOLD)
                Rectangle(pos=btn.pos, size=btn.size, outline=COLOR_GOLD)
            btn.bind(on_release=callback)
            return btn

        grid.add_widget(make_menu_btn("История", "📖", self.go_to_history))
        grid.add_widget(make_menu_btn("Заметки", "📝", self.go_to_notes))
        grid.add_widget(make_menu_btn("Статистика", "📊", self.go_to_stats))
        grid.add_widget(make_menu_btn("Настройки", "⚙️", self.go_to_settings))

        layout.add_widget(grid)
        self.add_widget(layout)

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size

    def update_progress_bar(self, instance, *args):
        instance.canvas.before.clear()
        with instance.canvas.before:
            Color(0.2, 0.2, 0.2, 1)
            Rectangle(pos=instance.pos, size=instance.size)
            if self.progress_value > 0:
                Color(0.9, 0.5, 0.1, 1)
                width = (self.progress_value / 100) * instance.width
                Rectangle(pos=instance.pos, size=(width, instance.height))
            Color(*COLOR_GOLD)
            Rectangle(pos=instance.pos, size=instance.size, outline=COLOR_GOLD)

    def go_to_fact_of_day(self, instance):
        viewed_facts = set(self.user_prefs.data["viewed_facts"])
        unviewed_facts = [f for f in FACTS_DATABASE if f["id"] not in viewed_facts]
        if unviewed_facts:
            scored_facts = [(f, self.user_prefs.get_recommendation_score(f)) for f in unviewed_facts]
            scored_facts.sort(key=lambda x: x[1], reverse=True)
            best_fact = scored_facts[0][0]
        else:
            liked = self.user_prefs.data["liked_facts"]
            if liked: best_fact = get_fact_by_id(random.choice(liked))
            else: best_fact = random.choice(FACTS_DATABASE)
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
        with self.canvas.before:
            Color(*COLOR_BG)
            self.rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self.update_rect, size=self.update_rect)

        layout = BoxLayout(orientation='vertical', padding=15, spacing=10)

        top_panel = BoxLayout(size_hint=(1, 0.08), spacing=8)
        back_btn = Button(text="<--", size_hint=(0.15, 1), background_color=(0.2, 0.2, 0.2, 0.8), color=COLOR_GOLD)
        back_btn.bind(on_release=self.go_back)
        top_panel.add_widget(back_btn)

        self.ext_btn = Button(text="[i] Подробнее", size_hint=(0.85, 1), background_color=(0.1, 0.15, 0.12, 1), color=COLOR_GOLD)
        self.ext_btn.bind(on_release=self.toggle_extended)
        top_panel.add_widget(self.ext_btn)
        layout.add_widget(top_panel)

        self.image_placeholder = Button(text="ФОТО", size_hint=(1, 0.25), background_color=(0.1, 0.15, 0.12, 1), color=COLOR_GOLD)
        layout.add_widget(self.image_placeholder)

        self.text_scroll = ScrollView(size_hint=(1, 0.3))
        self.fact_text = Label(text="", font_size='18sp', color=COLOR_TEXT, halign='left', valign='top', size_hint=(1, None), text_size=(Window.width - 30, None))
        self.fact_text.bind(texture_size=self.fact_text.setter('size'))
        self.text_scroll.add_widget(self.fact_text)
        layout.add_widget(self.text_scroll)

        self.ext_scroll = ScrollView(size_hint=(1, 0.25))
        self.ext_text = Label(text="", font_size='14sp', color=(0.8, 0.8, 0.8, 1), halign='left', valign='top', size_hint=(1, None), text_size=(Window.width - 30, None))
        self.ext_text.bind(texture_size=self.ext_text.setter('size'))
        self.ext_scroll.add_widget(self.ext_text)
        self.ext_scroll.opacity = 0
        self.ext_scroll.disabled = True
        layout.add_widget(self.ext_scroll)

        self.tags_label = Label(text="", font_size='12sp', color=COLOR_GOLD, size_hint=(1, 0.05), halign='center')
        layout.add_widget(self.tags_label)

        action_row = BoxLayout(size_hint=(1, 0.1), spacing=8)
        def make_action_btn(text, callback):
            btn = Button(text=text, font_size='20sp', background_color=(0.1, 0.15, 0.12, 1), color=COLOR_GOLD)
            btn.bind(on_release=callback)
            return btn

        self.like_btn = make_action_btn("[+]", self.toggle_like)
        self.dislike_btn = make_action_btn("[-]", self.toggle_dislike)
        self.note_btn = make_action_btn("[N]", self.open_note_popup)
        next_btn = make_action_btn("[>]", self.next_fact)

        action_row.add_widget(self.like_btn)
        action_row.add_widget(self.dislike_btn)
        action_row.add_widget(self.note_btn)
        action_row.add_widget(next_btn)
        layout.add_widget(action_row)

        self.status_label = Label(text="", font_size='11sp', color=(0.5, 0.5, 0.5, 1), size_hint=(1, 0.04))
        layout.add_widget(self.status_label)
        self.add_widget(layout)

    def update_rect(self, *args):
        self.rect.pos = self.pos
        self.rect.size = self.size

    def on_size(self, *args):
        if hasattr(self, 'fact_text'): self.fact_text.text_size = (self.width - 30, None)
        if hasattr(self, 'ext_text'): self.ext_text.text_size = (self.width - 30, None)

    def show_fact(self, fact):
        self.current_fact = fact
        self.showing_extended = False
        self.ext_scroll.opacity = 0
        self.ext_scroll.disabled = True
        self.ext_btn.text = "[i] Подробнее"
        self.image_placeholder.text = f"ПОРТРЕТ\n{fact.get('title', '')}"
        self.fact_text.text = fact["text"]
        self.fact_text.text_size = (self.width - 30, None)
        if "extended" in fact and fact["extended"]:
            self.ext_text.text = fact["extended"]
            self.ext_text.text_size = (self.width - 30, None)
            self.has_extended = True
        else:
            self.ext_text.text = "Нет дополнительной информации"
            self.has_extended = False
        tags_info = []
        for tag in fact["tags"]:
            score = self.user_prefs.get_tag_score(tag)
            if score > 0: tags_info.append(f"#{tag} +{score}")
            elif score < 0: tags_info.append(f"#{tag} {score}")
            else: tags_info.append(f"#{tag}")
        self.tags_label.text = "  ".join(tags_info)
        status = self.user_prefs.get_fact_status(fact["id"])
        self.update_buttons(status)
        if self.user_prefs.has_note(fact["id"]):
            self.note_btn.text = "[N*]"
            self.note_btn.color = (0.2, 0.8, 0.2, 1)
        else:
            self.note_btn.text = "[N]"
            self.note_btn.color = COLOR_GOLD
        if fact["id"] not in self.user_prefs.data["viewed_facts"]: self.user_prefs.add_view(fact["id"], fact["tags"])
        stats = self.user_prefs.get_user_stats()
        self.status_label.text = f"Просмотрено: {stats['unique_facts_viewed']} | [+]: {stats['liked_count']} | Заметок: {len(self.user_prefs.get_all_notes())}"

    def toggle_extended(self, instance):
        if not self.has_extended:
            self.status_label.text = "Нет доп. информации"
            return
        self.showing_extended = not self.showing_extended
        if self.showing_extended:
            self.ext_scroll.opacity = 1
            self.ext_scroll.disabled = False
            self.ext_btn.text = "[i] Скрыть"
            anim = Animation(opacity=1, duration=0.3)
            anim.start(self.ext_scroll)
        else:
            anim = Animation(opacity=0, duration=0.3)
            anim.bind(on_complete=lambda *args: setattr(self.ext_scroll, 'disabled', True))
            anim.start(self.ext_scroll)
            self.ext_btn.text = "[i] Подробнее"

    def open_note_popup(self, instance):
        if not self.current_fact: return
        fact_id = self.current_fact["id"]
        existing_note = self.user_prefs.get_note(fact_id)
        content = BoxLayout(orientation='vertical', padding=10, spacing=8)
        content.add_widget(Label(text="ЗАМЕТКА", font_size='18sp', color=COLOR_GOLD, bold=True))
        text_input = TextInput(text=existing_note, hint_text="Введите текст...", multiline=True, background_color=(0.1, 0.15, 0.12, 1), foreground_color=COLOR_TEXT)
        content.add_widget(text_input)
        btn_row = BoxLayout(size_hint=(1, 0.2), spacing=8)
        cancel_btn = Button(text="Отмена", background_color=(0.3, 0.3, 0.3, 0.8), color=COLOR_TEXT)
        save_btn = Button(text="Сохранить", background_color=COLOR_RED, color=COLOR_GOLD)
        btn_row.add_widget(cancel_btn)
        btn_row.add_widget(save_btn)
        content.add_widget(btn_row)
        popup = Popup(title="", content=content, size_hint=(0.9, 0.6), background_color=(0,0,0,0.9))
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
        with self.canvas.before:
            Color(*COLOR_BG)
            self.rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self.update_rect, size=self.update_rect)
        layout = BoxLayout(orientation='vertical', padding=10, spacing=6)
        layout.add_widget(make_header("История", self.go_back, 0.1))
        scroll = ScrollView(size_hint=(1, 0.9))
        content = BoxLayout(orientation='vertical', size_hint_y=None, spacing=10)
        content.bind(minimum_height=content.setter('height'))
        liked = self.user_prefs.data["liked_facts"]
        viewed = self.user_prefs.data["viewed_facts"]
        not_liked = [fid for fid in viewed if fid not in liked]
        content.add_widget(Label(text=f"★ ПОНРАВИВШИЕСЯ ({len(liked)})", font_size='15sp', color=COLOR_GOLD, size_hint=(1, None), height=40))
        for fact_id in reversed(liked):
            fact = get_fact_by_id(fact_id)
            if fact:
                btn = Button(text=f"[★] {_fact_label(fact, 40)}", size_hint=(1, None), height=50, background_color=COLOR_RED, color=COLOR_GOLD)
                btn.bind(on_release=lambda x, f=fact: self.view_fact(f))
                content.add_widget(btn)
        content.add_widget(Label(text="", size_hint=(1, None), height=10))
        content.add_widget(Label(text=f"▸ ИЗУЧЕННЫЕ ({len(not_liked)})", font_size='15sp', color=COLOR_TEXT, size_hint=(1, None), height=40))
        for fact_id in reversed(not_liked):
            fact = get_fact_by_id(fact_id)
            if fact:
                btn = Button(text=f"[i] {_fact_label(fact, 40)}", size_hint=(1, None), height=50, background_color=(0.1, 0.15, 0.12, 1), color=COLOR_TEXT)
                btn.bind(on_release=lambda x, f=fact: self.view_fact(f))
                content.add_widget(btn)
        scroll.add_widget(content)
        layout.add_widget(scroll)
        self.add_widget(layout)

    def update_rect(self, *args):
        self.rect.pos = self.pos; self.rect.size = self.size
    def view_fact(self, fact):
        self.manager.current = 'fact_screen'
        self.manager.get_screen('fact_screen').show_fact(fact)
    def go_back(self, instance):
        self.manager.current = 'main_menu'


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
        with self.canvas.before:
            Color(*COLOR_BG)
            self.rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self.update_rect, size=self.update_rect)
        layout = BoxLayout(orientation='vertical', padding=10, spacing=6)
        layout.add_widget(make_header("Мои заметки", self.go_back, 0.1))
        scroll = ScrollView(size_hint=(1, 0.9))
        notes_box = BoxLayout(orientation='vertical', size_hint_y=None, spacing=8)
        notes_box.bind(minimum_height=notes_box.setter('height'))
        all_notes = self.user_prefs.get_all_notes()
        if all_notes:
            for fact_id_str, text in all_notes.items():
                fact = get_fact_by_id(int(fact_id_str))
                if fact:
                    btn = Button(text=f"[N] {_fact_label(fact, 30)}\n\n{text[:80]}...", size_hint=(1, None), height=90, background_color=(0.1, 0.15, 0.12, 1), color=COLOR_TEXT)
                    btn.bind(on_release=lambda x, f=fact: self.view_fact(f))
                    notes_box.add_widget(btn)
        else:
            notes_box.add_widget(Label(text="Нет заметок", color=COLOR_TEXT))
        scroll.add_widget(notes_box)
        layout.add_widget(scroll)
        self.add_widget(layout)

    def update_rect(self, *args):
        self.rect.pos = self.pos; self.rect.size = self.size
    def view_fact(self, fact):
        self.manager.current = 'fact_screen'
        self.manager.get_screen('fact_screen').show_fact(fact)
    def go_back(self, instance):
        self.manager.current = 'main_menu'


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
        with self.canvas.before:
            Color(*COLOR_BG)
            self.rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self.update_rect, size=self.update_rect)
        layout = BoxLayout(orientation='vertical', padding=10, spacing=6)
        layout.add_widget(make_header("Статистика", self.go_back, 0.09))
        scroll = ScrollView(size_hint=(1, 0.91))
        content = BoxLayout(orientation='vertical', size_hint_y=None, spacing=10)
        content.bind(minimum_height=content.setter('height'))
        stats = self.user_prefs.get_user_stats()
        total_facts = get_facts_count()
        progress = self.user_prefs.get_total_progress(total_facts)
        content.add_widget(Label(text="[ ОБЩИЙ ПРОГРЕСС ]", font_size='16sp', color=COLOR_GOLD, size_hint=(1, None), height=40))
        content.add_widget(Label(text=f"Изучено: {stats['unique_facts_viewed']} / {total_facts}", font_size='14sp', color=COLOR_TEXT, size_hint=(1, None), height=30))
        content.add_widget(Label(text=f"Прогресс: {progress}%", font_size='14sp', color=COLOR_TEXT, size_hint=(1, None), height=30))
        content.add_widget(Label(text="[ ДОСТИЖЕНИЯ ]", font_size='16sp', color=COLOR_GOLD, size_hint=(1, None), height=40))
        for ach in self.user_prefs.get_achievement_progress():
            content.add_widget(Label(text=f"[+] {ach['name']}", font_size='14sp', color=COLOR_TEXT, size_hint=(1, None), height=30))
        scroll.add_widget(content)
        layout.add_widget(scroll)
        self.add_widget(layout)

    def update_rect(self, *args):
        self.rect.pos = self.pos; self.rect.size = self.size
    def go_back(self, instance):
        self.manager.current = 'main_menu'


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
        with self.canvas.before:
            Color(*COLOR_BG)
            self.rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self.update_rect, size=self.update_rect)
        layout = BoxLayout(orientation='vertical', padding=15, spacing=15)
        layout.add_widget(make_header("Настройки", self.go_back, 0.1))
        layout.add_widget(Label(text=f"Версия: {__version__}", font_size='14sp', color=COLOR_TEXT))
        btn_clear = Button(text="ОЧИСТИТЬ ИСТОРИЮ", background_color=COLOR_RED, color=COLOR_GOLD, size_hint=(1, None), height=50)
        btn_clear.bind(on_release=self.clear_history)
        layout.add_widget(btn_clear)
        btn_reset = Button(text="СБРОСИТЬ ВСЁ", background_color=(0.5, 0.1, 0.1, 1), color=COLOR_GOLD, size_hint=(1, None), height=50)
        btn_reset.bind(on_release=self.reset_all)
        layout.add_widget(btn_reset)
        self.add_widget(layout)

    def update_rect(self, *args):
        self.rect.pos = self.pos; self.rect.size = self.size
    def clear_history(self, instance):
        self.user_prefs.clear_history()
        self.build_ui()
    def reset_all(self, instance):
        self.user_prefs.reset_data()
        self.build_ui()
    def go_back(self, instance):
        self.manager.current = 'main_menu'


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
