# README temporaire — Comprendre le notebook d'exploration

Ce document explique la version actuelle de `notebooks/01_data_exploration.ipynb`, bloc par bloc.
Les blocs ci-dessous suivent l'ordre des 11 cellules de code. Aucun code du notebook n'est modifié.

## Comment travailler avec ce guide

Ouvrir le notebook et ce document côte à côte. Lire une explication, exécuter la cellule correspondante, puis regarder son résultat.
Choisir le noyau Python `.venv` et commencer au bloc 1 : les cellules suivantes utilisent des variables créées plus haut.
Après un redémarrage du noyau, il faut réexécuter les cellules dans l'ordre.
Les numéros d'exécution affichés par Jupyter ne sont pas forcément les numéros des blocs : ils dépendent de l'ordre dans lequel les cellules ont été lancées.

Ce notebook explore les données en mémoire. Il ne réalise pas encore le chargement ETL et n'écrit pas dans une base.

## Quelques bases de syntaxe

| Syntaxe | Signification |
| --- | --- |
| `nom = valeur` | Enregistrer une valeur dans une variable. |
| `"texte"` | Une chaîne de caractères. |
| `outil(...)` | Appeler une fonction ou un outil avec des arguments. |
| `objet.methode(...)` | Appeler une action disponible sur cet objet. |
| `objet.attribut` | Lire une information de cet objet, par exemple `chemin.name`. |
| `[...]` | Créer une liste, ou accéder à un élément lorsqu'il y a un objet avant les crochets. |
| `{"cle": valeur}` | Créer un dictionnaire associant des clés à des valeurs. |
| `(a, b)` | Créer un tuple contenant deux éléments. |
| `:` après `if`, `for`, `with` ou `def` | Commencer un bloc indenté. |
| Indentation | Les espaces à gauche indiquent quelles instructions appartiennent au bloc. |

Par exemple, `client["C_NAME"]` signifie « récupérer la valeur associée à la clé C_NAME dans le dictionnaire client ».


## Bloc 1 — Importer les outils

```python
from pathlib import Path
import csv
from datetime import date
from decimal import Decimal
from collections import Counter
```

**But :** rendre disponibles les outils utilisés dans les cellules suivantes.

| Instruction | Explication |
| --- | --- |
| `from pathlib import Path` | Prendre l'outil `Path` dans la bibliothèque `pathlib` pour manipuler les chemins. |
| `import csv` | Charger la bibliothèque qui lit des fichiers découpés en colonnes. |
| `from datetime import date` | Prendre l'outil qui représente une date. |
| `from decimal import Decimal` | Prendre l'outil pour lire des nombres décimaux avec précision. |
| `from collections import Counter` | Prendre l'outil qui compte les occurrences de chaque valeur. |

`from ... import ...` importe un outil précis. `import csv` importe le module, puis on utilise ses outils avec un point, par exemple `csv.reader`.

Tous ces outils font partie de Python : aucune installation supplémentaire n'est nécessaire.
Cette cellule n'ouvre encore aucun fichier.

## Bloc 2 — Trouver le dossier data

```python
data_path = Path("../data")
if not data_path.exists():
    data_path = Path("data")

print( data_path.exists())
```

**But :** indiquer où se trouvent les fichiers.

- `data_path = ...` crée une variable appelée `data_path`.
- `Path("../data")` représente le dossier `data` situé un niveau au-dessus du dossier de travail courant. `..` signifie « remonter d'un dossier ».
- `data_path.exists()` vérifie si ce chemin existe et renvoie `True` ou `False`.
- `if not ...:` signifie « si ce chemin n'existe pas ».
- La ligne indentée essaie alors `Path("data")`, c'est-à-dire le dossier `data` directement dans le dossier courant.
- `print(...)` affiche le résultat. Ici, on attend `True`.

Les chemins relatifs sont calculés depuis le dossier de travail du noyau Python. Le premier cas convient si ce dossier est `notebooks`, le second si c'est la racine du projet.

Le test final affiche seulement le résultat : si les deux chemins sont absents, il ne stoppe pas le notebook. L'ouverture du fichier échouera dans le bloc suivant.

## Bloc 3 — Lire une première ligne et retirer le champ supplémentaire

