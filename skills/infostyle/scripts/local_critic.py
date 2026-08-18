#!/usr/bin/env python3
"""Локальный независимый критик для инфостиля.

Прогоняет прозаические абзацы markdown-файла через локальные модели (ollama)
в режиме «найди кальки → цитата → замена». НИЧЕГО не применяет: выход — отчёт,
применение остаётся за GLM с фильтром инвариантов (см. references/local-critic.md).

Модели-профили:
  default   t-lite,yandex   — быстрый дуэт (3–4 мин на 30 абзацев), в памяти вместе
  final     qwen,yandex     — финальный прогон важных артефактов (~2–3× медленнее)

Использование:
  python3 local_critic.py <файл.md> [--models t-lite,yandex] [--limit N]

Graceful degradation: ollama недоступна или модель не скачана — предупреждение,
exit 0 (шаг критика пропускается, работа не ломается).
"""
import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.request

MODELS = {
    "t-lite": {
        "id": "hf.co/t-tech/T-lite-it-2.1-GGUF:Q4_K_M",
        "label": "T-lite-8B",
        "mode": "generate",
        "no_think": True,  # Qwen3-семья: суффикс-тег в конце промпта
    },
    "yandex": {
        "id": "yandex/YandexGPT-5-Lite-8B-instruct-GGUF",
        "label": "Яндекс-8B",
        "mode": "generate",
        "no_think": False,
    },
    "qwen": {
        "id": "qwen3:14b",
        "label": "Qwen3-14B",
        "mode": "chat",  # generate + /no_think НЕ работает: thinking съедает лимит
        "no_think": False,
    },
}

API = "http://localhost:11434"

# Промпт ЗАМОРОЖЕН — протестирован на живых абзацах 2026-08-18.
# Не переформулировать: модель обучалась пониманию именно этой формы
# (задача первым словом + few-shot; Яндекс игнорирует system-роль).
CRITIC_PROMPT = """Найди в тексте кальки с английского и неестественные для русского языка обороты. Для каждого приведи точную цитату из текста и свой вариант замены. Если оборот нормальный — не упоминай его. Формат ответа:
— «цитата» → «замена»

Пример:
Текст: Реализация данного функционала позволяет осуществлять мониторинг на уровне процессов.
Ответ:
— «Реализация данного функционала позволяет осуществлять» → «Функция умеет»

Текст: {text}
Ответ:"""

MIN_PARA_LEN = 120  # короче — не проза, пропуск


def call_ollama(model, prompt, timeout=300):
    """Один вызов модели. Возвращает (текст, сек). Бросает исключение при сбое."""
    cfg = MODELS[model]
    p = prompt
    if cfg["no_think"]:
        p = p.rstrip() + " /no_think"
    if cfg["mode"] == "chat":
        payload = {
            "model": cfg["id"],
            "messages": [{"role": "user", "content": p}],
            "stream": False,
            "think": False,
            "options": {"temperature": 0.2, "num_predict": 600},
        }
        url = f"{API}/api/chat"
    else:
        payload = {
            "model": cfg["id"],
            "prompt": p,
            "stream": False,
            "options": {"temperature": 0.2, "num_predict": 600},
        }
        url = f"{API}/api/generate"
    req = urllib.request.Request(
        url, data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"})
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=timeout) as r:
        d = json.loads(r.read())
    resp = d.get("response") or d.get("message", {}).get("content", "")
    if "</think>" in resp:  # страховка от протёкшего thinking
        resp = resp.split("</think>")[-1]
    return resp.strip(), time.time() - t0


def split_paragraphs(md_text):
    """Прозаические абзацы: без кода, таблиц, заголовков, диаграмм."""
    # вырезаем fenced-блоки (``` и ~~~) целиком
    md_text = re.sub(r"^(?:```|~~~).*?^(?:```|~~~)[^\n]*$", "", md_text,
                     flags=re.MULTILINE | re.DOTALL)
    out = []
    for raw in re.split(r"\n\s*\n", md_text):
        p = raw.strip()
        if len(p) < MIN_PARA_LEN:
            continue
        if p.startswith(("#", "|", ">", "-", "*", "1.")):  # заголовки/таблицы/цитаты/списки
            continue
        if p.startswith(("```", "~~~")):
            continue
        out.append(p)
    return out


QUOTE_MAP = {"„": "«", "“": "«", "”": "»", '"': "«", '"': "»", "'": "«", "'": "»"}


