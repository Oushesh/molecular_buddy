from django.db import models


class Molecule(models.Model):
    """Represents a chemical molecule stored in the database."""

    name = models.CharField(max_length=255)
    smiles = models.TextField(unique=True, help_text="SMILES string representation of the molecule")
    description = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.smiles[:30]}...)" if len(self.smiles) > 30 else f"{self.name} ({self.smiles})"
