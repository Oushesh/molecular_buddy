from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from .models import Molecule
from .utils import (
    upsert_molecule,
    delete_molecule,
    search_similar_molecules,
    smiles_to_image_base64,
    smiles_to_fingerprint,
)

# ---------------------------------------------------------------------------
# Molecule list / home
# ---------------------------------------------------------------------------


def index(request):
    """Home page – lists all stored molecules."""
    molecules = Molecule.objects.all()
    molecules_with_images = []
    for mol in molecules:
        img = smiles_to_image_base64(mol.smiles, size=(200, 140))
        molecules_with_images.append({"molecule": mol, "image": img})
    return render(request, "molecules/index.html", {"molecules": molecules_with_images})


# ---------------------------------------------------------------------------
# Add molecule
# ---------------------------------------------------------------------------


def add_molecule(request):
    """Form to add a new molecule."""
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        smiles = request.POST.get("smiles", "").strip()
        description = request.POST.get("description", "").strip()

        if not name or not smiles:
            messages.error(request, "Name and SMILES are required.")
            return render(request, "molecules/add.html", {"name": name, "smiles": smiles, "description": description})

        # Validate SMILES via fingerprint generation
        fp = smiles_to_fingerprint(smiles)
        if fp is None:
            messages.error(request, f"Invalid SMILES string: '{smiles}'. Please check and try again.")
            return render(request, "molecules/add.html", {"name": name, "smiles": smiles, "description": description})

        if Molecule.objects.filter(smiles=smiles).exists():
            messages.warning(request, "A molecule with this SMILES string already exists.")
            return render(request, "molecules/add.html", {"name": name, "smiles": smiles, "description": description})

        mol = Molecule.objects.create(name=name, smiles=smiles, description=description)
        success = upsert_molecule(mol.id, mol.smiles, mol.name, mol.description)
        if not success:
            mol.delete()
            messages.error(request, "Could not index molecule – invalid SMILES.")
            return render(request, "molecules/add.html", {"name": name, "smiles": smiles, "description": description})

        messages.success(request, f"Molecule '{name}' added successfully.")
        return redirect("molecules:index")

    return render(request, "molecules/add.html", {})


# ---------------------------------------------------------------------------
# Delete molecule
# ---------------------------------------------------------------------------


@require_POST
def delete_molecule_view(request, pk):
    """Delete a molecule from the database and vector store."""
    mol = get_object_or_404(Molecule, pk=pk)
    name = mol.name
    delete_molecule(mol.id)
    mol.delete()
    messages.success(request, f"Molecule '{name}' deleted.")
    return redirect("molecules:index")


# ---------------------------------------------------------------------------
# Search similar molecules
# ---------------------------------------------------------------------------


def search(request):
    """Search form and results – find similar molecules by SMILES query."""
    results = []
    query_smiles = ""
    query_image = None
    searched = False
    error = None

    if request.method == "POST":
        query_smiles = request.POST.get("smiles", "").strip()
        searched = True

        if not query_smiles:
            error = "Please enter a SMILES string to search."
        else:
            fp = smiles_to_fingerprint(query_smiles)
            if fp is None:
                error = f"Invalid SMILES string: '{query_smiles}'."
            else:
                query_image = smiles_to_image_base64(query_smiles, size=(300, 200))
                n_results = int(request.POST.get("n_results", 5))
                hits = search_similar_molecules(query_smiles, n_results=n_results)
                for hit in hits:
                    hit["image"] = smiles_to_image_base64(hit["smiles"], size=(200, 140))
                results = hits

                if not results:
                    messages.info(request, "No molecules found in the database. Add some molecules first.")

    return render(
        request,
        "molecules/search.html",
        {
            "query_smiles": query_smiles,
            "query_image": query_image,
            "results": results,
            "searched": searched,
            "error": error,
        },
    )


# ---------------------------------------------------------------------------
# Molecule detail
# ---------------------------------------------------------------------------


def molecule_detail(request, pk):
    """Show details and structural image for a single molecule."""
    mol = get_object_or_404(Molecule, pk=pk)
    image = smiles_to_image_base64(mol.smiles, size=(400, 300))
    similar = search_similar_molecules(mol.smiles, n_results=6)
    # Exclude the molecule itself
    similar = [h for h in similar if h["id"] != mol.id][:5]
    for hit in similar:
        hit["image"] = smiles_to_image_base64(hit["smiles"], size=(200, 140))
    return render(
        request,
        "molecules/detail.html",
        {"mol": mol, "image": image, "similar": similar},
    )


# ---------------------------------------------------------------------------
# API: validate SMILES (AJAX helper)
# ---------------------------------------------------------------------------


def validate_smiles(request):
    smiles = request.GET.get("smiles", "")
    fp = smiles_to_fingerprint(smiles)
    return JsonResponse({"valid": fp is not None})
