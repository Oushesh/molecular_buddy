# Molecular Buddy – Rust Backend

This folder will contain the **Rust** translation of the Django app in `../django/`.

## Framework: [Axum](https://github.com/tokio-rs/axum)

Axum was chosen for its simplicity, ergonomic API, and tight integration with the Tokio async ecosystem.

### Planned Endpoints (mirror of the Django app)

| Method | Path | Description |
|--------|------|-------------|
| `GET`  | `/` | List all molecules |
| `GET`  | `/molecules/:id` | Molecule detail |
| `POST` | `/molecules` | Add a new molecule (JSON body: `name`, `smiles`, `description`) |
| `DELETE` | `/molecules/:id` | Delete a molecule |
| `POST` | `/search` | Find similar molecules (JSON body: `smiles`, `n_results`) |
| `GET`  | `/api/validate-smiles?smiles=...` | Validate a SMILES string |

### Key Crates (planned)

| Crate | Purpose |
|-------|---------|
| `axum` | Web framework |
| `tokio` | Async runtime |
| `serde` / `serde_json` | JSON serialisation |
| `sqlx` | SQLite database |
| `rdkit` or `chemcore` | Molecular fingerprints |
| `qdrant-client` | Vector store (replaces ChromaDB) |

---

> 🔄 Translation in progress – see `../django/` for the reference implementation.
