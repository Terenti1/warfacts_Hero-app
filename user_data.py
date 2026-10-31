import json
import os
from datetime import datetime
from data import get_facts_count, get_facts_by_tag, get_all_tags


def _get_storage_path(filename):
    try:
        from kivy.app import App
        app = App.get_running_app()
        if app is not None:
            data_dir = app.user_data_dir
            os.makedirs(data_dir, exist_ok=True)
            return os.path.join(data_dir, filename)
    except Exception as e:
        print(f"[STORAGE] Не удалось получить user_data_dir: {e}")
    return filename


class UserPreferences:
    def __init__(self, storage_file="user_data.json"):
        self.storage_file = _get_storage_path(storage_file)
        self.data = self.load_data()

    def load_data(self):
        if os.path.exists(self.storage_file):
            try:
                with open(self.storage_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                default = self.get_default_data()
                for key in default:
                    if key not in data:
                        data[key] = default[key]
                return data
            except Exception:
                return self.get_default_data()
        return self.get_default_data()

    def get_default_data(self):
        return {
            "viewed_facts": [], "liked_facts": [], "disliked_facts": [],
            "tag_scores": {}, "tag_history": [], "notes": {},
            "tag_progress": {}, "achievements": [], "streak_days": 0,
            "last_activity": None, "total_views": 0, "last_visit": None,
            "quiz_score": 0, "quiz_attempts": 0, "quiz_correct": 0,
            "visited_months": [], "feedback": []
        }

    def save_data(self):
        try:
            self.data["last_visit"] = datetime.now().isoformat()
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def add_view(self, fact_id, tags):
        if fact_id not in self.data["viewed_facts"]:
            self.data["viewed_facts"].append(fact_id)
            for tag in tags:
                if tag not in self.data["tag_progress"]:
                    self.data["tag_progress"][tag] = []
                if fact_id not in self.data["tag_progress"][tag]:
                    self.data["tag_progress"][tag].append(fact_id)
        self.data["total_views"] += 1
        self.update_streak()
        self.save_data()

    def update_streak(self):
        today = datetime.now().date()
        current_month = today.strftime("%Y-%m")

        if "visited_months" not in self.data:
            self.data["visited_months"] = []
        if current_month not in self.data["visited_months"]:
            self.data["visited_months"].append(current_month)

        last = self.data.get("last_activity")
        if last:
            try:
                last_date = datetime.fromisoformat(last).date()
                diff = (today - last_date).days
                if diff == 1:
                    self.data["streak_days"] = self.data.get("streak_days", 0) + 1
                elif diff > 1:
                    self.data["streak_days"] = 1
            except Exception:
                self.data["streak_days"] = 1
        else:
            self.data["streak_days"] = 1
        self.data["last_activity"] = datetime.now().isoformat()

    def add_quiz_result(self, is_correct):
        self.data["quiz_attempts"] += 1
        if is_correct:
            self.data["quiz_correct"] += 1
            self.data["quiz_score"] += 10
        self.save_data()

    def get_quiz_stats(self):
        return {
            "score": self.data.get("quiz_score", 0),
            "attempts": self.data.get("quiz_attempts", 0),
            "correct": self.data.get("quiz_correct", 0)
        }

    def get_total_progress(self, total_facts):
        if total_facts == 0: return 0
        return round((len(self.data["viewed_facts"]) / total_facts) * 100)

    def get_achievement_progress(self):
        all_achievements = []
        total_facts = get_facts_count()
        viewed_count = len(self.data["viewed_facts"])

        # 1. Прогресс (10 шагов по 10%)
        for pct in range(10, 110, 10):
            req = int(total_facts * pct / 100)
            all_achievements.append({
                "name": f"{pct}% пути",
                "desc": f"Изучено {req} фактов",
                "is_obtained": viewed_count >= req
            })

        # 2. Теги (100% тега)
        for tag in get_all_tags():
            total_in_tag = len(get_facts_by_tag(tag))
            viewed_in_tag = len(self.data.get("tag_progress", {}).get(tag, []))
            all_achievements.append({
                "name": f"Эксперт: #{tag}",
                "desc": f"Изучены все факты ({total_in_tag})",
                "is_obtained": viewed_in_tag >= total_in_tag
            })

        # 3. Отдельные личности
        legendary_heroes = {
            1: "Марат Казей", 8: "Вера Хоружая", 25: "Дмитрий Карбышев",
            28: "Василий Талаш", 37: "Константин Рокоссовский"
        }
        for fid, name in legendary_heroes.items():
            all_achievements.append({
                "name": f"Знакомство: {name}",
                "desc": "Прочитан факт",
                "is_obtained": fid in self.data["viewed_facts"]
            })

        # 4. Серии дней
        streak = self.data.get("streak_days", 0)
        streaks = [
            (3, "Постоянный", "3 дня подряд"),
            (7, "Неутомимый", "7 дней подряд"),
            (30, "Преданный делу", "30 дней подряд"),
            (180, "Полугодие", "180 дней подряд"),
            (365, "Год с историей", "365 дней подряд")
        ]
        for req, name, desc in streaks:
            all_achievements.append({"name": name, "desc": desc, "is_obtained": streak >= req})

        # 5. Месяцы (общие вехи)
        visited_months = self.data.get("visited_months", [])
        month_milestones = [
            (1, "Первый месяц", "1 месяц с приложением"),
            (3, "Три месяца", "3 месяца с приложением"),
            (6, "Полгода", "6 месяцев с приложением"),
            (12, "Круглый год", "12 месяцев с приложением")
        ]
        for req, name, desc in month_milestones:
            all_achievements.append({"name": name, "desc": desc, "is_obtained": len(visited_months) >= req})

        # 6. Конкретные месяцы (Январь, Февраль и т.д.)
        month_names = {
            "01": "Январь", "02": "Февраль", "03": "Март", "04": "Апрель", "05": "Май",
            "06": "Июнь", "07": "Июль", "08": "Август", "09": "Сентябрь", "10": "Октябрь",
            "11": "Ноябрь", "12": "Декабрь"
        }
        visited_m_codes = [m.split('-')[1] for m in visited_months]
        for m_code, m_name in month_names.items():
            all_achievements.append({
                "name": f"Месяц: {m_name}",
                "desc": f"Активность в {m_name}e",
                "is_obtained": m_code in visited_m_codes
            })

        # 7. Викторина
        quiz_correct = self.data.get("quiz_correct", 0)
        quiz_milestones = [
            (5, "Эрудит", "5 правильных ответов"),
            (15, "Знаток викторины", "15 правильных ответов"),
            (50, "Мастер викторины", "50 правильных ответов"),
            (100, "Гений истории", "100 правильных ответов")
        ]
        for req, name, desc in quiz_milestones:
            all_achievements.append({"name": name, "desc": desc, "is_obtained": quiz_correct >= req})

        all_achievements.sort(key=lambda x: not x["is_obtained"])

        return all_achievements

    def get_streak_days(self):
        return self.data.get("streak_days", 0)

    def add_note(self, fact_id, note_text):
        if note_text and note_text.strip():
            self.data["notes"][str(fact_id)] = note_text.strip()
        else:
            if str(fact_id) in self.data["notes"]:
                del self.data["notes"][str(fact_id)]
        self.save_data()
        return True

    def get_note(self, fact_id):
        return self.data["notes"].get(str(fact_id), "")

    def has_note(self, fact_id):
        return str(fact_id) in self.data["notes"]

    def get_all_notes(self):
        return self.data.get("notes", {}).copy()

    def add_like(self, fact_id, tags):
        if fact_id in self.data["disliked_facts"]:
            self.data["disliked_facts"].remove(fact_id)
        if fact_id not in self.data["liked_facts"]:
            self.data["liked_facts"].append(fact_id)
            for tag in tags:
                self.data["tag_scores"][tag] = self.data["tag_scores"].get(tag, 0) + 1
            self.save_data()
            return True
        return False

    def add_dislike(self, fact_id, tags):
        if fact_id in self.data["liked_facts"]:
            self.data["liked_facts"].remove(fact_id)
        if fact_id not in self.data["disliked_facts"]:
            self.data["disliked_facts"].append(fact_id)
            for tag in tags:
                self.data["tag_scores"][tag] = self.data["tag_scores"].get(tag, 0) - 1
            self.save_data()
            return True
        return False

    def remove_like(self, fact_id, tags):
        if fact_id in self.data["liked_facts"]:
            self.data["liked_facts"].remove(fact_id)
            for tag in tags:
                self.data["tag_scores"][tag] = self.data["tag_scores"].get(tag, 0) - 1
            self.save_data()
            return True
        return False

    def remove_dislike(self, fact_id, tags):
        if fact_id in self.data["disliked_facts"]:
            self.data["disliked_facts"].remove(fact_id)
            for tag in tags:
                self.data["tag_scores"][tag] = self.data["tag_scores"].get(tag, 0) + 1
            self.save_data()
            return True
        return False

    def get_tag_score(self, tag):
        return self.data["tag_scores"].get(tag, 0)

    def get_top_tags(self, limit=5):
        sorted_tags = sorted(self.data["tag_scores"].items(), key=lambda x: x[1], reverse=True)
        return sorted_tags[:limit]

    def get_recommendation_score(self, fact):
        if "tags" not in fact: return 0
        total_score = sum(self.get_tag_score(tag) for tag in fact["tags"])
        if fact["id"] in self.data["viewed_facts"]: total_score -= 5
        if fact["id"] not in self.data["viewed_facts"]: total_score += 2
        if fact["id"] in self.data["liked_facts"]: total_score += 3
        return total_score

    def get_user_stats(self):
        return {
            "total_views": self.data["total_views"],
            "liked_count": len(self.data["liked_facts"]),
            "disliked_count": len(self.data["disliked_facts"]),
            "unique_facts_viewed": len(set(self.data["viewed_facts"])),
            "top_tags": self.get_top_tags(5),
            "streak_days": self.get_streak_days()
        }

    def get_fact_status(self, fact_id):
        if fact_id in self.data["liked_facts"]:
            return "liked"
        elif fact_id in self.data["disliked_facts"]:
            return "disliked"
        return "neutral"

    def clear_history(self):
        self.data["viewed_facts"] = []
        self.data["tag_progress"] = {}
        self.data["total_views"] = 0
        self.data["streak_days"] = 0
        self.data["last_activity"] = None
        self.save_data()

    def reset_data(self):
        self.data = self.get_default_data()
        self.save_data()
