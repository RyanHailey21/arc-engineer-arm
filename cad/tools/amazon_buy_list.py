# -*- coding: utf-8 -*-
"""Amazon US sources for every purchased part of the FOURBAR arm, plus what the model leaves out (servo bus adapter,
12 V supply, cables, raw stock, filament). Plain Python:

    python -I cad/tools/amazon_buy_list.py      -> cad/out/fourbar/amazon_buy_list.csv

Looked up 2026-11-22 (M3 / M4 kits 2026-11-27) with the Amazon MCP (search_products / get_product); quantities from cad/out/fourbar/BOM.csv
(cad/tools/bom.py). Column `prototype`: needed for the fully printed fit-and-motion build (cad/tools/export_print.py).
Re-check prices and stock before ordering; update R when the BOM changes.
"""
import csv
import os

CAD = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
A = "https://www.amazon.com/dp/"
# section, bom item, need, product, ASIN, packs, price per pack, note
R = [
("Electronics", "STS3215 (J1-J4, gripper)", "5", "FEETECH STS3215 12 V 30 kg*cm, 1:345, 2-pack", "B0FMXVR77Y", 3, 48.99, "6 servos, 1 spare. Confirm 12 V / 1:345 and 25T spline on receipt; horns and 3-pin cables come in the box"),
("Electronics", "Bus adapter (not in model)", "1", "FE-URT-1 serial bus servo adapter (USB to TTL/RS485)", "B0FRQZQQF3", 1, 16.99, "PC or Pi to the servo bus; feeds the supply onto the bus"),
("Electronics", "12 V supply (not in model)", "1", "12 V 10 A 120 W adapter, 5.5x2.1 plug", "B0G31W3J97", 1, 23.74, "check the plug against the URT-1 power input; each servo stalls at about 2.7 A"),
("Electronics", "Servo bus cables (not in model)", "as needed", "5264 3-pin servo cables, 3 x 90 cm + 3 x 30 cm", "B0GZVMQ6TB", 1, 9.60, "base-to-wrist runs are longer than the cables in the servo box"),
("Bearings", "6700ZZ 10x15x4", "6", "uxcell 6700ZZ, 10 pcs", "B082PPYZQX", 1, 8.09, ""),
("Bearings", "6701ZZ 12x18x4", "1", "uxcell 6701ZZ, 5 pcs", "B0CRBC4ZS2", 1, 7.59, ""),
("Bearings", "6804ZZ 20x32x7", "2", "uxcell 6804ZZ ABEC3, 2 pcs", "B08H1RQQSV", 1, 6.74, ""),
("Bearings", "6805ZZ 25x37x7", "1", "uxcell 6805ZZ, 2 pcs", "B07TJFL7N8", 1, 7.29, ""),
("Bearings", "MR105ZZ 5x10x4", "6", "Apex RC MR105ZZ, 10 pcs", "B00XQ9212C", 1, 8.99, ""),
("Fasteners", "BHCS M3x6 / x8 / x10 / x30 (kit)", "27 / 18 / 4 / 6", "QOOSIKICC 1050 pc M3 button head kit, SS: M3x4-35 (4/6/8/10/12/16/20/25/30/35), nuts, washers", "B0DFWYBJJJ", 1, 13.98, "one kit for every M3 button head except x5 (horn screws, own pack); count the M3x6 on arrival (need 27, buy a 100-pack B0DKXNXQNJ if short)"),
("Fasteners", "BHCS M3x5", "8", "M3x5 button head, 304 SS, 100 pcs", "B09HQLC89R", 1, 7.00, "horn screws: the kit has no x5"),
("Fasteners", "CSK M3x6", "8", "M3x6 flat head DIN 7991, 304 SS, 80 pcs", "B0DKY3G1CS", 1, 6.29, ""),
("Fasteners", "SHCS M4x8 / M4x12 + Washer M4 (kit)", "1 / 4 + 1 washer", "SVLING M4 socket head kit, 304 SS: 25x M4x8, 20x M4x12, 129 flat washers 4x9, nuts", "B0GHMMCZKM", 1, 7.99, "replaces the separate M4x8, M4x12 and M4 washer packs (stage 1 standardisation, 2026-11-27); nylocs still from the Nyloc M4 line"),
("Fasteners", "SHCS M5x10", "2", "M5x10 socket head, 304 SS, 50 pcs", "B0GCSYGVNN", 1, 7.99, ""),
("Fasteners", "SB5x8 shoulder screw (d5, M4)", "3", "uxcell shoulder bolt 5 dia x 8 L, M4, 5 pcs", "B077GWC559", 1, 9.99, ""),
("Fasteners", "SB5x10 shoulder screw", "1", "uxcell 5 dia x 10 L, M4, 6 pcs", "B0DP7173LB", 1, 6.89, "confirm the listing is a shoulder bolt"),
("Fasteners", "SB5x12 shoulder screw", "1", "Shoulder bolt 5 dia x 12 L, M4, 30 pcs", "B0HKRSVY7K", 1, 9.89, ""),
("Fasteners", "SB5x4 shoulder screw (Ev1)", "1", "uxcell shoulder bolt 5 dia x 5 L, M4, 10 pcs", "B077GWXJHB", 1, 13.49, "no 4 mm shoulder on Amazon: use the 5 mm one with 1.0 mm of 5x9 shims (shim kit) so the nyloc still clamps"),
("Fasteners", "Nyloc M3", "10", "M3 nylock nuts with washers, 304 SS", "B0HC671TFL", 1, 9.99, ""),
("Fasteners", "Nyloc M4", "6", "M4 nylock nuts, SS, 150 pcs", "B0DPKSD7MV", 1, 6.99, ""),
("Fasteners", "Washer M5 (ISO 7089)", "2", "M5 washer 5x10x1, 304 SS, 250 pcs", "B07WZ5WQCG", 1, 12.99, ""),
("Fasteners", "WASHER-D4 4x8x0.5 (+ SB5x4 shims)", "2", "Shim washer kit 3x6 to 10x16, 0.1-0.5 mm", "B0GQ3JGHPZ", 1, 16.99, "also has the 5x9 shims for SB5x4"),
("Fasteners", "PAN-M2x12 self-tapping", "16", "M2x12 pan head self-tapping, 316 SS, 50 pcs", "B0FJD4G1P6", 1, 6.19, "into the servo bottom-cap holes; snug only"),
("Fasteners", "Insert M3 (bore D4.0 x 4 deep)", "18", "M3x4x5 brass heat-set inserts, 100 pcs", "B0FDKYTMZ8", 1, 6.49, "4 mm long, 5 mm knurl OD; test one in a printed D4.0 bore first"),
("Fasteners", "ECLIP DIN 6799 size 7 (D10 shafts)", "3", "Stainless E-clip kit 1.5-15 mm, incl. 7 mm", "B0D5HFR1CP", 1, 9.70, ""),
("Pins and collars", "PIN-D4x8", "4", "uxcell 4x8 bearing-steel dowels, +/-0.02, 100 pcs", "B0F54G8WPB", 1, 6.93, ""),
("Pins and collars", "PIN-D4x14", "10", "HARFINGTON 4x14 304 SS dowels, 50 pcs", "B0F6CVZQGT", 1, 6.89, "stainless, not hardened 52100: fine at these loads; check the fit in the reamed 4 H8 bores"),
("Pins and collars", "PIN-D4x20", "1", "uxcell 4x20 bearing-steel dowels, +/-0.02, 100 pcs", "B0F54FSG1Q", 1, 9.89, ""),
("Pins and collars", "PIN-D4x30", "1", "4x30 precision-ground SS dowels, 30 pcs", "B0GS18FXL3", 1, 5.99, ""),
("Pins and collars", "COLLAR10 D10 x D24 x 9", "2", "M1C-10 steel one-piece clamp collar, 10 bore, 24 OD, M3x10 screw", "B0026GU9M0", 2, 6.30, "matches Stafford 1LM010"),
("Pins and collars", "9271K56 torsion spring", "1", "McMaster-Carr 9271K56 (no Amazon match)", "", 0, 0, "NOT ON AMAZON: order 9271K56 and the alternate 9271K52 from McMaster; the back-drive bench test picks one"),
("Cable management", "CLIP adhesive tie mount", "2", "XHF 3/4 in adhesive tie mounts, 100 pcs", "B07M69LK65", 1, 6.45, "19 mm square against the 10 mm modelled: check the spot on the base"),
("Cable management", "PCLIP 9 mm bundle, M3", "2", "3/8 in rubber-lined stainless P-clamps, 30 pcs", "B0B1H55XZZ", 1, 9.99, ""),
("Stock: plate", "CF 3 mm (19 plates, longest 451 mm)", "1 sheet", "MECCANIXITY 3K CF 600 x 500 x 3 mm", "B0DN6BRSYZ", 1, 120.49, "a 400 x 500 sheet would be about 90 percent used before kerf; 600 x 500 leaves room for a re-cut. Needs a CNC router or waterjet"),
("Stock: plate", "CF 4 mm (Rod_2, 366 x 16)", "1 sheet", "cncarbonfiber 4 mm 300 x 400", "B07DZJ2Q75", 1, 66.95, "one part: a cutting service that supplies CF is cheaper for this one"),
("Stock: plate", "Al 6061 5 mm (Base_Plate_AL5, 160 x 150)", "1", "uxcell 6061 200 x 200 x 5 mm", "B0CQXPPDFB", 1, 25.59, "cut, drill and tap from the current model, not the released DXF (old 345 x 224 plate)"),
("Stock: bar", "Al round D40 (J1 hub, J2 hub, roll hub)", "2", "6061 round bar D40 x 100 mm", "B0FG66GY2L", 2, 28.06, "lathe and mill: 27 + 38.5 + 16 mm of parts plus facing and parting"),
("Stock: bar", "Al round D25 (level hubs, coupler, sleeve, spacers)", "1", "METERXITY D25 x 100 mm, 2 pcs", "B0FH2JYPPB", 1, 11.49, "hex af19 hubs, D24 coupler, D13 sleeve, D9 spacers"),
("Stock: bar", "Al round D8 (standoffs 88 and 33 mm)", "1", "D8 x 300 mm aluminium rod, 2 pcs", "B09Y2F61DL", 1, 9.19, "drill D2.5 through, tap M3 both ends"),
("Stock: bar", "Al round D6 (gripper standoffs 46 mm)", "1", "D6 x 300 mm 6061 rod, 10 pcs", "B0C495BFV2", 1, 11.99, "tap M3 both ends"),
("Stock: bar", "Steel D10 shafts (elbow 101, wrist 70)", "1", "10 x 200 mm case-hardened linear shaft, 2 pcs", "B0BZQ9GPL7", 1, 10.39, "h8, not the h6 specified: check the fit in the bearing bores. The e-clip grooves and the wrist D6 step need a lathe with a carbide tool"),
("Stock: misc", "PTFE rod D13 (thrust sleeve)", "1", "PTFE rod D15 x 330 mm", "B0CKK5MRG6", 1, 8.08, "turn to D13"),
("Stock: misc", "PTFE sheet 1.0 mm (2 washers)", "1", "Virgin PTFE 100 x 100 x 1 mm, 2 pcs", "B0F83SXDK9", 1, 13.99, ""),
("Stock: misc", "SS shim 0.5 mm (3 shims)", "1", "304 SS sheet 0.5 mm, 12 x 6 in, 2 pcs", "B0GJRDWP66", 1, 6.99, "304 instead of 301 spring temper: fine for spacers"),
("Stock: misc", "SS 1.5 mm (Shim_A)", "1", "304 SS plate 1.5 x 100 x 100 mm", "B0DDLC781F", 1, 12.99, ""),
("Print", "PETG-CF (frames, cradle, housing, palm, jaws, gears)", "about 0.6 kg", "ELEGOO PETG-CF 1.75 mm 1 kg", "B0F37YCK6K", 1, 17.99, "the 54T/18T spur and 77T sector gears are specified in PA12/POM; PETG-CF is the build-as-is choice, swap if they wear"),
("Stock: misc", "Neoprene 1/16 in (grip faces on the printed pads)", "4 strips", "Neoprene rubber sheet 1/16 x 12 x 12 in", "B0BKQRN7S6", 1, 6.89, "solid, not sponge (sponge compresses and moves the contact); no adhesive back: bond with 3M 300LSE transfer tape or CA"),
]
out = os.path.join(CAD, "out", "fourbar", "amazon_buy_list.csv")
tot = 0.0
ptot = {}


