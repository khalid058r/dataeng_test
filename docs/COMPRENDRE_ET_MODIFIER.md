# Comprendre le projet et apprendre à le modifier

Ce guide prépare la lecture du code et les adaptations possibles après la livraison. Pour chaque changement, commencer par une règle métier précise, un petit exemple et son résultat attendu.

## 1. Le parcours d'une ligne de vente

```text
lineitem.tbl : commande 10, ligne 1, quantité 2, prix étendu 10,05, remise 10 %
    → lecture et conversions : prix 1005 centimes, remise 10 pour cent
    → table source lineitem
    → jointure à orders : récupérer le client et la date de commande
    → fact_sales : conserver ces clés et les mesures de la ligne
    → rapport : (1005 × 90 + 50) / 100 = 905 centimes après arrondi
    → agrégation par mois, client ou pays
```

La quantité est déjà incluse dans le prix étendu. Une commande peut avoir plusieurs lignes ; utiliser son total sur chaque fait ferait compter le même montant plusieurs fois.

## 2. Lire les fichiers dans cet ordre

| Ordre | Fichier | Question à comprendre |
| --- | --- | --- |
| 1 | `README.md` et `docs/README_ETAPE_3.md` | Quelles règles métier applique-t-on ? |
| 2 | `sql/01_sources.sql` | Quelles informations brutes garde-t-on et quelles contraintes les protègent ? |
| 3 | `etl/load_sources.py` : `main`, puis `load_sources` | Comment démarre le chargement et où est la transaction ? |
| 4 | Même fichier : `load_file`, `convert_value`, `hundredths` | Comment lit-on et convertit-on un champ ? |
| 5 | `sql/02_star_schema.sql`, puis `load_star` | Pourquoi séparer dimensions et faits ? |
| 6 | `sql/03_monthly_sales.sql` et `sql/04_business_reports.sql` | Comment obtient-on les résultats métier ? |
| 7 | `etl/export_reports.py` | Comment transforme-t-on une requête en CSV ? |
| 8 | `scripts/run_pipeline.sh` | Comment enchaîne-t-on les étapes et évite-t-on les chevauchements ? |
| 9 | `tests/` | Comment prouve-t-on que les cas attendus et les erreurs sont traités ? |

Les guides des étapes 4 à 9 expliquent chaque partie plus en détail. Les exercices de `src/algorithms.py` sont indépendants du pipeline ETL.

## 3. Répondre aux questions d'entretien

Préparer une réponse avec un exemple pour chacune de ces questions :

- Pourquoi SQLite pour cet exercice, et quand passer à une base client/serveur ?
- Pourquoi une ligne de commande par fait et une clé composée ?
- Pourquoi conserver les montants en centimes entiers ?
- Pourquoi arrondir chaque ligne avant la somme ?
- Pourquoi conserver les clients sans commande dans la dimension ?
- Quelle différence entre une période absente et une période à revenu nul ?
- Que se passe-t-il si le dernier fichier contient une erreur ?
- Que se passe-t-il si deux exécutions démarrent ensemble ?
- Pourquoi comparer juillet à juin 1998 au lieu d'utiliser la date du jour ?
- Pourquoi le chargement actuel ne doit-il pas recevoir seulement les nouvelles lignes ?

Pour expliquer sans réciter, prendre une ligne des tests, suivre ses transformations et calculer le résultat à la main. Pour les erreurs, suivre le chemin jusqu'à `rollback` et montrer ce qui reste dans la base.

## 4. Où modifier selon une nouvelle proposition ?

| Proposition | Fichiers à examiner | Vérification à prévoir |
| --- | --- | --- |
| Ajouter un rapport par segment | Nouvelle vue dans `sql/04_business_reports.sql`, puis `REPORT_QUERIES` pour l'export | Deux segments sur un petit jeu, total conservé |
| Changer la définition du revenu | Règle métier, vues mensuelles et clients, contrôle de capacité de `load_star` | Exemples manuels, arrondis, cohérence de tous les rapports |
| Utiliser la date d'expédition | Dimension date, transformation des faits et règles de période | Commande et expédition dans deux mois différents |
| Ajouter un attribut client | `SOURCE_COLUMNS` si nécessaire, SQL source, `dim_customer`, `load_star` | Valeur conservée, migration et relance |
| Ajouter une table produit | Description du fichier, schéma source, ordre de chargement, dimension et clés des faits | Clés absentes, doublons et absence de multiplication des faits |
| Charger uniquement les changements | Stratégie d'alimentation, clés, corrections et suppressions, tests de reprise | Même lot rejoué, correction d'une ligne, suppression |
| Passer à PostgreSQL | Connexions, DDL, migrations et fonctions SQL propres à SQLite | Même petit jeu et mêmes résultats métier |

