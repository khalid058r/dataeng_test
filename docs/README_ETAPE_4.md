# Étape 4 — Charger les trois tables sources

Le chargement de CUSTOMER, ORDERS et LINEITEM est implémenté. Il suit les règles de `README_ETAPE_3.md` et prépare l'alimentation du modèle en étoile à l'étape 5.

Depuis l'étape 5, la commande ci-dessous charge aussi les dimensions et les faits dans la même transaction. Depuis l'étape 7, elle charge également NATION avant CUSTOMER et contrôle la référence pays. Ce document détaille le chargement initial des trois sources ; consulter `README_ETAPE_7.md` pour le périmètre et la migration actuels.

## 1. Exécuter le chargement

Prérequis : Python 3.12 et SQLite 3.37 ou supérieur, accessible via le module standard `sqlite3`. Le chargeur utilise uniquement la bibliothèque standard Python. Datasette sert à consulter les résultats et pytest à exécuter les tests.

Depuis la racine du projet, avec l'environnement déjà préparé :

```bash
source .venv/bin/activate
python -m etl.load_sources
```

Le chargeur lit `data/customer.tbl`, `data/orders.tbl` et `data/lineitem.tbl`, puis crée `outputs/warehouse.sqlite`. Ces chemins par défaut sont calculés depuis l'emplacement du code.

Volumes sources attendus avec les fichiers fournis (la sortie actuelle inclut aussi les trois tables du schéma en étoile) :

```text
CUSTOMER : 1 500 lignes chargées
ORDERS : 15 000 lignes chargées
LINEITEM : 60 175 lignes chargées
Chargement validé : <racine du projet>/outputs/warehouse.sqlite
```

Les volumes ne sont affichés qu'après validation de toute la transaction. Ils sont comptés à la lecture, sans limite de lignes codée pour le jeu fourni.

Pour choisir les chemins :

```bash
python -m etl.load_sources --data-dir data --database outputs/warehouse.sqlite
```

Les chemins explicitement fournis sont relatifs au dossier courant. Depuis un autre dossier, on peut utiliser le chemin absolu vers `etl/load_sources.py` et des chemins absolus pour les arguments.

## 2. Comprendre les fichiers de code

| Fichier | Responsabilité |
| --- | --- |
| `etl/load_sources.py` | Lire les fichiers, convertir les champs, charger les sources et le modèle en étoile, puis gérer la transaction. |
| `sql/01_sources.sql` | Définir les trois tables sources et leurs contraintes. |
| `sql/02_star_schema.sql` | Définir les dimensions et les faits ajoutés à l'étape 5. |
| `tests/test_load_sources.py` | Vérifier conversions, intégrité, relances, erreurs et données fournies. |

Les fichiers sont lus ligne par ligne ; le chargeur ne les conserve pas entièrement en mémoire. Les colonnes sont décrites dans l'ordre des fichiers, puisque ceux-ci n'ont pas d'en-tête.

## 3. Qu'est-ce qui est stocké ?

Les noms de colonnes restent ceux de l'énoncé, sauf les champs convertis dont le suffixe indique l'unité :

| Colonne source | Colonne SQLite | Exemple |
| --- | --- | --- |
| `C_ACCTBAL` | `C_ACCTBAL_CENTS` | `-12.34` → `-1234` |
| `O_TOTALPRICE` | `O_TOTALPRICE_CENTS` | `100.25` → `10025` |
| `L_EXTENDEDPRICE` | `L_EXTENDEDPRICE_CENTS` | `10.05` → `1005` |
| `L_DISCOUNT` | `L_DISCOUNT_PERCENT` | `0.10` → `10` |
| `L_TAX` | `L_TAX_PERCENT` | `0.02` → `2` |

La conversion utilise `Decimal` : elle vérifie d'abord que la valeur est représentable avec deux décimales, puis la multiplie par 100 et la convertit en entier. Les valeurs comme `1.001` sont refusées et ne sont pas tronquées en centimes. Les soldes clients négatifs sont acceptés. Les dates sont validées puis conservées en texte `AAAA-MM-JJ`. Les téléphones et les espaces des commentaires sont conservés comme texte.