```python
with (data_path / "customer.tbl").open(encoding="ascii", newline="") as f:
    lecteur = csv.reader(f, delimiter="|", quoting=csv.QUOTE_NONE)
    l = next(lecteur)

print("Avant :", len(l), "éléments")
if len(l) == 9 and l[-1] == "":
    l.pop()
print("Après :", len(l), "colonnes")
print(l)
```

**But :** comprendre le format avant de charger toutes les lignes.

- `data_path / "customer.tbl"` construit un chemin. Avec un objet `Path`, `/` assemble des parties de chemin ; ici ce n'est pas une division.
- `.open(...)` ouvre le fichier en lecture, car aucun autre mode n'est indiqué.
- `encoding="ascii"` indique l'encodage du texte. Une valeur incompatible provoquerait une erreur de lecture.
- `newline=""` laisse le lecteur `csv` gérer les fins de ligne.
- `with ... as f:` donne au fichier ouvert le nom `f` et garantit sa fermeture en quittant le bloc, même en cas d'erreur.
- `csv.reader(f, ...)` prépare un lecteur qui découpe les lignes du fichier.
- `delimiter="|"` choisit le caractère séparant les colonnes.
- `quoting=csv.QUOTE_NONE` traite les guillemets comme des caractères ordinaires.
- `next(lecteur)` récupère seulement la première ligne. La variable `l` est une liste de textes. Ici, `l` est la lettre L minuscule.
- `len(l)` donne le nombre d'éléments de cette liste.
- `==` compare deux valeurs ; `=` affecte une valeur à une variable.
- `and` demande que les deux conditions soient vraies.
- `l[-1]` désigne le dernier élément. Les indices positifs commencent à `0` ; l'indice `-1` part de la fin.
- `""` est une chaîne de texte vide.
- `l.pop()` retire le dernier élément de la liste et modifie directement `l`.

Exemple de la logique :

```text
Ligne du fichier : 1|Alice|
Liste obtenue    : ["1", "Alice", ""]
Après pop()     : ["1", "Alice"]
```

Dans CUSTOMER, on attend 8 colonnes. Le séparateur final en produit 9 à la lecture. On retire le dernier élément uniquement si le nombre est 9 **et** si cet élément est vide.

On attend donc `Avant : 9 éléments`, puis `Après : 8 colonnes`. Le dernier `print(l)` affiche les valeurs.

## Bloc 4 — Nommer les colonnes

```python
customer_columns = [
    "C_CUSTKEY", "C_NAME", "C_ADDRESS", "C_NATIONKEY",
    "C_PHONE", "C_ACCTBAL", "C_MKTSEGMENT", "C_COMMENT"
]

orders_columns = [
    "O_ORDERKEY", "O_CUSTKEY", "O_ORDERSTATUS", "O_TOTALPRICE",
    "O_ORDERDATE", "O_ORDERPRIORITY", "O_CLERK", "O_SHIPPRIORITY", "O_COMMENT"
]

lineitem_columns = [
    "L_ORDERKEY", "L_PARTKEY", "L_SUPPKEY", "L_LINENUMBER",
    "L_QUANTITY", "L_EXTENDEDPRICE", "L_DISCOUNT", "L_TAX",
    "L_RETURNFLAG", "L_LINESTATUS", "L_SHIPDATE", "L_COMMITDATE",
    "L_RECEIPTDATE", "L_SHIPINSTRUCT", "L_SHIPMODE", "L_COMMENT"
]

nation_columns = ["N_NATIONKEY", "N_NAME", "N_REGIONKEY", "N_COMMENT"]
```

**But :** associer ensuite un nom à chaque valeur lue.

- Les crochets `[...]` créent une **liste**, c'est-à-dire une suite d'éléments conservant leur ordre.
- Chaque nom entre guillemets est une chaîne de texte.
- Les virgules séparent les éléments. Une liste peut être écrite sur plusieurs lignes entre ses crochets.
- `customer_columns`, `orders_columns`, `lineitem_columns` et `nation_columns` sont quatre variables différentes.

Les noms proviennent de `ddl.sql`. Leur ordre doit correspondre exactement à celui des valeurs dans les fichiers.

| Liste | Nombre de colonnes | Représente |
| --- | --- | --- |
| `customer_columns` | 8 | Les clients |
| `orders_columns` | 9 | Les commandes |
| `lineitem_columns` | 16 | Les lignes de commande |
| `nation_columns` | 4 | Les pays |

