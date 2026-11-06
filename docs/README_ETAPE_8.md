# Étape 8 — Les deux exercices d'algorithmique

Les deux solutions sont dans [`src/algorithms.py`](../src/algorithms.py). Elles utilisent uniquement la bibliothèque standard Python. Les tests sont dans [`tests/test_algorithms.py`](../tests/test_algorithms.py).

## 1. Exécuter les tests et essayer les fonctions

Depuis la racine du projet :

```bash
source .venv/bin/activate
python -m pytest -q tests/test_algorithms.py
```

Pour tester les fonctions dans une console Python ouverte depuis cette même racine :

```python
from src.algorithms import reverse_words, full_justify

print(reverse_words("  hello world  "))
# world hello

lines = full_justify(
    ["This", "is", "an", "example", "of", "text", "justification."],
    16,
)
for line in lines:
    print(repr(line), len(line))
# 'This    is    an' 16
# 'example  of text' 16
# 'justification.  ' 16
```

`repr` permet de voir les espaces finaux avant le guillemet fermant. La fonction retourne une liste de chaînes ; elle ne modifie pas la liste de mots fournie. Le paramètre Python `max_width` correspond à `maxWidth` dans l'énoncé.

## 2. Inverser les mots d'une chaîne

La fonction `reverse_words` effectue trois opérations :

1. `s.split()` découpe le texte en mots et retire les espaces de début, de fin et les séparateurs répétés.
2. `reversed(words)` parcourt les mots dans l'ordre inverse.
3. `" ".join(...)` les rassemble avec un seul espace entre eux.

Exemple :

```text
Entrée           : "a good   example"
Après split      : ["a", "good", "example"]
Parcours inversé : "example", "good", "a"
Résultat         : "example good a"
```

Un mot unique reste identique ; les lettres et les chiffres à l'intérieur des mots ne sont pas inversés. L'énoncé garantit au moins un mot et des espaces ordinaires comme séparateurs.

**Complexité :** pour `n` caractères en entrée, le temps est `O(n)` et la mémoire supplémentaire est `O(n)`. Le découpage crée les mots et la jointure crée une nouvelle chaîne.

**Question complémentaire sur le traitement en place :** une chaîne Python `str` est immuable. Cette solution ne peut donc pas modifier directement la chaîne reçue avec une mémoire supplémentaire constante. Avec un tableau de caractères déjà mutable, on peut compacter les espaces, inverser l'ensemble des caractères utiles, puis inverser les caractères de chaque mot, avec deux indices et des échanges. Cela prend `O(n)` en temps et `O(1)` en mémoire supplémentaire. Convertir d'abord une chaîne Python en liste de caractères demanderait toutefois `O(n)` de mémoire.

## 3. Justifier le texte

La fonction `full_justify` construit les lignes de gauche à droite. Elle utilise une approche **gloutonne** : pour chaque ligne, elle prend le plus grand nombre de mots possible avant de passer à la suivante.

### Choisir les mots de la ligne

`start` indique le premier mot de la ligne. `end` avance jusqu'au premier mot qui ne tient plus ; ce mot sera repris dans la ligne suivante. `letters` compte les caractères des mots retenus, sans les espaces.

Pour ajouter le mot d'indice `end`, la longueur minimale nécessaire est :

```text
letters + longueur du nouveau mot + (end - start)
```

`end - start` représente les espaces minimum nécessaires entre tous ces mots. Tant que cette longueur ne dépasse pas `max_width`, le mot est retenu.

### Répartir les espaces

Si la ligne a plusieurs mots et n'est pas la dernière :

```text
Nombre d'intervalles = nombre de mots − 1
Espaces à distribuer = max_width − nombre de lettres
```

`divmod(espaces, intervalles)` donne le nombre d'espaces de base dans chaque intervalle et le nombre d'espaces supplémentaires à placer à gauche.

Exemple avec `aa`, `bb`, `cc`, `dd`, une largeur de 13 et d'autres mots restant à traiter :

```text
Lettres                  : 8
Intervalles              : 3
Espaces à distribuer     : 13 − 8 = 5
divmod(5, 3)             : (1, 2)
Espaces par intervalle   : 2, 2, 1
Ligne obtenue            : "aa  bb  cc dd"
```

La différence entre deux intervalles ne dépasse donc pas un espace, et les plus grands intervalles sont à gauche. La fonction assemble des morceaux avec `join` pour construire chaque chaîne de sortie.

### Dernière ligne et ligne à un seul mot

Ces lignes sont alignées à gauche : un espace entre les mots, puis des espaces finaux pour atteindre la largeur exacte. L'expression `" ".join(...).ljust(max_width)` réalise ces deux opérations.

L'énoncé garantit une liste non vide de mots non vides, sans espaces internes, et une largeur suffisante pour chaque mot. La fonction rejette aussi les largeurs non positives, les listes vides, les mots vides et ceux qui dépassent la largeur, avec `ValueError`.

**Complexité :** soit `m` le nombre de mots, `L` le nombre de lignes et `w` la largeur. La sortie contient `C = L × w` caractères. Le temps est `O(m + C)` : les mots sont parcourus et les caractères de sortie sont écrits. La mémoire du résultat est `O(C)` ; la mémoire temporaire supplémentaire, hors entrée et résultat, est `O(w)` pour construire une ligne. Les deux boucles imbriquées ne rendent pas le parcours des mots quadratique : `start` reprend à `end`, sans repartir du début.

## 4. Ce qui est vérifié

Les 26 tests de cette étape couvrent les trois exemples d'inversion, les trois exemples de justification, les espaces multiples, les lettres et chiffres, le mot unique, la largeur de 1, les lignes remplies exactement, les espaces supplémentaires à gauche et la dernière ligne.

Ils vérifient aussi les contraintes maximales de l'énoncé : une chaîne de 10 000 caractères, puis 300 mots de 20 caractères avec une largeur de 100. Sur 100 jeux supplémentaires générés avec une graine fixe, ils contrôlent la conservation des mots et de leur ordre, la largeur exacte, le choix du maximum de mots par ligne et la bonne répartition des espaces.

Pour vérifier également le pipeline et les rapports :

```bash
python -m pytest -q tests
```

Résultat vérifié : **106 tests réussis** sur la suite complète, dont les 26 nouveaux tests d'algorithmique.

L'exploitation et l'architecture sont maintenant documentées dans `README_ETAPE_9.md`. La validation finale comprend 109 tests avec les trois tests du lanceur. Le guide `COMPRENDRE_ET_MODIFIER.md` prépare la lecture du code et ses adaptations.
