# Molecular Buddy – Django App

A Django web application for **vector search on molecules**. It stores molecular structures as [Morgan fingerprints](https://www.rdkit.org/docs/GettingStartedInPython.html#morgan-algorithm-circular-fingerprints) (ECFP4, 2048-bit) in a [ChromaDB](https://www.trychroma.com/) vector database and lets you find structurally similar molecules using **Tanimoto similarity**.

> Inspired by: *"I Tried Vector Search on Molecules, Here's What Happened"* – Towards AI

---

## Features

- 🧬 **Add molecules** by SMILES string with live validation and structure preview
- 🔍 **Similarity search** – query any SMILES and get the top-N most similar molecules from the library
- 📊 **Tanimoto scores** displayed with colour-coded badges (high / medium / low)
- 🖼️ **2D structure rendering** using RDKit's drawing module
- 🗄️ **ChromaDB** for persistent vector storage (no external service required)
- 🌐 Django admin interface at `/admin/`

---

## Tech Stack

| Layer | Tool |
|---|---|
| Web framework | Django 6 |
| Molecular fingerprints | RDKit |
| Vector database | ChromaDB (persistent, local) |
| Package manager | **uv** |
| Database | SQLite (default) |

---

## Quickstart (with `uv`)

```bash

# 1- Go the root folder
cd django
# 2 – Install uv (if not already installed)
pip install uv

# 3 – Install dependencies
uv sync

# 4 – Run database migrations
uv run python manage.py migrate

# 5 – (Optional) Seed with sample molecules
uv run python manage.py seed_molecules

# 6 – Start the development server
uv run python manage.py runserver
```

Then open http://127.0.0.1:8000/ in your browser.

---

## Project Layout

```
django/
├── pyproject.toml          # uv / PEP 517 project metadata & dependencies
├── uv.lock                 # Locked dependency tree
├── manage.py               # Django management entry-point
├── molecular_buddy/        # Django project settings & URL config
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
└── molecules/              # Main Django app
    ├── models.py           # Molecule model (SQLite)
    ├── views.py            # Index, Add, Search, Detail, Delete, AJAX
    ├── urls.py
    ├── admin.py
    ├── utils.py            # RDKit fingerprinting + ChromaDB helpers
    ├── management/
    │   └── commands/
    │       └── seed_molecules.py
    └── templates/
        └── molecules/
            ├── base.html
            ├── index.html  # Molecule library
            ├── add.html    # Add molecule form
            ├── search.html # Similarity search
            └── detail.html # Molecule detail page
```

---

## How It Works

1. **Fingerprinting** – Each molecule's SMILES is converted to a 2048-bit Morgan fingerprint (radius 2, equivalent to ECFP4) using RDKit.
2. **Indexing** – The fingerprint vector is stored in ChromaDB (cosine-distance HNSW index) alongside the molecule's metadata.
3. **Searching** – A query SMILES is fingerprinted, sent to ChromaDB for approximate nearest-neighbour retrieval, then re-ranked by Tanimoto similarity for accuracy.

---

## Notes

- The ChromaDB data is stored in `chroma_db/` inside the project directory.
- The SQLite database is stored as `db.sqlite3`.
- `rdkit` requires Python >= 3.10.