Exemple : la première valeur d'une ligne CUSTOMER correspond à `C_CUSTKEY`, la deuxième à `C_NAME`.
Cette cellule prépare les noms ; elle ne charge pas les données.

## Bloc 5 — Créer la fonction de lecture et charger les quatre tables

```python
def lire_fichier(nom, colonnes):
    lignes = []
    with (data_path / nom).open(encoding="ascii", newline="") as fichier:
        lecteur = csv.reader(fichier, delimiter="|", quoting=csv.QUOTE_NONE)
        for numero, ligne in enumerate(lecteur, start=1):
            if len(ligne) == len(colonnes) + 1 and ligne[-1] == "":
                ligne.pop()
            if len(ligne) != len(colonnes):
                raise ValueError(f"{nom}, ligne {numero} : nombre de colonnes incorrect")
            lignes.append(dict(zip(colonnes, ligne)))
    return lignes

customers = lire_fichier("customer.tbl", customer_columns)
orders = lire_fichier("orders.tbl", orders_columns)
lineitems = lire_fichier("lineitem.tbl", lineitem_columns)
nations = lire_fichier("nation.tbl", nation_columns)

print("Clients :", len(customers))
print("Commandes :", len(orders))
print("Lignes de commande :", len(lineitems))
print("Pays :", len(nations))
```

**But :** réutiliser la même lecture pour plusieurs fichiers.

**Définition de la fonction :**

- `def lire_fichier(nom, colonnes):` définit une fonction. `nom` et `colonnes` sont ses paramètres, c'est-à-dire les informations à lui fournir.
- Le code indenté sous `def` s'exécute lors d'un appel à la fonction.
- `lignes = []` crée la liste vide qui recevra les lignes.
- Le `with` ouvre le fichier demandé dans `data_path`.
- `for numero, ligne in enumerate(lecteur, start=1):` parcourt les lignes et fournit leur numéro, en commençant à 1.
- Le premier `if` retire le champ supplémentaire créé par le dernier `|`.
- `len(colonnes) + 1` adapte ce contrôle au nombre de colonnes du fichier demandé : 9 pour CUSTOMER, 10 pour ORDERS, etc.
- Le deuxième `if` vérifie que le nombre de valeurs est correct après ce retrait.
- `!=` signifie « différent de ».
- `raise ValueError(...)` arrête l'exécution en signalant un format incorrect.
- Le `f` devant `f"..."` crée un texte dans lequel `{nom}` et `{numero}` sont remplacés par leurs valeurs. Il n'a pas de rapport avec la variable `f` du bloc 3.

**Cette ligne associe les noms et les valeurs :**

```python
lignes.append(dict(zip(colonnes, ligne)))
```

On peut la lire de l'intérieur vers l'extérieur :

1. `zip(colonnes, ligne)` associe les éléments deux à deux : premier nom avec première valeur, deuxième nom avec deuxième valeur.
2. `dict(...)` transforme ces couples en dictionnaire.
3. `lignes.append(...)` ajoute ce dictionnaire à la liste des lignes.

Exemple :

```python
colonnes = ["id", "nom"]
ligne = ["1", "Alice"]
# dict(zip(colonnes, ligne)) donne {"id": "1", "nom": "Alice"}
```

La longueur est vérifiée **avant** `zip`, car `zip` s'arrêterait à la plus courte des deux listes.
`return lignes` renvoie le résultat à la personne qui appelle la fonction. Cette instruction est placée après la boucle pour renvoyer toutes les lignes.

**Appels de la fonction :**

`customers = lire_fichier("customer.tbl", customer_columns)` appelle la fonction et enregistre sa réponse dans `customers`. Les trois autres appels font la même chose avec leurs propres fichiers.

Chaque variable contient une liste de dictionnaires. Par exemple, `customers[0]["C_NAME"]` donne le nom du premier client.
Les valeurs restent des textes : `"1"` n'est pas encore le nombre `1`.

Les quatre affichages donnent respectivement **1 500**, **15 000**, **60 175** et **25** lignes. Rien n'est encore écrit dans SQLite.

## Bloc 6 — Compter les lignes des huit fichiers

```python
total = 0
for chemin in sorted(data_path.glob("*.tbl")):
    with chemin.open(encoding="ascii") as fichier:
        nombre = sum(1 for ligne in fichier)
    print(chemin.name, ":", nombre)
    total += nombre

print("Total :", total)
```

