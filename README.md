# Gestion de Finances Personnelles

Application de bureau (Windows) pour gérer tes entrées/sorties d'argent,
tes dépenses, tes budgets mensuels, avec statistiques et export Excel.
Les données sont sauvegardées dans un fichier local `finances.db` (SQLite),
créé automatiquement à côté du `.exe` — tes données restent d'une session à l'autre.

## Obtenir le fichier .exe (sans installer Python) via GitHub Actions

Tu as déjà Git installé, donc voici la marche à suivre. Ça prend environ 10 minutes
la première fois, puis 2 minutes pour chaque mise à jour future.

### Étape 1 : Créer un compte GitHub (si tu n'en as pas)

Va sur https://github.com et crée un compte gratuit.

### Étape 2 : Créer un nouveau dépôt (repository)

1. Clique sur le bouton "+" en haut à droite, puis "New repository"
2. Donne-lui un nom, par exemple `gestion-finances`
3. Laisse-le en "Public" ou "Private" (peu importe)
4. Ne coche PAS "Add a README" (on a déjà le nôtre)
5. Clique sur "Create repository"

GitHub va t'afficher une page avec des commandes — garde cette page ouverte,
tu en auras besoin à l'étape 4.

### Étape 3 : Préparer le dossier sur ton PC

Crée un dossier sur ton PC (par exemple `gestion-finances`) et mets-y
tous les fichiers fournis, en respectant cette structure exacte :

```
gestion-finances/
├── .github/
│   └── workflows/
│       └── build.yml
├── gestion_finances.py
├── database.py
├── export_excel.py
├── requirements.txt
└── README.md
```

Important : le dossier `.github` doit être à la racine, avec un point devant.

### Étape 4 : Envoyer le code sur GitHub avec Git

Ouvre une invite de commande (cmd) **dans ce dossier**, puis tape ces
commandes une par une (remplace `TON-NOM-UTILISATEUR` et `gestion-finances`
par les tiens, visibles sur la page GitHub de l'étape 2) :

```
git init
git add .
git commit -m "Premiere version de l'application"
git branch -M main
git remote add origin https://github.com/TON-NOM-UTILISATEUR/gestion-finances.git
git push -u origin main
```

GitHub te demandera peut-être de te connecter (une fenêtre s'ouvre, ou on
te demande un token) — suis les instructions à l'écran.

### Étape 5 : Récupérer ton .exe compilé

1. Va sur la page de ton dépôt GitHub dans ton navigateur
2. Clique sur l'onglet "Actions" (en haut)
3. Tu verras un workflow en cours ("Build Windows EXE") — attends qu'il
   devienne vert (environ 2-3 minutes)
4. Clique dessus, puis descends jusqu'à la section "Artifacts"
5. Clique sur "GestionFinances-exe" pour télécharger un fichier `.zip`
6. Dézippe-le : à l'intérieur se trouve `GestionFinances.exe`

C'est ton exécutable, prêt à l'emploi. Double-clique dessus pour lancer
l'application — aucune installation de Python n'est nécessaire sur cette machine.

### Mettre à jour l'application plus tard

Si je te fournis une nouvelle version des fichiers `.py`, remplace-les dans
ton dossier, puis dans l'invite de commande :

```
git add .
git commit -m "Mise a jour"
git push
```

Un nouveau `.exe` sera automatiquement recompilé — reviens à l'étape 5 pour
le télécharger.

## Utilisation de l'application

- **Tableau de bord** : solde, revenus/dépenses du mois, dernières transactions
- **Transactions** : ajouter/modifier/supprimer, filtrer par mois ou type
- **Budgets** : définir un budget mensuel par catégorie, suivre la progression
- **Statistiques** : camembert des dépenses, comparatif revenus/dépenses sur 6 mois
- **Export Excel** : bouton en haut du tableau de bord

Le fichier `finances.db` est créé à côté de `GestionFinances.exe` au premier
lancement. Ne le supprime pas si tu veux garder ton historique. Tu peux le
copier ailleurs pour faire une sauvegarde.

## Personnaliser les catégories ou la devise

Ouvre `gestion_finances.py` et modifie en haut du fichier :

```python
CATEGORIES_DEPENSE = ["Alimentation", "Transport", "Logement", ...]
CATEGORIES_REVENU = ["Salaire", "Freelance", ...]
```

Pour la devise, remplace "DA" par la tienne dans `gestion_finances.py` et
`export_excel.py`, puis relance les étapes 4 et 5 pour recompiler.
