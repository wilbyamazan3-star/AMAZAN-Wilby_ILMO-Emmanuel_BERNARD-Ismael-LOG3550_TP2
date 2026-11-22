"""Moteur SQLite, session par requête et données de départ."""
from sqlmodel import Session, SQLModel, create_engine, select

from app.models import Livre

DATABASE_URL = "sqlite:///./bibliotheque.db"

# check_same_thread=False : FastAPI traite les requêtes dans plusieurs threads.
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

LIVRES_DE_DEPART = [
    {"titre": "Les Misérables", "auteur": "Victor Hugo", "annee": 1862, "categorie": "roman"},
    {"titre": "Gouverneurs de la rosée", "auteur": "Jacques Roumain", "annee": 1944, "categorie": "roman"},
    {"titre": "Le Petit Prince", "auteur": "Antoine de Saint-Exupéry", "annee": 1943,
     "categorie": "roman", "isbn": "9782070612758"},
    {"titre": "Une brève histoire du temps", "auteur": "Stephen Hawking", "annee": 1988, "categorie": "science"},
    {"titre": "Cosmos", "auteur": "Carl Sagan", "annee": 1980, "categorie": "science"},
    {"titre": "Les Jacobins noirs", "auteur": "C. L. R. James", "annee": 1938, "categorie": "histoire"},
    {"titre": "Sapiens", "auteur": "Yuval Noah Harari", "annee": 2011,
     "categorie": "histoire", "isbn": "9780062316097"},
    {"titre": "Clean Code", "auteur": "Robert C. Martin", "annee": 2008,
     "categorie": "informatique", "isbn": "9780132350884"},
    {"titre": "Introduction to Algorithms", "auteur": "Thomas H. Cormen et al.", "annee": 1990,
     "categorie": "informatique"},
    {"titre": "Le Hobbit", "auteur": "J. R. R. Tolkien", "annee": 1937, "categorie": "autre", "disponible": False},
]


def get_session():
    """Dépendance FastAPI : une session par requête, fermée à la fin."""
    with Session(engine) as session:
        yield session


def init_db() -> None:
    """Crée les tables et charge les livres de départ si la table est vide."""
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        if session.exec(select(Livre)).first() is None:
            session.add_all(Livre(**donnees) for donnees in LIVRES_DE_DEPART)
            session.commit()