def proto(s, i):
    """Is the line needed for the fully printed prototype (cad/tools/export_print.py)?"""
    if s.startswith("Stock") and "D10" in i:
        return "optional"          # printed shafts work for fit; the real rod runs truer in the bearings
    if s.startswith("Stock"):
        return "no"                # printed instead
    if s == "Print" and "PETG" in i:
        return "yes, 2 packs"      # about 1.4 kg for the whole arm printed
    return "yes"


with open(out, "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f, lineterminator="\n")
    w.writerow(["section", "bom_item", "need", "buy", "asin", "packs", "pack_usd", "line_usd", "prototype", "url", "note"])
    for s, i, n, p, a, k, pr, no in R:
        l = round(k * pr, 2)
        tot += l
        pt = proto(s, i)
        ptot[pt] = ptot.get(pt, 0) + l
        w.writerow([s, i, n, p, a, k, "%.2f" % pr if pr else "", "%.2f" % l if l else "", pt, A + a if a else "", no])
    w.writerow(["PROTOTYPE TOTAL", "", "", "", "", "", "", "%.2f" % (ptot.get("yes", 0) + 2 * ptot.get("yes, 2 packs", 0)),
                "yes lines", "", "plus %.2f optional (D10 rod)" % ptot.get("optional", 0)])
    w.writerow(["TOTAL", "", "", "", "", "", "", "%.2f" % tot, "", "",
                "Amazon US prices on 2026-11-22, before tax and shipping; excludes the McMaster spring and any cutting or machining"])
sec = {}
for s, i, n, p, a, k, pr, no in R:
    sec[s] = sec.get(s, 0) + k * pr
print(len(R), "lines, total %.2f" % tot, ptot)
for s, v in sec.items():
    print("  %-18s %8.2f" % (s, v))
