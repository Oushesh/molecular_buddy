from django.test import TestCase, Client
from django.urls import reverse

from .models import Molecule
from .utils import smiles_to_fingerprint, smiles_to_image_base64, tanimoto_similarity


class FingerprintTests(TestCase):
    """Test RDKit fingerprint and Tanimoto utilities."""

    def test_valid_smiles_returns_fingerprint(self):
        fp = smiles_to_fingerprint("CC(=O)Oc1ccccc1C(=O)O")  # Aspirin
        self.assertIsNotNone(fp)
        self.assertEqual(len(fp), 2048)

    def test_invalid_smiles_returns_none(self):
        fp = smiles_to_fingerprint("NOT_A_SMILES!!!")
        self.assertIsNone(fp)

    def test_same_molecule_tanimoto_is_one(self):
        fp = smiles_to_fingerprint("CC(=O)Oc1ccccc1C(=O)O")
        self.assertAlmostEqual(tanimoto_similarity(fp, fp), 1.0)

    def test_different_molecules_tanimoto_less_than_one(self):
        fp1 = smiles_to_fingerprint("CC(=O)Oc1ccccc1C(=O)O")   # Aspirin
        fp2 = smiles_to_fingerprint("Cn1c(=O)c2c(ncn2C)n(c1=O)C")  # Caffeine
        sim = tanimoto_similarity(fp1, fp2)
        self.assertGreaterEqual(sim, 0.0)
        self.assertLess(sim, 1.0)

    def test_image_base64_valid_smiles(self):
        img = smiles_to_image_base64("CCO")  # Ethanol
        self.assertIsNotNone(img)
        self.assertGreater(len(img), 100)

    def test_image_base64_invalid_smiles(self):
        img = smiles_to_image_base64("INVALID_SMILES")
        self.assertIsNone(img)


class MoleculeModelTests(TestCase):
    def test_str_short_smiles(self):
        mol = Molecule(name="Ethanol", smiles="CCO")
        self.assertIn("Ethanol", str(mol))

    def test_str_long_smiles_truncated(self):
        long_smiles = "C" * 50
        mol = Molecule(name="LongMol", smiles=long_smiles)
        self.assertIn("...", str(mol))


class MoleculeViewTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_index_status_ok(self):
        response = self.client.get(reverse("molecules:index"))
        self.assertEqual(response.status_code, 200)

    def test_add_page_status_ok(self):
        response = self.client.get(reverse("molecules:add"))
        self.assertEqual(response.status_code, 200)

    def test_search_page_status_ok(self):
        response = self.client.get(reverse("molecules:search"))
        self.assertEqual(response.status_code, 200)

    def test_validate_smiles_valid(self):
        response = self.client.get(reverse("molecules:validate_smiles"), {"smiles": "CCO"})
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {"valid": True})

    def test_validate_smiles_invalid(self):
        response = self.client.get(reverse("molecules:validate_smiles"), {"smiles": "NOT_VALID!!!"})
        self.assertEqual(response.status_code, 200)
        self.assertJSONEqual(response.content, {"valid": False})

    def test_add_molecule_post_valid(self):
        response = self.client.post(
            reverse("molecules:add"),
            {"name": "Ethanol", "smiles": "CCO", "description": "Simple alcohol"},
        )
        # Should redirect to index on success
        self.assertRedirects(response, reverse("molecules:index"))
        self.assertTrue(Molecule.objects.filter(smiles="CCO").exists())

    def test_add_molecule_post_invalid_smiles(self):
        response = self.client.post(
            reverse("molecules:add"),
            {"name": "Bad", "smiles": "NOT_SMILES!!!", "description": ""},
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Invalid SMILES")
        self.assertFalse(Molecule.objects.filter(name="Bad").exists())
