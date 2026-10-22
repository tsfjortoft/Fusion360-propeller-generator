# Fusion 360-script: parametrisk propell (lofta blader med vridning)
# Bruk: Utilities > Scripts and Add-Ins > Scripts > "+" (Create new script, Python)
#       lim inn denne koden i .py-filen, og trykk Run.
import adsk.core
import adsk.fusion
import traceback
import math

# ---------------- PARAMETERE (mm og grader) ----------------
D = 24.0        # propelldiameter (dyse 26 mm minus ca. 1 mm klaring per side)
HUB_D = 8.0     # navdiameter
BORE_D = 5.1    # hull til aksel (5 mm aksel + 0.1 mm klaring)
HUB_L = 10.0    # navlengde
BLADES = 3      # antall blader
PHI_07 = 25.0   # stigningsvinkel ved 0.7R (grader)
C_MAX = 10.0    # kordelengde (bladbredde) midt på bladet
T = 1.0         # bladtykkelse
HAND = 1        # 1 eller -1: speiler propellen (høyre-/venstredreiende)
N_SEC = 6       # antall snitt i loften
ROOT_R = 3.5    # innerste snitt (ligger litt inne i navet)
RPM = 1500      # kun brukt i overslagsberegningen på slutten
# ------------------------------------------------------------


def cm(mm):
    return mm / 10.0   # Fusion API bruker cm internt


def add_section(comp, r, phi, chord, thick, s):
    """Tegner et rektangel (kordelinje x tykkelse) på et plan ved radius r,
    rotert phi grader fra rotasjonsplanet."""
    planes = comp.constructionPlanes
    pin = planes.createInput()
    pin.setByOffset(comp.yZConstructionPlane,
                    adsk.core.ValueInput.createByReal(cm(r)))
    plane = planes.add(pin)
    o = plane.geometry.origin

    sk = comp.sketches.add(plane)

    cp, sp = math.cos(phi), math.sin(phi)
    u = (cp, s * sp)      # korderetning (y, z)
    n = (-s * sp, cp)     # normal til kordelinjen (y, z)

    def pt(a, b):
        p = adsk.core.Point3D.create(
            o.x,
            o.y + cm(a * u[0] + b * n[0]),
            o.z + cm(a * u[1] + b * n[1]))
        return sk.modelToSketchSpace(p)

    h, w = chord / 2.0, thick / 2.0
    p0, p1, p2, p3 = pt(-h, -w), pt(h, -w), pt(h, w), pt(-h, w)

    lines = sk.sketchCurves.sketchLines
    l1 = lines.addByTwoPoints(p0, p1)
    l2 = lines.addByTwoPoints(l1.endSketchPoint, p2)
    l3 = lines.addByTwoPoints(l2.endSketchPoint, p3)
    lines.addByTwoPoints(l3.endSketchPoint, l1.startSketchPoint)
    return sk.profiles.item(0)


def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui = app.userInterface
        design = adsk.fusion.Design.cast(app.activeProduct)
        root = design.rootComponent

        # Part Design kan bare ha én komponent, så vi bygger i rotkomponenten
        comp = root

        R = D / 2.0
        P = 2 * math.pi * 0.7 * R * math.tan(math.radians(PHI_07))
        s = 1 if HAND >= 0 else -1

        # --- Nav (akse langs Z) ---
        sk_hub = comp.sketches.add(comp.xYConstructionPlane)
        sk_hub.sketchCurves.sketchCircles.addByCenterRadius(
            adsk.core.Point3D.create(0, 0, 0), cm(HUB_D / 2.0))
        ext = comp.features.extrudeFeatures
        ein = ext.createInput(sk_hub.profiles.item(0),
                              adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        ein.setSymmetricExtent(adsk.core.ValueInput.createByReal(cm(HUB_L)), True)
        hub = ext.add(ein).bodies.item(0)
        hub.name = 'Propell'

        # --- Ett blad: loft mellom vridde snitt ---
        profiles = []
        for i in range(N_SEC):
            r = ROOT_R + (R - ROOT_R) * i / (N_SEC - 1)
            phi = math.atan(P / (2 * math.pi * r))
            x = r / R
            chord = C_MAX * max(0.35 + 2.2 * x * (1 - x), 0.3)
            profiles.append(add_section(comp, r, phi, chord, T, s))

        lofts = comp.features.loftFeatures
        lin = lofts.createInput(adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        for p in profiles:
            lin.loftSections.add(p)
        lin.isSolid = True
        loft = lofts.add(lin)

        # --- Mønster rundt Z ---
        blade_bodies = [loft.bodies.item(0)]
        if BLADES > 1:
            ents = adsk.core.ObjectCollection.create()
            ents.add(loft)
            pat = comp.features.circularPatternFeatures
            pin = pat.createInput(ents, comp.zConstructionAxis)
            pin.quantity = adsk.core.ValueInput.createByReal(BLADES)
            pin.totalAngle = adsk.core.ValueInput.createByString('360 deg')
            pin.isSymmetric = False
            pf = pat.add(pin)
            for i in range(pf.bodies.count):
                blade_bodies.append(pf.bodies.item(i))

        # --- Slå sammen nav + blader (kun propellens egne legemer) ---
        tools = adsk.core.ObjectCollection.create()
        for b in blade_bodies:
            if b.entityToken != hub.entityToken:
                tools.add(b)
        cin = comp.features.combineFeatures.createInput(hub, tools)
        cin.operation = adsk.fusion.FeatureOperations.JoinFeatureOperation
        comp.features.combineFeatures.add(cin)

        # --- Akselhull ---
        sk_bore = comp.sketches.add(comp.xYConstructionPlane)
        sk_bore.sketchCurves.sketchCircles.addByCenterRadius(
            adsk.core.Point3D.create(0, 0, 0), cm(BORE_D / 2.0))
        cut = ext.createInput(sk_bore.profiles.item(0),
                              adsk.fusion.FeatureOperations.CutFeatureOperation)
        cut.setSymmetricExtent(adsk.core.ValueInput.createByReal(cm(HUB_L * 2)), True)
        cut.participantBodies = [hub]   # ikke kutt i resten av modellen
        ext.add(cut)

        # --- Overslagsberegning ---
        n = RPM / 60.0
        v_th = P / 1000.0 * n
        Dm = D / 1000.0
        thrust = 0.25 * 1000 * n ** 2 * Dm ** 4
        torque = 0.03 * 1000 * n ** 2 * Dm ** 5
        power = torque * 2 * math.pi * n
        ui.messageBox(
            'Propell ferdig\n\n'
            'Stigning P = %.1f mm (P/D = %.2f)\n'
            'Teoretisk fart ved %d rpm: %.2f m/s (realistisk 50-70 %%)\n'
            'Skyv (grovt): %.3f N per propell\n'
            'Moment: %.2f mNm, akseleffekt: %.3f W'
            % (P, P / D, RPM, v_th, thrust, torque * 1000, power))

    except Exception:
        if ui:
            ui.messageBox('Feil:\n{}'.format(traceback.format_exc()))