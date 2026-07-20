# Nutritional Food Tracker (NutriTrack)

A Flask web app for tracking daily nutrition, macros, and goals. Built by Uptej Singh using Flask, SQLite, HTML5, and CSS3.

## Links

- **GitHub:** [https://github.com/UPTEJ-1/nutritional-food-tracker](https://github.com/UPTEJ-1/nutritional-food-tracker)
- **Trello board:** add your project board URL here (e.g. `https://trello.com/b/your-board-id`)

## Features

- Registration, login, logout (Flask-Login, hashed passwords)
- Live food search (SQL `LIKE` + JavaScript filter) with starred favourites
- Dashboard macro cards, colour-coded progress, meals grouped with subtotals
- Custom goals with server-side validation (min 500 kcal)
- 14-day history table, weekly average, Chart.js trends

## Project structure

```
nutritional-food-tracker/
├── app.py
├── database.py
├── models.py
├── requirements.txt
├── README.md
├── database/
│   └── nutrition_tracker.db   (created on first run)
├── static/
│   ├── css/style.css
│   └── js/
│       ├── log_food.js
│       └── history.js
└── templates/
    ├── base.html
    ├── dashboard.html
    ├── log_food.html
    ├── history.html
    ├── goals.html
    ├── login.html
    ├── register.html
    └── profile.html
```

Food nutrition values are seeded from USDA FoodData Central (per 100 g).

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Open [http://127.0.0.1:5000](http://127.0.0.1:5000).

Optional manual DB init: `python database.py`

## Configuration

- Set `SECRET_KEY` in the environment for production.
- SQLite file path: `database/nutrition_tracker.db`

## Quality checks

- `pycodestyle app.py models.py database.py` (PEP 8 style)
- Tested in Firefox; responsive breakpoints at 768px and 480px

## Out of scope (by design)

- Custom food submission form (users contact the developer to add catalog items)
