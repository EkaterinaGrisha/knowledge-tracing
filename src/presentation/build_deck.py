"""Generate the project presentation (presentation.pptx) from pipeline outputs.

Reads reports/metrics.json + reports/figures/*.png and builds a 5-7 slide deck
covering: business task, data & features, ML-system architecture, test results,
and business conclusions. Run after the pipeline:  python -m src.presentation.build_deck
"""

from __future__ import annotations

import json

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.util import Inches, Pt

from ..utils import get_logger, resolve

LOG = get_logger()

NAVY = RGBColor(0x1F, 0x2D, 0x5A)
BLUE = RGBColor(0x4C, 0x72, 0xB0)
GREY = RGBColor(0x55, 0x55, 0x55)


def _load_metrics() -> dict:
    path = resolve("reports/metrics.json")
    if not path.exists():
        raise FileNotFoundError("reports/metrics.json not found — run the pipeline first.")
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _title_slide(prs: Presentation) -> None:
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    box = slide.shapes.add_textbox(Inches(0.7), Inches(2.2), Inches(12), Inches(2.5))
    tf = box.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    r = p.add_run()
    r.text = "Автоматизация ML-пайплайна"
    r.font.size = Pt(44)
    r.font.bold = True
    r.font.color.rgb = NAVY
    p2 = tf.add_paragraph()
    r2 = p2.add_run()
    r2.text = "Knowledge Tracing на датасете ASSISTments 2009\nBKT · DKT+Optuna · AutoML (FLAML)"
    r2.font.size = Pt(22)
    r2.font.color.rgb = GREY


def _bullets_slide(prs: Presentation, title: str, bullets: list[str], image: str | None = None) -> None:
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    t = slide.shapes.add_textbox(Inches(0.6), Inches(0.4), Inches(12), Inches(1))
    tr = t.text_frame.paragraphs[0].add_run()
    tr.text = title
    tr.font.size = Pt(32)
    tr.font.bold = True
    tr.font.color.rgb = NAVY

    text_w = Inches(6.2) if image else Inches(12)
    body = slide.shapes.add_textbox(Inches(0.7), Inches(1.5), text_w, Inches(5.5))
    tf = body.text_frame
    tf.word_wrap = True
    for i, b in enumerate(bullets):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        run = p.add_run()
        run.text = "•  " + b
        run.font.size = Pt(18)
        p.space_after = Pt(8)

    if image:
        img_path = resolve(f"reports/figures/{image}")
        if img_path.exists():
            slide.shapes.add_picture(str(img_path), Inches(7.1), Inches(1.5), width=Inches(5.8))


def _results_slide(prs: Presentation, metrics: dict) -> None:
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    t = slide.shapes.add_textbox(Inches(0.6), Inches(0.4), Inches(12), Inches(1))
    tr = t.text_frame.paragraphs[0].add_run()
    tr.text = "Результаты тестирования модели"
    tr.font.size = Pt(32)
    tr.font.bold = True
    tr.font.color.rgb = NAVY

    results = metrics["results"]
    rows = len(results) + 1
    table = slide.shapes.add_table(rows, 5, Inches(0.7), Inches(1.6), Inches(6.0), Inches(0.4 * rows)).table
    headers = ["Модель", "AUC", "Accuracy", "F1", "RMSE"]
    for j, h in enumerate(headers):
        cell = table.cell(0, j)
        cell.text = h
        cell.text_frame.paragraphs[0].runs[0].font.bold = True
        cell.text_frame.paragraphs[0].runs[0].font.size = Pt(13)
    for i, (name, m) in enumerate(results.items(), start=1):
        vals = [name, f"{m['auc']:.3f}", f"{m['accuracy']:.3f}", f"{m['f1']:.3f}", f"{m['rmse']:.3f}"]
        for j, v in enumerate(vals):
            cell = table.cell(i, j)
            cell.text = v
            cell.text_frame.paragraphs[0].runs[0].font.size = Pt(12)

    img = resolve("reports/figures/model_comparison.png")
    if img.exists():
        slide.shapes.add_picture(str(img), Inches(7.0), Inches(1.6), width=Inches(6.0))

    note = slide.shapes.add_textbox(Inches(0.7), Inches(1.7 + 0.4 * rows), Inches(6.0), Inches(1.2))
    nr = note.text_frame.paragraphs[0].add_run()
    nr.text = f"Лучшая модель: {metrics['best_model']} · AutoML выбрал: {metrics['automl_best_estimator']}"
    nr.font.size = Pt(14)
    nr.font.color.rgb = BLUE
    nr.font.bold = True


