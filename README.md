# Data Engineer Interview Test

Solution Python et SQL : quatre sources chargées dans SQLite, un schéma en étoile, les cinq analyses métier et les deux exercices de programmation. Les rapports sont disponibles dans Datasette et en CSV.

## Installation et exécution

Prérequis : Linux, Python 3.12 avec `venv`, SQLite embarqué 3.37 ou supérieur, Bash et `flock` (util-linux). L'installation des dépendances nécessite un accès au registre Python. Depuis la racine du projet :

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pip check
python -c 'import sqlite3; print(sqlite3.sqlite_version); assert sqlite3.sqlite_version_info >= (3, 37, 0)'
python -m pytest -q tests
bash scripts/run_pipeline.sh
```

Le dossier `data/` est fourni. S'il est absent, le recréer avec `python -m zipfile -e data.zip data`.

Le lanceur affiche le chemin de son journal dans `logs/`, charge `outputs/warehouse.sqlite`, puis écrit les sept CSV. Son code de sortie est `0` en cas de succès, `75` si une autre exécution détient le verrou. Les volumes et les erreurs éventuelles sont dans le journal.

Pour exécuter séparément le chargement et l'export :

```bash
python -m etl.load_sources --data-dir data --database outputs/warehouse.sqlite
python -m etl.export_reports --database outputs/warehouse.sqlite --output-dir outputs
```

Les chemins par défaut sont calculés depuis le code ; les arguments explicites sont relatifs au dossier courant. En exploitation, utiliser le lanceur pour couvrir les deux étapes avec le même verrou.

## Consulter les rapports

```bash
datasette serve outputs/warehouse.sqlite --host 127.0.0.1 --port 8001
```

Ouvrir [la base](http://127.0.0.1:8001/warehouse), puis choisir une table ou une vue. Arrêter le serveur avec Ctrl+C.

| Analyse | Vue SQL et export CSV du même nom |
| --- | --- |
| Top 5 des pays | `top_5_nations` |
| Transport le plus fréquent pour ces pays | `top_shipping_modes` |
| Meilleurs mois | `best_sales_months` |
| Meilleurs clients par revenu | `customers_by_revenue` |
| Meilleurs clients par quantité | `customers_by_quantity` |
| Comparaison de périodes | `period_comparison` |
| Rapport mensuel chronologique | `monthly_sales` |

Les exports exemples se trouvent dans [`outputs/`](outputs/). Les [requêtes et résultats détaillés](docs/resultats.md) permettent de reproduire les cinq analyses.

## Modèle et résultats attendus

Les fichiers `.tbl` sont du texte ASCII sans en-tête, séparé par `|`, avec un séparateur final. Les sources NATION → CUSTOMER → ORDERS → LINEITEM alimentent `dim_customer`, `dim_date` et `fact_sales`.

Un fait représente une ligne de commande, identifiée par `(order_id, line_number)`. Le revenu correspond au prix étendu après remise, hors taxe, arrondi au centime par ligne. Les montants restent des centimes entiers ; le prix étendu inclut déjà la quantité.

| Table | Lignes du jeu fourni |
| --- | ---: |
| `nation` | 25 |
| `customer` | 1 500 |
| `orders` | 15 000 |
| `lineitem` | 60 175 |
| `dim_customer` | 1 500 |
| `dim_date` | 2 406 |
| `fact_sales` | 60 175 |

Le rapport mensuel couvre 80 périodes, de janvier 1992 à août 1998. Le revenu global est de **204 513 495 230 centimes**. La comparaison utilise juillet contre juin 1998 ; août reste signalé comme potentiellement partiel. Les volumes ci-dessus décrivent les données fournies, sans être imposés aux autres lots.

Le [modèle et les règles métier](docs/modele_et_regles.md) précisent les clés, les conversions, les arrondis et le profilage.

## Tests et exercices Python

La suite complète compte **109 tests**, dont 26 pour les exercices. Elle vérifie les sources, les conversions, les contraintes, les annulations, les migrations, les relances, les cinq analyses, les exports et le lanceur.

Les fonctions `reverse_words` et `full_justify` sont dans [`src/algorithms.py`](src/algorithms.py). Elles reprennent les exemples de l'[énoncé original](ENONCE.md), avec les cas limites et les contraintes maximales :

```bash
python -m pytest -q tests/test_algorithms.py
```

L'inversion des mots prend `O(n)` en temps et mémoire. La justification prend `O(m + C)` en temps, avec `m` mots et `C` caractères produits, `O(C)` pour le résultat et `O(w)` pour construire une ligne de largeur `w`. Les chaînes Python sont immuables ; la variante en place avec un tableau déjà mutable peut compacter les espaces puis inverser la séquence et chaque mot en `O(n)` temps et `O(1)` mémoire supplémentaire.

## Organisation du code et documentation

| Emplacement | Rôle |
| --- | --- |
| `etl/load_sources.py` | Lecture, conversions, transaction et alimentation de l'étoile |
| `etl/export_reports.py` | Lecture des vues et export CSV |
| `sql/` | Tables, contraintes et vues métier |
| `scripts/run_pipeline.sh` | Chargement et export sous verrou, avec journaux |
| `src/algorithms.py` | Deux exercices Python |
| `tests/` | Tests automatisés |
| `notebooks/01_data_exploration.ipynb` | Exploration des sources |

Pour évaluer les choix et reproduire les résultats :

- [Modèle et règles métier](docs/modele_et_regles.md)
- [Exploitation, déploiement et architecture](docs/exploitation.md)
- [Analyses SQL et résultats](docs/resultats.md)
- [Énoncé original](ENONCE.md), [DDL](ddl.sql) et [ERD](erd.png) fournis

## Périmètre et limites

Le pipeline recharge complètement les sept tables dans une transaction. Une erreur conserve la dernière base validée. Il attend un lot complet de quatre fichiers stables ; il ne réalise pas de chargement incrémental. Les CSV sont des copies et leur publication n'est pas atomique pour l'ensemble des sept fichiers. Les références aux régions, produits et fournisseurs non chargés ne sont pas contrôlées.

Le livrable s'exécute sur un hôte unique. Le [guide d'exploitation](docs/exploitation.md) répond aux questions de cron, de déploiement, de production et de croissance mensuelle de 6,1 à 12,7 %. Il n'installe aucune crontab ni aucun serveur permanent.

Le profilage initial est réalisé et le revenu est calculé dans les requêtes. Les bonus suivants restent reportés : Docker, streaming, génération de données, classification des soldes, déplacement des dates et colonne persistée de revenu par ligne.