Changer la date de référence implique aussi d'étendre le calendrier aux dates réellement utilisées. Si un montant doit inclure la taxe, décider explicitement de l'ordre des opérations et des arrondis. Une règle écrite avant le code évite des résultats incompatibles entre rapports.

## 5. Faire un changement sans perdre le résultat de référence

1. Décrire le comportement souhaité et calculer un exemple à la main.
2. Ajouter un test qui distingue l'ancien comportement du nouveau.
3. Modifier les fichiers concernés, puis lancer le test ciblé et la suite complète.
4. Utiliser une base et un dossier d'export de travail séparés :

```bash
python -m etl.load_sources --database outputs/essai.sqlite
python -m etl.export_reports --database outputs/essai.sqlite --output-dir outputs/essai
```

5. Comparer les volumes, les résultats attendus et les invariants qui doivent rester vrais : un fait par ligne source, pas de référence absente, totaux conservés quand la règle ne change pas.
6. Mettre à jour les instructions et les exemples, puis préparer le commit.

Une vue déjà présente n'est pas remplacée par `CREATE VIEW IF NOT EXISTS`. Pour changer sa définition dans une base existante, prévoir sa suppression et sa recréation dans la transaction du chargement, ou une migration adaptée. Tester aussi le chemin de mise à niveau : réussir sur une base neuve ne vérifie pas une ancienne base.

Pour une modification de tables, prévoir une nouvelle version de schéma et sa migration ; ne pas augmenter seulement `SCHEMA_VERSION`. La migration actuelle couvre précisément les versions 1 et 2 vers 3. Ces changements feront de bons exercices pratiques après la compréhension du parcours actuel.

## 6. Première lecture du chargeur Python

Le fichier à ouvrir est `etl/load_sources.py`. Commencer par sa dernière ligne :

```python
if __name__ == "__main__":
    raise SystemExit(main())
```

Quand on lance `python -m etl.load_sources`, ce bloc appelle `main`. `main` lit les options de la commande (`--data-dir` et `--database`), appelle le chargement et affiche les volumes si celui-ci réussit. `SystemExit` transmet le code de fin au terminal : `0` pour un succès, `1` pour une erreur gérée.

L'appel central de `main` est :

```python
counts = load_sources(args.data_dir, args.database)
```

`args.data_dir` est le dossier des fichiers ; `args.database` est le chemin de la base. `counts` reçoit un dictionnaire associant chaque table au nombre de lignes chargées.

La fonction `load_sources` suit six étapes, numérotées dans le code : vérifier les fichiers, lire les scripts SQL, ouvrir la base et commencer la transaction, vider les anciennes données, charger les nouvelles données, puis tout valider. En cas d'erreur, `rollback` annule les écritures ; `finally` ferme la connexion.

La boucle suivante appelle le même lecteur pour chaque source :

```python
counts = {}
for table in SOURCE_COLUMNS:
    counts[table] = load_file(connection, data_dir, table)
counts.update(load_star(connection))
```

`SOURCE_COLUMNS` donne les tables dans l'ordre NATION, CUSTOMER, ORDERS, LINEITEM. À chaque tour, `load_file` lit le fichier correspondant et retourne son nombre de lignes. `load_star` construit ensuite les dimensions et les faits. `update` ajoute leurs volumes au dictionnaire.

Pour faciliter cette lecture, la préparation des noms de colonnes, des scripts de migration et des volumes utilise des boucles classiques. Les quatre fichiers SQL sont regroupés dans `SQL_FILES`, dans leur ordre d'exécution. Les règles de conversion, les contraintes et la transaction restent les mêmes.
