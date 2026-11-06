# Exploration des données sources

Périmètre : huit fichiers complets, sans échantillonnage. Le chargement ETL et les règles des rapports seront traités à l'étape suivante.

| Table | Colonnes | Clé primaire |
| --- | --- | --- |
| nation | 4 | N_NATIONKEY |
| region | 3 | R_REGIONKEY |
| part | 9 | P_PARTKEY |
| supplier | 7 | S_SUPPKEY |
| partsupp | 5 | PS_PARTKEY, PS_SUPPKEY |
| customer | 8 | C_CUSTKEY |
| orders | 9 | O_ORDERKEY |
| lineitem | 16 | L_ORDERKEY, L_LINENUMBER |

## Format et volumes

Texte ASCII sans en-tête, séparé par `|`, avec un séparateur final. Les décimales utilisent un point et les dates le format AAAA-MM-JJ.

| Table | Lignes | Colonnes utiles | Octets | Identique au ZIP |
| --- | --- | --- | --- | --- |
| nation | 25 | 4 | 2224 | True |
| region | 5 | 3 | 389 | True |
| part | 2000 | 9 | 237134 | True |
| supplier | 100 | 7 | 13795 | True |
| partsupp | 8000 | 5 | 1161705 | True |
| customer | 1500 | 8 | 240990 | True |
| orders | 15000 | 9 | 1659137 | True |
| lineitem | 60175 | 16 | 7264250 | True |

## Qualité des fichiers

Toutes les lignes ont été lues et les types ont été convertis. Une erreur de structure ou de conversion interrompt l'exécution avec sa cause.

| Table | Valeurs vides | Clés répétées (lignes en excès) | Lignes identiques en excès | Conversions |
| --- | --- | --- | --- | --- |
| nation | 0 | 0 | 0 | OK |
| region | 0 | 0 | 0 | OK |
| part | 0 | 0 | 0 | OK |
| supplier | 0 | 0 | 0 | OK |
| partsupp | 0 | 0 | 0 | OK |
| customer | 0 | 0 | 0 | OK |
| orders | 0 | 0 | 0 | OK |
| lineitem | 0 | 0 | 0 | OK |

## Intégrité référentielle

| Relation | Lignes orphelines |
| --- | --- |
| nation (N_REGIONKEY) → region | 0 |
| customer (C_NATIONKEY) → nation | 0 |
| supplier (S_NATIONKEY) → nation | 0 |
| orders (O_CUSTKEY) → customer | 0 |
| partsupp (PS_PARTKEY) → part | 0 |
| partsupp (PS_SUPPKEY) → supplier | 0 |
| lineitem (L_ORDERKEY) → orders | 0 |
| lineitem (L_PARTKEY, L_SUPPKEY) → partsupp | 0 |

## Dates et contrôles métier

| Table | Date | Minimum | Maximum |
| --- | --- | --- | --- |
| orders | O_ORDERDATE | 1992-01-01 | 1998-08-02 |
| lineitem | L_SHIPDATE | 1992-01-04 | 1998-11-29 |
| lineitem | L_COMMITDATE | 1992-02-02 | 1998-10-28 |
| lineitem | L_RECEIPTDATE | 1992-01-09 | 1998-12-25 |

| Contrôle / observation | Nombre de lignes |
| --- | --- |
| Quantités nulles ou négatives | 0 |
| Prix étendus négatifs | 0 |
| Remises hors [0, 1] | 0 |
| Taxes hors [0, 1] | 0 |
| Expéditions avant commande | 0 |
| Réceptions avant expédition | 0 |
| Clients avec solde négatif (observation) | 139 |
| Réceptions après date d'engagement (observation) | 37897 |

## Catégories et cardinalités

### customer.C_MKTSEGMENT

| Valeur | Nombre de lignes |
| --- | --- |
| AUTOMOBILE | 302 |
| BUILDING | 337 |
| FURNITURE | 279 |
| HOUSEHOLD | 294 |
| MACHINERY | 288 |

### orders.O_ORDERSTATUS

| Valeur | Nombre de lignes |
| --- | --- |
| F | 7304 |
| O | 7333 |
| P | 363 |

### lineitem.L_SHIPMODE

| Valeur | Nombre de lignes |
| --- | --- |
| AIR | 8491 |
| FOB | 8641 |
| MAIL | 8669 |
| RAIL | 8566 |
| REG AIR | 8616 |
| SHIP | 8482 |
| TRUCK | 8710 |

### lineitem.L_RETURNFLAG

