# Contrôle de conformité avant envoi — 06/11/2026

L'énoncé est conservé dans la dernière partie de `README.md`. Le tableau ci-dessous distingue les exigences techniques réalisées, les bonus facultatifs et les actions de remise qui nécessitent le dépôt GitHub d'origine.

## 1. Exigences techniques

| Demande de l'énoncé | Réalisation | État |
| --- | --- | --- |
| Utiliser Python et SQL, avec une solution reproductible | Bibliothèque standard pour ETL et export ; dépendances fixées pour Datasette et pytest | Réalisé |
| Décrire le format des fichiers | ASCII, séparateur `\|`, absence d'en-tête, séparateur final, types et volumes documentés | Réalisé |
| Charger au moins 2 à 3 tables pour Junior/Mid | NATION, CUSTOMER, ORDERS et LINEITEM chargées | Réalisé |
| Concevoir un schéma en étoile | `dim_customer`, `dim_date`, `fact_sales`, grain d'une ligne de commande et clés documentées | Réalisé |
| Alimenter ce schéma | Sources, dimensions et faits dans une transaction, contraintes et contrôles de conservation | Réalisé |
| Livrer un rapport agrégé et une consultation simple | Rapport mensuel, vues Datasette et sept exports CSV | Réalisé |
| Répondre aux cinq questions métier | Pays, transport, mois, clients par deux mesures et comparaison de périodes | Réalisé |
| Expliquer plusieurs exécutions quotidiennes | Exemple cron et lanceur avec verrou, journaux et arrêt après erreur | Réalisé ; installation cron laissée à l'exploitant |
| Expliquer le déploiement | Procédure Linux et dépendances dans le README et le guide d'exploitation | Réalisé |
| Proposer une architecture de production | Limites du système local et évolution vers PostgreSQL et orchestration selon les besoins | Réalisé |
| Analyser une croissance mensuelle de 6,1 à 12,7 % | Projections composées à 6, 12 et 24 mois, effets sur les traitements et le stockage | Réalisé |
| Résoudre les deux exercices Python | Inversion des mots et justification, exemples, limites et complexités | Réalisé |
| Fournir des instructions pas à pas | Installation, tests, chargement, export, consultation et exploitation | Réalisé |
| Employer de bonnes pratiques | Conversions exactes, SQL paramétré, contraintes, transaction, relance, tests et exclusion des fichiers locaux | Vérifié sur le périmètre livré |

Les choix métier sont explicités : pays du client, fréquence du transport comptée par ligne, revenu après remise hors taxe et comparaison juillet/juin 1998 à partir des dates du jeu. Le dernier mois est signalé comme potentiellement partiel. La solution couvre le socle Junior/Mid ; elle ne prétend pas être une infrastructure de production déjà déployée.

## 2. Vérifications avant constitution de l'archive

Le 06/11/2026, la commande `python -m pip check` ne signale aucune incompatibilité et `python -m pytest -q tests` donne **109 tests réussis** sur le code de travail actuel. Ce résultat inclut les simplifications pédagogiques du chargeur intervenues après la première livraison locale.

La nouvelle archive est reconstruite depuis le dépôt de revue après synchronisation des fichiers actuels. Son manifeste et ses empreintes sont régénérés ; la base SQLite, les environnements virtuels, les journaux et les configurations privées sont exclus.

Le contenu extrait dans un autre dossier a lui aussi donné **109 tests réussis**. Le lanceur fonctionne depuis un dossier de travail différent, crée une base initialement absente et reproduit les sept CSV exemples. Une deuxième exécution donne les mêmes contenus des sept tables et les mêmes empreintes des sept exports. Les contrôles d'intégrité et de clés étrangères SQLite réussissent ; le revenu total est de 204 513 495 230 centimes.

Les huit fichiers sources sont identiques à ceux de `data.zip`. Les liens locaux de documentation sont valides. Les sept pages de rapports et leurs exports CSV dans Datasette retournent HTTP 200 ; les données téléchargées sont identiques aux exports SQL. La vérification utilise l'environnement indépendant installé depuis `requirements.txt` lors de la validation précédente, dont les dépendances restent inchangées et compatibles.

Le code et les données de l'archive finale sont comparés par empreinte au contenu extrait testé ; seules les notes de résultat de contrôle sont finalisées après ce test. Le manifeste enregistre le commit effectivement livré, afin d'éviter d'envoyer une ancienne version.

## 3. Bonus et profilage

Le profilage initial des huit sources est réalisé et ses conséquences sur les types, clés, relations et contrôles sont documentées dans `docs/exploration_donnees.md`.

Les bonus suivants restent volontairement reportés : Docker, streaming, génération de données, classification des soldes, déplacement des dates et ajout d'une colonne persistée de revenu par ligne. Le revenu est calculé par ligne dans les requêtes avant agrégation. Ces bonus ne sont pas nécessaires pour satisfaire les exigences obligatoires du parcours retenu.

## 4. Actions de remise encore nécessaires

- Publier la branche et ouvrir la Pull Request dans le dépôt fourni `https://github.com/khalid058r/dataeng_test` avec les accès nécessaires. Ce dépôt personnel était vide et n'est pas un fork ; l'URL du dépôt original reste nécessaire si la consigne de fork doit être appliquée à un dépôt tiers.
- Ouvrir la Pull Request avec le texte préparé dans `docs/PR_DESCRIPTION.md`.
- Remplacer le lien et le nom dans le brouillon de `docs/LIVRAISON.md`, puis envoyer le message de fin de test au destinataire voulu.
- Préparer l'explication personnelle du code pour l'entretien ; les tests ne vérifient pas cette capacité orale. Le guide `docs/COMPRENDRE_ET_MODIFIER.md` sert de support.

Ces actions ne sont pas considérées réalisées par la seule création d'une archive ou d'un commit local. Aucun message n'est envoyé dans le cadre de ce contrôle.
