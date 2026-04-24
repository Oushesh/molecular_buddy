"""Management command to seed the database with sample molecules."""

from django.core.management.base import BaseCommand
from molecules.models import Molecule
from molecules.utils import upsert_molecule

SAMPLE_MOLECULES = [
    {
        "name": "Aspirin",
        "smiles": "CC(=O)Oc1ccccc1C(=O)O",
        "description": "Analgesic, anti-inflammatory, and antipyretic drug.",
    },
    {
        "name": "Caffeine",
        "smiles": "Cn1c(=O)c2c(ncn2C)n(c1=O)C",
        "description": "Central nervous system stimulant found in coffee and tea.",
    },
    {
        "name": "Ibuprofen",
        "smiles": "CC(C)Cc1ccc(cc1)C(C)C(=O)O",
        "description": "Non-steroidal anti-inflammatory drug (NSAID).",
    },
    {
        "name": "Paracetamol",
        "smiles": "CC(=O)Nc1ccc(O)cc1",
        "description": "Analgesic and antipyretic drug.",
    },
    {
        "name": "Dopamine",
        "smiles": "NCCc1ccc(O)c(O)c1",
        "description": "Neurotransmitter involved in reward and motor control.",
    },
    {
        "name": "Serotonin",
        "smiles": "NCCc1c[nH]c2ccc(O)cc12",
        "description": "Neurotransmitter regulating mood, sleep, and appetite.",
    },
    {
        "name": "Glucose",
        "smiles": "OC[C@H]1OC(O)[C@H](O)[C@@H](O)[C@@H]1O",
        "description": "Simple sugar and primary energy source for cells.",
    },
    {
        "name": "Cholesterol",
        "smiles": "[C@@H]1([C@H](CCCC(C)C)C)[C@@]2(CC[C@H]3[C@@H]([C@@]2(CC1)C)CC=C4[C@]3(CC[C@@H](C4)O)C)C",
        "description": "Lipid molecule essential for cell membrane structure.",
    },
    {
        "name": "Penicillin G",
        "smiles": "CC1(C)SC2C(NC(=O)Cc3ccccc3)C(=O)N2C1C(=O)O",
        "description": "Beta-lactam antibiotic.",
    },
    {
        "name": "Melatonin",
        "smiles": "COc1ccc2[nH]cc(CCNC(C)=O)c2c1",
        "description": "Hormone regulating the sleep-wake cycle.",
    },
]


class Command(BaseCommand):
    help = "Seed the database with sample molecules and index them in ChromaDB."

    def handle(self, *args, **options):
        added = 0
        skipped = 0
        for data in SAMPLE_MOLECULES:
            if Molecule.objects.filter(smiles=data["smiles"]).exists():
                self.stdout.write(f"  Skipping '{data['name']}' (already exists)")
                skipped += 1
                continue
            mol = Molecule.objects.create(**data)
            success = upsert_molecule(mol.id, mol.smiles, mol.name, mol.description)
            if success:
                self.stdout.write(self.style.SUCCESS(f"  Added '{mol.name}'"))
                added += 1
            else:
                mol.delete()
                self.stdout.write(self.style.ERROR(f"  Failed to index '{data['name']}' (invalid SMILES)"))

        self.stdout.write(self.style.SUCCESS(f"\nDone – added {added} molecules, skipped {skipped}."))
