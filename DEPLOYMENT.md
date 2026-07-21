# Petit Guide d'installation

N'hésite à être critique. Je te donne un moyen de tester plutôt "technique".
L'idée est que puisse me penché plus tard sur un moyen simple (Graphique avec des boutons et tout ce qui va bien) de tester/utilisé l'outil.

## Mise en place

Installation d'`uv`.
C'est un outil pour gerer/manipuler les projets python de manière "simple" de mon point de vue.
Au besoin voici la documentation d'`uv`: [docs.astral.sh/uv](https://docs.astral.sh/uv/).
Tu aura besoin d'un terminal/powershell.


Pour l'installer voici le ligne de commande:

```sh
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Installation de git : [git](https://git-scm.com/install/windows)

En suite une simple ligne de commande et `chenin` est installer:
```sh
uv tool install git+https://github.com/Ezacuak/chenin.git@dev
```

## Utilisation

C'est tres simple ! (J'espère 🤞)

Pour avoir tout le rapport qui sort:
```sh
chenin chemin_vers_le_fichier.txt
```

Pour avoir juste une section (par exemple la section 3):
```sh
chenin chemin_vers_le_fichier.txt -s s3
```

Si tu as une erreur tu peu avoir de l'aide avec:
```sh
chenin -h
```
*PS:** Je te conseil de la taper une fois avant, il y a des exemples dedans.



## Note

### Utilisation d'un terminal

Pour voir ou est ce qu'on est:
```sh
ls
```

pour aller vers un dossier:
```sh
cd nom_du_dossier
```

Pour le moment on extrait rapport par rapport, pas encore en masse donc 😢.