Le schéma SQLite est `STRICT` : les colonnes entières ne stockent pas de valeurs flottantes. Les clés sont `C_CUSTKEY`, `O_ORDERKEY` et le couple `(L_ORDERKEY, L_LINENUMBER)`. Les références contrôlées sont ORDERS → CUSTOMER et LINEITEM → ORDERS. Les références vers NATION, PART et PARTSUPP attendent leur intégration.

Le DDL original `ddl.sql` est conservé comme partie de l'énoncé. Le chargeur utilise `sql/01_sources.sql`, adapté à ce périmètre et aux unités choisies.

## 4. Relance et gestion des erreurs

À chaque exécution, les données des six tables sont remplacées intégralement, sans suppression du fichier SQLite. L'ordre est le suivant :

1. Vérifier la présence des trois fichiers non vides et la destination.
2. Activer les clés étrangères et démarrer une transaction d'écriture.
3. Créer les tables si nécessaire.
4. Vider les faits et dimensions, puis LINEITEM, ORDERS et CUSTOMER.
5. Charger CUSTOMER, puis ORDERS, puis LINEITEM.
6. Charger les dimensions, puis les faits, et contrôler les volumes et les mesures.
7. Valider la transaction seulement si tout a réussi.

Une ligne invalide, une clé répétée ou une référence absente provoque l'annulation de toute l'exécution. Les données précédemment validées restent disponibles. Si le premier chargement échoue après ouverture de la base, un fichier SQLite vide peut rester sur disque, sans tables ni données partielles.

Le programme termine avec le code `0` en cas de succès et `1` en cas d'erreur de chargement. Le message d'erreur est écrit sur la sortie d'erreur et indique le fichier, la ligne et la colonne quand ils sont disponibles. Aucun doublon ni aucune ligne invalide ne sont ignorés silencieusement.

Une base existante non vide sans l'identifiant du projet est refusée pour éviter de remplacer des tables étrangères au projet. L'identifiant et la version sont stockés dans les métadonnées SQLite `application_id` et `user_version`. Les autres tables d'une base du projet ne sont pas supprimées.

Depuis l'étape 5, les dimensions et les faits sont reconstruits dans la même transaction afin de garder sources et entrepôt cohérents. La base de l'étape 4 est mise à niveau automatiquement lors d'un chargement réussi.

## 5. Consulter les données

Après le chargement :

```bash
datasette serve outputs/warehouse.sqlite --host 127.0.0.1 --port 8001
```

Ouvrir `http://127.0.0.1:8001`, puis la base et les tables. Arrêter le serveur avec Ctrl+C.

Exemples de contrôles SQL :

```sql
SELECT 'CUSTOMER' AS table_name, COUNT(*) AS row_count FROM customer
UNION ALL
SELECT 'ORDERS', COUNT(*) FROM orders
UNION ALL
SELECT 'LINEITEM', COUNT(*) FROM lineitem;

SELECT SUM(L_QUANTITY) AS quantity,
       SUM(L_EXTENDEDPRICE_CENTS) AS extended_price_cents
FROM lineitem;

PRAGMA foreign_key_check;
```

Le dernier contrôle ne doit retourner aucune ligne.

## 6. Exécuter les tests

Depuis la racine du projet :

```bash
python -m pytest -q tests
```

Les tests travaillent dans des dossiers temporaires. Ils couvrent les fichiers avec ou sans séparateur final, les conversions exactes, la clé composée, les références entre tables, les champs invalides, les fichiers absents ou vides, les erreurs de lecture et la relance sans doublons. Ils vérifient aussi qu'une erreur conserve la version précédente, qu'une première exécution ratée ne laisse pas de tables partielles et qu'une base étrangère est préservée.

Un test charge les fichiers fournis et compare les quantités et les montants stockés aux totaux calculés séparément depuis les fichiers.

L'alimentation de `dim_customer`, `dim_date` et `fact_sales` est réalisée à l'étape 5. Le rapport agrégé `monthly_sales` est réalisé à l'étape 6 ; consulter `README_ETAPE_6.md`.

## 7. Lire le code simplement

