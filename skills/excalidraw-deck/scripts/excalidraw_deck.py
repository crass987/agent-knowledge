"""Библиотека сборки .excalidraw-дек: слайд = фрейм 1920x1080.

Скилл: excalidraw-deck (agent-knowledge). См. SKILL.md и references/templates.md.

Ключевые решения:
- каждый слайд — element type 'frame' с именем «NN · метка»; дети помечены frameId;
- текст внутри фигуры ВСЕГДА bound (containerId + boundElements) — Excalidraw сам
  переносит строки внутри рамки, переполнение по ширине невозможно;
- цвета только из PAL (semantic роли), шрифт fontFamily=2 по умолчанию;
- программа-element'ы не содержат 'index' (дробный порядок Excalidraw) — он
  регенерируется при загрузке; унаследованные элементы сохраняют свой.
"""

import json
import math
import secrets
import time

FRAME_W, FRAME_H, GAP = 1920, 1080, 240
PAD = 12            # внутренний отступ bound-текста (Excalidraw использует 2x5)
INK = "#1e1e1e"
MUTED = "#495057"
FAINT = "#868e96"
NUMBER = "#adb5bd"

# Роль -> (мягкая заливка, обводка). Полный смысл ролей — references/palette.md.
PAL = {
    "blue":   ("#a5d8ff", "#1971c2"),   # факты, классика, техника
    "violet": ("#d0bfff", "#6741d9"),   # вступление, теория, рамка доклада
    "green":  ("#b2f2bb", "#2f9e44"),   # решения, «как правильно»
    "amber":  ("#ffec99", "#f08c00"),   # ключевые формулы, акцент-баннеры
    "red":    ("#ffc9c9", "#e03131"),   # анти-паттерны, финал, предупреждения
    "gray":   ("#e9ecef", "#495057"),   # нейтральное, плейсхолдеры
}

# грубая ширина глифа в долях fontSize (для оценки переноса строк)
_GLYPH = {1: 0.58, 2: 0.52, 3: 0.60}
LINE_H = 1.25

# Пресеты стилей — references/style-presets.md. Один пресет на деку.
THEMES = {
    "handdrawn": {"paper": "#ffffff", "ink": "#1e1e1e", "muted": "#495057",
                  "faint": "#868e96", "roughness": 1},
    "clean":     {"paper": "#ffffff", "ink": "#1e1e1e", "muted": "#495057",
                  "faint": "#868e96", "roughness": 0},
    "dark":      {"paper": "#1a1a1a", "ink": "#f1f3f5", "muted": "#ced4da",
                  "faint": "#adb5bd", "roughness": 1,
                  "gray": ("#343a40", "#adb5bd")},
}


def _new_id():
    return secrets.token_hex(10)


def _base(kind, x, y, font=2):
    """Каркас элемента с обязательными полями формата Excalidraw v2."""
    now = int(time.time() * 1000)
    return {
        "id": _new_id(), "type": kind, "x": x, "y": y,
        "width": 0, "height": 0, "angle": 0,
        "strokeColor": INK, "backgroundColor": "transparent",
        "fillStyle": "solid", "strokeWidth": 1, "strokeStyle": "solid",
        "roughness": 1, "opacity": 100, "roundness": None,
        "seed": secrets.randbelow(2**31), "version": 2,
        "versionNonce": secrets.randbelow(2**31), "isDeleted": False,
        "boundElements": None, "updated": now, "link": None, "locked": False,
        "fontFamily": font,
    }


def est_wrapped_height(text, box_width, fs, font=2):
    """Оценка высоты текста после переноса в коробку шириной box_width."""
    cpl = max(6, int(box_width / (fs * _GLYPH.get(font, 0.55))))
    lines = sum(max(1, math.ceil(len(l) / cpl)) for l in text.split("\n"))
    return lines * fs * LINE_H


