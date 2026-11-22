# LOG3550 – Devoir 2 : backend FastAPI (bibliothèque)

Dépôt Git : 


## Réponses aux questions

### Rôle de FastAPI, d'Uvicorn et de Pydantic ; pourquoi séparer modèle et schémas
FastAPI est le framework : il associe les URL aux fonctions Python et génère la doc /docs.
Uvicorn est le serveur qui écoute le réseau et passe les requêtes HTTP à FastAPI.
Pydantic valide les données reçues et envoyées d'après les types et les règles déclarés.
Le modèle de base (SQLModel) décrit la table ; les schémas décrivent ce qui circule dans l'API.
On les sépare pour que le client ne choisisse jamais l'id et pour faire évoluer l'un sans casser l'autre.

### Format de l'erreur 422
Quand une règle de validation échoue, FastAPI répond 422 avec 


### PUT et PATCH ; idempotence
PUT remplace la ressource entière : tous les champs obligatoires doivent être envoyés.
PATCH ne modifie que les champs envoyés et laisse les autres intacts.
Une opération est idempotente si la répéter donne le même état final qu'une seule fois.
PUT l'est (même contenu deux fois = même livre) et DELETE aussi (après le premier, le livre n'existe plus).
POST ne l'est pas : chaque appel crée un nouveau livre avec un nouvel id.

## Sources et outils d'assistance
Ce devoir a été réalisé avec l'aide de Claude (IA, Anthropic) pour générer le code du backend.
documentation officielle de FastAPI, SQLModel et pytest.
