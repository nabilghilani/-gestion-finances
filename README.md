# Gestion Financière — Version 2 (multi-entités)

Nouvelle version complète de l'application : écran de sélection d'entité,
menu par zone (Recettes / Dépenses / Dettes / Dashboard), catégories
modifiables, et un dashboard où cliquer une ligne renvoie directement dans
le formulaire de modification. Base de données locale SQLite (`finances.db`),
créée à côté du `.exe`.

Cette version **remplace complètement** les fichiers de l'ancienne version
dans ton dépôt GitHub `nabilghilani/-gestion-finances`.

## Étape 1 : Nettoyer l'ancien dossier

Dans ton dossier `gestion finance` sur ton PC, **supprime ces anciens
fichiers** (ils ne servent plus) :
- `gestion_finances.py` (ancienne version, avec un "s")
- `export_excel.py`
- Les éventuels fichiers `.xlsx` que tu aurais mis dedans

Garde uniquement le dossier `.github` (on va remplacer son contenu) et le
`.git` cachée (ne surtout pas la toucher).

## Étape 2 : Copier les nouveaux fichiers

Place ces fichiers dans le même dossier `gestion finance`, en remplaçant
`.github/workflows/build.yml` par la nouvelle version fournie :

```
gestion finance/
├── .github/
│   └── workflows/
│       └── build.yml        <- remplace l'ancien
├── gestion_financiere.py    <- nouveau fichier principal
├── database.py               <- remplace l'ancien
├── requirements.txt          <- remplace l'ancien
└── README.md                 <- remplace l'ancien
```

## Étape 3 : Envoyer la mise à jour sur GitHub

Ouvre ton terminal dans ce dossier (celui qui fonctionnait déjà pour toi) :

```
git add .
git commit -m "Version 2 - multi-entites"
git push
```

## Étape 4 : Récupérer le nouveau .exe

1. Va sur **https://github.com/nabilghilani/-gestion-finances**
2. Onglet **"Actions"**
3. Attends la coche verte ✅ (2-3 minutes)
4. Télécharge l'artefact **"GestionFinanciere-exe"**, dézippe-le
5. Tu obtiens `GestionFinanciere.exe`

Double-clique dessus pour lancer l'application.

**Important** : c'est un nouveau nom de fichier (`GestionFinanciere.exe`,
sans "s") et une nouvelle base de données (`finances.db` recréée à zéro,
vide au départ) — l'ancien `.exe` et son ancienne base peuvent être
supprimés ou gardés de côté, ils ne sont plus utilisés.

## Utilisation

1. **Écran de démarrage** : choisis une entité (Personnel, ou crée-en une
   nouvelle avec le champ en bas) ou supprime une entité existante
2. **Menu** : clique Recettes / Dépenses / Dettes / Dashboard
3. Dans une zone : remplis le formulaire puis clique **Ajouter**. Clique une
   ligne de la liste pour la charger dans le formulaire, modifie puis clique
   **Enregistrer les modifications**, ou **Supprimer la sélection**
4. **Dashboard** : filtre par catégorie, regarde tes indicateurs et ton
   camembert de dépenses. **Double-clique une ligne** du tableau pour être
   renvoyé directement dans le formulaire de modification de cette ligne
5. Le bouton **"☰ Menu"** en haut de chaque zone te ramène au menu de
   l'entité ; **"↩ Changer d'entité"** te ramène à l'écran de démarrage

## Ajouter une catégorie

Dans les zones Recettes / Dépenses / Dettes, clique **"+ Nouvelle
catégorie"** à côté du champ Catégorie : elle est immédiatement disponible
dans la liste déroulante.

## Sauvegarder tes données

Le fichier `finances.db`, créé à côté de `GestionFinanciere.exe`, contient
tout ton historique (entités, recettes, dépenses, dettes, catégories).
Copie-le régulièrement ailleurs (clé USB, cloud) pour faire une sauvegarde.