| Valeur | Nombre de lignes |
| --- | --- |
| A | 14876 |
| N | 30397 |
| R | 14902 |

### lineitem.L_LINESTATUS

| Valeur | Nombre de lignes |
| --- | --- |
| F | 30126 |
| O | 30049 |

| Observation | Résultat |
| --- | --- |
| Clients sans commande | 500 |
| Commandes sans ligne | 0 |
| Minimum de lignes par commande présente dans LINEITEM | 1 |
| Maximum de lignes par commande présente dans LINEITEM | 7 |

## Dictionnaire des données

| Table | Colonne | Type de lecture | Vides | Valeurs distinctes | Minimum | Maximum |
| --- | --- | --- | --- | --- | --- | --- |
| nation | N_NATIONKEY | INTEGER | 0 | 25 | 0 | 24 |
| nation | N_NAME | TEXT | 0 | 25 | — | — |
| nation | N_REGIONKEY | INTEGER | 0 | 5 | 0 | 4 |
| nation | N_COMMENT | TEXT | 0 | 25 | — | — |
| region | R_REGIONKEY | INTEGER | 0 | 5 | 0 | 4 |
| region | R_NAME | TEXT | 0 | 5 | — | — |
| region | R_COMMENT | TEXT | 0 | 5 | — | — |
| part | P_PARTKEY | INTEGER | 0 | 2000 | 1 | 2000 |
| part | P_NAME | TEXT | 0 | 2000 | — | — |
| part | P_MFGR | TEXT | 0 | 5 | — | — |
| part | P_BRAND | TEXT | 0 | 25 | — | — |
| part | P_TYPE | TEXT | 0 | 150 | — | — |
| part | P_SIZE | INTEGER | 0 | 50 | 1 | 50 |
| part | P_CONTAINER | TEXT | 0 | 40 | — | — |
| part | P_RETAILPRICE | Decimal | 0 | 1099 | 901.00 | 1900.99 |
| part | P_COMMENT | TEXT | 0 | 1959 | — | — |
| supplier | S_SUPPKEY | INTEGER | 0 | 100 | 1 | 100 |
| supplier | S_NAME | TEXT | 0 | 100 | — | — |
| supplier | S_ADDRESS | TEXT | 0 | 100 | — | — |
| supplier | S_NATIONKEY | INTEGER | 0 | 25 | 0 | 24 |
| supplier | S_PHONE | TEXT | 0 | 100 | — | — |
| supplier | S_ACCTBAL | Decimal | 0 | 100 | -966.20 | 9915.24 |
| supplier | S_COMMENT | TEXT | 0 | 100 | — | — |
| partsupp | PS_PARTKEY | INTEGER | 0 | 2000 | 1 | 2000 |
| partsupp | PS_SUPPKEY | INTEGER | 0 | 100 | 1 | 100 |
| partsupp | PS_AVAILQTY | INTEGER | 0 | 5497 | 3 | 9998 |
| partsupp | PS_SUPPLYCOST | Decimal | 0 | 7665 | 1.05 | 999.99 |
| partsupp | PS_COMMENT | TEXT | 0 | 8000 | — | — |
| customer | C_CUSTKEY | INTEGER | 0 | 1500 | 1 | 1500 |
| customer | C_NAME | TEXT | 0 | 1500 | — | — |
| customer | C_ADDRESS | TEXT | 0 | 1500 | — | — |
| customer | C_NATIONKEY | INTEGER | 0 | 25 | 0 | 24 |
| customer | C_PHONE | TEXT | 0 | 1500 | — | — |
| customer | C_ACCTBAL | Decimal | 0 | 1499 | -994.79 | 9987.71 |
| customer | C_MKTSEGMENT | TEXT | 0 | 5 | — | — |
| customer | C_COMMENT | TEXT | 0 | 1500 | — | — |
| orders | O_ORDERKEY | INTEGER | 0 | 15000 | 1 | 60000 |
| orders | O_CUSTKEY | INTEGER | 0 | 1000 | 1 | 1499 |
| orders | O_ORDERSTATUS | TEXT | 0 | 3 | — | — |
| orders | O_TOTALPRICE | Decimal | 0 | 14996 | 874.89 | 466001.28 |
| orders | O_ORDERDATE | DATE | 0 | 2401 | 1992-01-01 | 1998-08-02 |
| orders | O_ORDERPRIORITY | TEXT | 0 | 5 | — | — |
| orders | O_CLERK | TEXT | 0 | 1000 | — | — |
| orders | O_SHIPPRIORITY | INTEGER | 0 | 1 | 0 | 0 |
| orders | O_COMMENT | TEXT | 0 | 14995 | — | — |
| lineitem | L_ORDERKEY | INTEGER | 0 | 15000 | 1 | 60000 |
| lineitem | L_PARTKEY | INTEGER | 0 | 2000 | 1 | 2000 |
| lineitem | L_SUPPKEY | INTEGER | 0 | 100 | 1 | 100 |
| lineitem | L_LINENUMBER | INTEGER | 0 | 7 | 1 | 7 |
| lineitem | L_QUANTITY | INTEGER | 0 | 50 | 1 | 50 |
| lineitem | L_EXTENDEDPRICE | Decimal | 0 | 35921 | 904.00 | 94949.50 |
| lineitem | L_DISCOUNT | Decimal | 0 | 11 | 0.00 | 0.10 |
| lineitem | L_TAX | Decimal | 0 | 9 | 0.00 | 0.08 |
| lineitem | L_RETURNFLAG | TEXT | 0 | 3 | — | — |
| lineitem | L_LINESTATUS | TEXT | 0 | 2 | — | — |
| lineitem | L_SHIPDATE | DATE | 0 | 2518 | 1992-01-04 | 1998-11-29 |
| lineitem | L_COMMITDATE | DATE | 0 | 2460 | 1992-02-02 | 1998-10-28 |
| lineitem | L_RECEIPTDATE | DATE | 0 | 2529 | 1992-01-09 | 1998-12-25 |
| lineitem | L_SHIPINSTRUCT | TEXT | 0 | 4 | — | — |
| lineitem | L_SHIPMODE | TEXT | 0 | 7 | — | — |
| lineitem | L_COMMENT | TEXT | 0 | 58616 | — | — |

