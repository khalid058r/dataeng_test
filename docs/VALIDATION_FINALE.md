# Validation finale du livrable

Vérifications réalisées le 05/11/2026 sur Linux, dans une copie indépendante du code, des tests, des scripts et des données, placée hors du dossier de travail initial.

## 1. Installation depuis zéro

- Nouvel environnement virtuel Python 3.12.3, sans réutilisation de `.venv` du projet.
- Installation des versions de `requirements.txt` depuis le registre de paquets : réussie.
- `python -m pip check` : aucune dépendance incompatible déclarée.
- SQLite embarqué compatible avec le minimum 3.37 demandé par le projet.

Les téléchargements et le contrôle de Datasette ont été exécutés hors du bac à sable de l'agent, qui restreint le réseau et certains échanges entre threads. Le fonctionnement normal du projet ne nécessite pas ce bac à sable.

## 2. Tests automatisés

Commande : `python -m pytest -q tests`.

**Résultat : 109 tests réussis** dans l'environnement neuf. Ils couvrent les conversions, les fichiers invalides, les clés, les annulations, les migrations des bases précédentes, les rapports et leurs cas limites, les exports, les deux exercices Python et le lanceur.

Les trois tests du lanceur vérifient un chargement et un export depuis un autre dossier, l'arrêt sans export après une erreur de source et le refus d'une exécution concurrente avec le code `75`.

## 3. Base absente et relance

Le lanceur `bash scripts/run_pipeline.sh` a été exécuté dans la copie neuve avec une base initialement absente.

| Table | Lignes vérifiées |
| --- | ---: |
| nation | 25 |
| customer | 1 500 |
| orders | 15 000 |
| lineitem | 60 175 |
| dim_customer | 1 500 |
| dim_date | 2 406 |
| fact_sales | 60 175 |

Le premier traitement a pris environ 4,69 secondes sur cette machine ; cette observation ne constitue pas une garantie de performance sur une autre machine ou un volume différent.

Une deuxième exécution a donné les mêmes empreintes du contenu trié des sept tables et les mêmes empreintes des sept CSV. `PRAGMA integrity_check` retourne `ok`, et `PRAGMA foreign_key_check` ne retourne aucune ligne. Le revenu mensuel total est de **204 513 495 230 centimes**.

## 4. Consultation et exports

Les sept vues de rapport ont été ouvertes via le client applicatif de Datasette de l'environnement neuf. Chaque page HTML et chaque export CSV retourne HTTP 200. Les enregistrements CSV téléchargés ont été comparés aux fichiers produits par `etl.export_reports` : contenus identiques, indépendamment de l'ordre d'affichage choisi dans l'interface.

Les volumes sont de 80 mois, cinq pays, un mode de transport au premier rang, 80 mois classés, 1 000 clients dans chaque classement et une ligne de comparaison de périodes.

## 5. Portabilité et préparation Git

Le code retrouve ses chemins par défaut depuis son emplacement et expose des chemins configurables. Les fichiers de code, tests et documentation ont été relus avec une recherche ciblée de chemins personnels et de formats courants de clés privées ou de jetons ; aucune détection n'a été trouvée. Ce contrôle accompagne la sélection explicite des fichiers livrables et l'exclusion des configurations privées.

La base générée, `.venv`, les journaux, les verrous et les caches sont exclus du versionnement. Les sources de l'exercice et les sept CSV exemples sont conservés pour la revue. Les instructions, le brouillon de Pull Request et le brouillon du message de livraison sont prêts dans `docs/LIVRAISON.md` et `docs/PR_DESCRIPTION.md`.

La création du fork et la publication de la Pull Request restent à effectuer sur le dépôt GitHub d'origine, dont l'URL doit être fournie. Aucun message n'a été envoyé au recruteur. La validation locale ne vaut pas publication GitHub.

## 6. Nouveau contrôle avant envoi — 06/11/2026

Après les simplifications pédagogiques du chargeur, la suite complète a été relancée : 109 tests réussis. L'archive de livraison, qui contenait encore le premier instantané, a été mise à jour.

Le projet extrait de cette archive donne également 109 tests réussis. Son lancement depuis un autre dossier charge une base initialement absente et génère les sept rapports conformes aux exemples livrés. Une relance conserve les sept tables et les sept exports. Les contrôles SQLite et les sept pages et exports Datasette réussissent. Le code et les données du livrable final sont comparés à cette copie extraite testée.

Le tableau de conformité à l'énoncé, les bonus reportés et les actions GitHub restantes sont détaillés dans `CONTROLE_AVANT_ENVOI.md`. Le commit et les empreintes des fichiers livrés sont dans `delivery/release_manifest.json`, à côté de l'archive et du bundle locaux.
