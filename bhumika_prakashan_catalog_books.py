import argparse
import csv
import logging
import os
import re
import time
from dataclasses import dataclass
from typing import Dict, Iterable, List, Optional, Tuple

import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class BookRecord:
    ebook_id: int
    title: str
    grade: Optional[int]


def fetch_html(ebook_id: int, session: requests.Session, timeout_s: int = 10) -> Tuple[Optional[str], int]:
    url = f"https://bhumikaprakashan.com/myebook2/{ebook_id}"
    headers = {"User-Agent": "Mozilla/5.0"}

    try:
        resp = session.get(url, headers=headers, timeout=timeout_s)
        return resp.text if resp.status_code == 200 else None, resp.status_code
    except Exception as e:
        logger.warning(f"Request failed for id={ebook_id}: {e}")
        return None, 0


def extract_title_from_html(html: str, ebook_id: int) -> str:
    meta_desc_match = re.search(
        r"<meta[^>]*name=[\"\']Description[\"\'][^>]*content=[\"\']([^\"\']+)[\"\']",
        html,
        re.IGNORECASE,
    )
    if meta_desc_match:
        return meta_desc_match.group(1).strip()

    title_match = re.search(r"<title>(.*?)</title>", html, re.IGNORECASE)
    if title_match:
        book_title = title_match.group(1).strip()
        book_title = re.sub(r"\s*-\s*.*$", "", book_title)
        book_title = re.sub(r"^[^\w]*", "", book_title)
        book_title = re.sub(r"[^\w\s-]", "", book_title)
        book_title = book_title.strip()
        if book_title:
            return book_title

    name_patterns = [
        r"bookTitle\s*[:=]\s*[\"\']([^\"\']+)[\"\']",
        r"title\s*[:=]\s*[\"\']([^\"\']+)[\"\']",
        r"<h1[^>]*>(.*?)</h1>",
        r"<h2[^>]*>(.*?)</h2>",
    ]
    for pattern in name_patterns:
        match = re.search(pattern, html, re.IGNORECASE)
        if match:
            book_title = match.group(1).strip()
            book_title = re.sub(r"[^\w\s-]", "", book_title)
            book_title = book_title.strip()
            if book_title:
                return book_title

    return f"Ebook_{ebook_id}"


_GRADE_PATTERNS: List[re.Pattern] = [
    re.compile(r"\bclass\s*(\d{1,2})\b", re.IGNORECASE),
    re.compile(r"\bgrade\s*(\d{1,2})\b", re.IGNORECASE),
    re.compile(r"\bstd\.?\s*(\d{1,2})\b", re.IGNORECASE),
    re.compile(r"\bstandard\s*(\d{1,2})\b", re.IGNORECASE),
    re.compile(r"\b(\d{1,2})\s*(?:th|st|nd|rd)\s*class\b", re.IGNORECASE),
    re.compile(r"\b(\d{1,2})\s*(?:th|st|nd|rd)\s*grade\b", re.IGNORECASE),
    re.compile(r"-(\d{1,2})\b", re.IGNORECASE),  # titles ending with -5, -10, etc.
]


def infer_grade_from_title(title: str) -> Optional[int]:
    for pat in _GRADE_PATTERNS:
        m = pat.search(title)
        if not m:
            continue
        try:
            g = int(m.group(1))
        except Exception:
            continue
        if 1 <= g <= 12:
            return g
    return None


def crawl_books(
    start_id: int,
    max_id: int,
    delay_s: float,
    stop_after_misses: int,
    timeout_s: int,
) -> List[BookRecord]:
    records: List[BookRecord] = []
    misses = 0

    with requests.Session() as session:
        for ebook_id in range(start_id, max_id + 1):
            html, status = fetch_html(ebook_id, session=session, timeout_s=timeout_s)

            if html is None:
                misses += 1
                logger.info(f"id={ebook_id}: missing (status={status}); misses={misses}/{stop_after_misses}")
                if misses >= stop_after_misses:
                    logger.info("Stopping crawl due to consecutive misses threshold.")
                    break
            else:
                misses = 0
                title = extract_title_from_html(html, ebook_id)
                grade = infer_grade_from_title(title)
                logger.info(f"id={ebook_id}: title=\"{title}\" grade={grade}")
                records.append(BookRecord(ebook_id=ebook_id, title=title, grade=grade))

            if delay_s > 0:
                time.sleep(delay_s)

    return records


