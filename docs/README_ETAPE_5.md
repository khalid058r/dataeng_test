# Étape 5 — Alimenter le schéma en étoile

Les sources et les trois tables du modèle en étoile sont maintenant chargées ensemble. Le premier rapport mensuel est disponible depuis l'étape 6 ; consulter `README_ETAPE_6.md`.

Ce guide décrit le périmètre de l'étape 5. Depuis l'étape 7, le pipeline charge sept tables avec NATION et ajoute `nation_name` à la dimension client. Consulter `README_ETAPE_7.md` pour le périmètre actuel et la mise à niveau des anciennes bases.

## 1. Exécuter le pipeline

Depuis la racine du projet, avec l'environnement préparé à l'étape 1 :

```bash
source .venv/bin/activate
python -m etl.load_sources
python -m pytest -q tests
```

La commande existante charge désormais les six tables dans `outputs/warehouse.sqlite`. Les options `--data-dir` et `--database` restent disponibles.

Résultat avec les fichiers fournis :

```text
CUSTOMER : 1 500 lignes chargées
ORDERS : 15 000 lignes chargées
LINEITEM : 60 175 lignes chargées
DIM_CUSTOMER : 1 500 lignes chargées
DIM_DATE : 2 406 lignes chargées
FACT_SALES : 60 175 lignes chargées
Chargement validé : <racine du projet>/outputs/warehouse.sqlite
```

## 2. Comprendre les transformations

Les contraintes du modèle sont dans `sql/02_star_schema.sql`. La fonction `load_star` de `etl/load_sources.py` alimente les tables dans cet ordre :

1. `dim_customer` reçoit tous les clients : identifiant, nom, segment et code pays. Les 500 clients sans commande du jeu fourni sont conservés.
2. `dim_date` reçoit chaque jour entre la première et la dernière date de commande, bornes incluses. Les jours sans commande sont présents. Pour le jeu fourni, le calendrier compte 2 406 jours.
3. `fact_sales` reçoit chaque ligne de LINEITEM, jointe à ORDERS pour récupérer le client et la date de commande.

La clé des faits est `(order_id, line_number)`. Les clés `customer_id` et `date_id` pointent vers les dimensions. Le code pays reste un attribut client ; NATION sera ajouté à l'étape 7.

Les faits conservent la quantité, le prix étendu en centimes, la remise en pourcentage entier et le mode de transport. Le prix étendu inclut déjà la quantité. Le total de la commande n'est pas recopié sur chaque ligne.

Pour comprendre le code, suivre `load_sources` jusqu'à `load_star` : copie des clients avec `INSERT … SELECT`, boucle Python pour le calendrier, puis jointure SQL des lignes et commandes pour les faits. `load_star` ne valide pas la transaction ; seul `load_sources` le fait après tous les contrôles.

## 3. Préparer le calcul du revenu

Le revenu sera calculé dans les rapports à partir des mesures conservées, sans colonne persistée supplémentaire. Pour chaque ligne :

```sql
(extended_price_cents * (100 - discount_percent) + 50) / 100
```

Cette expression entière donne les centimes après remise, hors taxe, arrondis par ligne avec `ROUND_HALF_UP`. Par exemple, `1005` centimes avec `10` pour cent de remise donnent `905` centimes. Deux lignes de `5` centimes avec `10` pour cent de remise donnent ensemble `10` centimes après arrondi de chaque ligne.

Avant de valider, le chargeur vérifie que la multiplication et l'ajout de `50` restent dans la capacité des entiers SQLite. Il vérifie également les sommes de quantités, de prix avant remise et de revenu. Un dépassement annule le chargement ; SQLite ne doit pas basculer silencieusement le calcul du revenu vers un flottant.

## 4. Relance et évolution de la base

Une seule transaction couvre la création du schéma, le remplacement des six tables et les contrôles. Les anciennes données sont vidées dans l'ordre suivant : faits, dimensions, LINEITEM, ORDERS, CUSTOMER. Les sources sont ensuite rechargées, suivies des dimensions et des faits.

Une erreur à n'importe quelle étape restaure la version précédente complète. La sortie de succès et les volumes ne sont affichés qu'après validation. Les autres tables de la base du projet sont conservées.

Une base de l'étape 4, identifiée comme appartenant au projet et de version `1`, est automatiquement complétée au prochain chargement réussi. La version devient `2`. Si le chargement échoue, elle reste en version `1` et les nouvelles tables ne sont pas publiées. Une base étrangère ou une version inconnue reste refusée.

## 5. Consulter et contrôler les tables

```bash
datasette serve outputs/warehouse.sqlite --host 127.0.0.1 --port 8001
```

Ouvrir `http://127.0.0.1:8001`, puis `dim_customer`, `dim_date` ou `fact_sales`. Dans l'éditeur SQL de la base, on peut comparer les sources et les faits :

```sql
SELECT 'source' AS origin, COUNT(*) AS rows,
       SUM(L_QUANTITY) AS quantity,
       SUM(L_EXTENDEDPRICE_CENTS) AS extended_price_cents
FROM lineitem
UNION ALL
SELECT 'facts', COUNT(*), SUM(quantity), SUM(extended_price_cents)
FROM fact_sales;

SELECT MIN(date_id) AS first_day, MAX(date_id) AS last_day,
       COUNT(*) AS calendar_days
FROM dim_date;

PRAGMA foreign_key_check;
PRAGMA integrity_check;
```

Exécuter chaque instruction séparément. Le contrôle des clés étrangères ne doit retourner aucune ligne ; le contrôle d'intégrité doit retourner `ok`.

Sur le jeu fourni, les sources et les faits donnent chacun 60 175 lignes, 1 536 127 unités et 215 218 976 047 centimes avant remise. Le revenu total après remise et arrondi par ligne est de 204 513 495 230 centimes. Le calendrier couvre le 01/01/1992 au 02/08/1998. Une relance a été comparée sur le contenu complet des six tables ; les contrôles SQLite ont réussi.

## 6. Vérifications automatisées

Les 47 tests de `tests/test_load_sources.py` vérifient désormais les six tables lors des relances et des annulations. Ils couvrent aussi la correspondance exacte d'un petit jeu avec les faits attendus, les clients sans commande, le calendrier continu avec année bissextile, les arrondis par ligne, la remise de 100 %, les dépassements d'entiers et la mise à niveau transactionnelle de la base de l'étape 4.

Sur les fichiers fournis, ils comparent les quantités et les prix des faits aux fichiers, calculent indépendamment le revenu avec `Decimal`, puis rechargent les données pour vérifier que les six tables sont identiques.
