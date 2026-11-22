"""Tests de l'API sur une base SQLite en mémoire, séparée de la vraie base."""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine

from app import models  # noqa: F401  (enregistre la table Livre)
from app.database import get_session
from app.main import app

LIVRE = {
    "titre": "Gouverneurs de la rosée",
    "auteur": "Jacques Roumain",
    "annee": 1944,
    "categorie": "roman",
    "isbn": "9782070360000",
}


@pytest.fixture(name="client")
def client_fixture():
    # StaticPool : une seule connexion, donc la base en mémoire survit à la requête.
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    SQLModel.metadata.create_all(engine)

    def session_de_test():
        with Session(engine) as session:
            yield session

    app.dependency_overrides[get_session] = session_de_test
    # Pas de « with » : le démarrage (et les livres de départ) n'est pas exécuté.
    yield TestClient(app)
    app.dependency_overrides.clear()


def creer(client, **changements):
    reponse = client.post("/livres", json={**LIVRE, **changements})
    assert reponse.status_code == 201, reponse.text
    return reponse.json()


def test_sante(client):
    reponse = client.get("/sante")
    assert reponse.status_code == 200
    assert reponse.json() == {"statut": "ok"}


def test_creer_livre(client):
    reponse = client.post("/livres", json=LIVRE)
    assert reponse.status_code == 201
    livre = reponse.json()
    assert livre["id"] >= 1
    assert livre["disponible"] is True
    assert reponse.headers["location"] == f"/livres/{livre['id']}"


def test_creer_ignore_id_du_client(client):
    livre = creer(client, id=999)
    assert livre["id"] != 999


def test_lire_livre(client):
    cree = creer(client)
    reponse = client.get(f"/livres/{cree['id']}")
    assert reponse.status_code == 200
    assert reponse.json()["titre"] == LIVRE["titre"]


def test_lire_livre_absent_404(client):
    reponse = client.get("/livres/12345")
    assert reponse.status_code == 404
    assert "detail" in reponse.json()


def test_liste_filtree_et_pagination(client):
    creer(client, titre="Cosmos", auteur="Carl Sagan", categorie="science", isbn=None)
    creer(client, titre="Clean Code", auteur="Robert Martin", categorie="informatique",
          isbn=None, disponible=False)
    creer(client, titre="Les Misérables", auteur="Victor Hugo", categorie="roman", isbn=None)

    assert len(client.get("/livres").json()) == 3
    assert [l["titre"] for l in client.get("/livres?categorie=science").json()] == ["Cosmos"]
    assert [l["titre"] for l in client.get("/livres?q=hugo").json()] == ["Les Misérables"]
    assert [l["titre"] for l in client.get("/livres?disponible=false").json()] == ["Clean Code"]
    assert len(client.get("/livres?skip=1&limit=1").json()) == 1


def test_limite_maximale_100(client):
    assert client.get("/livres?limit=101").status_code == 422
    assert client.get("/livres?limit=100").status_code == 200


def test_remplacer_livre_put(client):
    cree = creer(client)
    nouveau = {**LIVRE, "titre": "Compère Général Soleil", "disponible": False}
    reponse = client.put(f"/livres/{cree['id']}", json=nouveau)
    assert reponse.status_code == 200
    assert reponse.json()["titre"] == "Compère Général Soleil"
    assert reponse.json()["disponible"] is False


def test_modifier_livre_patch(client):
    cree = creer(client)
    reponse = client.patch(f"/livres/{cree['id']}", json={"disponible": False})
    assert reponse.status_code == 200
    assert reponse.json()["disponible"] is False
    assert reponse.json()["titre"] == LIVRE["titre"]  # le reste est inchangé


def test_modifier_livre_absent_404(client):
    assert client.patch("/livres/12345", json={"disponible": False}).status_code == 404
    assert client.put("/livres/12345", json=LIVRE).status_code == 404


def test_patch_refuse_titre_null(client):
    cree = creer(client)
    assert client.patch(f"/livres/{cree['id']}", json={"titre": None}).status_code == 422


def test_supprimer_livre(client):
    cree = creer(client)
    reponse = client.delete(f"/livres/{cree['id']}")
    assert reponse.status_code == 204
    assert client.get(f"/livres/{cree['id']}").status_code == 404
    assert client.delete(f"/livres/{cree['id']}").status_code == 404


@pytest.mark.parametrize(
    "changement",
    [
        {"titre": "A"},                    # trop court
        {"auteur": "x" * 201},             # trop long
        {"annee": 1449},                   # avant 1450
        {"annee": 9999},                   # dans le futur
        {"categorie": "cuisine"},          # hors de la liste
        {"isbn": "12345"},                 # ni 10 ni 13 chiffres
        {"isbn": "97820703600AB"},         # lettres
    ],
)
def test_validation_422(client, changement):
    reponse = client.post("/livres", json={**LIVRE, **changement})
    assert reponse.status_code == 422
    assert reponse.json()["detail"][0]["loc"][0] == "body"


def test_isbn_en_double_409(client):
    creer(client)
    reponse = client.post("/livres", json=LIVRE)
    assert reponse.status_code == 409
    assert "ISBN" in reponse.json()["detail"]


def test_isbn_en_double_409_sur_patch(client):
    creer(client)
    autre = creer(client, titre="Autre livre", isbn="9782070360001")
    reponse = client.patch(f"/livres/{autre['id']}", json={"isbn": LIVRE["isbn"]})
    assert reponse.status_code == 409


def test_isbn_facultatif_plusieurs_sans_isbn(client):
    creer(client, isbn=None)
    creer(client, isbn=None, titre="Second sans ISBN")  # plusieurs NULL sont permis
