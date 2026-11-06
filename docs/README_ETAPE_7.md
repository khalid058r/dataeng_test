# Étape 7 — NATION et les cinq analyses métier

Les quatre sources NATION, CUSTOMER, ORDERS et LINEITEM alimentent maintenant le schéma en étoile. Les cinq questions de l'énoncé sont couvertes par des vues SQL consultables dans Datasette et exportables en CSV.

## 1. Reproduire les résultats

Depuis la racine du projet :

```bash
source .venv/bin/activate
python -m etl.load_sources
python -m etl.export_reports
python -m pytest -q tests
datasette serve outputs/warehouse.sqlite --host 127.0.0.1 --port 8001
```

Ouvrir `http://127.0.0.1:8001/warehouse`, puis choisir une vue. Les fichiers SQL se trouvent dans `sql/03_monthly_sales.sql` et `sql/04_business_reports.sql`. La commande d'export lit un instantané cohérent de la base en lecture seule, puis écrit les sept CSV dans `outputs/` avec leurs en-têtes. Elle remplace les précédents exports de ces noms. Les champs SQL `NULL` deviennent des cellules vides dans les CSV.

Pour choisir les destinations :

```bash
python -m etl.load_sources --data-dir data --database outputs/warehouse.sqlite
python -m etl.export_reports --database outputs/warehouse.sqlite --output-dir outputs
```

Les chemins par défaut sont calculés depuis l'emplacement du code. Les chemins fournis explicitement sont relatifs au dossier courant. Les commandes retournent `0` en cas de succès et `1` en cas d'erreur ; lancer l'export après un chargement réussi pour publier les nouveaux résultats.

## 2. Ajouter le pays sans changer le grain

NATION contient 25 lignes dans les fichiers fournis. Ses colonnes sont `N_NATIONKEY`, `N_NAME`, `N_REGIONKEY` et `N_COMMENT`. La clé pays peut valoir zéro. La référence vers REGION n'est pas contrôlée puisque cette table n'est pas chargée.

Le chargement suit l'ordre NATION → CUSTOMER → ORDERS → LINEITEM. Une clé étrangère relie désormais `customer.C_NATIONKEY` à `nation.N_NATIONKEY`. Un client associé à un pays absent fait échouer toute l'exécution, avec le fichier, la ligne et la colonne concernés.

`dim_customer` conserve `nation_id` et reçoit `nation_name` par jointure de CUSTOMER avec NATION. Il s'agit du **pays du client**, et non d'un pays de livraison. Le grain des faits reste une ligne de commande, identifiée par `(order_id, line_number)`.

Le pays est recopié dans la dimension pour permettre les analyses depuis l'étoile. Il n'est pas nécessaire de joindre la table source NATION dans les rapports. Les 1 500 clients sont conservés dans la dimension, y compris les 500 sans commande.

## 3. Les cinq analyses

Dans l'éditeur SQL de Datasette, exécuter chaque requête séparément.

### 1 — Top 5 des pays par revenu

```sql
SELECT * FROM top_5_nations
ORDER BY revenue_cents DESC, nation_id;
```

La vue `sales_by_customer` additionne les revenus des lignes par client. `sales_by_nation` additionne ces totaux par pays. `top_5_nations` retient les cinq pays de revenu le plus élevé ; le code pays croissant départage les égalités. Si moins de cinq pays ont des ventes, tous sont retournés.

Résultat sur les fichiers fournis :

| Code | Pays | Lignes | Revenu après remise |
| --- | --- | ---: | ---: |
| 3 | CANADA | 3 089 | 105 337 575,25 |
| 4 | EGYPT | 2 945 | 102 254 395,42 |
| 10 | IRAN | 2 952 | 100 283 452,47 |
| 2 | BRAZIL | 2 843 | 94 333 197,23 |
| 0 | ALGERIA | 2 773 | 93 680 675,67 |

### 2 — Mode de transport le plus fréquent parmi ces pays

```sql
SELECT * FROM top_shipping_modes ORDER BY ship_mode;
```

Le comptage est **global sur les lignes des cinq pays réunis**. Une ligne compte une fois, quelle que soit sa quantité ou son revenu. Tous les modes ex æquo au premier rang sont retournés, par nom croissant. Le top des pays et les fréquences sont calculés une fois dans des CTE `MATERIALIZED`, pour éviter de refaire ces agrégations pendant les jointures.

Résultat : **FOB, avec 2 118 lignes**.

### 3 — Meilleurs mois de vente

```sql
SELECT * FROM best_sales_months ORDER BY position LIMIT 5;
```

La vue classe les 80 périodes année-mois par revenu décroissant, puis chronologiquement en cas d'égalité. Elle reprend le rapport mensuel de l'étape 6 et conserve sa note « potentiellement partiel » pour août 1998. Les mois sans vente sont absents.

| Rang | Période | Revenu après remise |
| --- | --- | ---: |
| 1 | 1993-12 | 29 616 353,18 |
| 2 | 1993-10 | 29 558 233,42 |
| 3 | 1992-01 | 29 253 389,85 |
| 4 | 1996-08 | 28 974 470,92 |
| 5 | 1995-12 | 28 896 188,46 |

### 4 — Meilleurs clients par revenu et par quantité

```sql
SELECT * FROM customers_by_revenue ORDER BY position LIMIT 10;
```

```sql
SELECT * FROM customers_by_quantity ORDER BY position LIMIT 10;
```

