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
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.image import Image
from kivy.uix.layout import Layout
from kivy.core.window import Window
from kivy.graphics import Color, RoundedRectangle, BorderImage, Line
from kivy.utils import get_color_from_hex
from kivy.metrics import dp
from kivy.clock import Clock
from kivy.properties import NumericProperty, ReferenceListProperty

from data import FACTS_DATABASE, get_facts_count, get_fact_by_id
from user_data import UserPreferences

try:
    from version import __version__
except Exception:
    __version__ = "1.0.0"

COLOR_BG = get_color_from_hex('#1e2a1f')
COLOR_GOLD = get_color_from_hex('#D4AF37')
COLOR_CREAM = get_color_from_hex('#F5E6C8')
COLOR_RED = get_color_from_hex('#8B2525')


def _up():
    try:
        app = App.get_running_app()
        if app is not None and hasattr(app, 'user_prefs') and app.user_prefs is not None:
            return app.user_prefs
    except Exception:
        pass
    return UserPreferences()


def pick_recommended_fact(user_prefs):
    viewed_facts = set(user_prefs.data["viewed_facts"])
    unviewed = [f for f in FACTS_DATABASE if f["id"] not in viewed_facts]
    if not unviewed:
        liked = user_prefs.data["liked_facts"]
        return get_fact_by_id(random.choice(liked)) if liked else random.choice(FACTS_DATABASE)

    scored = [(f, user_prefs.get_recommendation_score(f)) for f in unviewed]
    scored.sort(key=lambda x: x[1], reverse=True)
    top5 = scored[:5]
    return top5[0][0] if random.random() < 0.8 else random.choice(top5)[0]


class WrapLayout(Layout):
    spacing = NumericProperty(dp(10))
    padding = ReferenceListProperty(NumericProperty(dp(0)), NumericProperty(dp(0)), NumericProperty(dp(0)),
                                    NumericProperty(dp(0)))

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(width=self.update_layout, children=self.update_layout, spacing=self.update_layout,
                  padding=self.update_layout)
        Clock.schedule_once(self.update_layout, 0)

    def update_layout(self, *args):
        self.do_layout()

    def do_layout(self, *largs):
        children = self.children[::-1]
        if not children: return

        padding_left, padding_top, padding_right, padding_bottom = self.padding

        total_width = self.width - padding_left - padding_right
        row_width = 0
        row_height = 0
        total_height = padding_top + padding_bottom

        # 1. Сначала вычисляем итоговую высоту
        for child in children:
            if child.width == 0 and child.height == 0: continue

            if row_width + child.width > total_width and row_width > 0:
                total_height += row_height + self.spacing
                row_width = 0
                row_height = 0

            row_width += child.width + self.spacing
            row_height = max(row_height, child.height)

        total_height += row_height

        # 2. Устанавливаем высоту контейнера
        if self.height != total_height:
            self.height = total_height

        # 3. Теперь расставляем элементы сверху вниз
        current_top = self.height - padding_top
        row_height = 0
        x = padding_left

        for child in children:
            if child.width == 0 and child.height == 0: continue

            if x + child.width + padding_right > self.width and x > padding_left:
                x = padding_left
                current_top -= row_height + self.spacing
                row_height = 0

            child.x = x
            child.top = current_top
            x += child.width + self.spacing
            row_height = max(row_height, child.height)


class Panel(BoxLayout):
    def __init__(self, source='panel_card_9slice.png', **kwargs):
        super().__init__(**kwargs)
        self.tex = Image(source=source).texture
        with self.canvas.before:
            Color(1, 1, 1, 1)
            self.bg = BorderImage(texture=self.tex, border=(dp(20), dp(20), dp(20), dp(20)))
        self.bind(pos=self.update_bg, size=self.update_bg)

    def update_bg(self, instance, value):
        self.bg.pos = instance.pos
        self.bg.size = instance.size


