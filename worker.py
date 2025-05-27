# worker.py

import time
import json
import hashlib
import feedparser
import requests
from bs4 import BeautifulSoup
from transformers import pipeline
from storage import (
    init_db, add_source, get_all_sources, update_last_checked,
    add_news, get_unqueued_news, enqueue, update_news_topics_and_summary
)
from config import DB_PATH

# 1) Ініціалізація БД та завантаження джерел
def load_sources():
    with open("sources.json", encoding="utf-8") as f:
        sources = json.load(f)
    for s in sources:
        add_source(s["type"], s["url"])

# 2) Інстанції NLP-пайплайнів
classifier = pipeline(
    "zero-shot-classification",
    model="MoritzLaurer/mDeBERTa-v3-base-xnli",
    device=-1,
    multi_label=True
)
summarizer = pipeline("summarization", model="t5-small", tokenizer="t5-small")
translator = pipeline(
    "translation_en_to_uk",
    model="Helsinki-NLP/opus-mt-en-uk"
)

# 3) Список тем (англ.)
with open("topics_list.json", encoding="utf-8") as f:
    TOPICS = json.load(f)
LOWBANK_TOPICS = TOPICS["lowbank"]
GENERAL_TOPICS = TOPICS["general"]

THRESHOLD = 0.5      # score ≥50% вважаємо релевантним
OTHER_THRESHOLD = 0.4

# 4) Функції завантаження новин
def fetch_rss(url):
    d = feedparser.parse(url)
    entries = []
    for e in d.entries:
        published = (
            int(time.mktime(e.published_parsed))
            if hasattr(e, "published_parsed") else int(time.time())
        )
        entries.append({
            "url": e.link,
            "title": e.title,
            "content": getattr(e, "summary", ""),
            "published": published
        })
    return entries

def fetch_html(url):
    r = requests.get(url, timeout=10)
    soup = BeautifulSoup(r.text, "html.parser")
    title = soup.title.string if soup.title else url
    # Найпростіший екстрактор — перші <p>
    paras = soup.find_all("p")
    content = "\n".join(p.get_text() for p in paras[:3])
    return [{"url": url, "title": title, "content": content, "published": int(time.time())}]

FETCHERS = {
    "rss": fetch_rss,
    "html": fetch_html,  # для випадків, коли в джерелі вказано html
    # telegram/twitter/reddit/discord/youtube — можна впровадити через API пізніше
}

# 5) Основний конвеєр обробки
def process_sources():
    for src in get_all_sources():
        fetcher = FETCHERS.get(src["type"])
        if not fetcher:
            continue  # поки підтримуємо лише rss/html
        try:
            entries = fetcher(src["url"])
        except Exception as e:
            print(f"[ERROR] fetching {src['url']}: {e}")
            continue

        now = int(time.time())
        for e in entries:
            url = e["url"]
            hash_str = hashlib.sha256(url.encode()).hexdigest()
            add_news(
                src["id"], url, e["title"], e["content"],
                e["published"], [], hash_str
            )
        update_last_checked(src["id"], now)

def classify_and_enqueue():
    unqueued = get_unqueued_news()
    for item in unqueued:
        text = item["title"] + ". " + item["summary"]
        # 1) Класифікація тем
        res = classifier(text, candidate_labels=LOWBANK_TOPICS + GENERAL_TOPICS + ["Other"])
        labels, scores = res["labels"], res["scores"]
        selected = [
            lbl for lbl, sc in zip(labels, scores)
            if sc >= THRESHOLD
        ]
        if not selected and max(scores) >= OTHER_THRESHOLD:
            selected = ["Other"]

        # 2) Стискання англійською
        summ = summarizer(text, max_length=60, min_length=25)[0]["summary_text"]

        # 3) Переклад на українську
        summ_uk = translator(summ)[0]["translation_text"]

        # 4) Оновлення новини
        update_news_topics_and_summary(item["id"], summ_uk, selected)

        # 5) Додавання в чергу для обох дайджестів, якщо підходить
        if any(t in LOWBANK_TOPICS for t in selected):
            enqueue(item["id"], "lowbank")
        if any(t in GENERAL_TOPICS for t in selected) or selected == ["Other"]:
            enqueue(item["id"], "general")

def main():
    # 1) Ініціалізація схеми БД + джерел
    init_db()
    load_sources()

    # 2) Збір новин та збереження в БД
    process_sources()

    # 3) Класифікація, сумаризація, переклад і черга
    classify_and_enqueue()

if __name__ == "__main__":
    main()
