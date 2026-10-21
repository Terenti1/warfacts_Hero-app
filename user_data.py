# user_data.py - Система рейтинга тегов, заметок и прогрессии (Android-совместимая)

import json
import os
from datetime import datetime

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
            except Exception as e:
                return self.get_default_data()
        return self.get_default_data()

    def get_default_data(self):
        return {
            "viewed_facts": [], "liked_facts": [], "disliked_facts": [],
            "tag_scores": {}, "tag_history": [], "notes": {},
            "tag_progress": {}, "achievements": [], "streak_days": 0,
            "last_activity": None, "total_views": 0, "last_visit": None
        }

    def save_data(self):
        try:
            self.data["last_visit"] = datetime.now().isoformat()
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
        except Exception as e:
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
        last = self.data.get("last_activity")
        if last:
            try:
                last_date = datetime.fromisoformat(last).date()
                diff = (today - last_date).days
                if diff == 1: self.data["streak_days"] = self.data.get("streak_days", 0) + 1
                elif diff > 1: self.data["streak_days"] = 0
            except Exception: self.data["streak_days"] = 1
        else: self.data["streak_days"] = 1
        self.data["last_activity"] = datetime.now().isoformat()

    def get_total_progress(self, total_facts):
        if total_facts == 0: return 0
        return round((len(self.data["viewed_facts"]) / total_facts) * 100)

    def get_achievement_progress(self):
        achievements = []
        viewed_count = len(self.data["viewed_facts"])
        if viewed_count >= 1: achievements.append({"id": "first_fact", "name": "Первый шаг", "desc": "Прочитан первый факт"})
        if viewed_count >= 10: achievements.append({"id": "ten_facts", "name": "Любознательный", "desc": "Прочитано 10 фактов"})
        if viewed_count >= 25: achievements.append({"id": "twenty_five", "name": "Исследователь", "desc": "Прочитано 25 фактов"})
        if viewed_count >= 50: achievements.append({"id": "fifty_facts", "name": "Знаток истории", "desc": "Прочитано 50 фактов"})
        streak = self.data.get("streak_days", 0)
        if streak >= 3: achievements.append({"id": "streak_3", "name": "Постоянный", "desc": "Активен 3 дня подряд"})
        return achievements

    def get_streak_days(self):
        return self.data.get("streak_days", 0)

    def add_note(self, fact_id, note_text):
        if note_text and note_text.strip(): self.data["notes"][str(fact_id)] = note_text.strip()
        else:
            if str(fact_id) in self.data["notes"]: del self.data["notes"][str(fact_id)]
        self.save_data()
        return True

    def get_note(self, fact_id): return self.data["notes"].get(str(fact_id), "")
    def has_note(self, fact_id): return str(fact_id) in self.data["notes"]
    def get_all_notes(self): return self.data.get("notes", {}).copy()

    def add_like(self, fact_id, tags):
        if fact_id in self.data["disliked_facts"]: self.data["disliked_facts"].remove(fact_id)
        if fact_id not in self.data["liked_facts"]:
            self.data["liked_facts"].append(fact_id)
            for tag in tags: self.data["tag_scores"][tag] = self.data["tag_scores"].get(tag, 0) + 1
            self.save_data()
            return True
        return False

    def add_dislike(self, fact_id, tags):
        if fact_id in self.data["liked_facts"]: self.data["liked_facts"].remove(fact_id)
        if fact_id not in self.data["disliked_facts"]:
            self.data["disliked_facts"].append(fact_id)
            for tag in tags: self.data["tag_scores"][tag] = self.data["tag_scores"].get(tag, 0) - 1
            self.save_data()
            return True
        return False

    def remove_like(self, fact_id, tags):
        if fact_id in self.data["liked_facts"]:
            self.data["liked_facts"].remove(fact_id)
            for tag in tags: self.data["tag_scores"][tag] = self.data["tag_scores"].get(tag, 0) - 1
            self.save_data()
            return True
        return False

    def remove_dislike(self, fact_id, tags):
        if fact_id in self.data["disliked_facts"]:
            self.data["disliked_facts"].remove(fact_id)
            for tag in tags: self.data["tag_scores"][tag] = self.data["tag_scores"].get(tag, 0) + 1
            self.save_data()
            return True
        return False

    def get_tag_score(self, tag): return self.data["tag_scores"].get(tag, 0)
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
            "total_views": self.data["total_views"], "liked_count": len(self.data["liked_facts"]),
            "disliked_count": len(self.data["disliked_facts"]), "unique_facts_viewed": len(set(self.data["viewed_facts"])),
            "top_tags": self.get_top_tags(5), "streak_days": self.get_streak_days()
        }

    def get_fact_status(self, fact_id):
        if fact_id in self.data["liked_facts"]: return "liked"
        elif fact_id in self.data["disliked_facts"]: return "disliked"
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