def norm_quotes(s):
    for k, v in QUOTE_MAP.items():
        s = s.replace(k, v)
    # закрывающая « второй раз внутри строки: «a «b» → грубая нормализация хватает
    return re.sub(r"«([^«»]*)«", r"«\1»", s)


LINE_RE = re.compile(
    r"^\s*[—–-]\s*[«\"„'](.+?)[»\"“']\s*(?:→|->)\s*[«\"„'](.+?)[»\"“']\s*$")


def parse_suggestions(resp):
    out = []
    for line in resp.splitlines():
        m = LINE_RE.match(line.strip())
        if m:
            out.append((m.group(1).strip(), m.group(2).strip()))
    return out


def check_alive(models):
    alive = []
    try:
        with urllib.request.urlopen(f"{API}/api/tags", timeout=5) as r:
            installed = {m.get("name", "") for m in json.loads(r.read()).get("models", [])}
    except (urllib.error.URLError, OSError):
        return []
    for m in models:
        mid = MODELS[m]["id"]
        if any(name == mid or name.startswith(mid + ":") for name in installed):
            alive.append(m)
        else:
            print(f"⚠ модель `{m}` ({mid}) не установлена — пропущена", file=sys.stderr)
    return alive


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("file", help="markdown-файл для проверки")
    ap.add_argument("--models", default="t-lite,yandex",
                    help="профиль моделей: t-lite,yandex (дефолт) | qwen,yandex")
    ap.add_argument("--limit", type=int, default=0, help="проверить только N абзацев")
    args = ap.parse_args()

    try:
        text = open(args.file, encoding="utf-8").read()
    except OSError as e:
        sys.exit(f"не читается {args.file}: {e}")

    models = [m.strip() for m in args.models.split(",") if m.strip() in MODELS]
    unknown = [m for m in args.models.split(",") if m.strip() not in MODELS]
    if unknown:
        print(f"⚠ неизвестные модели пропущены: {unknown}; доступны: {list(MODELS)}",
              file=sys.stderr)

    alive = check_alive(models)
    if not alive:
        print("\n## Локальный критик недоступен (ollama не запущена или модели не "
              "установлены) — шаг пропущен, работа не блокируется.")
        return

    paras = split_paragraphs(text)
    if args.limit:
        paras = paras[: args.limit]
    if not paras:
        print("\n## Локальный критик: прозаических абзацев не найдено — нечего проверять.")
        return

    # Батч по моделям (не по абзацам): в qwen-профиле модели не живут в памяти вместе
    results = {m: [] for m in alive}  # (абзац_idx, quote, replacement, matched)
    for m in alive:
        label = MODELS[m]["label"]
        for i, para in enumerate(paras):
            try:
                resp, dt = call_ollama(m, CRITIC_PROMPT.format(text=para))
            except Exception as e:  # noqa: BLE001 — любая сетевая/модельная беда
                print(f"⚠ {label}: сбой вызова ({e}) — модель пропущена", file=sys.stderr)
                break
            for q, rep in parse_suggestions(resp):
                ok = norm_quotes(q) in norm_quotes(para)
                results[m].append((i, q, rep, ok))

    # Отчёт
    print(f"\n## Локальный критик — {len(paras)} абз., модели: "
          f"{', '.join(MODELS[m]['label'] for m in alive)}\n")
    total_valid = 0
    for i, para in enumerate(paras):
        lines = []
        for m in alive:
            for (pi, q, rep, ok) in results[m]:
                if pi == i and ok:
                    lines.append(f"- «{q}» → «{rep}» *({MODELS[m]['label']})*")
                    total_valid += 1
        if lines:
            print(f"**Абзац {i + 1}**: «{para[:80]}…»\n")
            for ln in lines:
                print(ln)
            print()
    unmatched = [(MODELS[m]['label'], q, rep)
                 for m in alive for (_, q, rep, ok) in results[m] if not ok]
    if unmatched:
        print("**Не сопоставлено с текстом** (цитата не найдена дословно — не применять, "
              "разобрать глазами; возможна галлюцинация модели):\n")
        for label, q, rep in unmatched:
            print(f"- [{label}] «{q}» → «{rep}»")
        print()
    print(f"**Итог: {total_valid} валидных замен на {len(paras)} абзацев"
          + (f", {len(unmatched)} неспаренных" if unmatched else "")
          + ". Применение — за GLM по правилам references/local-critic.md "
            "(термины, цитаты, ссылки, код — не трогать).**")


if __name__ == "__main__":
    main()