**But :** connaître le volume de toutes les sources.

- `total = 0` initialise le compteur général.
- `data_path.glob("*.tbl")` trouve les fichiers dont le nom se termine par `.tbl`. L'étoile signifie « n'importe quelle suite de caractères ».
- `sorted(...)` trie ces chemins pour les parcourir dans un ordre stable.
- `for chemin in ...:` traite un fichier à la fois.
- `with chemin.open(...) as fichier:` ouvre le fichier courant.
- `sum(1 for ligne in fichier)` ajoute `1` pour chaque ligne parcourue : c'est un comptage.
- `chemin.name` donne seulement le nom du fichier, sans son dossier.
- `total += nombre` signifie `total = total + nombre`.
- Le dernier `print` est hors de la boucle : il affiche le total une fois tous les fichiers parcourus.

La notation `1 for ligne in fichier` est une **expression génératrice** : elle fournit les valeurs à `sum` au fur et à mesure.
Ce comptage ne contrôle pas les colonnes des quatre autres fichiers ; il compte seulement leurs lignes physiques.

Résultat attendu : **86 805 lignes** au total.

## Bloc 7 — Compter les valeurs vides

```python
tables = {"customer": customers, "orders": orders, "lineitem": lineitems, "nation": nations}

for nom, lignes in tables.items():
    vides = 0
    for ligne in lignes:
        for valeur in ligne.values():
            if valeur.strip() == "":
                vides += 1
    print(nom, ":", vides, "valeurs vides")
```

**But :** vérifier si les quatre tables chargées contiennent des champs vides.

- `{...}` crée ici un dictionnaire : chaque nom de table est associé à sa liste de lignes.
- `tables.items()` fournit les couples nom/contenu de ce dictionnaire.
- `for nom, lignes in ...:` récupère séparément les deux éléments de chaque couple.
- `vides = 0` remet le compteur à zéro au début de chaque table.
- `for ligne in lignes:` parcourt les enregistrements de la table.
- `ligne.values()` donne les valeurs du dictionnaire d'un enregistrement.
- La troisième boucle examine chaque valeur de cet enregistrement.
- `valeur.strip()` renvoie un texte sans les espaces de début et de fin. La valeur stockée dans la ligne reste inchangée.
- `== ""` vérifie si le résultat est vide.
- `vides += 1` augmente le compteur.

Les trois boucles correspondent à : **table → ligne → valeur**.
Le `print` est dans la boucle des tables, après les deux boucles intérieures : il affiche un résultat par table.

Exemples : `""` et `"   "` sont comptés comme vides ; `"Alice"` ne l'est pas. Le texte `"NULL"` ne serait pas compté comme vide par ce code.

Résultat attendu : **0 valeur vide** dans chacune des quatre tables.

## Bloc 8 — Chercher les doublons

```python
customer_ids = [client["C_CUSTKEY"] for client in customers]
order_ids = [commande["O_ORDERKEY"] for commande in orders]
lineitem_ids = [(ligne["L_ORDERKEY"], ligne["L_LINENUMBER"]) for ligne in lineitems]
nation_ids = [pays["N_NATIONKEY"] for pays in nations]

print("Clés clients répétées :", len(customer_ids) - len(set(customer_ids)))
print("Clés commandes répétées :", len(order_ids) - len(set(order_ids)))
print("Clés lignes répétées :", len(lineitem_ids) - len(set(lineitem_ids)))
print("Clés pays répétées :", len(nation_ids) - len(set(nation_ids)))

for nom, lignes in tables.items():
    lignes_uniques = set(tuple(ligne.values()) for ligne in lignes)
    print(nom, ":", len(lignes) - len(lignes_uniques), "lignes identiques en trop")
```

**But :** vérifier les clés et les lignes complètes.

Cette notation :

```python
customer_ids = [client["C_CUSTKEY"] for client in customers]
```

est une **compréhension de liste**. Elle veut dire : « pour chaque client, prendre sa clé et l'ajouter à la nouvelle liste ».
Une écriture plus longue, équivalente, serait :

```python
customer_ids = []
for client in customers:
    customer_ids.append(client["C_CUSTKEY"])
```

Les autres listes suivent le même principe. Pour LINEITEM, l'identifiant est un couple `(commande, numéro de ligne)`.
Ce couple entre parenthèses est un **tuple**. Le numéro de commande seul ne suffit pas, car une commande contient plusieurs lignes.