class Slide:
    """Один фрейм-слайд. Все координаты методов — ЛОКАЛЬНЫЕ (от угла фрейма)."""

    def __init__(self, deck, num, name, accent):
        self.deck = deck
        self.num = num
        self.accent = accent
        self.x0 = 0
        self.y0 = len(deck.slides) * (FRAME_H + GAP)
        self._counters = {}
        fr = _base("frame", self.x0, self.y0)
        fr["width"], fr["height"] = FRAME_W, FRAME_H
        fr["name"] = f"{num} · {name}"
        fr["fillStyle"] = "solid"
        fr["strokeColor"] = "#dee2e6"
        fr["customData"] = {"deck-key": f"frame/{num}"}
        deck.elements.append(fr)
        self.frame = fr

    def _tag(self, el, kind, text=None):
        """Стабильный ключ элемента (для режима слияния поверх правок владельца)."""
        n = self._counters.get(kind, 0) + 1
        self._counters[kind] = n
        cd = el.setdefault("customData", {})
        cd["deck-key"] = f"{self.num}/{kind}/{n}"
        if el["type"] == "text" and text is not None:
            cd["gen_text"] = text
        return el

    # -- служебное ---------------------------------------------------------
    def _own(self, el):
        el["frameId"] = self.frame["id"]
        el["roughness"] = self.deck.theme["roughness"]
        self.deck.elements.append(el)
        return el

    def _pal(self, accent):
        """Цвет роли с учётом пресета (тёмная тема перекрашивает серый)."""
        if accent == "gray" and "gray" in self.deck.theme:
            return self.deck.theme["gray"]
        return PAL[accent]

    def _text(self, x, y, text, fs, color=None, font=2, kind="text"):
        el = self._own(_base("text", self.x0 + x, self.y0 + y, font))
        el.update(text=text, originalText=text, fontSize=fs, lineHeight=LINE_H,
                  baseline=round(fs * 1.05, 2), textAlign="left",
                  verticalAlign="top", autoResize=True,
                  strokeColor=color or self.deck.theme["ink"])
        lines = text.split("\n")
        el["height"] = round(len(lines) * fs * LINE_H, 2)
        el["width"] = round(max(len(l) for l in lines) * fs * _GLYPH[font], 2)
        self._tag(el, kind, text)
        return el

    # -- примитивы ----------------------------------------------------------
    def title(self, text, fs=64, color=None, x=120, y=140):
        return self._text(x, y, text, fs, color, kind="title")

    def subtitle(self, text, fs=30, color=None, x=120, y=None):
        return self._text(x, y if y is not None else 330, text, fs,
                          color or self.deck.theme["muted"], kind="subtitle")

    def row(self, x, y, text, fs=28, color=None):
        return self._text(x, y, text, fs, color, kind="row")

    def big(self, x, y, text, color=None, fs=56):
        return self._text(x, y, text, fs, color, kind="big")

    def underline(self, x, y, accent=None, w=120):
        _, st = PAL[accent or self.accent]
        el = self._own(_base("line", self.x0 + x, self.y0 + y))
        el.update(points=[[0, 0], [w, 0]], width=w, height=0,
                  strokeColor=st, strokeWidth=4)
        self._tag(el, "underline")
        return el

    def pill(self, x, y, text, accent=None, fs=18):
        """Надзаголовок-чип. Ширина по тексту."""
        bg, st = self._pal(accent or self.accent)
        w = round(len(text) * fs * _GLYPH[2] + 52, 2)  # запас, чтобы оценка переноса не была пограничной
        h = round(fs * LINE_H + 18, 2)
        r = self._own(_base("rectangle", self.x0 + x, self.y0 + y))
        r.update(width=w, height=h, backgroundColor=bg, strokeColor=st,
                 roundness={"type": 3})
        tid = _new_id()
        t = self._own(_base("text", 0, 0))
        t.update(id=tid, text=text, originalText=text, fontSize=fs,
                 lineHeight=LINE_H, baseline=round(fs * 1.05, 2),
                 containerId=r["id"], textAlign="center",
                 verticalAlign="middle", autoResize=False, strokeColor=INK)
        t["x"] = self.x0 + x + 16
        t["y"] = self.y0 + y + round(h / 2 - fs * LINE_H / 2, 2)
        t["width"] = round(w - 32, 2)
        t["height"] = round(fs * LINE_H, 2)
        r["boundElements"] = [{"id": tid, "type": "text"}]
        self._tag(r, "pill")
        self._tag(t, "pill.t", text)
        return r

    def card(self, x, y, w, text, accent="gray", fs=26, align="center",
             h=None, pad_h=40):
        """Фигура с bound-текстом. Высота — по оценке переноса (или явная h)."""
        bg, st = self._pal(accent)
        th = est_wrapped_height(text, w - 2 * PAD, fs)
        hh = round(h or th + pad_h, 2)
        r = self._own(_base("rectangle", self.x0 + x, self.y0 + y))
        r.update(width=w, height=hh, backgroundColor=bg, strokeColor=st,
                 roundness={"type": 3})
        tid = _new_id()
        t = self._own(_base("text", 0, 0))
        t.update(id=tid, text=text, originalText=text, fontSize=fs,
                 lineHeight=LINE_H, baseline=round(fs * 1.05, 2),
                 containerId=r["id"], textAlign=align,
                 verticalAlign="middle", autoResize=False,
                 strokeColor=self.deck.theme["ink"])
        t["x"] = self.x0 + x + PAD
        t["y"] = self.y0 + y + round(hh / 2 - th / 2, 2)
        t["width"] = round(w - 2 * PAD, 2)
        t["height"] = round(th, 2)
        r["boundElements"] = [{"id": tid, "type": "text"}]
        self._tag(r, "card")
        self._tag(t, "card.t", text)
        return r

    def arrow(self, x, y, dx, dy, curve=True, color=None, width=2):
        """Стрелка из (x,y) со смещением (dx,dy). points относительные."""
        el = self._own(_base("arrow", self.x0 + x, self.y0 + y))
        el.update(points=[[0, 0], [dx, dy]], width=abs(dx), height=abs(dy),
                  endArrowhead="arrow", strokeWidth=width,
                  strokeColor=color or self.deck.theme["muted"],
                  roundness={"type": 2} if curve else None)
        self._tag(el, "arrow")
        return el

    def number(self, accent=None):
        """Номер слайда в правом верхнем углу фрейма."""
        _, st = PAL[accent or self.accent]
        return self._text(FRAME_W - 160, 110, self.num, 18, st, kind="num")

    def screenshot_placeholder(self, x, y, w, caption, accent="gray"):
        return self.card(x, y, w, caption, accent, fs=24, h=180)

    # -- инфографика (references/infographics.md) ---------------------------
    def timeline(self, x, y, w, items, accent=None):
        """Линия времени: точки по числу событий, подписи снизу.
        items: [(текст, роль|None)]."""
        _, st = PAL[accent or self.accent]
        line = self._own(_base("line", self.x0 + x, self.y0 + y))
        line.update(points=[[0, 0], [w, 0]], width=w, height=0,
                    strokeColor=st, strokeWidth=3)
        self._tag(line, "tl.line")
        n = max(len(items) - 1, 1)
        step = w / n
        for i, (label, role) in enumerate(items):
            bg, rst = PAL[role or accent or self.accent]
            cx = x + i * step
            dot = self._own(_base("ellipse", self.x0 + cx - 8, self.y0 + y - 8))
            dot.update(width=16, height=16, strokeColor=rst,
                       backgroundColor=bg, fillStyle="solid")
            self._tag(dot, "tl.dot")
            t = self._text(cx - 150, y + 28, label, 22, kind="tl.label")
            t["textAlign"] = "center"
            t["x"] = self.x0 + cx - t["width"] / 2

    def stat(self, x, y, number, label, accent=None, fs=120):
        """Цифра-удар: гигантское число + подпись под ним."""
        _, st = PAL[accent or self.accent]
        self._text(x, y, str(number), fs, st, kind="stat.num")
        self._text(x, y + round(fs * LINE_H * 1.02, 2), label, 28,
                   self.deck.theme["muted"], kind="stat.label")

    def bars(self, x, y, w, items, accent="blue"):
        """Горизонтальные бары: items=[(label, value)], сортируй по убыванию.
        Колонка лейблов 340px, бар по доле максимума, значение справа."""
        bg, st = PAL[accent]
        maxv = max(v for _, v in items)
        bar_w = w - 420
        for i, (label, v) in enumerate(items):
            yb = y + i * 76
            self._text(x, yb + 6, label, 24, kind="bar.label")
            r = self._own(_base("rectangle", self.x0 + x + 340, self.y0 + yb))
            bw = round(max(bar_w * v / maxv, 24), 2)
            r.update(width=bw, height=48, backgroundColor=bg,
                     strokeColor=st, roundness={"type": 3})
            self._tag(r, "bar.rect")
            self._text(x + 340 + bw + 16, yb + 6, str(v), 24,
                       self.deck.theme["muted"], kind="bar.val")


