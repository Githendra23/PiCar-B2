import time

from CapteurSuiviLigne import CapteurSuiviLigne
from Moteur import Moteur, m1
from Roues import Roues
from ServoController import ServoController



VITESSE_CROISIERE   = 40   # ligne bien centrée
VITESSE_CORRECTION  = 25   # ajustement léger (perte 1 LED)
VITESSE_VIRAGE_FORT = 20   # braquage important
VITESSE_LENTE       = 10   # récupération (perte 2 LEDs)
VITESSE_RECUL       = 15   # marche arrière
VITESSE_MINI        = 5    # micro-ajustements

ANGLE_CENTRE      = 90
ANGLE_MIN         = 0
ANGLE_MAX         = 130
PLAGE_DROITE      = ANGLE_CENTRE - ANGLE_MIN   # 90
PLAGE_GAUCHE      = ANGLE_MAX - ANGLE_CENTRE   # 40


TIMEOUT_CORRECTION   = 0.4   # s avant de passer au virage fort
TIMEOUT_VIRAGE_FORT  = 0.8   # s avant de lancer la récupération
DT                   = 0.05  # période de boucle principale (s)
DUREE_RECUL          = 0.3   # s de recul avant contre-braquage
DUREE_CONTRE_BRAQUAGE = 0.3  # s de contre-braquage en marche arrière
MAX_TENTATIVES_RECUL = 5     # manœuvres max avant abandon


def angle_depuis_pourcentage(pourcentage: float, direction: str) -> int:
    """
    Convertit un pourcentage de braquage (0–100 %) en angle absolu.
    direction : 'gauche' ou 'droite'

    Les plages ne sont pas symétriques :
      - droite : ANGLE_CENTRE - pourcentage * PLAGE_DROITE / 100
      - gauche : ANGLE_CENTRE + pourcentage * PLAGE_GAUCHE / 100
    """
    pct = max(0.0, min(100.0, pourcentage))
    if direction == "droite":
        return int(ANGLE_CENTRE - pct * PLAGE_DROITE / 100)
    else:
        return int(ANGLE_CENTRE + pct * PLAGE_GAUCHE / 100)


