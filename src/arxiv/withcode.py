import arxivscraper
import datetime
import time
import requests
import json
from datetime import timedelta
import os
import pathlib
import yaml


def get_daily_code(DateToday, cats):
    """
    @param DateToday: str
    @param cats: dict
    @return paper_with_code: dict
    """
    from_day = until_day = DateToday
    content = dict()
    # content
    output = dict()
    for k, v in cats.items():
        scraper = arxivscraper.Scraper(
            category=k,
            date_from=from_day,
            date_until=until_day,
            filters={"categories": v},
        )
        tmp = scraper.scrape()
        print(tmp)
        if isinstance(tmp, list):
            for item in tmp:
                if item["id"] not in output:
                    output[item["id"]] = item
        time.sleep(30)

    base_url = "https://arxiv.paperswithcode.com/api/v0/papers/"
    cnt = 0

    for k, v in output.items():
        print(v["id"])
        _id = v["id"]
        paper_title = " ".join(v["title"].split())
        paper_url = v["url"]
        paper_date = v.get("published", DateToday)
        if isinstance(paper_date, datetime.datetime):
            paper_date = paper_date.strftime("%Y-%m-%d")
        url = base_url + _id
        try:
            r = requests.get(url).json()
            if "official" in r and r["official"]:
                cnt += 1
                repo_url = r["official"]["url"]
                repo_name = repo_url.split("/")[-1]

                content[_id] = {
                    "title": paper_title,
                    "paper_url": paper_url,
                    "repo_url": repo_url,
                    "repo_name": repo_name,
                    "date": paper_date,
                    "abstract": v.get("summary", ""),
                    "authors": ", ".join([author.name for author in v.get("authors", [])])
                }
        except Exception as e:
            print(f"exception: {e} with id: {_id}")
    data = {DateToday: content}
    return data


def update_daily_json(filename, data_all):
    with open(filename, "r") as f:
        content = f.read()
        if not content:
            m = {}
        else:
            m = json.loads(content)

    # 将datas更新到m中
    for data in data_all:
        m.update(data)

    # save data to daily.json
    with open(filename, "w") as f:
        json.dump(m, f)


def ensure_archive_dirs():
    """Create archive directory structure if it doesn't exist"""
    archive_base = "archives"
    current_year = datetime.date.today().year

    # Create base archives dir
    pathlib.Path(archive_base).mkdir(exist_ok=True)

    # Create directories for all years from 2021 to current year
    for year in range(2021, current_year + 1):
        year_dir = os.path.join(archive_base, str(year))
        pathlib.Path(year_dir).mkdir(exist_ok=True)

        # Create month directories if they don't exist
        for month in range(1, 13):
            month_file = os.path.join(year_dir, f"{month:02d}.md")
            if not os.path.exists(month_file):
                with open(month_file, "w") as f:
                    f.write(
                        f"# {datetime.date(year, month, 1).strftime('%B %Y')} Archive\n\n"
                    )

def build_frontmatter_appleblog(
    author, cover_image_url, description, keywords, pubdate, tags, title
):
    frontmatter = {
        "author": author,
        "cover": {
            "alt": "cover",
            "square": cover_image_url,
            "url": cover_image_url,
        },
        "description": description,
        "featured": True,
        "keywords": keywords,
        "layout": "../../layouts/MarkdownPost.astro",
        "meta": [
            {"content": author, "name": "author"},
            {"content": keywords, "name": "keywords"},
        ],
        "pubDate": pubdate,
        "tags": tags,
        "theme": "light",
        "title": title,
    }
    return yaml.dump(frontmatter, default_flow_style=False)


