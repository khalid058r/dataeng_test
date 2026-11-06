# Analyses SQL et résultats

Les vues sont définies dans [`sql/03_monthly_sales.sql`](../sql/03_monthly_sales.sql) et [`sql/04_business_reports.sql`](../sql/04_business_reports.sql). Elles utilisent le revenu après remise, hors taxe, arrondi par ligne selon les [règles métier](modele_et_regles.md).

Les colonnes numériques de montant sont en **centimes entiers**. Les montants lisibles ci-dessous sont divisés par 100 ; aucune devise n'est spécifiée par le jeu. Les sept CSV de [`outputs/`](../outputs/) sont des résultats exemples, reproductibles avec `python -m etl.export_reports`.

## 1. Top 5 des pays par revenu

```sql
SELECT * FROM top_5_nations ORDER BY revenue_cents DESC, nation_id;
```

| Pays du client | Lignes de vente | Revenu |
| --- | ---: | ---: |
| CANADA | 3 089 | 105 337 575,25 |
| EGYPT | 2 945 | 102 254 395,42 |
| IRAN | 2 952 | 100 283 452,47 |
| BRAZIL | 2 843 | 94 333 197,23 |
| ALGERIA | 2 773 | 93 680 675,67 |

Le pays vient du client. En cas d'égalité de revenu, le code pays croissant départage les résultats. Export : [`top_5_nations.csv`](../outputs/top_5_nations.csv).

## 2. Transport le plus fréquent parmi ces cinq pays

```sql
SELECT * FROM top_shipping_modes ORDER BY ship_mode;
```

Résultat : **FOB, avec 2 118 lignes**. Le comptage est global sur les cinq pays réunis, sans pondération par la quantité ou le revenu. Tous les modes ex æquo au premier rang seraient retournés. Export : [`top_shipping_modes.csv`](../outputs/top_shipping_modes.csv).

## 3. Meilleurs mois de vente

```sql
SELECT * FROM best_sales_months ORDER BY position LIMIT 5;
```

| Rang | Période | Revenu |
| --- | --- | ---: |
| 1 | 1993-12 | 29 616 353,18 |
| 2 | 1993-10 | 29 558 233,42 |
| 3 | 1992-01 | 29 253 389,85 |
| 4 | 1996-08 | 28 974 470,92 |
| 5 | 1995-12 | 28 896 188,46 |

Le classement porte sur l'année-mois. Les égalités sont départagées chronologiquement. Les mois sans vente sont absents et le dernier mois garde sa note « potentiellement partiel ». Export complet, 80 périodes : [`best_sales_months.csv`](../outputs/best_sales_months.csv).

## 4. Meilleurs clients par revenu et quantité

```sql
SELECT * FROM customers_by_revenue ORDER BY position LIMIT 10;
```

```sql
SELECT * FROM customers_by_quantity ORDER BY position LIMIT 10;
```

| Rang par revenu | Client | Revenu | Quantité |
| --- | --- | ---: | ---: |
| 1 | 1489 — Customer#000001489 | 5 203 674,08 | 3 868 |
| 2 | 214 — Customer#000000214 | 4 503 703,94 | 3 369 |
| 3 | 73 — Customer#000000073 | 4 466 381,07 | 3 384 |

Les premiers clients par quantité sont **1489 (3 868)**, **1396 (3 408)** et **73 (3 384)**. Chaque classement contient les 1 000 clients avec des lignes de vente ; l'identifiant croissant départage les égalités. Les clients sans vente restent dans la dimension.

Exports complets : [`customers_by_revenue.csv`](../outputs/customers_by_revenue.csv) et [`customers_by_quantity.csv`](../outputs/customers_by_quantity.csv).

## 5. Période courante contre période précédente

```sql
SELECT * FROM period_comparison;
```

| Mesure | Résultat |
| --- | ---: |
| Juillet 1998 | 26 283 122,09 |
| Juin 1998 | 23 423 472,23 |
| Écart | +2 859 649,86 |
| Variation | +12,21 % |
| Statut | `ok` |

La dernière commande est datée du 02/08/1998. Le rapport exclut donc août et compare les deux mois précédents. L'écart reste en centimes entiers ; `change_percent` est le ratio affiché à deux décimales.

Si une période n'a aucune ligne, son revenu et les variations sont `NULL`, avec le statut « période absente ». Si le revenu précédent est nul mais la période présente, l'écart reste calculé, le pourcentage est `NULL` et le statut est « base précédente nulle ». Export : [`period_comparison.csv`](../outputs/period_comparison.csv).

## Rapport mensuel et rapprochement

```sql
SELECT * FROM monthly_sales ORDER BY period;
```

Le rapport couvre **80 mois**, de janvier 1992 à août 1998. Août est conservé avec 44 lignes et un revenu de 1 515 799,62, signalé comme potentiellement partiel. Export : [`monthly_sales.csv`](../outputs/monthly_sales.csv).

```sql
SELECT SUM(sales_lines) AS sales_lines,
       SUM(quantity) AS quantity,
       SUM(revenue_cents) AS revenue_cents
FROM monthly_sales;
```

Totaux attendus : **60 175 lignes**, **1 536 127 unités** et **204 513 495 230 centimes**, soit **2 045 134 952,30**. Les agrégations par client, pays et mois donnent le même revenu global. La colonne `revenue` du rapport mensuel est un texte d'affichage ; utiliser `revenue_cents` pour les calculs et les tris numériques.