def build(output: str = "presentation/presentation.pptx") -> str:
    metrics = _load_metrics()
    ds = metrics["dataset"]
    results = metrics["results"]
    best = metrics["best_model"]
    best_auc = results[best]["auc"]

    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)

    # 1. Title
    _title_slide(prs)

    # 2. Business task
    _bullets_slide(
        prs,
        "Бизнес-задача",
        [
            "Ключевой вопрос: ответит ли студент верно на следующую задачу по навыку?",
            "Зачем: точный прогноз знаний → адаптивные рекомендации (что учить, что повторить).",
            "Эффект: меньше отвала и фрустрации, выше завершаемость курса.",
            "Тип задачи: бинарная классификация на временных рядах (knowledge tracing).",
            "Метрика успеха: ROC-AUC прогноза следующего ответа.",
        ],
    )

    # 3. Data & features
    _bullets_slide(
        prs,
        "Данные и признаки",
        [
            "Датасет: публичный ASSISTments 2009 (skill-builder) — стандартный бенчмарк KT.",
            f"Объём: {ds['n_students']} студентов, {ds['n_interactions']} взаимодействий, {ds['n_skills']} навыков.",
            "Сырьё: (студент, навык, верно/неверно) в хронологическом порядке.",
            "Причинные признаки: прошлая доля верных у студента и по навыку,",
            "номер попытки, сложность навыка, скользящая успешность за 3 шага.",
            "Сплит по студентам (без утечки между train/val/test).",
        ],
        image="dataset_overview.png",
    )

    # 4. ML system architecture
    _bullets_slide(
        prs,
        "Архитектура ML-системы",
        [
            "ETL: Extract (загрузка/кэш) → Transform (очистка, признаки, сплит) → Load (parquet).",
            "Модели: BKT (байесовский baseline), DKT (LSTM),",
            "DKT+Optuna (автопоиск архитектуры), AutoML FLAML (выбор модели+гиперпараметров).",
            "Контейнеризация: Docker (slim, non-root); оркестрация — единый pipeline.py.",
            "CI/CD: GitHub Actions (lint + pytest + docker build + smoke-run).",
            "Мониторинг: MLflow (метрики/артефакты), PSI-дрейф, контроль качества данных, ресурсы.",
        ],
    )

    # 5. Results
    _results_slide(prs, metrics)

    # 6. Conclusions
    _bullets_slide(
        prs,
        "Ключевые выводы для бизнеса",
        [
            f"Лучшая модель — {best}: AUC = {best_auc:.3f} на отложенной выборке.",
            "Глубокие модели (DKT) превосходят классический BKT на реальных данных.",
            "AutoML/Optuna автоматизируют подбор модели → быстрее итерации, меньше ручного труда.",
            "Прогноз даёт основу для адаптивных рекомендаций и раннего выявления пробелов.",
            "Пайплайн воспроизводим (Docker+CI) и наблюдаем (MLflow+дрейф) — готов к развитию.",
        ],
    )

    out = resolve(output)
    out.parent.mkdir(parents=True, exist_ok=True)
    prs.save(str(out))
    LOG.info("Presentation saved -> %s (%d slides)", out, len(prs.slides._sldIdLst))
    return str(out)


if __name__ == "__main__":
    build()