`set(...)` crée un **ensemble**, qui conserve uniquement les valeurs distinctes.

```text
Liste          : ["1", "1", "2"] → 3 éléments
Ensemble       : {"1", "2"}      → 2 éléments
Répétitions    : 3 - 2           → 1 ligne en trop
```

`len(liste) - len(set(liste))` compte donc les occurrences supplémentaires d'une clé, pas le nombre de clés distinctes concernées.

La dernière boucle vérifie les lignes complètes :

- `ligne.values()` récupère toutes les valeurs d'une ligne dans leur ordre d'insertion.
- `tuple(...)` transforme ces valeurs en un objet utilisable dans un ensemble. Une liste ou un dictionnaire ne peut pas être directement un élément d'un `set`.
- `set(... for ligne in lignes)` conserve les lignes complètes distinctes. L'ordre des colonnes est identique pour toutes les lignes lues dans une même table.
- La différence de tailles compte les lignes identiques supplémentaires.

Résultat attendu : **0** pour tous ces contrôles.

## Bloc 9 — Vérifier les relations entre tables

```python
client_keys = set(customer_ids)
order_keys = set(order_ids)
nation_keys = set(nation_ids)

commandes_sans_client = 0
for commande in orders:
    if commande["O_CUSTKEY"] not in client_keys:
        commandes_sans_client += 1

lignes_sans_commande = 0
for ligne in lineitems:
    if ligne["L_ORDERKEY"] not in order_keys:
        lignes_sans_commande += 1

clients_sans_pays = 0
for client in customers:
    if client["C_NATIONKEY"] not in nation_keys:
        clients_sans_pays += 1

print("Commandes sans client :", commandes_sans_client)
print("Lignes sans commande :", lignes_sans_commande)
print("Clients sans pays :", clients_sans_pays)
```

**But :** vérifier que les références pointent vers des enregistrements existants.

Les trois premières lignes construisent les ensembles de clés existantes. Ils servent à rechercher rapidement une clé.

Pour les commandes :

1. `commandes_sans_client = 0` initialise un compteur.
2. `for commande in orders:` parcourt toutes les commandes.
3. `commande["O_CUSTKEY"]` récupère la clé du client de cette commande.
4. `not in client_keys` vérifie si cette clé est absente des clients.
5. Si elle est absente, le compteur augmente de 1.

`in` signifie « appartient à » ; `not in` signifie « n'appartient pas à ».
La même logique vérifie les lignes de commande puis les pays des clients.

```text
CUSTOMER.C_CUSTKEY ← ORDERS.O_CUSTKEY
ORDERS.O_ORDERKEY  ← LINEITEM.L_ORDERKEY
NATION.N_NATIONKEY ← CUSTOMER.C_NATIONKEY
```

Exemple : si une commande référence le client `"999"` mais que cette clé n'existe pas dans CUSTOMER, cette commande est comptée comme une référence manquante.

Résultat attendu : **0** pour les trois compteurs. Ce bloc vérifie ces trois relations, pas toutes les relations du schéma complet.

## Bloc 10 — Lire les dates et les nombres

```python
dates_commandes = [date.fromisoformat(commande["O_ORDERDATE"]) for commande in orders]
soldes = [Decimal(client["C_ACCTBAL"]) for client in customers]
prix_commandes = [Decimal(commande["O_TOTALPRICE"]) for commande in orders]
quantites = [int(ligne["L_QUANTITY"]) for ligne in lineitems]
prix_lignes = [Decimal(ligne["L_EXTENDEDPRICE"]) for ligne in lineitems]
remises = [Decimal(ligne["L_DISCOUNT"]) for ligne in lineitems]
taxes = [Decimal(ligne["L_TAX"]) for ligne in lineitems]

print("Dates des commandes :", min(dates_commandes), "à", max(dates_commandes))
print("Soldes clients :", min(soldes), "à", max(soldes))
print("Clients avec solde négatif :", sum(solde < 0 for solde in soldes))
print("Prix des commandes :", min(prix_commandes), "à", max(prix_commandes))
print("Quantités :", min(quantites), "à", max(quantites))
print("Prix des lignes :", min(prix_lignes), "à", max(prix_lignes))
print("Remises :", min(remises), "à", max(remises))
print("Taxes :", min(taxes), "à", max(taxes))

for colonne in ["L_SHIPDATE", "L_COMMITDATE", "L_RECEIPTDATE"]:
    dates = [date.fromisoformat(ligne[colonne]) for ligne in lineitems]
    print(colonne, ":", min(dates), "à", max(dates))
```