Commencer par `main`, en bas de `etl/load_sources.py`, puis suivre les appels dans cet ordre :

```text
main
  → load_sources : préparer la base et la transaction
      → load_file : lire chaque fichier et insérer ses lignes
          → convert_value : convertir un champ
              → hundredths : convertir les montants et les taux
      → load_star : alimenter les dimensions, les faits et contrôler les mesures
```

### Les colonnes et leurs types

`SOURCE_COLUMNS` décrit chaque fichier. Par exemple :

```python
"C_CUSTKEY": "integer",
"C_NAME": "text",
"C_ACCTBAL": "hundredths",
```

Cela signifie : lire le code client comme un entier, garder son nom comme texte et convertir son solde en centimes. Les colonnes sont écrites dans le même ordre que les champs du fichier.

`STORED_NAMES` donne les noms des colonnes dont l'unité change dans SQLite. Par exemple, `C_ACCTBAL` devient `C_ACCTBAL_CENTS` afin que le nom indique clairement ce qu'on stocke.

### Convertir une valeur

`convert_value` commence par refuser un champ vide, puis choisit une conversion selon le type :

| Type dans le code | Texte lu | Résultat transmis à SQLite |
| --- | --- | --- |
| `text` | `Alice` | `Alice`, conservé comme texte |
| `integer` | `12` | `12`, converti en entier |
| `date` | `1998-07-01` | Le même texte, après vérification de la date |
| `hundredths` | `12.34` | `1234`, un entier |
| `hundredths` | `0.10` | `10`, un entier utilisé comme pourcentage |

La fonction `hundredths` utilise `Decimal`, qui lit directement le texte décimal sans passer par un nombre flottant. Elle compare la valeur à sa version à deux décimales : si elles diffèrent, elle refuse la valeur. Cette comparaison empêche `1.001` d'être transformé silencieusement en `100` centimes. `localcontext(prec=28)` fixe la précision du calcul décimal ; elle suffit pour les nombres qu'on peut stocker dans un entier SQLite.

Les conversions vérifient la forme des valeurs. Les contraintes de `sql/01_sources.sql` vérifient les règles métier : par exemple, `CHECK (L_QUANTITY > 0)` refuse une quantité nulle ou négative. Ces règles restent ainsi vérifiées par la base elle-même.

### Lire et insérer une ligne

Dans `load_file`, `csv.reader` sépare les champs avec `|`. Pour une ligne terminée par `|`, il produit aussi un dernier champ vide. On retire ce champ supplémentaire, puis on vérifie le nombre de colonnes.

La boucle avec `zip(columns.items(), row)` associe chaque nom de colonne et son type à la valeur située au même emplacement dans la ligne. Chaque valeur est convertie, puis ajoutée à la liste `values`.

L'insertion utilise des paramètres SQL :

```python
connection.execute(statement, values)
```

`statement` contient une requête de la forme `INSERT INTO customer (...) VALUES (?, ?, ...)`. Chaque `?` est remplacé par la valeur correspondante de `values`, transmise séparément à SQLite. Le texte d'un nom ou d'un commentaire n'est donc pas assemblé dans la requête SQL.

### Tout valider ou tout annuler

`load_sources` commence la transaction et crée les tables si nécessaire. Depuis l'étape 5, il vide d'abord les faits et les dimensions, puis les sources enfants avant les parents : LINEITEM, ORDERS, CUSTOMER. Il recharge les sources dans l'ordre inverse, puis appelle `load_star` pour les dimensions et les faits.

Les trois opérations finales ont des rôles différents :

```python
connection.commit()    # Succès : conserver toutes les nouvelles données.
connection.rollback()  # Erreur : retrouver toutes les anciennes données.
connection.close()     # Dans tous les cas : fermer la connexion.
```

Dans le code, `commit` est dans le bloc `try`, `rollback` dans `except` et `close` dans `finally`. `raise` transmet l'erreur à `main`, qui affiche le message et termine avec le code d'échec `1`.

`check_destination` est un contrôle séparé : il autorise une base vide ou une base déjà créée par ce projet. Il évite de remplacer les données d'une autre base SQLite.