## Conséquences pour le futur ETL

- CUSTOMER contient 8 colonnes, ORDERS 9 et LINEITEM 16. Retirer seulement le champ supplémentaire créé par le séparateur final.
- Relations principales : CUSTOMER.C_CUSTKEY → ORDERS.O_CUSTKEY puis ORDERS.O_ORDERKEY → LINEITEM.L_ORDERKEY. Un client peut avoir plusieurs commandes, une commande plusieurs lignes.
- Le DDL utilise les clés composées (L_ORDERKEY, L_LINENUMBER) et (PS_PARTKEY, PS_SUPPKEY). L'image ERD présente des identifiants l_id, l_ps_id et ps_id absents des fichiers et du DDL : retenir les clés du DDL pour la lecture source.
- Les clés et quantités se lisent comme des entiers ; téléphones et commentaires restent du texte ; les dates restent au format ISO.
- Les montants, remises et taxes contiennent des décimales malgré les INTEGER du DDL. En exploration, utiliser Decimal. Pour SQLite, prévoir des centimes entiers pour les montants sources et des centièmes entiers pour les taux (0.04 → 4).
- Le calcul après remise peut produire des fractions de centime : la règle retenue à l'étape 3 est l'arrondi au centime par ligne avec ROUND_HALF_UP, puis la somme des montants arrondis. Voir `README_ETAPE_3.md` pour la spécification.
- Les données sont historiques. Choisir une période de comparaison dans les données disponibles ; réserver la redistribution des dates au bonus.
- Ne pas supprimer automatiquement les soldes négatifs ni les retards de livraison : conserver ces observations et expliquer leur sens métier.
- Ne pas additionner O_TOTALPRICE après une jointure qui le répète pour chaque ligne de commande.
- Préserver les clients sans commande dans la future dimension client.
- Le périmètre Junior/Mid commence avec CUSTOMER, ORDERS et LINEITEM ; NATION sera nécessaire pour les analyses par pays. Les références à des tables non chargées devront être gérées explicitement.

## Utiliser le notebook simplifié

Ce rapport conserve les résultats de l'exploration complète des huit fichiers effectuée le 04/11/2026.

Le notebook `notebooks/01_data_exploration.ipynb` a ensuite été simplifié pour expliquer les étapes : lecture des fichiers, comptage, valeurs vides, doublons, relations, dates, montants et catégories. Il détaille CUSTOMER, ORDERS et LINEITEM, ainsi que NATION pour les pays, et compte les lignes des huit fichiers. Il ne refait pas tous les contrôles détaillés de ce rapport et ne le régénère pas.

Ouvrir le notebook avec le noyau Python `.venv`, puis exécuter les cellules une par une. Il utilise uniquement les bibliothèques standard de Python et ne modifie pas les données sources.
