# `Measurement` — valeur + incertitude

`src/synthesis/measurement.py` définit un petit **objet-valeur immuable** qui associe une mesure à
son **incertitude 1 σ**, avec une arithmétique qui **propage l'incertitude** correctement. C'est le
moteur d'incertitude de toute la synthèse.

```python
from synthesis import Measurement

pb210 = Measurement(1224.40, 64.48)   # activité ± incertitude (mBq/g)
ra226 = Measurement(178.16, 6.20)
pb_exc = pb210 - ra226                 # Measurement(1046.24, 64.77)
```

## Pourquoi c'est nécessaire

Chaque activité d'un rapport G2K arrive avec une incertitude. Dès qu'on **combine** des activités,
l'incertitude doit suivre les règles standard de propagation d'erreur — sinon les colonnes
`Incertitude …` de la synthèse seraient fausses. Deux situations reviennent constamment :

- **Formules entre nucléides** : `PB-Exc = PB-210 − RA-226`. La valeur se soustrait, mais
  l'incertitude, elle, se combine en quadrature.
- **Plusieurs raies pour un même nucléide** : `RA-226` est estimé via trois raies filles. La
  « meilleure » activité est la **moyenne pondérée inverse-variance** de ces raies.

`Measurement` encapsule tout ça : `builder.py` et `providers.py` écrivent juste `pb210 - ra226` ou
`Measurement.weighted_mean(peaks)` et obtiennent **à la fois** la valeur et l'incertitude justes.
Sans cet objet, il faudrait recoder la propagation d'erreur à la main dans chaque formule.

## Ce qu'il fait

### Champs et helpers

| Membre | Rôle |
|---|---|
| `value`, `uncertainty` | la mesure et son incertitude 1 σ (dataclass gelée). |
| `is_nan` | vrai si la valeur est `NaN` (mesure manquante). |
| `Measurement.missing()` | une mesure manquante (`NaN`, `NaN`). |

### Propagation d'incertitude (opérateurs)

| Opération | Valeur | Incertitude |
|---|---|---|
| `a + b`, `a - b` | `a.value ± b.value` | **quadrature** : `√(σₐ² + σᵦ²)` |
| `a * b`, `a / b` | `a.value ∘ b.value` | **quadrature relative** : `\|v\|·√((σₐ/a)² + (σᵦ/b)²)` |
| `-a` | `-a.value` | inchangée |

### Moyenne pondérée inverse-variance

```python
Measurement.weighted_mean([m1, m2, m3])
```

Combine plusieurs mesures d'une même grandeur (typiquement les raies d'un nucléide) :

- poids `wᵢ = 1/σᵢ²` (les mesures les plus précises pèsent le plus) ;
- valeur combinée `Σ(wᵢ·vᵢ) / Σwᵢ` ;
- incertitude combinée `√(1 / Σwᵢ)`.

C'est le **standard scientifique** pour combiner plusieurs lignes gamma, et ce que Génie 2000 lui-même
reporte comme activité moyenne pondérée. Les mesures à valeur `NaN`, à incertitude `NaN` ou à
incertitude ≤ 0 sont **ignorées** ; si rien d'exploitable ne reste, le résultat est `missing()`.

## Où c'est utilisé

- `providers.py` — `_peak_measurement()` produit un `Measurement` par raie ; `resolve_nuclide()`
  les combine via `weighted_mean()` ; `evaluate_formula()` évalue les formules sur des `Measurement`.
- `builder.py` — chaque colonne devient un `Measurement`, dont `value`/`uncertainty` remplissent les
  colonnes `Activite …` / `Incertitude …`.

## À conserver

Composant central et bien ciblé : il n'a pas de dépendance, isole toute la logique d'incertitude en
un seul endroit testable, et garde les formules du fichier build triviales à écrire. Le retirer
signifierait perdre la propagation d'incertitude (les colonnes `Incertitude …` deviendraient
fausses ou ad hoc).