Chaque vue contient le classement complet des 1 000 clients ayant des lignes de vente ; les requêtes ci-dessus en affichent les dix premiers. En cas d'égalité sur la mesure classée, l'identifiant client croissant départage les résultats. Les clients sans vente restent dans la dimension et ne figurent pas dans ces classements.

Premiers clients par revenu :

| Rang | Client | Revenu après remise | Quantité |
| --- | --- | ---: | ---: |
| 1 | 1489 — Customer#000001489 | 5 203 674,08 | 3 868 |
| 2 | 214 — Customer#000000214 | 4 503 703,94 | 3 369 |
| 3 | 73 — Customer#000000073 | 4 466 381,07 | 3 384 |

Premiers clients par quantité : **1489 (3 868 unités)**, **1396 (3 408 unités)**, puis **73 (3 384 unités)**.

### 5 — Revenu de la période courante contre la précédente

```sql
SELECT * FROM period_comparison;
```

Le rapport utilise les deux mois civils précédant celui de la date de commande maximale. Il ne dépend pas de la date du jour. Avec une dernière commande au 02/08/1998, il compare **juillet 1998 à juin 1998** et exclut août, potentiellement partiel. Ce choix suppose la complétude des mois antérieurs ; les fichiers seuls ne permettent pas de la certifier.

| Mesure | Résultat |
| --- | ---: |
| Revenu de juillet 1998 | 26 283 122,09 |
| Revenu de juin 1998 | 23 423 472,23 |
| Écart absolu | +2 859 649,86 |
| Variation | +12,21 % |
| Statut | `ok` |

Les revenus et l'écart sont des centimes entiers. `change_percent` affiche le ratio `100 × (courant − précédent) / précédent` avec deux décimales, sous forme de texte ; seule cette division de pourcentage utilise le calcul réel SQLite.

Si une période n'a aucune ligne, son revenu est `NULL`, les variations sont `NULL` et le statut est « période absente ». On ne la remplace pas par un autre mois. Si le revenu précédent est zéro mais la période présente, l'écart absolu reste calculé, le pourcentage est `NULL` et le statut est « base précédente nulle ».

## 4. Unités et jointures

Tous les rapports utilisent le prix étendu après remise, hors taxe, arrondi au centime par ligne avec `ROUND_HALF_UP`. Les montants numériques portent le suffixe `_cents` ; diviser par 100 uniquement pour l'affichage. Aucune devise ni conversion de devise n'est définie par les sources.

Le prix étendu inclut déjà la quantité. Les rapports ne le multiplient pas par la quantité et ne recopient pas `O_TOTALPRICE` sur les faits. Les jointures utilisent les clés uniques des dimensions : aucune ligne de vente n'est multipliée. La somme du revenu par client, par pays ou par mois est la même : **204 513 495 230 centimes**.

## 5. Migration et relance

La base est maintenant de version `3`. Les versions `1` et `2` du projet sont mises à niveau automatiquement lors du prochain chargement réussi. Dans la transaction, les enfants sont d'abord vidés, puis CUSTOMER et `dim_customer` sont recréées pour ajouter respectivement la référence à NATION et le nom du pays. Les autres tables du projet sont rechargées ; les tables étrangères au pipeline, comme d'éventuelles notes, sont conservées.

Toutes les créations, la migration et les écritures font partie de la même transaction. Si un fichier, une clé, une conversion ou un contrôle échoue, la structure et les données précédentes sont restaurées. Les versions inconnues et les bases étrangères au projet sont refusées. La relance avec les mêmes fichiers conserve les sept tables et les résultats des rapports.

Volumes vérifiés : 25 pays, 1 500 clients, 15 000 commandes, 60 175 lignes sources, 1 500 clients en dimension, 2 406 dates et 60 175 faits.

## 6. Fichiers exportés et contrôles

| Fichier dans `outputs/` | Nombre de lignes de résultat |
| --- | ---: |
| `monthly_sales.csv` | 80 |
| `top_5_nations.csv` | 5 |
| `top_shipping_modes.csv` | 1 |
| `best_sales_months.csv` | 80 |
| `customers_by_revenue.csv` | 1 000 |
| `customers_by_quantity.csv` | 1 000 |
| `period_comparison.csv` | 1 |

Les en-têtes ne sont pas compris dans ces nombres. Les CSV se retéléchargent aussi depuis chaque vue Datasette, avec le suffixe `.csv?_size=max` ; trier par `position` pour les classements, par `period` pour le rapport mensuel et par `revenue_cents` décroissant pour les pays.

La suite complète compte **80 tests réussis**. Les contrôles couvrent NATION et ses références, les doublons, les ex æquo, les arrondis, les mois absents, les revenus précédents nuls, le passage d'une année à l'autre, les migrations réussies ou annulées et les exports reproductibles. Les résultats sur le jeu fourni sont comparés à des calculs indépendants depuis les fichiers avec `Decimal` et des compteurs Python.

Sur la base générée, une relance a donné les mêmes sept tables et les mêmes sept rapports. `PRAGMA integrity_check` retourne `ok` et `PRAGMA foreign_key_check` ne retourne aucune ligne.

Les pages HTML et les exports CSV des sept rapports ont également été vérifiés dans Datasette : HTTP 200 et contenu des CSV conforme aux exports SQL locaux.

Les deux exercices d'algorithmique sont réalisés à l'étape 8 ; consulter `README_ETAPE_8.md`. L'exploitation et l'architecture sont documentées à l'étape 9 ; la validation locale finale est consignée dans `VALIDATION_FINALE.md`.
