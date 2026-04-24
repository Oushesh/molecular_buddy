"""
Utility functions for molecule fingerprinting and vector similarity search.

Uses RDKit for generating Morgan fingerprints (circular fingerprints) and
ChromaDB for persistent vector storage and similarity retrieval.
"""

from __future__ import annotations

import io
import base64
import logging
from typing import Optional

import numpy as np
from django.conf import settings

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# RDKit helpers
# ---------------------------------------------------------------------------

def smiles_to_fingerprint(smiles: str, radius: int = 2, n_bits: int = 2048) -> Optional[list[int]]:
    """Convert a SMILES string to a Morgan fingerprint bit vector.

    Args:
        smiles: SMILES representation of the molecule.
        radius: Morgan algorithm radius (2 ≈ ECFP4).
        n_bits: Length of the bit vector.

    Returns:
        A list of integers (0/1) of length ``n_bits``, or ``None`` if the
        SMILES string is invalid.
    """
    try:
        from rdkit import Chem
        from rdkit.Chem import rdFingerprintGenerator

        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return None
        gen = rdFingerprintGenerator.GetMorganGenerator(radius=radius, fpSize=n_bits)
        fp = gen.GetFingerprintAsNumPy(mol)
        return fp.tolist()
    except Exception as exc:
        logger.error("Error generating fingerprint for '%s': %s", smiles, exc)
        return None


def smiles_to_image_base64(smiles: str, size: tuple[int, int] = (300, 200)) -> Optional[str]:
    """Render a SMILES string to a PNG image and return it as a base-64 string.

    Returns ``None`` if the SMILES is invalid or rendering fails.
    """
    try:
        from rdkit import Chem
        from rdkit.Chem import Draw

        mol = Chem.MolFromSmiles(smiles)
        if mol is None:
            return None
        img = Draw.MolToImage(mol, size=size)
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        return base64.b64encode(buffer.getvalue()).decode("utf-8")
    except Exception as exc:
        logger.error("Error rendering molecule '%s': %s", smiles, exc)
        return None


def tanimoto_similarity(fp1: list[int], fp2: list[int]) -> float:
    """Compute the Tanimoto (Jaccard) similarity between two bit fingerprints."""
    a = np.array(fp1, dtype=np.uint8)
    b = np.array(fp2, dtype=np.uint8)
    intersection = int(np.bitwise_and(a, b).sum())
    union = int(np.bitwise_or(a, b).sum())
    return intersection / union if union > 0 else 0.0


# ---------------------------------------------------------------------------
# ChromaDB vector store helpers
# ---------------------------------------------------------------------------

_chroma_client = None
_collection = None

COLLECTION_NAME = "molecules"


def _get_collection():
    """Return (and lazily create) the ChromaDB collection."""
    global _chroma_client, _collection
    if _collection is not None:
        return _collection

    import chromadb

    db_path = str(getattr(settings, "CHROMA_DB_PATH", "./chroma_db"))
    _chroma_client = chromadb.PersistentClient(path=db_path)
    _collection = _chroma_client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )
    return _collection


def upsert_molecule(molecule_id: int, smiles: str, name: str, description: str = "") -> bool:
    """Add or update a molecule in the ChromaDB vector store.

    Returns ``True`` on success, ``False`` if the fingerprint could not be
    generated (invalid SMILES).
    """
    fp = smiles_to_fingerprint(smiles)
    if fp is None:
        return False

    collection = _get_collection()
    collection.upsert(
        ids=[str(molecule_id)],
        embeddings=[fp],
        metadatas=[{"name": name, "smiles": smiles, "description": description}],
    )
    return True


def delete_molecule(molecule_id: int) -> None:
    """Remove a molecule from the ChromaDB vector store."""
    try:
        collection = _get_collection()
        collection.delete(ids=[str(molecule_id)])
    except Exception as exc:
        logger.warning("Could not delete molecule %s from ChromaDB: %s", molecule_id, exc)


def search_similar_molecules(
    query_smiles: str,
    n_results: int = 5,
) -> list[dict]:
    """Search for molecules similar to ``query_smiles`` using cosine distance.

    Returns a list of dicts with keys: ``id``, ``name``, ``smiles``,
    ``description``, ``similarity`` (Tanimoto score).
    """
    query_fp = smiles_to_fingerprint(query_smiles)
    if query_fp is None:
        return []

    collection = _get_collection()
    total = collection.count()
    if total == 0:
        return []

    n_results = min(n_results, total)
    results = collection.query(
        query_embeddings=[query_fp],
        n_results=n_results,
        include=["metadatas", "embeddings", "distances"],
    )

    hits = []
    for i, doc_id in enumerate(results["ids"][0]):
        meta = results["metadatas"][0][i]
        stored_fp = results["embeddings"][0][i]
        similarity = tanimoto_similarity(query_fp, [int(x) for x in stored_fp])
        hits.append(
            {
                "id": int(doc_id),
                "name": meta.get("name", ""),
                "smiles": meta.get("smiles", ""),
                "description": meta.get("description", ""),
                "similarity": round(similarity, 4),
            }
        )

    # Sort by Tanimoto similarity descending
    hits.sort(key=lambda x: x["similarity"], reverse=True)
    return hits
