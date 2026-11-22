"""Modèle de base de données : la table « livre »."""
from enum import Enum
from typing import Optional

from sqlmodel import Field, SQLModel


class Categorie(str, Enum):
    """Catégories autorisées pour un livre."""

    roman = "roman"
    science = "science"
    histoire = "histoire"
    informatique = "informatique"
    autre = "autre"


class Livre(SQLModel, table=True):
    """Table SQLite des livres.

    L'index unique sur `isbn` est garanti par la base elle-même :
    SQLite autorise plusieurs NULL, donc l'ISBN reste facultatif.
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    titre: str
    auteur: str
    annee: int
    categorie: str = Field(index=True)
    isbn: Optional[str] = Field(default=None, unique=True, index=True)
    disponible: bool = True
