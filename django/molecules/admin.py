from django.contrib import admin
from .models import Molecule


@admin.register(Molecule)
class MoleculeAdmin(admin.ModelAdmin):
    list_display = ("name", "smiles", "created_at")
    search_fields = ("name", "smiles")
    readonly_fields = ("created_at",)