def json_to_md(filename):
    """
    Convert JSON data to markdown files with archives
    @param filename: str
    @return None
    """
    with open(filename, "r") as f:
        content = f.read()
        if not content:
            data = {}
        else:
            data = json.loads(content)

    # Ensure archive structure exists
    ensure_archive_dirs()

    # Group entries by year and month
    entries_by_month = {}
    latest_entries = []
    today = datetime.date.today()
    week_ago = today - timedelta(days=7)

    for day in sorted(data.keys(), reverse=True):
        day_date = datetime.datetime.strptime(day, "%Y-%m-%d").date()
        year_month = day_date.strftime("%Y/%m")

        # Collect entries for archives
        if day_date > week_ago:
            latest_entries.append((day, data[day]))

        if year_month not in entries_by_month:
            entries_by_month[year_month] = []
        entries_by_month[year_month].append((day, data[day]))

    # Update main README.md
    with open("README.md", "w", encoding="utf-8") as f:
        # Write header and overview
        f.write("# Daily ArXiv\n\n")
        f.write(
            "A curated collection of arXiv papers with open-source implementations, specifically focusing on Signal Processing (eess.SP) "
        )
        f.write(
            "and Information Theory (cs.IT) categories. This repository is designed to serve researchers and practitioners in information "
        )
        f.write(
            "and communication systems by providing easy access to papers that come with their source code implementations.\n\n"
        )

        f.write("## Overview\n")
        f.write(
            "This project automatically tracks and analyzes papers from eess.SP (Electrical Engineering and Systems Science - Signal Processing) "
        )
        f.write(
            "and cs.IT (Computer Science - Information Theory) categories on arXiv daily using GitHub Actions. It specifically identifies "
        )
        f.write(
            "and catalogs papers that have released their source code, making it easier for researchers in information and communication "
        )
        f.write("systems to find implementable research work.\n\n")

        f.write("The main features include:\n")
        f.write("- Daily updates of papers with open-source implementations\n")
        f.write("- Focus on signal processing and information theory research\n")
        f.write("- Automatic tracking and organization\n\n")

        # Write latest updates
        f.write("## Latest Updates \n")
        yymm = f"{str(today.year)[2:]}{today.month:02d}"
        f.write("|date|paper|code|\n" + "|---|---|---|\n")
        for day, day_content in latest_entries:
            if not day_content:
                continue
            for k, v in day_content.items():
                  if k.startswith(yymm):
                     title = v.get("title", "Unknown Paper")
                     paper_url = v.get("paper_url", "")
                     repo_name = v.get("repo_name", "no repo")
                     repo_url = v.get("repo_url","")
                     f.write(f"|{day}|[{title}]({paper_url})|[{repo_name}]({repo_url})|\n")
        f.write("\n")

        # Write archive links
        f.write("\n## Archives\n")
        for year_month in sorted(entries_by_month.keys(), reverse=True):
            year, month = year_month.split("/")
            month_name = datetime.date(int(year), int(month), 1).strftime("%B")
            f.write(f"- [{month_name} {year}](archives/{year}/{int(month):02d}.md)\n")

    # Update archive files
    for year_month, entries in entries_by_month.items():
        year, month = year_month.split("/")
        archive_file = f"archives/{year}/{int(month):02d}.md"
        with open(archive_file, "w", encoding="utf-8") as f:
           f.write(f"# {datetime.date(int(year), int(month), 1).strftime('%B %Y')} Archive\n\n")
           f.write("[Back to README](../../README.md)\n\n")
           f.write("|date|paper|code|\n" + "|---|---|---|\n")
           for day, day_content in entries:
                if not day_content:
                     continue
                for k,v in day_content.items():
                     title = v.get("title", "Unknown Paper")
                     paper_url = v.get("paper_url", "")
                     repo_name = v.get("repo_name", "no repo")
                     repo_url = v.get("repo_url", "")
                     f.write(f"|{day}|[{title}]({paper_url})|[{repo_name}]({repo_url})|\n")

           f.write("\n")

    print("Finished generating markdown files")


if __name__ == "__main__":
    DateToday = datetime.date.today()
    N = 7
    data_all = []
    for i in range(1, N):
        day = str(DateToday + timedelta(-i))
        # you can add the categories in cats
        cats = {"eess": ["eess.SP"], "cs": ["cs.IT"]}
        data = get_daily_code(day, cats)
        data_all.append(data)
    update_daily_json("daily.json", data_all)
    json_to_md("daily.json")
