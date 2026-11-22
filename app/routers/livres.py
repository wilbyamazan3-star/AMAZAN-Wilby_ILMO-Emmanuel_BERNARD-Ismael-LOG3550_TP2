"""Points d'accès CRUD pour les livres."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, col, or_, select

from app.database import get_session
from app.models import Categorie, Livre
from app.schemas import LivreCreate, LivreRead, LivreUpdate

router = APIRouter(prefix="/livres", tags=["Livres"])

NON_TROUVE = {404: {"description": "Livre introuvable"}}
ISBN_EN_DOUBLE = {409: {"description": "Un livre avec cet ISBN existe déjà"}}


def _trouver(session: Session, livre_id: int) -> Livre:
    livre = session.get(Livre, livre_id)
    if livre is None:
        raise HTTPException(status_code=404, detail=f"Aucun livre avec l'id {livre_id}.")
    return livre


def _enregistrer(session: Session, livre: Livre) -> Livre:
    """Sauvegarde ; l'index unique de la base décide si l'ISBN est en double."""
    session.add(livre)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise HTTPException(status_code=409, detail="Un livre avec cet ISBN existe déjà.")
    session.refresh(livre)
    return livre


@router.get(
    "",
    response_model=list[LivreRead],
    summary="Lister les livres",
    description="Retourne les livres, avec filtres facultatifs (`q`, `categorie`, "
    "`disponible`) et pagination (`skip`, `limit` jusqu'à 100).",
)
def lister_livres(
    q: Optional[str] = Query(default=None, min_length=1, description="Recherche dans le titre ou l'auteur"),
    categorie: Optional[Categorie] = Query(default=None, description="Filtrer par catégorie"),
    disponible: Optional[bool] = Query(default=None, description="Filtrer par disponibilité"),
    skip: int = Query(default=0, ge=0, description="Nombre de livres à sauter"),
    limit: int = Query(default=20, ge=1, le=100, description="Nombre maximal de livres (≤ 100)"),
    session: Session = Depends(get_session),
):
    requete = select(Livre)
    if q:
        motif = f"%{q}%"
        requete = requete.where(or_(col(Livre.titre).ilike(motif), col(Livre.auteur).ilike(motif)))
    if categorie is not None:
        requete = requete.where(Livre.categorie == categorie.value)
    if disponible is not None:
        requete = requete.where(Livre.disponible == disponible)
    requete = requete.order_by(col(Livre.id)).offset(skip).limit(limit)
    return session.exec(requete).all()


@router.get(
    "/{livre_id}",
    response_model=LivreRead,
    summary="Lire un livre",
    description="Retourne un livre par son identifiant.",
    responses=NON_TROUVE,
)
def lire_livre(livre_id: int, session: Session = Depends(get_session)):
    return _trouver(session, livre_id)


@router.post(
    "",
    response_model=LivreRead,
    status_code=status.HTTP_201_CREATED,
    summary="Créer un livre",
    description="Crée un livre. L'identifiant est généré par le serveur ; "
    "l'en-tête `Location` donne l'adresse du nouveau livre.",
    responses=ISBN_EN_DOUBLE,
)
def creer_livre(donnees: LivreCreate, response: Response, session: Session = Depends(get_session)):
    livre = _enregistrer(session, Livre(**donnees.model_dump()))
    response.headers["Location"] = f"/livres/{livre.id}"
    return livre


@router.put(
    "/{livre_id}",
    response_model=LivreRead,
    summary="Remplacer un livre",
    description="Remplacement complet : tous les champs obligatoires doivent être fournis.",
    responses={**NON_TROUVE, **ISBN_EN_DOUBLE},
)
def remplacer_livre(livre_id: int, donnees: LivreCreate, session: Session = Depends(get_session)):
    livre = _trouver(session, livre_id)
    for champ, valeur in donnees.model_dump().items():
        setattr(livre, champ, valeur)
    return _enregistrer(session, livre)


@router.patch(
    "/{livre_id}",
    response_model=LivreRead,
    summary="Modifier partiellement un livre",
    description="Seuls les champs envoyés sont modifiés.",
    responses={**NON_TROUVE, **ISBN_EN_DOUBLE},
)
def modifier_livre(livre_id: int, donnees: LivreUpdate, session: Session = Depends(get_session)):
    livre = _trouver(session, livre_id)
    for champ, valeur in donnees.model_dump(exclude_unset=True).items():
        setattr(livre, champ, valeur)
    return _enregistrer(session, livre)


@router.delete(
    "/{livre_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Supprimer un livre",
    description="Supprime un livre. Réponse vide (204).",
    responses=NON_TROUVE,
)
def supprimer_livre(livre_id: int, session: Session = Depends(get_session)):
    livre = _trouver(session, livre_id)
    session.delete(livre)
    session.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