class MenuButton(Button):
    def __init__(self, text, icon_source, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = 'btn_wide_plain.png'
        self.background_down = 'panel_card_light_9slice.png'
        self.border = (dp(20), dp(20), dp(20), dp(20))
        self.text = "      " + text
        self.halign = 'left'
        self.valign = 'middle'
        self.color = COLOR_GOLD
        self.font_size = '18sp'

        self.icon = Image(source=icon_source, size_hint=(None, None), size=(dp(30), dp(30)))
        self.add_widget(self.icon)
        self.bind(pos=self.update_icon, size=self.update_icon)

    def update_icon(self, instance, value):
        self.icon.center_y = self.center_y
        self.icon.x = self.x + dp(15)


class TagLabel(Button):
    def __init__(self, text, **kwargs):
        super().__init__(**kwargs)
        self.background_normal = 'chip_tag_9slice.png'
        self.border = (dp(15), dp(15), dp(15), dp(15))
        self.text = text
        self.color = COLOR_GOLD
        self.font_size = '12sp'
        self.size_hint = (None, None)
        self.texture_update()
        self.width = self.texture_size[0] + dp(30)
        self.height = dp(35)


class QuizButton(ButtonBehavior, BoxLayout):
    def __init__(self, text, **kwargs):
        super().__init__(**kwargs)
        self.padding = dp(10)
        self.size_hint_y = None
        self.height = dp(55)

        with self.canvas.before:
            self.bg_color = Color(0.12, 0.16, 0.13, 1)
            self.rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(10)])
            self.line_color = Color(*COLOR_GOLD)
            self.line = Line(rounded_rectangle=(self.x, self.y, self.width, self.height, dp(10)), width=2)

        self.bind(pos=self.update_rect, size=self.update_rect)

        self.label = Label(text=text, font_size='16sp', color=COLOR_GOLD, bold=True, halign='center',
                           valign='middle')
        self.label.bind(size=lambda i, v: setattr(i, 'text_size', v))
        self.add_widget(self.label)

    def update_rect(self, instance, value):
        self.rect.pos = instance.pos
        self.rect.size = instance.size
        self.line.rounded_rectangle = (instance.x, instance.y, instance.width, instance.height, dp(10))

    def set_state(self, state):
        if state == 'correct':
            self.bg_color.rgba = (0.2, 0.6, 0.2, 1)
            self.label.color = (1, 1, 1, 1)
            self.line_color.rgba = (1, 1, 1, 1)
        elif state == 'wrong':
            self.bg_color.rgba = (0.6, 0.2, 0.2, 1)
            self.label.color = (1, 1, 1, 1)
            self.line_color.rgba = (1, 1, 1, 1)
        elif state == 'disabled':
            self.bg_color.rgba = (0.12, 0.16, 0.13, 0.5)
            self.label.color = (0.5, 0.5, 0.5, 1)
            self.line_color.rgba = (0.5, 0.5, 0.5, 1)
        else:
            self.bg_color.rgba = (0.12, 0.16, 0.13, 1)
            self.label.color = COLOR_GOLD
            self.line_color.rgba = COLOR_GOLD


class FactDayCard(ButtonBehavior, Panel):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = [dp(10), dp(10), dp(10), dp(5)]
        self.spacing = dp(5)
        self.size_hint = (1, None)
        self.height = dp(130)

        self.add_widget(
            Image(source='star_red_green_gold.png', size_hint=(1, 0.6), allow_stretch=True, keep_ratio=True))
        self.add_widget(Label(text="ФАКТ ДНЯ", font_size='22sp', color=COLOR_GOLD, bold=True, size_hint=(1, 0.4)))


class MainMenuScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.user_prefs = _up()
        self.build_ui()

    def on_enter(self, *args):
        self.clear_widgets()
        self.build_ui()

    def build_ui(self):
        main_layout = FloatLayout()
        main_layout.add_widget(
            Image(source='bg_fact_1080x2400.png', allow_stretch=True, keep_ratio=False, size_hint=(1, 1)))

        layout = BoxLayout(orientation='vertical', padding=[dp(15), dp(45), dp(15), dp(15)], spacing=dp(10),
                           size_hint=(1, 1))
        main_layout.add_widget(layout)

        header = BoxLayout(orientation='vertical', size_hint=(1, None), height=dp(85))
        header.add_widget(Label(text="НИКТО НЕ ЗАБЫТ", font_size='12sp', color=COLOR_GOLD, bold=True))
        header.add_widget(Label(text="ГЕРОИ БЕЛАРУСИ", font_size='28sp', color=COLOR_GOLD, bold=True))
        header.add_widget(Label(text="Партизаны, лётчики, подпольщики", font_size='14sp', color=COLOR_CREAM))
        layout.add_widget(header)

        total_facts = get_facts_count()
        viewed = len(self.user_prefs.data["viewed_facts"])
        progress = self.user_prefs.get_total_progress(total_facts)
        streak = self.user_prefs.get_streak_days()

        prog_box = BoxLayout(orientation='vertical', size_hint=(1, None), height=dp(45), spacing=dp(5))
        prog_labels = BoxLayout(size_hint=(1, None), height=dp(20))
        prog_labels.add_widget(
            Label(text=f"Прогресс: {viewed}/{total_facts}", font_size='14sp', color=COLOR_CREAM, halign='left'))
        prog_labels.add_widget(
            Label(text=f"Серия: {streak} дн.", font_size='14sp', color=COLOR_GOLD, halign='right'))
        prog_box.add_widget(prog_labels)

        pbar = FloatLayout(size_hint=(1, None), height=dp(15))
        with pbar.canvas:
            Color(0.1, 0.1, 0.1, 1)
            bg_rect = RoundedRectangle(pos=pbar.pos, size=pbar.size, radius=[dp(7)])
            Color(*COLOR_GOLD)
            fill_rect = RoundedRectangle(pos=pbar.pos, size=(pbar.width * (progress / 100), pbar.height),
                                         radius=[dp(7)])

        def update_pbar(instance, value):
            bg_rect.pos = instance.pos
            bg_rect.size = instance.size
            fill_rect.pos = instance.pos
            fill_rect.size = (instance.width * (progress / 100), instance.height)

        pbar.bind(pos=update_pbar, size=update_pbar)
        prog_box.add_widget(pbar)
        layout.add_widget(prog_box)

        layout.add_widget(BoxLayout(size_hint=(1, 1)))

        self.fact_card = FactDayCard()
        self.fact_card.height = dp(110)
        self.fact_card.bind(on_release=self.go_to_fact_of_day)
        layout.add_widget(self.fact_card)

        btn_quiz = MenuButton("Викторина", "icon_check.png")
        btn_quiz.size_hint = (1, None)
        btn_quiz.height = dp(60)
        btn_quiz.bind(on_release=self.go_to_quiz)
        layout.add_widget(btn_quiz)

        grid = GridLayout(cols=2, spacing=dp(10), size_hint=(1, None), height=dp(150))

        btn_history = MenuButton("История", "icon_book.png")
        btn_history.bind(on_release=self.go_to_history)
        grid.add_widget(btn_history)

        btn_notes = MenuButton("Заметки", "icon_notes.png")
        btn_notes.bind(on_release=self.go_to_notes)
        grid.add_widget(btn_notes)

        btn_stats = MenuButton("Статистика", "icon_chart_bar.png")
        btn_stats.bind(on_release=self.go_to_stats)
        grid.add_widget(btn_stats)

        btn_settings = MenuButton("Настройки", "icon_settings.png")
        btn_settings.bind(on_release=self.go_to_settings)
        grid.add_widget(btn_settings)

        layout.add_widget(grid)
        layout.add_widget(BoxLayout(size_hint=(1, None), height=dp(110)))

        self.add_widget(main_layout)

    def go_to_fact_of_day(self, instance):
        best_fact = pick_recommended_fact(self.user_prefs)
        self.manager.current = 'fact_screen'
        self.manager.get_screen('fact_screen').show_fact(best_fact)

    def go_to_history(self, instance): self.manager.current = 'history_screen'

    def go_to_notes(self, instance): self.manager.current = 'notes_screen'

    def go_to_stats(self, instance): self.manager.current = 'stats_screen'

    def go_to_settings(self, instance): self.manager.current = 'settings_screen'

    def go_to_quiz(self, instance): self.manager.current = 'quiz_screen'


class FactScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_fact = None
        self.showing_extended = False
        self.user_prefs = _up()
        self.build_ui()

    def build_ui(self):
        main_layout = FloatLayout(size_hint=(1, 1))
        main_layout.add_widget(
            Image(source='bg_fact_1080x2400.png', allow_stretch=True, keep_ratio=False, size_hint=(1, 1)))

        layout = BoxLayout(orientation='vertical', padding=[dp(15), dp(40), dp(15), dp(55)], spacing=dp(10),
                           size_hint=(1, 1))
        main_layout.add_widget(layout)

        top_panel = BoxLayout(size_hint=(1, None), height=dp(60), spacing=dp(10))
        back_btn = Button(background_normal='btn_back.png', background_down='btn_back_down.png', size_hint=(None, 1),
                          width=dp(60))
        back_btn.bind(on_release=self.go_back)
        top_panel.add_widget(back_btn)

        self.ext_btn = Button(background_normal='btn_details.png', background_down='btn_details_down.png',
                              size_hint=(1, 1))
        self.ext_btn.bind(on_release=self.toggle_extended)
        top_panel.add_widget(self.ext_btn)
        layout.add_widget(top_panel)

        self.scroll = ScrollView(size_hint=(1, 1), bar_width=dp(0), do_scroll_x=False)
        content_box = BoxLayout(orientation='vertical', size_hint=(1, None), spacing=dp(15))
        content_box.bind(minimum_height=content_box.setter('height'))

        photo_layout = RelativeLayout(size_hint=(1, None), height=dp(230))
        photo_layout.add_widget(
            Image(source='photo_frame_960x680.png', size_hint=(1, 1), allow_stretch=True, keep_ratio=False))
        photo_layout.add_widget(Image(source='photo_placeholder_904x512.png', size_hint=(0.9, 0.65),
                                      pos_hint={'center_x': 0.5, 'top': 0.87}, allow_stretch=True, keep_ratio=True))

        self.photo_title = Label(
            text="", font_size='15sp', color=COLOR_CREAM, bold=True,
            size_hint=(0.8, None), height=dp(35),
            pos_hint={'center_x': 0.5, 'y': 0.04},
            halign='center', valign='middle'
        )
        self.photo_title.bind(size=lambda instance, value: setattr(instance, 'text_size', value))
        photo_layout.add_widget(self.photo_title)
        content_box.add_widget(photo_layout)

        self.text_panel = Panel(size_hint=(1, None))
        self.text_panel.bind(minimum_height=self.text_panel.setter('height'))

        text_layout = BoxLayout(orientation='vertical', padding=dp(20), size_hint=(1, None))
        text_layout.bind(minimum_height=text_layout.setter('height'))

        self.fact_text = Label(text="", font_size='16sp', color=COLOR_CREAM, halign='left', valign='top',
                               size_hint_y=None)
        self.fact_text.bind(width=lambda instance, value: setattr(instance, 'text_size', (value, None)))
        self.fact_text.bind(texture_size=lambda instance, value: setattr(instance, 'height', value[1]))
        text_layout.add_widget(self.fact_text)

        # --- ГЛАВНОЕ ИЗМЕНЕНИЕ ЗДЕСЬ ---
        # Изначально высота доп. текста = 0, чтобы рамка была маленькой
        self.ext_text = Label(text="", font_size='15sp', color=COLOR_GOLD, halign='left', valign='top',
                              size_hint_y=None, height=0)
        self.ext_text.bind(width=self.on_ext_text_width)
        text_layout.add_widget(self.ext_text)
        # --------------------------------

        self.text_panel.add_widget(text_layout)
        content_box.add_widget(self.text_panel)

        self.tags_box = WrapLayout(size_hint=(1, None), height=dp(40), spacing=dp(10))
        content_box.add_widget(self.tags_box)

        content_box.add_widget(BoxLayout(size_hint=(1, None), height=dp(10)))
        self.scroll.add_widget(content_box)
        layout.add_widget(self.scroll)

        layout.add_widget(
            Image(source='divider_star.png', size_hint=(1, None), height=dp(30), allow_stretch=True, keep_ratio=False))

        action_row = BoxLayout(size_hint=(1, None), height=dp(80), spacing=dp(10))
        self.like_btn = Button(background_normal='btn_like.png', background_down='btn_like_down.png')
        self.like_btn.bind(on_release=self.toggle_like)

        self.dislike_btn = Button(background_normal='btn_dislike.png', background_down='btn_dislike_down.png')
        self.dislike_btn.bind(on_release=self.toggle_dislike)

        self.note_btn = Button(background_normal='btn_note.png', background_down='btn_note_down.png')
        self.note_btn.bind(on_release=self.open_note_popup)

        next_btn = Button(background_normal='btn_next.png', background_down='btn_next_down.png')
        next_btn.bind(on_release=self.next_fact)

        action_row.add_widget(self.like_btn)
        action_row.add_widget(self.dislike_btn)
        action_row.add_widget(self.note_btn)
        action_row.add_widget(next_btn)
        layout.add_widget(action_row)

        self.add_widget(main_layout)

    # Вспомогательный метод для пересчета высоты при изменении ширины экрана
    def on_ext_text_width(self, instance, value):
        instance.text_size = (value, None)
        if self.showing_extended:
            instance.texture_update()
            instance.height = instance.texture_size[1]
        else:
            instance.height = 0

    def show_fact(self, fact):
        self.current_fact = fact
        self.showing_extended = False
        self.ext_text.opacity = 0
        self.ext_text.height = 0  # Прячем текст и обнуляем высоту
        self.ext_btn.background_normal = 'btn_details.png'
        self.ext_btn.background_down = 'btn_details_down.png'
        self.scroll.scroll_y = 1

        self.photo_title.text = fact.get('title', '')
        self.fact_text.text = fact["text"]

        if "extended" in fact and fact["extended"]:
            self.ext_text.text = fact["extended"]
            self.has_extended = True
        else:
            self.ext_text.text = "Нет дополнительной информации"
            self.has_extended = False

        self.tags_box.clear_widgets()
        for tag in fact["tags"]:
            self.tags_box.add_widget(TagLabel(f"#{tag}"))
        self.tags_box.do_layout()

        status = self.user_prefs.get_fact_status(fact["id"])
        self.like_btn.opacity = 1.0 if status == "liked" else 0.6
        self.dislike_btn.opacity = 1.0 if status == "disliked" else 0.6
        self.note_btn.opacity = 1.0 if self.user_prefs.has_note(fact["id"]) else 0.6

        if fact["id"] not in self.user_prefs.data["viewed_facts"]:
            self.user_prefs.add_view(fact["id"], fact["tags"])

    def toggle_extended(self, instance):
        if not self.has_extended: return
        self.showing_extended = not self.showing_extended
        if self.showing_extended:
            # Показываем текст и вычисляем его реальную высоту
            self.ext_text.opacity = 1
            self.ext_text.text_size = (self.ext_text.width, None)
            self.ext_text.texture_update()
            self.ext_text.height = self.ext_text.texture_size[1]
            self.ext_btn.background_normal = 'btn_details_hide.png'
            self.ext_btn.background_down = 'btn_details_hide_down.png'
        else:
            # Скрываем текст и обнуляем высоту, чтобы рамка сжалась
            self.ext_text.opacity = 0
            self.ext_text.height = 0
            self.ext_btn.background_normal = 'btn_details.png'
            self.ext_btn.background_down = 'btn_details_down.png'

    def open_note_popup(self, instance):
        if not self.current_fact: return
        fact_id = self.current_fact["id"]
        existing_note = self.user_prefs.get_note(fact_id)

        content = BoxLayout(orientation='vertical', padding=dp(15), spacing=dp(10))
        content.add_widget(Label(text="ЗАМЕТКА", font_size='20sp', color=COLOR_GOLD, bold=True))
        text_input = TextInput(text=existing_note, hint_text="Введите текст...", multiline=True,
                               background_color=COLOR_BG, foreground_color=COLOR_CREAM)
        content.add_widget(text_input)

        btn_row = BoxLayout(size_hint=(1, None), height=dp(50), spacing=dp(10))
        cancel_btn = Button(text="Отмена", background_normal='', background_color=COLOR_RED, color=COLOR_CREAM)
        save_btn = Button(text="Сохранить", background_normal='', background_color=COLOR_GOLD, color=COLOR_BG)

        btn_row.add_widget(cancel_btn)
        btn_row.add_widget(save_btn)
        content.add_widget(btn_row)

        popup = Popup(title="", content=content, size_hint=(0.9, 0.6), background_color=(0, 0, 0, 0.8))

        def save_note(instance):
            self.user_prefs.add_note(fact_id, text_input.text)
            popup.dismiss()
            self.show_fact(self.current_fact)

        save_btn.bind(on_release=save_note)
        cancel_btn.bind(on_release=popup.dismiss)
        popup.open()

    def toggle_like(self, instance):
        if not self.current_fact: return
        fact_id = self.current_fact["id"]
        tags = self.current_fact["tags"]
        status = self.user_prefs.get_fact_status(fact_id)
        if status == "liked":
            self.user_prefs.remove_like(fact_id, tags)
        else:
            if status == "disliked": self.user_prefs.remove_dislike(fact_id, tags)
            self.user_prefs.add_like(fact_id, tags)
        self.show_fact(self.current_fact)

    def toggle_dislike(self, instance):
        if not self.current_fact: return
        fact_id = self.current_fact["id"]
        tags = self.current_fact["tags"]
        status = self.user_prefs.get_fact_status(fact_id)
        if status == "disliked":
            self.user_prefs.remove_dislike(fact_id, tags)
        else:
            if status == "liked": self.user_prefs.remove_like(fact_id, tags)
            self.user_prefs.add_dislike(fact_id, tags)
        self.show_fact(self.current_fact)

    def next_fact(self, instance):
        self.show_fact(pick_recommended_fact(self.user_prefs))

    def go_back(self, instance):
        self.manager.current = 'main_menu'


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
        main_layout = FloatLayout(size_hint=(1, 1))
        main_layout.add_widget(
            Image(source='bg_fact_1080x2400.png', allow_stretch=True, keep_ratio=False, size_hint=(1, 1)))

        layout = BoxLayout(orientation='vertical', padding=[dp(15), dp(40), dp(15), dp(50)], spacing=dp(10),
                           size_hint=(1, 1))
        main_layout.add_widget(layout)

        top_panel = BoxLayout(size_hint=(1, None), height=dp(60))
        back_btn = Button(background_normal='btn_back.png', background_down='btn_back_down.png',
                          size_hint=(None, 1), width=dp(60))
        back_btn.bind(on_release=self.go_back)
        top_panel.add_widget(back_btn)
        top_panel.add_widget(Label(text="ПРОВЕРКА ЗНАНИЙ", font_size='20sp', color=COLOR_GOLD, bold=True))
        top_panel.add_widget(BoxLayout(size_hint=(None, 1), width=dp(60)))
        layout.add_widget(top_panel)

        q_stats = self.user_prefs.get_quiz_stats()
        self.score_label = Label(
            text=f"Счёт: {q_stats['score']}  |  Правильно: {q_stats['correct']} из {q_stats['attempts']}",
            font_size='18sp', color=COLOR_CREAM, bold=True, size_hint=(1, None), height=dp(30)
        )
        layout.add_widget(self.score_label)

        self.question_panel = Panel(size_hint=(1, 0.3))
        self.question_label = Label(text="", font_size='18sp', color=COLOR_GOLD, bold=True, halign='center',
                                    valign='middle', padding=[dp(20), dp(20)])
        self.question_label.bind(width=lambda i, v: setattr(i, 'text_size', (v, None)))
        self.question_panel.add_widget(self.question_label)
        layout.add_widget(self.question_panel)

        self.options_grid = GridLayout(cols=1, spacing=dp(10), size_hint=(1, 0.5))
        layout.add_widget(self.options_grid)

        self.add_widget(main_layout)

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
            self.question_label.text = f"Нужно изучить минимум 4 факта.\nИзучено: {len(pool)}."
            return

        self.current_fact = random.choice(pool)
        self.current_q = random.choice(self.current_fact["quiz"])
        self.question_label.text = self.current_q["q"]

        options = [self.current_q["correct"]] + list(self.current_q["wrong"])
        random.shuffle(options)

        for option in options:
            btn = QuizButton(option)
            btn.bind(on_release=lambda b, opt=option: self.check_answer(b, opt))
            self.options_grid.add_widget(btn)
            self.option_buttons.append(btn)

    def check_answer(self, btn, selected_option):
        if not self.current_q: return

        for b in self.option_buttons:
            b.disabled = True
            b.set_state('disabled')

        is_correct = (selected_option == self.current_q["correct"])
        self.user_prefs.add_quiz_result(is_correct)

        q_stats = self.user_prefs.get_quiz_stats()
        self.score_label.text = f"Счёт: {q_stats['score']}  |  Правильно: {q_stats['correct']} из {q_stats['attempts']}"

        if is_correct:
            btn.set_state('correct')
        else:
            btn.set_state('wrong')
            for b in self.option_buttons:
                if b.label.text == self.current_q["correct"]:
                    b.set_state('correct')

        Clock.schedule_once(lambda dt: self.start_new_round(), 1.5)

    def go_back(self, instance):
        self.manager.current = 'main_menu'