def _safe_filename(s: str) -> str:
    s = s.strip().lower()
    s = re.sub(r"\s+", "_", s)
    s = re.sub(r"[^a-z0-9_\-]", "", s)
    return s or "output"


def write_all_books_csv(records: Iterable[BookRecord], out_dir: str) -> str:
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "all_books.csv")

    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["ebook_id", "title", "grade"])
        for r in records:
            w.writerow([r.ebook_id, r.title, "" if r.grade is None else r.grade])

    return path


def group_by_grade(records: Iterable[BookRecord]) -> Dict[str, List[BookRecord]]:
    grouped: Dict[str, List[BookRecord]] = {}
    for r in records:
        key = f"Grade {r.grade}" if r.grade is not None else "Uncategorized"
        grouped.setdefault(key, []).append(r)

    for k in grouped:
        grouped[k].sort(key=lambda x: x.ebook_id)

    return grouped


def write_grade_csvs(grouped: Dict[str, List[BookRecord]], out_dir: str) -> List[str]:
    os.makedirs(out_dir, exist_ok=True)
    paths: List[str] = []

    for grade_label, items in grouped.items():
        filename = f"{_safe_filename(grade_label)}.csv"
        path = os.path.join(out_dir, filename)

        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["ebook_id", "title"])
            for r in items:
                w.writerow([r.ebook_id, r.title])

        paths.append(path)

    return paths


def write_markdown_report(grouped: Dict[str, List[BookRecord]], out_dir: str) -> str:
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "books_by_grade.md")

    with open(path, "w", encoding="utf-8") as f:
        for grade_label in sorted(
            grouped.keys(),
            key=lambda k: (999 if k == "Uncategorized" else int(re.search(r"\d+", k).group(0))),
        ):
            f.write(f"# {grade_label}\n\n")
            f.write("| Ebook ID | Title |\n")
            f.write("|---:|---|\n")
            for r in grouped[grade_label]:
                title = r.title.replace("|", "\\|")
                f.write(f"| {r.ebook_id} | {title} |\n")
            f.write("\n")

    return path


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Crawl Bhumika Prakashan flipbooks and output grade-wise tables (based on title patterns)."
    )
    p.add_argument("--start-id", type=int, default=1)
    p.add_argument("--max-id", type=int, default=2000)
    p.add_argument("--delay", type=float, default=0.2)
    p.add_argument("--stop-after-misses", type=int, default=30)
    p.add_argument("--timeout", type=int, default=10)
    p.add_argument("--out", type=str, default="catalog_output")
    p.add_argument("--only-grade", type=int, default=None)
    return p.parse_args()


def main() -> None:
    args = parse_args()

    records = crawl_books(
        start_id=args.start_id,
        max_id=args.max_id,
        delay_s=args.delay,
        stop_after_misses=args.stop_after_misses,
        timeout_s=args.timeout,
    )

    if args.only_grade is not None:
        records = [r for r in records if r.grade == args.only_grade]

    all_csv = write_all_books_csv(records, args.out)
    grouped = group_by_grade(records)
    grade_csvs = write_grade_csvs(grouped, args.out)
    report = write_markdown_report(grouped, args.out)

    logger.info(f"Wrote: {all_csv}")
    logger.info(f"Wrote: {report}")
    logger.info(f"Wrote {len(grade_csvs)} grade CSV files into: {args.out}")


if __name__ == "__main__":
    main()
