# -*- coding: utf-8 -*-
"""
Procurement table for every PURCHASED line of fab/BOM.csv.
    python cad/fab/make_procurement.py   -> cad/fab/procurement.csv + procurement.md
status:
  VERIFIED   - supplier PN looked up 2026-11-14 (McMaster MCP get_product / vendor page) and the
               returned spec matches the BOM line
  CATALOGUE  - standard catalogue item, designation fully specified; supplier PN not yet looked up
  SOURCED    - vendor product page found matching the designation (2026-11-15); order-time confirmation in note
  SPECIAL    - not a stock item as specified; quote / secondary op required (see note)
"""
import csv
import os

HERE = os.path.dirname(os.path.abspath(__file__))
MC = "https://www.mcmaster.com/"

# item -> (designation, vendor, PN, url, status, note)
P = {
    # ---- verified McMaster lines
    "SHCS_M3x6": ("ISO 4762 M3x6 12.9 black oxide", "McMaster-Carr", "91290A111", MC + "91290A111", "VERIFIED", ""),
    "SHCS_M3x8": ("ISO 4762 M3x8 12.9 black oxide", "McMaster-Carr", "91290A113", MC + "91290A113", "VERIFIED", ""),
    "SHCS_M3x10": ("ISO 4762 M3x10 12.9 black oxide", "McMaster-Carr", "91290A115", MC + "91290A115", "VERIFIED", ""),
    "SHCS_M3x30": ("ISO 4762 M3x30 12.9 black oxide (part thread, 18 min)", "McMaster-Carr", "91290A130", MC + "91290A130", "VERIFIED", ""),
    "SHCS_M4x12": ("ISO 4762 M4x12 12.9 black oxide", "McMaster-Carr", "91290A148", MC + "91290A148", "VERIFIED", ""),
    "BHCS_M3x5": ("ISO 7380 M3x5 A2", "McMaster-Carr", "92095A177", MC + "92095A177", "VERIFIED", ""),
    "BHCS_M3x6": ("ISO 7380 M3x6 A2", "McMaster-Carr", "92095A179", MC + "92095A179", "VERIFIED", ""),
    "BHCS_M3x8": ("ISO 7380 M3x8 A2", "McMaster-Carr", "92095A181", MC + "92095A181", "VERIFIED", "user-confirmed lookup"),
    "BHCS_M3x10": ("ISO 7380 M3x10 A2", "McMaster-Carr", "92095A182", MC + "92095A182", "VERIFIED", ""),
    "CSK_M3x5": ("DIN 7991 M3x5 A2 (ISO 10642 equiv.)", "McMaster-Carr", "92125A125", MC + "92125A125", "VERIFIED", ""),
    "CSK_M3x6": ("ISO 10642 M3x6 A2", "McMaster-Carr", "92125A126", MC + "92125A126", "VERIFIED", ""),
    "Nyloc_M3": ("DIN 985 M3 A2 nylon-insert", "McMaster-Carr", "93625A100", MC + "93625A100", "VERIFIED", ""),
    "Nyloc_M4": ("DIN 985 M4 A2 nylon-insert", "McMaster-Carr", "93625A150", MC + "93625A150", "VERIFIED", ""),
    "Washer_M4": ("ISO 7089 M4 A2", "McMaster-Carr", "93475A230", MC + "93475A230", "VERIFIED", ""),
    "Insert_M3": ("M3 brass tapered heat-set insert, 3.8 mm", "McMaster-Carr", "94180A331", MC + "94180A331", "VERIFIED",
                  "BOM models 4.0 mm length; 3.8 mm installed length fits the 4 mm bosses"),
    # ---- verified vendor items (web search 2026-11-14)
    "STS3215": ("Feetech STS3215 serial-bus servo, 12 V 30 kg*cm (C018/C047), 1:345, magnetic encoder", "RobotShop / AIFitLab / Amazon",
                "STS3215-C018", "https://www.robotshop.com/products/feetech-12v-30kgcm-magnetic-encoding-servo-sts3215", "VERIFIED",
                "USD 22-49 each (2026-11-19); J1-J4 + gripper; the supplied horns are used"),
    "Brg_6804ZZ": ("Deep-groove ball bearing 6804ZZ 20x32x7", "McMaster-Carr / VXB", "6804ZZ", "https://www.vxb.com", "SOURCED",
                   "standard size; J1/J2 hub journals in the drive frames"),
    # ---- rev B (four-bar release, STS3215 drives) additions, 2026-11-19
    "9271K56": ("Torsion spring 90 deg RH, 0.499 in OD, 0.059 in wire, 4.5 in*lbf", "McMaster-Carr", "9271K56", MC + "9271K56", "VERIFIED", "opens the four-bar jaws unpowered"),
    "PIN-D4x14": ("Dowel pin D4 m6 x 14, 52100, ISO 8734", "McMaster-Carr", "91595A158", MC + "91595A158", "VERIFIED", "four-bar coupler + idler pivots"),
    "PIN-D4x20": ("Dowel pin D4 m6 x 20, 52100, ISO 8734", "McMaster-Carr", "91595A167", MC + "91595A167", "VERIFIED", "left drive pivot"),
    "PIN-D4x30": ("Dowel pin D4 m6 x 30, 52100, ISO 8734", "McMaster-Carr", "91595A179", MC + "91595A179", "VERIFIED", "right drive pivot"),
    "PIN-D4x8": ("Dowel pin D4 m6 x 8, 52100, ISO 8734", "McMaster-Carr", "91595A series", MC + "91595A", "SOURCED", "confirm the 4 x 8 part number"),
    "SB5x8_Dv2": ("Shoulder screw d5 x 8, M4 x 5 thread, 18-8 SS (ISO 7379 type)", "McMaster-Carr", "90265A577", MC + "90265A577", "VERIFIED", "level-keeping stage-2 pivot D"),
    "SB5x8_Ev2": ("Shoulder screw d5 x 8, M4 x 5 thread, 18-8 SS (ISO 7379 type)", "McMaster-Carr", "90265A577", MC + "90265A577", "VERIFIED", "level-keeping stage-2 pivot E"),
    "SHCS_M5x10": ("ISO 4762 M5x10 12.9 black oxide", "McMaster-Carr", "91290A224", MC + "91290A224", "SOURCED", "J1/J2 hub end screws; confirm the part number"),
    "Washer_M5": ("ISO 7089 M5 A2 (D12 x 1 at the hub ends)", "McMaster-Carr", "93475A240", MC + "93475A240", "SOURCED", "confirm the part number"),
    "Washer_LD": ("DIN 988 shim ring 4 x 8 x 0.5, stainless", "any supplier", "DIN 988 4x8x0.5", "", "SOURCED", "thrust washers at the palm ground layer"),
    "Washer_RD": ("DIN 988 shim ring 4 x 8 x 0.5, stainless", "any supplier", "DIN 988 4x8x0.5", "", "SOURCED", "thrust washers at the palm ground layer"),
    "PAN-M2x12": ("M2 x 12 thread-forming / PA2.0 self-tapping pan head, stainless", "McMaster-Carr", "99461A", MC + "99461A",
                  "SOURCED", "fixes each STS3215 through its cradle floor (replaces the bottom-cap screws)"),
    "M2006-P36": ("DJI RoboMaster M2006 P36", "DJI Store", "RM-M2006-P36",
                  "https://store.dji.com/product/rm-m2006-p36-brushless-motor", "VERIFIED", "USD 55"),
    "C610": ("DJI RoboMaster C610 ESC", "DJI Store", "RM-C610",
             "https://store.dji.com/product/rm-c610-brushless-dc-motor-speed-control", "VERIFIED", "USD 39"),
    "MGN9-RAIL": ("HIWIN MGN9R rail, cut to 83 mm", "HIWIN distributor (e.g. 3DPrintingUSA)", "MGN9R-83",
                  "https://3dprintingusa.com/products/mgn9h-linear-guide-block", "VERIFIED", "cut-to-length from stock rail"),
    "MGN9H": ("HIWIN MGN9H block Z0", "HIWIN distributor", "MGN9H1R..Z0CM",
              "https://3dprintingusa.com/products/mgn9h-linear-guide-block", "VERIFIED", ""),
    # ---- catalogue (designation exact, PN to pick from the linked family page)
    "SHCS_M3x35": ("ISO 4762 M3x35 12.9", "McMaster-Carr", "91290A (family)", MC + "91290A", "CATALOGUE", ""),
    "SHCS_M4x8": ("ISO 4762 M4x8 12.9 black oxide", "McMaster-Carr", "91290A140", MC + "91290A140", "VERIFIED", ""),
    "SHCS_M4x25": ("ISO 4762 M4x25 12.9", "McMaster-Carr", "91290A (family)", MC + "91290A", "CATALOGUE", ""),
    "BHCS_M3x4": ("ISO 7380 M3x4 A2", "McMaster-Carr", "92095A (family)", MC + "92095A", "CATALOGUE", ""),
    "SetScrew_M3": ("ISO 4029 M3x4 cup point", "McMaster-Carr", "91390A098", MC + "91390A098", "VERIFIED", ""),
    "SetScrew_M3x3": ("ISO 4029 M3x3 cup point", "McMaster-Carr", "91390A097", MC + "91390A097", "VERIFIED", ""),
    "Dowel_3x8": ("ISO 8734 3 m6 x 8 hardened", "McMaster-Carr", "91595A (family)", MC + "dowel-pins", "CATALOGUE", ""),
    "Dowel_4x6": ("ISO 8734 4 m6 x 6 hardened", "McMaster-Carr", "91595A (family)", MC + "dowel-pins", "CATALOGUE", ""),
    "Eclip_D10": ("DIN 6799 size 7 (groove 7, shaft 8-11)", "Wurth / Fabory", "0490100 / 36200.070.001", "https://www.fabory.com/en-GB/p/36200070001", "VERIFIED", ""),
    "SB5x5_Ev1": ("Shoulder screw d5 x 5, M4", "Minibearings", "SHLD050-005-SKT-S3", "https://minibearings.com.au/products/5-000-5-000mm-m4x0-70-screws-shoulder-socket-head-303-stainlessscrews-shld050005skts3", "SOURCED", "rocker hole opened to D5.1 for the stock 5 mm shoulder"),
    "SB5x8_A": ("Shoulder screw d5 x 8, M4 x 5 thread, 18-8 SS black oxide (ISO 7379 type)", "McMaster-Carr", "90265A577", MC + "90265A577", "VERIFIED", ""),
    "SB5x10_G1": ("ISO 7379 d5 x 10, M4 (shoulder 10)", "McMaster-Carr", "92981A030", MC + "92981A030", "VERIFIED", ""),
    "SB5x12_B": ("ISO 7379 d5 x 12, M4 (shoulder 12)", "McMaster-Carr", "92981A034", MC + "92981A034", "VERIFIED", ""),
    "Shim_8x10": ("DIN 988 shim 8x14x0.5", "Misumi / McMaster", "shim family", MC + "shims", "CATALOGUE", ""),
    "Shim_A": ("DIN 988 shim (see model)", "Misumi / McMaster", "shim family", MC + "shims", "CATALOGUE", ""),
    "Shim_Ev1": ("DIN 988 shim (see model)", "Misumi / McMaster", "shim family", MC + "shims", "CATALOGUE", ""),
    "Washer_PTFE": ("PTFE thrust washer (see model)", "McMaster-Carr", "PTFE washer family", MC + "ptfe-washers", "CATALOGUE", ""),
    "FA_Standoff": ("Al round standoff M3 F-F (length per model)", "Keystone / McMaster", "standoff family", MC + "standoffs", "CATALOGUE", ""),
    "Finger_Standoff": ("Al round standoff M3 F-F (length per model)", "Keystone / McMaster", "standoff family", MC + "standoffs", "CATALOGUE", ""),
    "Servo_Standoff": ("Al round standoff M3 F-F (length per model)", "Keystone / McMaster", "standoff family", MC + "standoffs", "CATALOGUE", ""),
    "UA_Standoff": ("Al round standoff M3 F-F (length per model)", "Keystone / McMaster", "standoff family", MC + "standoffs", "CATALOGUE", ""),
    "6700ZZ": ("6700ZZ 10x15x4", "VXB", "6700ZZ (10x15x4 shielded)", "https://vxb.com/products/10x15-bearing-6700zz-10x15x4-shielded", "VERIFIED", ""),
    "Brg_6700ZZ": ("6700ZZ 10x15x4", "VXB", "6700ZZ (10x15x4 shielded)", "https://vxb.com/products/10x15-bearing-6700zz-10x15x4-shielded", "VERIFIED", ""),
    "Brg_6701ZZ": ("6701ZZ 12x18x4", "VXB", "kit7125", "https://vxb.com/products/6701zz-bearing-12x18x4-shielded", "VERIFIED", ""),
    "Brg_6805ZZ": ("6805ZZ 25x37x7", "VXB", "Kit7501", "https://vxb.com/products/6805zz-bearing-25x37x7-shielded", "VERIFIED", ""),
    "Brg_688ZZ": ("688ZZ 8x16x5", "VXB", "688ZZ-1", "https://vxb.com/products/8x16-bearing-688zz-8x16x5-shielded-miniature", "VERIFIED", ""),
    "MR104ZZ": ("MR104ZZ 4x10x4", "VXB", "MR104ZZ 10-pack", "https://vxb.com/products/4x10-shielded-4x10x4-miniature-bearing-pack-of-10", "VERIFIED", "confirm 4 mm width (some MR104ZZ listings are 4x10x3)"),
    "Brg_MR105ZZ": ("MR105ZZ 5x10x4", "VXB", "mr105zz-1", "https://vxb.com/5x10-Bearing-5x10x4-Shielded-Miniature-p/mr105zz-1.htm", "VERIFIED", ""),
    "COLLAR10": ("One-piece clamp collar D10 x D24 x 9, 1215 steel black oxide, M3x10 clamp screw included", "Stafford", "1LM010", "https://shaft-collars-couplings.staffordmfg.com/printitem/round-bore-shaft-collars/one-piece-split-shaft-collars/1lm010", "VERIFIED", "mounted inboard against the forearm plate (y 7.5..16.5); axial hold 1650 N"),
    "Collar_D8": ("Set-screw shaft collar D8 x D16 x 8, zinc-plated steel, M4x5 set screw included", "Stafford", "34LM008P2", "https://shaft-collars-couplings.staffordmfg.com/printitem/round-bore-shaft-collars/set-screw-shaft-collars/34lm008p2", "VERIFIED", ""),
    "SHAFT10": ("D10 h6 ground shaft, e-clip grooves + D-flat", "Misumi", "PSFG10 (configurable)", "https://us.misumi-ec.com", "CATALOGUE",
                "configure grooves / flat in Misumi configurator"),
    "GEAR-M1-20T": ("Spur gear m1 20T, ground, 6 mm finished bore, S45C", "KHK", "SSG1-20J6", "https://catalog.khkgears.us/item/spur-gears/ground-spur-gears-ssg-/ssg1-20j6", "VERIFIED", "KHK J-bore comes with an M4 set screw (not M3)"),
    "GEAR-M1-32T": ("Spur gear m1 32T, ground hubless, 8 mm bore, S45C", "KHK", "SSAG1-32", "https://catalog.khkgears.us/item/spur-gears/ground-hubless-spur-gears-ssag-/ssag1-32", "VERIFIED", "hubless: retained by the D8 collar + Loctite 638"),
    "HORN-25T": ("25T aluminium disc horn D19.95, 4x M3 on PCD14 (supplied with each STS3215)", "Feetech (in the servo box)", "STS3215 horn", "https://www.robotshop.com/products/feetech-12v-30kgcm-magnetic-encoding-servo-sts3215", "VERIFIED", "no separate purchase"),
    "PCLIP": ("Cushioned loop clamp 3/8 in (10 mm) ID, 321 SS + neoprene, MS21919", "McMaster-Carr", "3177T51", MC + "3177T51", "VERIFIED", "hole sized for #10: fit with the M3 screw + ISO 7089 M3 washer"),
    "Cable_Clip": ("Adhesive-back 4-way cable tie mount, ABS, for 0.19 in ties", "McMaster-Carr", "7582K151", MC + "7582K151", "VERIFIED", ""),
    "GT2-BELT": ("GT2 (2 mm pitch) timing belt, 9 mm wide, sold by the metre (open length, clamp-spliced)", "3D Printing Canada", "GT2-9mm Timing Belt (1 m)", "https://3dprintingcanada.com/products/gt2-9mm-timing-belt-1-metre", "VERIFIED", "page: Belt Type GT2 (the 2 mm-pitch GT2 profile), Width 9 mm, sold by the metre, in stock. Tensile-cord material not published by the seller; Gates PowerGrip GT2 10 mm (same store) states 2 mm pitch explicitly if a branded belt is preferred"),
    "Dowel_3x7": ("ISO 8734 3 m6 x 7, hardened", "McMaster-Carr", "91595A113", MC + "91595A113", "VERIFIED", ""),
    "Dowel_4x5": ("ISO 8734 4 m6 x 5, hardened", "McMaster-Carr", "91595A123", MC + "91595A123", "VERIFIED", ""),
    "Dowel_3x20": ("ISO 8734 3 m6 x 20, hardened (storage-drum axle)", "McMaster-Carr", "91595A122", MC + "91595A122", "VERIFIED", ""),
    "SHCS_M3x40": ("ISO 4762 M3x40 12.9 black oxide (part thread, 18 min)", "McMaster-Carr", "91290A136", MC + "91290A136", "VERIFIED", "end-block tapped holes deepened to 15 mm"),
    "SHCS_M4x30": ("ISO 4762 M4x30 12.9 black oxide", "McMaster-Carr", "91290A172", MC + "91290A172", "VERIFIED", ""),
    "SB5x4_Ev1": ("Shoulder screw d5 x 4, M4 x 9 thread, alloy steel", "McMaster-Carr", "92981A747", MC + "92981A747", "VERIFIED", "step seats on the 688 race face; nyloc clamps shim + rocker"),
    # ---- special
    "TR8X8-BIDIR": ("Tr8x8 4-start, RH + LH sections on one shaft, 235 mm, D8 journals", "Alibaba listing 1600056822308", "Tr8*8 Left and Right thread, 4 starts", "https://www.alibaba.com/product-introduction/8mm-Diameter-Left-and-Right-Thread_1600056822308.html", "VERIFIED", "USD 37.50 @ qty 1; listing states L+R thread and brass nuts; confirm on order: LH nut included, 235 mm length, D8 journal ends"),
    "NUT-T8": ("Tr8x8 (P2, 4-start) brass lead-screw nut, RH (T8 flange nut)", "3D Printing Canada (Creality)", "Official Creality Brass 8mm T-slot 4-start Leadscrew Nut T8", "https://3dprintingcanada.com/products/official-creality-brass-8mm-tslot-2-start-leadscrew-nut", "VERIFIED", "page: brass, 8 mm dia, 2 mm pitch, 4-start, in stock; flange D22 / 4x M3 PCD16 not stated - check on receipt. LH nut is a machined part (drawing)"),
    "SPRING-MOTOR": ("Constant-force strip spring 21.9 N x 610 mm, 15.9 wide, 301 SS (two-drum motor, 0.22 N*m)", "McMaster-Carr", "9293K337", MC + "9293K337", "VERIFIED", "housing (printed) and output drum (6061) are custom parts with drawings; bench-test release torque vs M2006 back-drive"),
}


def main():
    rows = list(csv.DictReader(open(os.path.join(HERE, "BOM.csv"), encoding="utf-8")))
    out = []
    for r in rows:
        if r["type"] != "PURCHASED":
            continue
        it = r["item"]
        d = P.get(it, (r["description / process"], "", "", "", "MISSING", "no procurement entry"))
        out.append(dict(item=it, qty=r["qty"], description=r["description / process"], designation=d[0], vendor=d[1],
                        part_number=d[2], url=d[3], status=d[4], note=d[5]))
    out.append(dict(item="RAW_ROD_D10", qty="1", description="raw stock for Elbow_Shaft_D10x101 + Wrist_Shaft_D10x70",
                    designation="1055 steel D10 h6 x 500, precision ground, case hardened", vendor="McMaster-Carr",
                    part_number="6112K47", url=MC + "6112K47", status="VERIFIED", note="raw stock for 2 machined shafts (drawings)"))
    with open(os.path.join(HERE, "procurement.csv"), "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0]))
        w.writeheader()
        w.writerows(out)
    from collections import Counter
    c = Counter(o["status"] for o in out)
    print(len(out), "purchased lines", dict(c))
    for o in out:
        if o["status"] in ("MISSING",):
            print("  MISSING", o["item"])


main()