class Deck:
    def __init__(self, theme="handdrawn"):
        self.theme = THEMES[theme]
        self.elements = []
        self.slides = []

    def slide(self, name, accent="violet", num=None):
        num = num or f"{len(self.slides) + 1:02d}"
        s = Slide(self, num, name, accent)
        self.slides.append(s)
        return s

    def add_raw(self, elements, dx=0, dy=0, key_prefix=None):
        """Вставить готовые элементы (заметки, панель) со сдвигом, вне фреймов.
        key_prefix — включить в режим слияния (правки владельца уважаются)."""
        import copy
        for i, src in enumerate(elements):
            e = copy.deepcopy(src)
            e["id"] = _new_id()
            e.pop("index", None)
            e.pop("frameId", None)
            e.pop("groupId", None)
            e.pop("groupIds", None)
            e["x"] = e.get("x", 0) + dx
            e["y"] = e.get("y", 0) + dy
            if key_prefix:
                cd = e.setdefault("customData", {})
                cd["deck-key"] = f"{key_prefix}/{i:02d}"
                if e["type"] == "text":
                    cd["gen_text"] = e["text"]
            self.elements.append(e)

    def _manifest_path(self, path):
        return f"{path}.manifest.json"

    def _keys(self):
        out = set()
        for e in self.elements:
            k = (e.get("customData") or {}).get("deck-key")
            if k:
                out.add(k)
        return out

    def save(self, path):
        doc = {
            "type": "excalidraw", "version": 2,
            "source": "agent-knowledge/excalidraw-deck",
            "elements": self.elements, "appState": {
                "viewBackgroundColor": self.theme["paper"], "gridSize": None},
            "files": {},
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(doc, f, ensure_ascii=False)
        with open(self._manifest_path(path), "w", encoding="utf-8") as f:
            json.dump({"generated": sorted(self._keys())}, f)
        return path

    def merge_into(self, path):
        """Наложить план поверх существующей деки, уважая правки владельца.

        Политика: позиция/стиль/размер — всегда владельца; текст обновляется
        только если владелец его не правил; правленый текст при изменившемся
        плане = конфликт (остаётся текст владельца); ваших элементов план не
        касается; удалённое владельцем не восстанавливается (манифест).
        """
        import copy
        try:
            old = json.load(open(path, encoding="utf-8"))
        except FileNotFoundError:
            old = None
        if old is None:
            self.save(path)
            return {"mode": "baseline", "added": len(self.elements),
                    "updated": 0, "kept_user": 0, "conflicts": [],
                    "orphans": [], "skipped_deleted": []}
        by_key, by_id = {}, {}
        for e in old["elements"]:
            by_id[e["id"]] = e
            k = (e.get("customData") or {}).get("deck-key")
            if k:
                by_key[k] = e
        try:
            manifest = set(json.load(open(self._manifest_path(path)))["generated"])
        except Exception:
            manifest = set()

        if not by_key:
            # База ещё не помечена ключами — полная запись как первый прогон.
            self.save(path)
            return {"mode": "baseline", "added": len(self.elements),
                    "updated": 0, "kept_user": 0, "conflicts": [],
                    "orphans": [], "skipped_deleted": []}

        report = {"mode": "merge", "added": 0, "updated": 0, "kept_user": 0,
                  "conflicts": [], "orphans": [], "skipped_deleted": []}
        frame_map = {}
        additions = []
        plan_keys = set()

        for e in self.elements:
            k = (e.get("customData") or {}).get("deck-key")
            if not k:
                continue
            plan_keys.add(k)
            ex = by_key.get(k)
            if ex is None:
                if k in manifest:
                    report["skipped_deleted"].append(k)
                    continue
                e2 = copy.deepcopy(e)
                fid = e2.get("frameId")
                if fid and fid in frame_map:
                    e2["frameId"] = frame_map[fid]
                additions.append(e2)
                report["added"] += 1
                continue
            if e["type"] == "frame":
                frame_map[e["id"]] = ex["id"]  # фрейм целиком — владельца
                continue
            cd = ex.setdefault("customData", {})
            if e["type"] == "text":
                new_text = e["text"]
                gen = cd.get("gen_text")
                cur = ex["text"]
                if gen is None:  # первый учёт этого элемента
                    gen = cur
                if cur == gen:
                    if new_text != cur:
                        ex["text"] = new_text
                        ex["originalText"] = new_text
                        c = by_id.get(ex.get("containerId"))
                        if c:  # bound-текст: ширина от контейнера владельца
                            ex["width"] = round(c["width"] - 2 * PAD, 2)
                        ex["height"] = round(est_wrapped_height(
                            new_text, ex["width"], ex["fontSize"],
                            ex.get("fontFamily", 2)), 2)
                        report["updated"] += 1
                elif new_text != gen:
                    report["conflicts"].append(
                        f"{k}: план=«{new_text[:40]}», у владельца=«{cur[:40]}»")
                else:
                    report["kept_user"] += 1
                cd["gen_text"] = new_text
            else:
                report["kept_user"] += 1  # не-текст: синхронизировать нечего

        report["orphans"] = sorted(k for k in by_key if k not in plan_keys)
        old["elements"].extend(additions)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(old, f, ensure_ascii=False)
        with open(self._manifest_path(path), "w", encoding="utf-8") as f:
            json.dump({"generated": sorted(manifest | plan_keys)}, f)
        return report

    def validate(self):
        """Список проблем: FAIL чинить обязательно, WARN — по вкусу."""
        problems = []
        ids = [e["id"] for e in self.elements]
        if len(ids) != len(set(ids)):
            problems.append("FAIL: дубликаты id")
        by_id = {e["id"]: e for e in self.elements}
        frames = {e["id"]: e for e in self.elements if e["type"] == "frame"}
        for e in self.elements:
            if e.get("containerId"):
                c = by_id.get(e["containerId"])
                if not c:
                    problems.append(f"FAIL: текст {e['id']} без контейнера")
                    continue
                if not (c["x"] <= e["x"] and c["y"] <= e["y"] and
                        e["x"] + e["width"] <= c["x"] + c["width"] and
                        e["y"] + e["height"] <= c["y"] + c["height"]):
                    problems.append(
                        f"FAIL: bound-текст вне контейнера {c['id']}")
                th = est_wrapped_height(e["text"], e["width"],
                                        e["fontSize"], e["fontFamily"])
                if th > c["height"] - 4:
                    problems.append(
                        f"WARN: текст в {c['id']} тесноват "
                        f"(~{th:.0f} > {c['height']:.0f}): {e['text'][:40]!r}")
            fid = e.get("frameId")
            if fid and fid not in frames:
                problems.append(f"FAIL: frameId на несуществующий фрейм")
        for f in frames.values():
            kids = [e for e in self.elements if e.get("frameId") == f["id"]]
            outside = [e for e in kids
                       if e["x"] < f["x"] - 1 or e["y"] < f["y"] - 1 or
                       e["x"] + e["width"] > f["x"] + f["width"] + 1 or
                       e["y"] + e["height"] > f["y"] + f["height"] + 1]
            for e in outside:
                if e["type"] not in ("arrow",):  # стрелкам прощаем кривизну
                    problems.append(
                        f"WARN: {e['type']} вылезает из фрейма "
                        f"{f.get('name')}: {e.get('text', e['id'])[:40]!r}")
        return problems
