from django.urls import path
from . import views

app_name = "molecules"

urlpatterns = [
    path("", views.index, name="index"),
    path("add/", views.add_molecule, name="add"),
    path("search/", views.search, name="search"),
    path("<int:pk>/", views.molecule_detail, name="detail"),
    path("<int:pk>/delete/", views.delete_molecule_view, name="delete"),
    path("api/validate-smiles/", views.validate_smiles, name="validate_smiles"),
]
