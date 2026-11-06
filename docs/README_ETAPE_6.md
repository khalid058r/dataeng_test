# Étape 6 — Premier rapport de revenu mensuel

Le rapport `monthly_sales` répond à la question : **quel montant de ventes a-t-on par année et mois de commande ?** Le jalon minimum Junior/Mid est atteint : trois sources chargées, un schéma en étoile et un rapport agrégé reproductible.

Depuis l'étape 7, le pipeline charge aussi NATION et propose les cinq analyses métier, avec export de tous les rapports via `python -m etl.export_reports`. Consulter `README_ETAPE_7.md` pour ces ajouts et la migration en version 3 ; le rapport mensuel décrit ici conserve les mêmes résultats.

## 1. Reproduire le chargement et ouvrir le rapport

Depuis la racine du projet, avec l'environnement préparé :

```bash
source .venv/bin/activate
python -m etl.load_sources
python -m pytest -q tests
datasette serve outputs/warehouse.sqlite --host 127.0.0.1 --port 8001
```

Ouvrir [le tableau mensuel](http://127.0.0.1:8001/warehouse/monthly_sales?_sort=period&_size=max). On peut aussi ouvrir `http://127.0.0.1:8001`, choisir `warehouse`, puis la vue `monthly_sales` dans la liste des vues. Arrêter le serveur avec Ctrl+C.

Dans l'éditeur SQL de la base, la requête suivante affiche le même tableau :

```sql
SELECT * FROM monthly_sales ORDER BY period;
```

Pour exporter le résultat complet, ouvrir [le rapport CSV](http://127.0.0.1:8001/warehouse/monthly_sales.csv?_sort=period&_size=max). La vue interroge les données validées ; elle se met à jour après chaque chargement réussi. Un CSV téléchargé reste une copie à réexporter après un nouveau chargement.

Une copie du résultat vérifié est disponible dans [`outputs/monthly_sales.csv`](../outputs/monthly_sales.csv).

Le fichier `sql/03_monthly_sales.sql` contient la définition complète du rapport. Le chargeur l'installe dans la même transaction que les tables. Une base de l'étape 5 reçoit cette vue au prochain chargement réussi ; ses tables et leur version de schéma restent compatibles.

## 2. Lire les colonnes

| Colonne | Signification |
| --- | --- |
| `period` | Année-mois de commande, sous la forme `AAAA-MM`. |
| `sales_lines` | Nombre de lignes de vente, et non nombre de commandes. |
| `quantity` | Quantité totale des lignes du mois. |
| `revenue_cents` | Montant après remise et hors taxe, en centimes entiers. |
| `revenue` | Même montant affiché avec deux décimales, sous forme de texte exact. |
| `period_note` | Mention « potentiellement partiel » pour le mois de la date de commande maximale. |

Pour additionner ou classer les revenus, utiliser `revenue_cents`. `revenue` sert à l'affichage et à l'export lisible. Aucune devise n'est précisée dans les fichiers.

Les mois sans ligne de vente sont absents du rapport. Un mois qui contient des ventes dont le revenu est nul reste présent. Janvier 1997 et janvier 1998 sont deux périodes différentes.

Le calendrier conserve la date de commande maximale, y compris si cette commande n'a pas de ligne. Le signalement du dernier mois repose sur cette date, sans utiliser la date du jour. Une note vide ne prouve pas que le mois est complet.

## 3. Comprendre la requête et le calcul

La vue joint `fact_sales` à `dim_date` par `date_id`, puis regroupe les faits par `year` et `month`. Cette relation donne une seule date par fait. Le rapport n'utilise pas le total des commandes et ne multiplie pas à nouveau le prix étendu par la quantité.

Le calcul par ligne est :

```sql
(extended_price_cents * (100 - discount_percent) + 50) / 100
```

Les opérandes sont des entiers SQLite. Pour les montants non négatifs du projet, l'ajout de `50` suivi de la division entière par `100` réalise l'arrondi au centime `ROUND_HALF_UP`. Le rapport additionne ensuite ces montants arrondis. Le chargeur vérifie les capacités des entiers avant de valider les faits.

Toutes les lignes sont incluses, sans filtre de statut ou de retour. La mesure décrit les commandes du jeu de données, pas un chiffre d'affaires comptable encaissé. Les taxes sont exclues.

## 4. Vérifier avec un petit exemple

Les tests utilisent notamment les lignes suivantes :

| Mois | Prix étendu | Remise | Revenu arrondi |
| --- | ---: | ---: | ---: |
| 1997-01 | 10,05 | 10 % | 9,05 |
| 1997-01 | 5,00 | 0 % | 5,00 |
| 1998-01 | 0,05 | 10 % | 0,05 |
| 1998-01 | 0,05 | 10 % | 0,05 |
| 1998-03 | 20,00 | 100 % | 0,00 |

Résultats attendus : janvier 1997 = **14,05**, janvier 1998 = **0,10**, mars 1998 = **0,00**. Février 1998, sans vente, ne figure pas dans le résultat. Les deux montants de `0,045` sont arrondis séparément à `0,05` ; leur somme vaut `0,10`.

## 5. Résultat sur les fichiers fournis

Le rapport contient **80 mois**, de janvier 1992 à août 1998, pour des commandes datées du 01/01/1992 au 02/08/1998.

| Période | Lignes | Quantité | Revenu | Note |
| --- | ---: | ---: | ---: | --- |
| 1992-01 | 837 | 21 883 | 29 253 389,85 | |
| 1992-02 | 716 | 17 870 | 23 707 595,56 | |
| 1992-03 | 843 | 21 465 | 28 292 976,85 | |
| … | … | … | … | |
| 1998-06 | 681 | 17 556 | 23 423 472,23 | |
| 1998-07 | 757 | 19 758 | 26 283 122,09 | |
| 1998-08 | 44 | 1 125 | 1 515 799,62 | potentiellement partiel |

Au total : **60 175 lignes**, **1 536 127 unités** et **204 513 495 230 centimes**, soit **2 045 134 952,30** après remise et hors taxe. Août 1998 reste dans ce premier rapport ; son exclusion concerne uniquement la future comparaison de périodes de l'étape 7.

Pour retrouver ces totaux :

```sql
SELECT SUM(sales_lines) AS sales_lines,
       SUM(quantity) AS quantity,
       SUM(revenue_cents) AS revenue_cents
FROM monthly_sales;
```

## 6. Tests

`tests/test_monthly_sales.py` vérifie les résultats manuels, la séparation des années, les arrondis par ligne, les mois absents, les revenus nuls, la note du dernier mois et l'affichage exact des grands montants. Un test charge les fichiers fournis et compare chaque mois à un calcul indépendant réalisé depuis les fichiers avec `Decimal`.

La suite complète comptait 52 tests réussis à cette étape. Les réponses HTML et CSV de Datasette ont également été vérifiées : statut HTTP 200, 80 mois exportés et total conforme. L'ajout de NATION et des cinq analyses métier est maintenant réalisé à l'étape 7.
