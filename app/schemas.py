"""Schémas d'échange (Pydantic) : ce que le client envoie et reçoit.

On les sépare du modèle de base de données pour ne jamais laisser le client
choisir l'`id` et pour pouvoir faire évoluer la table sans casser l'API.
"""
from datetime import date
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.models import Categorie

EXEMPLE = {
    "titre": "Compère Général Soleil",
    "auteur": "Jacques Stephen Alexis",
    "annee": 1955,
    "categorie": "roman",
    "isbn": "9782070360000",
    "disponible": True,
}


def verifier_annee(valeur: Optional[int]) -> Optional[int]:
    """L'année ne peut pas dépasser l'année en cours."""
    annee_courante = date.today().year
    if valeur is not None and valeur > annee_courante:
        raise ValueError(f"L'année doit être au plus {annee_courante}.")
    return valeur


class LivreCreate(BaseModel):
    """Corps d'un POST ou d'un PUT : tous les champs obligatoires sont requis."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        use_enum_values=True,
        json_schema_extra={"example": EXEMPLE},
    )

    titre: str = Field(min_length=2, max_length=200, description="Titre (2 à 200 caractères)")
    auteur: str = Field(min_length=2, max_length=200, description="Auteur (2 à 200 caractères)")
    annee: int = Field(ge=1450, description="Année de publication (1450 à l'année en cours)")
    categorie: Categorie = Field(description="roman, science, histoire, informatique ou autre")
    isbn: Optional[str] = Field(
        default=None,
        pattern=r"^(\d{10}|\d{13})$",
        description="ISBN de 10 ou 13 chiffres, sans tirets (facultatif, unique)",
    )
    disponible: bool = Field(default=True, description="Le livre est-il disponible ?")

    @field_validator("annee")
    @classmethod
    def annee_pas_dans_le_futur(cls, v):
        return verifier_annee(v)


class LivreUpdate(BaseModel):
    """Corps d'un PATCH : tous les champs sont facultatifs."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        use_enum_values=True,
        json_schema_extra={"example": {"disponible": False}},
    )

    titre: Optional[str] = Field(default=None, min_length=2, max_length=200)
    auteur: Optional[str] = Field(default=None, min_length=2, max_length=200)
    annee: Optional[int] = Field(default=None, ge=1450)
    categorie: Optional[Categorie] = None
    isbn: Optional[str] = Field(default=None, pattern=r"^(\d{10}|\d{13})$")
    disponible: Optional[bool] = None

    @field_validator("annee")
    @classmethod
    def annee_pas_dans_le_futur(cls, v):
        return verifier_annee(v)

    @field_validator("titre", "auteur", "annee", "categorie", "disponible")
    @classmethod
    def refuser_null(cls, v):
        # Seul l'ISBN peut être remis à null (pour l'effacer).
        if v is None:
            raise ValueError("Ce champ ne peut pas être null.")
        return v


class LivreRead(BaseModel):
    """Réponse de l'API : le livre avec son identifiant généré."""

    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={"example": {"id": 1, **EXEMPLE}},
    )

    id: int
    titre: str
    auteur: str
    annee: int
    categorie: Categorie
    isbn: Optional[str] = None
    disponible: bool