class BaseScreen(Screen):
    def __init__(self, title, **kwargs):
        super().__init__(**kwargs)
        self.user_prefs = _up()
        self.title_text = title
        self.build_ui()

    def build_ui(self):
        main_layout = FloatLayout(size_hint=(1, 1))
        main_layout.add_widget(
            Image(source='bg_fact_1080x2400.png', allow_stretch=True, keep_ratio=False, size_hint=(1, 1)))

        layout = BoxLayout(orientation='vertical', padding=[dp(15), dp(40), dp(15), dp(50)], spacing=dp(10),
                           size_hint=(1, 1))

        top_panel = FloatLayout(size_hint=(1, None), height=dp(60))

        back_btn = Button(
            background_normal='btn_back.png', background_down='btn_back_down.png',
            size_hint=(None, 1), width=dp(60), pos_hint={'x': 0, 'y': 0}
        )
        back_btn.bind(on_release=self.go_back)
        top_panel.add_widget(back_btn)

        title_lbl = Label(
            text=self.title_text, font_size='24sp', color=COLOR_GOLD, bold=True,
            size_hint=(1, 1), pos_hint={'x': 0, 'y': 0}, halign='center', valign='middle'
        )
        title_lbl.bind(size=lambda i, v: setattr(i, 'text_size', (v[0], v[1])))
        top_panel.add_widget(title_lbl)

        layout.add_widget(top_panel)

        self.scroll = ScrollView(size_hint=(1, 1), do_scroll_x=False)
        self.content = BoxLayout(orientation='vertical', size_hint=(1, None), spacing=dp(10))
        self.content.bind(minimum_height=self.content.setter('height'))
        self.scroll.add_widget(self.content)
        layout.add_widget(self.scroll)

        main_layout.add_widget(layout)
        self.add_widget(main_layout)

    def go_back(self, instance):
        self.manager.current = 'main_menu'


class HistoryScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__("ИСТОРИЯ", **kwargs)

    def on_enter(self, *args):
        self.content.clear_widgets()

        liked = self.user_prefs.data["liked_facts"]
        viewed = self.user_prefs.data["viewed_facts"]
        not_liked = [fid for fid in viewed if fid not in liked]

        self.content.add_widget(
            Label(text=f"★ ПОНРАВИВШИЕСЯ ({len(liked)})", font_size='18sp', color=COLOR_GOLD, size_hint_y=None,
                  height=dp(40)))
        for fact_id in reversed(liked):
            fact = get_fact_by_id(fact_id)
            if fact:
                btn = Button(text=fact.get('title', ''), background_normal='panel_card_9slice.png',
                             border=(dp(20), dp(20), dp(20), dp(20)), color=COLOR_CREAM, size_hint_y=None,
                             height=dp(60), font_size='16sp')
                btn.bind(on_release=lambda x, f=fact: self.view_fact(f))
                self.content.add_widget(btn)

        self.content.add_widget(
            Label(text=f"▸ ИЗУЧЕННЫЕ ({len(not_liked)})", font_size='18sp', color=COLOR_CREAM, size_hint_y=None,
                  height=dp(40)))
        for fact_id in reversed(not_liked):
            fact = get_fact_by_id(fact_id)
            if fact:
                btn = Button(text=fact.get('title', ''), background_normal='panel_card_light_9slice.png',
                             border=(dp(20), dp(20), dp(20), dp(20)), color=COLOR_GOLD, size_hint_y=None,
                             height=dp(60), font_size='16sp')
                btn.bind(on_release=lambda x, f=fact: self.view_fact(f))
                self.content.add_widget(btn)

    def view_fact(self, fact):
        self.manager.current = 'fact_screen'
        self.manager.get_screen('fact_screen').show_fact(fact)


class NotesScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__("МОИ ЗАМЕТКИ", **kwargs)

    def on_enter(self, *args):
        self.content.clear_widgets()
        all_notes = self.user_prefs.get_all_notes()
        if all_notes:
            for fact_id_str, text in all_notes.items():
                fact = get_fact_by_id(int(fact_id_str))
                if fact:
                    btn = Button(
                        text=f"{fact.get('title', '')}\n{text[:50]}...",
                        background_normal='panel_card_9slice.png',
                        border=(dp(20), dp(20), dp(20), dp(20)),
                        color=COLOR_CREAM,
                        size_hint_y=None,
                        height=dp(90),
                        font_size='14sp'
                    )
                    btn.bind(on_release=lambda x, f=fact: self.view_fact(f))
                    self.content.add_widget(btn)
        else:
            self.content.add_widget(Label(text="У вас пока нет заметок", color=COLOR_CREAM, font_size='18sp'))

    def view_fact(self, fact):
        self.manager.current = 'fact_screen'
        self.manager.get_screen('fact_screen').show_fact(fact)


class StatsScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__("СТАТИСТИКА", **kwargs)

    def on_enter(self, *args):
        self.content.clear_widgets()
        stats = self.user_prefs.get_user_stats()
        q_stats = self.user_prefs.get_quiz_stats()
        total_facts = get_facts_count()
        progress = self.user_prefs.get_total_progress(total_facts)

        def add_stat_lbl(text, font_size='16sp', color=COLOR_CREAM, height=dp(30), bold=False):
            lbl = Label(text=text, font_size=font_size, color=color, size_hint_y=None, height=height, halign='left',
                        valign='middle', bold=bold)
            lbl.bind(width=lambda i, v: setattr(i, 'text_size', (v, None)))
            self.content.add_widget(lbl)

        add_stat_lbl("[ ОБЩИЙ ПРОГРЕСС ]", font_size='20sp', color=COLOR_GOLD, height=dp(40), bold=True)
        add_stat_lbl(f"Изучено: {stats['unique_facts_viewed']} / {total_facts}")
        add_stat_lbl(f"Прогресс: {progress}%")

        add_stat_lbl("[ ВИКТОРИНА ]", font_size='20sp', color=COLOR_GOLD, height=dp(40), bold=True)
        add_stat_lbl(f"Счёт: {q_stats['score']} очков")
        add_stat_lbl(f"Правильных ответов: {q_stats['correct']} из {q_stats['attempts']}")

        add_stat_lbl("[ ДОСТИЖЕНИЯ ]", font_size='20sp', color=COLOR_GOLD, height=dp(40), bold=True)
        achievements = self.user_prefs.get_achievement_progress()
        if achievements:
            for ach in achievements:
                add_stat_lbl(f"★ {ach['name']} — {ach['desc']}", font_size='14sp', height=dp(40))
        else:
            add_stat_lbl("Читайте факты, чтобы получать достижения!", font_size='14sp', color=(0.5, 0.5, 0.5, 1))


