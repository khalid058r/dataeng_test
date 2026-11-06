# Préparer la livraison GitHub

Le code, les données de l'exercice, les rapports exemples et les instructions constituent le livrable. Le dépôt de publication fourni est [khalid058r/dataeng_test](https://github.com/khalid058r/dataeng_test). Lors de sa vérification, il est public, vide et n'est pas un fork. Une base `main` peut conserver l'énoncé, avec l'implémentation sur `solution/python-sqlite-etl` pour la revue par Pull Request. Pour respecter aussi la consigne de fork d'un dépôt tiers, son URL d'origine doit être fournie.

Le dossier de travail initial n'a pas de dépôt Git propre ; les opérations Git se font dans une copie isolée sous `delivery/`. Ne pas utiliser le dépôt d'un autre projet détecté dans un dossier parent.

## 1. Contenu à versionner

Inclure `README.md`, `requirements.txt`, `.gitignore`, `.gitattributes`, `etl/`, `src/`, `sql/`, `scripts/`, `tests/`, `docs/`, les données et fichiers de référence de l'énoncé, ainsi que les sept CSV exemples de `outputs/`.

Exclure `.venv`, les bases SQLite générées, leurs journaux, les fichiers de verrouillage, `logs/`, les caches Python/pytest, les éventuelles configurations privées et le dossier local `delivery/`. Les résultats se reconstruisent à partir des sources et du code ; ne pas versionner le fichier `warehouse.sqlite`.

## 2. Préparer le dépôt et le commit

Si l'URL d'origine est disponible, créer son fork GitHub, le cloner dans un nouveau dossier et créer une branche de solution. Copier les fichiers livrables dans cette copie en conservant son propre dossier `.git`. Cette méthode conserve l'historique du dépôt d'origine. Dans le dépôt personnel vide fourni, préparer plutôt une branche `main` avec les fichiers de l'énoncé, puis la branche de solution ; cela permet une revue sans prétendre avoir créé un fork.

Depuis ce nouveau dépôt, vérifier que la racine Git et le dépôt distant correspondent au projet attendu :

```bash
git rev-parse --show-toplevel
git remote -v
git switch -c solution/python-sqlite-etl
git status --short
```

Après revue des fichiers à publier :

```bash
git add README.md requirements.txt .gitignore .gitattributes etl src sql scripts tests docs data data.zip ddl.sql erd.png bonus_etl_data_gen.txt notebooks README_TEMP_EXPLORATION.md todo outputs/*.csv
git diff --cached --stat
git diff --cached --check
git commit -m "Implement Python SQLite ETL, business reports and coding exercises"
git push -u origin solution/python-sqlite-etl
```

Ces commandes s'exécutent dans le clone du fork, pas dans le dossier de travail actuel si sa racine Git est un dossier parent. Vérifier l'identité d'auteur et les droits sur le fork au moment de la publication.

## 3. Ouvrir la Pull Request

La branche de comparaison est `solution/python-sqlite-etl` dans le fork. La branche de base appartient au dépôt d'origine ; vérifier son nom au lieu de supposer `main` ou `master`. Le fichier [`PR_DESCRIPTION.md`](PR_DESCRIPTION.md) contient le titre sur sa première ligne et le corps prêt à adapter au résultat final des contrôles.

Le parcours fork → branche → push → Pull Request est décrit dans la [documentation GitHub](https://docs.github.com/en/pull-requests/how-tos/create-pull-requests/creating-a-pull-request-from-a-fork). Aucun message au recruteur n'est envoyé automatiquement.

## 4. Message de livraison à compléter avec le lien réel

```text
Hello,

I have completed the Data Engineer test.

Pull request: <insert the actual pull request URL>

The solution includes a Python/SQLite ETL, a star schema, all five SQL analyses,
reproducible CSV reports and both Python coding exercises. The README provides
step-by-step setup and execution instructions, with scheduling, deployment and
architecture notes. Validation includes 109 passing tests and a clean setup run.

I am available to explain the implementation and the design choices.

Best regards,
<your name>
```

Remplacer les deux champs entre chevrons avant envoi. La publication du fork, le lien de la Pull Request et l'envoi restent à constater sur GitHub ; ne pas les considérer terminés sur la seule base de ces brouillons.
