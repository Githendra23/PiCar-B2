# Adeept PiCar-B2 — Robot Autonome Suiveur de Ligne

**Projet Mastercamp Systèmes Embarqués — EFREI Paris**

<p align="center">
  <img width="298" height="318" alt="Adeept PiCar-B2" src="https://github.com/user-attachments/assets/79ad1699-c452-4090-a4bf-2c61f6ddf20c" />
</p>

Ce projet consiste à programmer un robot mobile autonome basé sur un **Raspberry Pi 4** et le kit **Adeept PiCar-B2**. Le robot est capable de se centrer sur une ligne rouge au sol, de la suivre par vision par ordinateur, de détecter des flèches directionnelles pour choisir sa trajectoire, et de s'arrêter automatiquement devant un ruban bleu. L'ensemble est piloté par une architecture logicielle orientée objet, avec un retour vidéo en temps réel accessible via une interface web.

## Technologies utilisées

**Langage & Vision :**

<a href="https://docs.python.org/3/" target="_blank"><img src="https://img.icons8.com/color/48/000000/python--v1.png"/></a>
<a href="https://docs.opencv.org/" target="_blank"><img src="https://img.icons8.com/color/48/000000/opencv.png"/></a>
<a href="https://numpy.org/doc/" target="_blank"><img src="https://img.icons8.com/color/48/000000/numpy.png"/></a>

**Matériel :**

<a href="https://www.raspberrypi.com/documentation/" target="_blank"><img src="https://img.icons8.com/color/48/000000/raspberry-pi.png"/></a>
<a href="https://www.linux.org" target="_blank"><img src="https://img.icons8.com/color/48/000000/linux--v1.png"/></a>

**Communication matérielle :** I2C (PCA9685), SPI (WS2812), picamera2

## Fonctionnalités principales

#### Vision (module FluxVideo)
- Détection de la ligne rouge par masquage HSV et analyse de contours.
- Calcul de la position latérale et de l'angle de la ligne (deux points de repère).
- Détection du ruban bleu d'arrêt dans la zone proche du robot.
- Retour vidéo annoté diffusé en direct via un serveur web (flux MJPEG).

#### Pilotage (module main)
- Centrage automatique du robot sur la ligne, avec zone morte pour éviter les oscillations.
- Suivi de ligne par correction proportionnelle combinant position et angle (anticipation des virages).
- Arrêt automatique et sécurisé à la détection du ruban bleu.
- Manœuvre de recherche en cas de perte de la ligne.

#### Actionneurs
- **Moteur** : traction avant/arrière avec démarrage progressif pour préserver la transmission.
- **Direction** : direction type voiture par servomoteur, avec bornage des angles de sécurité.
- **Tourelle** : orientation de la caméra (axes horizontal et vertical).
- **Feux arrière & LED** : signalisation lumineuse WS2812 (clignotants, alertes).

## Architecture logicielle

Le projet sépare la **vision** du **pilotage** :

- `FluxVideo` (dossier `fonctions/`) — classe dédiée à la vision. Elle capture les images, effectue toute la détection et renvoie les informations (position, angle, présence du bleu) sans jamais commander le robot.
- `main.py` (racine) — contient toute la logique de suivi de ligne : il interroge `FluxVideo` puis pilote les actionneurs en conséquence.
- Dossier `classes/` — les classes matérielles : `Moteur`, `Direction`, `Tourelle`, ainsi que les classes de LED (`FeuxArriere`, `LEDDroitBas`, `LEDGaucheBas`) héritant d'une classe mère commune `BandeLed`.

---

### Boucle de contrôle

```
Capture image
  ├── Ruban bleu proche ?      → arrêt de la séquence
  ├── Ligne détectée ?          → calcul de l'angle de braquage → direction + moteur
  └── Ligne perdue ?            → manœuvre de recherche
```

### Communication matérielle

- **I2C (adresse 0x5f)** : pilotage des servomoteurs et du moteur via le contrôleur PCA9685.
- **SPI (GPIO10)** : commande des LED adressables WS2812 pour la signalisation.
- **Caméra CSI** : flux vidéo capturé via picamera2, traité par OpenCV.

### Alimentation

Le robot doit être alimenté par deux batteries 18650 (7,4 V) sur le connecteur Vin de la HAT lors du fonctionnement des moteurs. L'alimentation USB-C seule ne fournit pas le courant nécessaire et provoque des redémarrages (brownout).