class SettingsScreen(BaseScreen):
    def __init__(self, **kwargs):
        super().__init__("НАСТРОЙКИ", **kwargs)

    def on_enter(self, *args):
        self.content.clear_widgets()

        self.content.add_widget(
            Label(text=f"Версия: {__version__}", font_size='16sp', color=COLOR_CREAM, size_hint_y=None, height=dp(40)))

        btn_clear = Button(text="Очистить историю", background_normal='btn_wide_plain.png',
                           border=(dp(20), dp(20), dp(20), dp(20)), color=COLOR_GOLD, size_hint_y=None, height=dp(60),
                           font_size='18sp')
        btn_clear.bind(on_release=self.confirm_clear_history)
        self.content.add_widget(btn_clear)

        btn_reset = Button(text="Сбросить всё", background_normal='btn_wide_plain.png',
                           border=(dp(20), dp(20), dp(20), dp(20)), color=COLOR_RED, size_hint_y=None, height=dp(60),
                           font_size='18sp')
        btn_reset.bind(on_release=self.confirm_reset_all)
        self.content.add_widget(btn_reset)

    def confirm_clear_history(self, instance):
        def do_clear(inst):
            self.user_prefs.clear_history()
            popup.dismiss()
            self.on_enter()

        self._show_popup("Очистить историю просмотров?", do_clear)

    def confirm_reset_all(self, instance):
        def do_reset(inst):
            self.user_prefs.reset_data()
            popup.dismiss()
            self.on_enter()

        self._show_popup("Удалить ВСЕ данные?\n(Историю, лайки, заметки)", do_reset)

    def _show_popup(self, text, callback):
        content = BoxLayout(orientation='vertical', padding=dp(15), spacing=dp(15))
        content.add_widget(Label(text=text, font_size='16sp', color=COLOR_CREAM, halign='center'))

        btn_row = BoxLayout(size_hint=(1, None), height=dp(50), spacing=dp(10))
        cancel_btn = Button(text="Отмена", background_normal='', background_color=(0.3, 0.3, 0.3, 1),
                            color=COLOR_CREAM)
        confirm_btn = Button(text="Да", background_normal='', background_color=COLOR_RED, color=COLOR_CREAM)

        btn_row.add_widget(cancel_btn)
        btn_row.add_widget(confirm_btn)
        content.add_widget(btn_row)

        popup = Popup(title="", content=content, size_hint=(0.85, 0.35), background_color=(0, 0, 0, 0.8))
        confirm_btn.bind(on_release=callback)
        cancel_btn.bind(on_release=popup.dismiss)
        popup.open()


class WarFactApp(App):
    def build(self):
        Window.clearcolor = COLOR_BG
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
