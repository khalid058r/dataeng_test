# Environnement local Junior/Mid

Environnement initial préparé le 3 novembre 2026, puis vérifié à nouveau depuis zéro le 5 novembre 2026 après l'implémentation du projet.

Le pipeline charge maintenant quatre sources, les dimensions et les faits, puis exporte les rapports. Le `README.md` contient le parcours d'installation complet ; `README_ETAPE_9.md` détaille l'exploitation et le déploiement.

## Outils vérifiés

| Outil | Version | Rôle |
|---|---|---|
| Python | 3.12.3 | Scripts ETL et exercices |
| pip dans `.venv` | 24.0 | Installation des dépendances |
| SQLite via Python | 3.45.1 | Base locale sans serveur |
| Datasette | 0.65.5 | Consultation dans le navigateur |
| pytest | 9.2.0 | Tests du pipeline, des rapports et des exercices |
| Git | 2.43.0 | Versionnement et livraison |

Les dépendances Python et leurs versions sont enregistrées dans `requirements.txt` à la racine.
SQLite fait partie de l'installation Python utilisée ; il ne faut pas installer un paquet pip nommé `sqlite3`.

## Utiliser l'environnement déjà préparé

Depuis la racine du projet, dans chaque nouveau terminal :

```bash
source .venv/bin/activate
python --version
python -m pip --version
python -m pip check
datasette --version
python -m pytest --version
```

Pour quitter l'environnement : `deactivate`.

## Vérifier l'interface dans le navigateur

Démarrer une base de démonstration en mémoire, sans modifier les données du projet :

```bash
datasette serve --memory --host 127.0.0.1 --port 8001
```

Ouvrir `http://127.0.0.1:8001`. Arrêter le serveur avec Ctrl+C.
La base en mémoire disparaît à l'arrêt. Pour consulter la base métier après un chargement réussi, utiliser `datasette serve outputs/warehouse.sqlite --host 127.0.0.1 --port 8001`.

## Recréer l'environnement sur une autre machine

Prérequis : Python 3.12 avec le module venv, SQLite embarqué 3.37 ou supérieur et accès à Internet pour télécharger les dépendances. Bash et `flock` sont utilisés par le lanceur Linux.
Depuis la racine du dépôt :

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pip check
python -m pytest -q tests
bash scripts/run_pipeline.sh
```

Si la distribution Linux ne fournit pas venv/ensurepip, installer le paquet système correspondant, par exemple `python3-venv` sur Ubuntu.
La version SQLite dépend de l'installation Python de la machine et n'est pas fixée par `requirements.txt`.

## Contrôles effectués

- Création de `.venv` et vérification des outils installés.
- Vérification des dépendances avec `pip check` : aucune incompatibilité déclarée.
- Exécution d'une requête SQLite en mémoire : résultat attendu obtenu.
- Exécution d'une requête via Datasette en mémoire : réponse JSON avec `ok: true` et valeur `1`.
- Ajout des règles d'exclusion pour les bases locales et fichiers temporaires ; `.venv` était déjà exclu.

Le contrôle Datasette a nécessité une exécution hors du bac à sable de l'agent.
Aucun serveur permanent n'est laissé en cours d'exécution.
Le contrôle final dans un nouvel environnement a donné 109 tests réussis, un chargement depuis une base absente et une relance identique. Les pages et exports Datasette ont aussi été vérifiés. Voir `VALIDATION_FINALE.md`.

## Éléments restant à préparer

- Choisir l'éditeur de code selon sa préférence ; le terminal suffit pour exécuter le projet.
- Finaliser le fork et la Pull Request après confirmation de l'URL d'origine : le dossier `.git` présent est vide et protégé dans cet espace de travail. Ne pas utiliser un dépôt parent d'un autre projet.
- Utiliser `COMPRENDRE_ET_MODIFIER.md` pour préparer la compréhension et les adaptations du projet.

Docker, le streaming et la génération de données ne sont pas configurés dans ce socle Junior/Mid.
