import os
import json
import locale
import argparse

from datetime import date
from typing import List, Dict, Any, Optional

import yaml

from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML
from weasyprint.text.fonts import FontConfiguration


PLACES_PATH = "./data/places"
SCHEDULES_PATH = "./data/schedules"
TEMPLATES_PATH = "./templates"
TARGET_DIR = "./gen"
env = Environment(loader=FileSystemLoader(TEMPLATES_PATH))


def load_yaml_file(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as file:
        file_data = yaml.load(file.read(), Loader=yaml.Loader)
        return file_data


def load_json_file(path: str) -> Any:
    with open(path, "r", encoding="utf-8") as file:
        file_data = json.loads(file.read())
        return file_data


def get_options(path: str) -> List[str]:
    return [f.rstrip(".yaml") for f in os.listdir(path)]


def render_template(template: str, context: Dict[str, Any]) -> Any:
    return env.get_template(template).render(context)


def render_pdf(
        path: str, ctx: Dict[str, Any], name: Optional[str] = None) -> None:
    template_dir = path.rsplit('/', 1)[0]
    target_name = name if name is not None else template_dir
    HTML(
        string=render_template(path, ctx),
        base_url=f"{TEMPLATES_PATH}/{template_dir}"
    ).write_pdf(f"{TARGET_DIR}/{target_name}.pdf")


def main() -> None:
    places_list = get_options(PLACES_PATH)
    schedules = get_options(SCHEDULES_PATH)
    today = date.today()
    edition = today.year if today.month <= 3 else today.year + 1

    parser = argparse.ArgumentParser(
        description="Zosia-print - generates printables based on the HTML "
                    "templates and data from Zosia website.")
    parser.add_argument('--place', choices=places_list, required=True,
                        help="Name of the place where Zosia will be held.")
    parser.add_argument('--schedule', choices=schedules, default=edition,
                        help="Name of file with schedule for this year.")
    parser.add_argument('--data', default='data.json', help="Path to JSON file"
                        "generated by Zosia website.")
    args = parser.parse_args()
    print(args)

    schedule = load_yaml_file(f"{SCHEDULES_PATH}/{args.schedule}.yaml")
    place = load_yaml_file(f"{PLACES_PATH}/{args.place}.yaml")
    data = load_json_file(args.data)

    # TODO: Validate data
    # TODO: Load information about highlighted organizations
    # and contacts to organizers

    # Make sure that target directory exist
    os.makedirs(TARGET_DIR, exist_ok=True)

    # Enforce polish locale to generate proper month name
    locale.setlocale(locale.LC_ALL, 'pl_PL.utf8')
    start_date = date.fromisoformat(data["zosia"]["start_date"])
    end_date = date.fromisoformat(data["zosia"]["end_date"])
    zosia_date = f"{start_date:%-d} - {end_date:%-d %B %Y}"
    if start_date.month != end_date.month:
        zosia_date = f"{start_date:%-d %B} - {end_date:%-d %B %Y}"

    contacts = {
      "Aneta Kos": "111 222 333",
      "Jan Kowalski": "222 333 444",
      "Bartosz Kurek": "123 456 789",
    }

    # TODO: Render day-by-day schedule:
    days_schedule = []

    # Book
    render_pdf("book/book_template.html", {
        "days": days_schedule,
        "place": place,
        "contacts": contacts,
        "camp_date": zosia_date
    })

    # Schedule
    render_pdf("schedule/schedule_template.html", {
        "days": days_schedule
    })

    # Web schedule for zosia-site
    with open(f"{TARGET_DIR}/web_schedule.html", "w", encoding="utf-8") as file:
        file.write(render_template(
            "schedule/web_schedule_template.html", {
                "days": days_schedule
            }))

    # Identifier
    render_pdf("identifier/identifier_template.html", {
        "prefs": [],
        "camp_date": zosia_date
    })


if __name__ == "__main__":
    main()