class SuiviLigne:
    """Contrôleur principal du suivi de ligne."""

    # États internes
    ETAT_LIGNE        = "LIGNE"
    ETAT_CORRECTION   = "CORRECTION"
    ETAT_VIRAGE_FORT  = "VIRAGE_FORT"
    ETAT_RECUPERATION = "RECUPERATION"
    ETAT_PERDU        = "PERDU"

    def __init__(self, moteur: Moteur, roues: Roues, capteur: CapteurSuiviLigne):
        self.moteur  = moteur
        self.roues   = roues
        self.capteur = capteur

        self._etat            = self.ETAT_LIGNE
        self._t_changement    = time.time()
        self._derniere_direction = "droite"  # mémorise le côté perdu
        self._tentatives_recul  = 0

    def run(self):
        print("=== Démarrage du suivi de ligne ===")
        try:
            while True:
                lecture = self.capteur.statut()
                self._traiter(lecture)
                time.sleep(DT)
        except KeyboardInterrupt:
            print("\nArrêt demandé.")
        finally:
            self._arreter()


    def _traiter(self, capteurs: tuple):
        g, m, d = capteurs
        leds_actives = g + m + d

        if (g, m, d) == (1, 1, 1):
            self._transition(self.ETAT_LIGNE)
            self.roues.turn(ANGLE_CENTRE)
            self.moteur.avancer(VITESSE_CROISIERE)
            return

        if leds_actives == 0:
            self._traiter_perte_totale()
            return

        if leds_actives == 2:
            if (g, m, d) == (0, 1, 1):
                self._derniere_direction = "gauche"   # on dévie vers la gauche
                self._traiter_correction_legere("droite")
            elif (g, m, d) == (1, 1, 0):
                self._derniere_direction = "droite"
                self._traiter_correction_legere("gauche")
            elif (g, m, d) == (1, 0, 1):
                # Milieu perdu, situation ambiguë =  mini-ralentissement
                self._traiter_milieu_perdu()
            return

        if leds_actives == 1:
            if (g, m, d) == (0, 0, 1):
                self._derniere_direction = "gauche"
                self._traiter_forte_deviation("droite")
            elif (g, m, d) == (1, 0, 0):
                self._derniere_direction = "droite"
                self._traiter_forte_deviation("gauche")
            elif (g, m, d) == (0, 1, 0):
                # Seulement le milieu : on continue prudemment tout droit
                self._traiter_milieu_seul()
            return
        

    def _traiter_correction_legere(self, direction_virage: str):
        """Perte d'une LED latérale -> Phase 1 / Phase 2."""
        now = time.time()

        if self._etat != self.ETAT_CORRECTION and self._etat != self.ETAT_VIRAGE_FORT:
            # Premier instant de déviation -> Phase 1
            self._transition(self.ETAT_CORRECTION)

        elapsed = now - self._t_changement

        if self._etat == self.ETAT_CORRECTION:
            if elapsed < TIMEOUT_CORRECTION:
                # Virage léger 25 %
                angle = angle_depuis_pourcentage(25, direction_virage)
                self.roues.turn(angle)
                self.moteur.avancer(VITESSE_CORRECTION)
            else:
                # Phase 2 : virage fort
                self._transition(self.ETAT_VIRAGE_FORT)

        if self._etat == self.ETAT_VIRAGE_FORT:
            if elapsed < TIMEOUT_VIRAGE_FORT:
                angle = angle_depuis_pourcentage(50, direction_virage)
                self.roues.turn(angle)
                self.moteur.avancer(VITESSE_VIRAGE_FORT)
            else:
                # On n'a toujours pas retrouvé la ligne -> récupération
                self._transition(self.ETAT_RECUPERATION)
                self._tentatives_recul = 0

    def _traiter_forte_deviation(self, direction_virage: str):
        """1 seule LED active (latérale) -> récupération immédiate."""
        if self._etat != self.ETAT_RECUPERATION:
            self._transition(self.ETAT_RECUPERATION)
            self._tentatives_recul = 0

        self._manoeuvre_recul(direction_virage)

    def _traiter_milieu_perdu(self):
        """Gauche et droite actives, milieu éteint -> situation instable."""
        # Ralentissement et léger braquage du dernier côté connu
        angle = angle_depuis_pourcentage(10, self._derniere_direction)
        self.roues.turn(angle)
        self.moteur.avancer(VITESSE_LENTE)

    def _traiter_milieu_seul(self):
        """Seul le capteur central est actif -> avancer prudemment."""
        self.roues.turn(ANGLE_CENTRE)
        self.moteur.avancer(VITESSE_LENTE)

    def _traiter_perte_totale(self):
        """Aucun capteur actif → se souvenir du dernier côté."""
        if self._etat != self.ETAT_PERDU:
            self._transition(self.ETAT_PERDU)
            self._tentatives_recul = 0

        # Contra-braquage du côté opposé à la dernière déviation connue
        cote_recul = "gauche" if self._derniere_direction == "droite" else "droite"
        self._manoeuvre_recul(cote_recul)

    def _manoeuvre_recul(self, direction_contre_braquage: str):
        """
        Effectue une impulsion :
          1. Recul avec contre-braquage léger (≤ 10 %)
          2. Avance micro-ajustement
        Incrément le compteur de tentatives.
        """
        if self._tentatives_recul >= MAX_TENTATIVES_RECUL:
            print("⚠  Trop de tentatives de récupération — arrêt sécurité.")
            self._arreter()
            return

        print(f"[Récupération] tentative {self._tentatives_recul + 1} "
              f"— contre-braquage {direction_contre_braquage}")

        # Braquage faible pour micro-ajustement (max 10 %)
        angle_cb = angle_depuis_pourcentage(8, direction_contre_braquage)

        # Recul avec braquage
        self.roues.turn(angle_cb)
        self.moteur.reculer(VITESSE_RECUL)
        time.sleep(DUREE_RECUL)

        # Micro-avance pour sonder
        self.moteur.avancer(VITESSE_MINI)
        time.sleep(DUREE_CONTRE_BRAQUAGE)

        self._tentatives_recul += 1

    def _transition(self, nouvel_etat: str):
        if self._etat != nouvel_etat:
            print(f"[État] {self._etat} -> {nouvel_etat}")
            self._etat = nouvel_etat
            self._t_changement = time.time()

    def _arreter(self):
        self.moteur.stop()
        self.roues.reset()
        print("Robot arrêté — roues recentrées.")

        
if __name__ == "__main__":
    servo_controller = ServoController()
    roues   = Roues(servo_controller)
    capteur = CapteurSuiviLigne()

    controleur = SuiviLigne(moteur=m1, roues=roues, capteur=capteur)
    controleur.run()