**But :** vérifier certains types et observer leurs valeurs minimales et maximales.

Les valeurs issues des fichiers sont encore des textes. Les premières lignes créent de nouvelles listes de valeurs converties :

| Conversion | Exemple | Résultat |
| --- | --- | --- |
| `date.fromisoformat(...)` | `"1996-01-02"` | Un objet représentant une date |
| `Decimal(...)` | `"711.56"` | Un nombre décimal exact pour cette valeur |
| `int(...)` | `"17"` | Le nombre entier `17` |

Une conversion échoue si la valeur est incompatible. Par exemple, `int("abc")` déclenche une erreur.
On passe directement le texte à `Decimal` pour éviter un passage intermédiaire par un nombre flottant approximatif.
Ces conversions ne changent pas les textes dans `customers`, `orders` ou `lineitems` : elles remplissent d'autres listes.

- `min(liste)` donne la plus petite valeur.
- `max(liste)` donne la plus grande valeur.
- `solde < 0` donne `True` si le solde est négatif, sinon `False`.
- Dans `sum(solde < 0 for solde in soldes)`, `True` compte pour 1 et `False` pour 0. On obtient donc le nombre de clients avec un solde négatif.

La dernière boucle traite successivement trois colonnes de dates. À chaque tour, `colonne` contient le nom d'une colonne et `ligne[colonne]` récupère la date correspondante.

Quelques résultats attendus :

- Commandes du **1992-01-01** au **1998-08-02**.
- Soldes clients de **-994.79** à **9987.71**.
- **139** clients avec un solde négatif.
- Quantités de **1** à **50**.
- Remises de **0.00** à **0.10**. Une remise de `0.10` signifie 10 %.
- Taxes de **0.00** à **0.08**.

Le bloc observe ces valeurs : il ne les corrige pas et n'applique pas encore de règle de revenu ou d'arrondi.

## Bloc 11 — Compter les catégories et trouver les clients sans commande

```python
segments = Counter(client["C_MKTSEGMENT"] for client in customers)
transports = Counter(ligne["L_SHIPMODE"] for ligne in lineitems)

print("Segments clients :", dict(sorted(segments.items())))
print("Modes de transport :", dict(sorted(transports.items())))

clients_avec_commande = set(commande["O_CUSTKEY"] for commande in orders)
clients_sans_commande = client_keys - clients_avec_commande
print("Clients sans commande :", len(clients_sans_commande))
```

**But :** connaître la répartition des catégories et identifier les clients inactifs dans ces données.

- `Counter(client["C_MKTSEGMENT"] for client in customers)` compte les clients pour chaque segment.
- Le deuxième `Counter` compte les lignes de commande pour chaque mode de transport. Ce n'est pas un comptage de commandes distinctes.
- `.items()` fournit les couples catégorie/nombre.
- `sorted(...)` trie ces couples par catégorie.
- `dict(...)` les présente sous forme de dictionnaire pour l'affichage.

Exemple de `Counter` :

```text
Valeurs : ["AIR", "TRUCK", "AIR"]
Comptage : {"AIR": 2, "TRUCK": 1}
```

La fin du bloc utilise les ensembles :

- `clients_avec_commande` contient les clés des clients référencés par au moins une commande.
- `client_keys` contient les clés de tous les clients.
- `client_keys - clients_avec_commande` est une **différence d'ensembles** : on garde les clés présentes à gauche et absentes à droite.
- `len(clients_sans_commande)` compte ces clients.

```text
Tous les clients           : {"1", "2", "3"}
Clients avec commande      : {"1", "3"}
Clients sans commande      : {"2"}
```

Résultat attendu dans les fichiers du projet : **500 clients sans commande**.

## Ordre logique à retenir

```text
Importer les outils
→ Trouver les fichiers
→ Comprendre une ligne
→ Nommer les colonnes
→ Charger les fichiers en mémoire
→ Compter et vérifier
→ Observer les résultats
```

L'exploration approfondie est un bonus du README du test. Le travail déjà effectué sert de support d'apprentissage ; les autres bonus restent reportés après le socle Junior/Mid.
