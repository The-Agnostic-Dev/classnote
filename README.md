# Classnote

Classnote is the notice board and report card system for Greenfield Model College.

- **Notice board** (public): notices for the whole school or for specific classes,
  pinned notices on top, and expiry dates so old notices drop off by themselves.
- **Teacher area** (login): post, edit and take down notices; enter CA and exam
  scores per class and subject; view class results with averages, grades and
  positions; open a printable report card for every student.

## Stack

- Python 3.13, Django 5.2 (server-rendered templates, no frontend build step)
- SQLite
- Gunicorn + WhiteNoise in the container
- Tests: Django's test runner

## Running locally

```bash
python3.13 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo          # resets the demo school; dates are relative to today
python manage.py runserver 0.0.0.0:5106
```

Open http://localhost:5106.

### Demo accounts

All demo accounts use the password `classnote2026`.

| Username | Who | Notes |
| -------- | --- | ----- |
| `mrs.adeyemi` | Funke Adeyemi | Class teacher, JSS 1A |
| `mr.okafor` | Chinedu Okafor | Class teacher, JSS 2B |
| `principal` | Grace Bassey | Also has Django admin access at `/admin/` |

## Docker

```bash
docker compose up --build
```

The app is served on http://localhost:5106. The container runs migrations and
reloads the demo data on every start (set `CLASSNOTE_SEED_DEMO=0` to keep data).

## Tests

```bash
python manage.py test
```

## Project layout

```
classnote/        settings and root URLs
notices/          notice board: models, forms, views, board caching (services.py)
reports/          classes, students, subjects, terms, scores
  services.py     grades, averages and class positions
  signals.py      keeps Score.total in step with CA + exam
  management/commands/seed_demo.py
templates/        Django templates (base layout, notices, reports, login)
static/           CSS and favicon
```

## Grading rules

Scores are CA out of 40 plus exam out of 60. Grades:

| Total | Grade | Remark |
| ----- | ----- | ------ |
| 70 to 100 | A | Excellent |
| 60 to 69 | B | Very good |
| 50 to 59 | C | Good |
| 45 to 49 | D | Fair |
| 40 to 44 | E | Pass |
| 0 to 39 | F | Fail |

A student's term average is the mean of their subject totals, to one decimal place.
Class position ranks students by term average; equal averages share a position
(1st, 2nd, 2nd, 4th).

## Notice board rules

- Notices with no classes ticked go to the whole school and appear under every class filter.
- A notice stays up until the end of its expiry day.
- The board is cached for a few minutes; posting, editing or taking down a notice refreshes it.
