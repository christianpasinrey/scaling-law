"""Wire-mesh basket cable tray (Legrand Cablofil CF105/300 style, black) for copper / power cabling.

Run headless:
  blender.exe -b C:\\laragon\\www\\scaling-law\\blender\\studio_template.blend --python hall_03_wire_basket.py [-- --norender]

Real references:
  - Cablofil CF105/300: 300 mm wide, 105 mm side height, 3 m lengths, 50 x 100 mm welded mesh, ~4.5-5 mm wire,
    T-welded safety top wire (Legrand Cablofil catalogue). Bends/tees are field-cut from straight mesh in reality;
    here they are clean procedural fittings sized to one 600 mm grid cell.
  - Hall art direction (research 02-datacenter.md): black or chrome wire baskets for copper, under the yellow fibre.
Pieces (origin = floor under piece centre / elbow corner / tee centre; basket bottom at BASKET_Z = 3.45 m):
  Basket_Straight_3m, Basket_Elbow90, Basket_Tee, Basket_Hanger
Flow: a black cable bundle 'FLOW_cables*' (flow_kind 'power') + SOCKET_power_in/out on every piece.
"""
import bpy, bmesh, math, mathutils, os, sys
from mathutils import Vector

exec(open(r'C:\laragon\www\scaling-law\blender\lib\hw.py', encoding='utf-8').read())
exec(open(r'C:\laragon\www\scaling-law\blender\scripts\hall_lib.py', encoding='utf-8').read())

FILE = 'hall_03_wire_basket'
BLEND = os.path.join(BASE, FILE + '.blend')
reset_scene()
M = mats()
COL = 'HALL_WireBasket'
stats = []

WB, HB = 0.300, 0.105
HWB = WB / 2
R = 0.0024                      # wire radius (4.8 mm wire)
Z = BASKET_Z
WIRE = circle(R, 6)
BUNDLE = ellipse(0.085, 0.022, 12, 0.0, 3 * R + 0.022)
E = CELL / 2


class Path:
    def __init__(self, pts, radius=0.0):
        self.F = frames(fillet([Vector(p) for p in pts], radius, 12))
        self.L = self.F[-1][6]

    def at(self, u):
        F = self.F
        for i in range(len(F) - 1):
            if F[i + 1][6] >= u:
                t = (u - F[i][6]) / max(1e-9, F[i + 1][6] - F[i][6])
                p = F[i][0].lerp(F[i + 1][0], t)
                s = F[i][2].lerp(F[i + 1][2], t).normalized()
                up = F[i][3].lerp(F[i + 1][3], t).normalized()
                return p, s, up
        return F[-1][0], F[-1][2], F[-1][3]

    def offset(self, a, b, u0=0.0, u1=None):
        u1 = self.L if u1 is None else u1
        out = []
        for (p, t, s, up, m, sc, u) in self.F:
            if u0 - 1e-6 <= u <= u1 + 1e-6:
                out.append(p + s * a + up * b)
        for uu in (u0, u1):
            if not any(abs(f[6] - uu) < 1e-6 for f in self.F):
                p, s, up = self.at(uu)
                q = p + s * a + up * b
                if uu == u0:
                    out.insert(0, q)
                else:
                    out.append(q)
        return [tuple(v) for v in out]


def u_wire(path, u, left=True, right=True):
    p, s, up = path.at(u)
    pts = []
    if left:
        pts.append(p + s * (-HWB) + up * HB)
    pts += [p + s * (-HWB) + up * R, p + s * HWB + up * R]
    if right:
        pts.append(p + s * HWB + up * HB)
    return {'pts': [tuple(v) for v in pts], 'profile': WIRE, 'radius': 0.010}


def long_wires(path, sides=(-1, 1), u_ranges=None, floor=True):
    items = []
    if floor:
        for k in range(7):
            a = -HWB + k * 0.05
            items.append({'pts': path.offset(a, 3 * R), 'profile': WIRE})
    for sgn in sides:
        rng = (u_ranges or {}).get(sgn, [(0.0, path.L)])
        for (u0, u1) in rng:
            for b in (0.052, HB):
                items.append({'pts': path.offset(sgn * (HWB + 2 * R), b, u0, u1), 'profile': WIRE})
    return items


def transverse(path, skip=lambda u: None):
    items = []
    n = int(round(path.L / 0.1))
    for k in range(n):
        u = (k + 0.5) * path.L / n
        mode = skip(u)
        if mode == 'drop':
            continue
        items.append(u_wire(path, u, left=True, right=(mode != 'open_right')))
    return items


def ports(root, col, a, b, da, db, extra=()):
    joint('JOINT_a', a, da, root, col)
    joint('JOINT_b', b, db, root, col)
    socket('SOCKET_power_in', a, da, root, col)
    socket('SOCKET_power_out' if not extra else 'SOCKET_power_out_0', b, db, root, col)


# ------------------------------------------------------------------ straight 3 m
root, col = piece('Basket_Straight_3m', 'WB_S3', COL)
P = Path([(-1.5, 0, Z), (1.5, 0, Z)])
multi_sweep('Mesh', long_wires(P) + transverse(P), M['black_pc'], col, root)
sweep('FLOW_cables', [(-1.5, 0, Z), (1.5, 0, Z)], BUNDLE, M['rubber'], col, root, smooth=True, flow='power', root=root)
ports(root, col, (-1.5, 0, Z), (1.5, 0, Z), (-1, 0, 0), (1, 0, 0))
root['length_m'] = 3.0
finish_piece(root, 'WB_S3', FILE, stats)

# ------------------------------------------------------------------ elbow (pure quarter arc, one cell)
root, col = piece('Basket_Elbow90', 'WB_E', COL)
pts = [(-E, 0, Z), (0, 0, Z), (0, E, Z)]
P = Path(pts, E)
multi_sweep('Mesh', long_wires(P) + transverse(P), M['black_pc'], col, root)
sweep('FLOW_cables', pts, BUNDLE, M['rubber'], col, root, radius=E, segs90=12, smooth=True, flow='power', root=root)
ports(root, col, (-E, 0, Z), (0, E, Z), (-1, 0, 0), (0, 1, 0))
finish_piece(root, 'WB_E', FILE, stats)

# ------------------------------------------------------------------ tee (main X, branch +Y)
root, col = piece('Basket_Tee', 'WB_T', COL)
RF = 0.06
Pm = Path([(-E, 0, Z), (E, 0, Z)])
Pb = Path([(0, 0, Z), (0, E, Z)])
# main: +Y side (sgn=+1 is +Y for +X travel) is open over the branch mouth
gap0, gap1 = E - HWB - RF, E + HWB + RF
items = long_wires(Pm, sides=(-1, 1), u_ranges={1: [(0.0, gap0), (gap1, Pm.L)]})
items += transverse(Pm, skip=lambda u: 'open_right' if gap0 - 0.02 < u < gap1 + 0.02 else None)
# branch: walls only beyond the main tray, floor wires from the main centreline
for sgn in (-1, 1):
    for b in (0.052, HB):
        items.append({'pts': Pb.offset(sgn * (HWB + 2 * R), b, HWB + RF, Pb.L), 'profile': WIRE})
        # fillet arc joining main +Y wall and branch wall
        c = (sgn * (HWB + RF + 2 * R), HWB + RF + 2 * R)
        a0, a1 = (270, 180) if sgn > 0 else (270, 360)
        arc = [(x, y, Z + b) for x, y in arc_pts(c, RF, a0, a1, 6)]
        items.append({'pts': arc, 'profile': WIRE})
for k in range(7):
    a = -HWB + k * 0.05
    items.append({'pts': Pb.offset(a, 3 * R, HWB, Pb.L), 'profile': WIRE})
for y in (HWB + 0.05, HWB + 0.12):
    items.append(u_wire(Pb, y))
multi_sweep('Mesh', items, M['black_pc'], col, root)
sweep('FLOW_cables_main', [(-E, 0, Z), (E, 0, Z)], BUNDLE, M['rubber'], col, root, smooth=True, flow='power', root=root)
sweep('FLOW_cables_branch', [(-E, 0.06, Z + 0.02), (-0.05, 0.06, Z + 0.02), (-0.05, E, Z + 0.02)], ellipse(0.04, 0.016, 10, 0, 3 * R + 0.016),
      M['rubber'], col, root, radius=0.12, smooth=True, flow='power', root=root)
ports(root, col, (-E, 0, Z), (E, 0, Z), (-1, 0, 0), (1, 0, 0), extra=True)
joint('JOINT_c', (0, E, Z), (0, 1, 0), root, col)
socket('SOCKET_power_out_1', (0, E, Z), (0, 1, 0), root, col)
finish_piece(root, 'WB_T', FILE, stats)

# ------------------------------------------------------------------ trapeze hanger
root, col = piece('Basket_Hanger', 'WB_H', COL)
strut('Strut', WB + 0.14, (0, 0, Z - 0.0205), 'y', root, col, M)
for s in (-1, 1):
    threaded_rod(f'Rod_{s:+d}', 0, s * (HWB + 0.04), Z - 0.045, CEIL_Z, root, col, M)
    H['cyl'](f'Nut_{s:+d}', 0.009, 0.01, (0, s * (HWB + 0.04), Z - 0.046), M['zinc'], col, verts=6, parent=root)
    H['cyl'](f'Anchor_{s:+d}', 0.03, 0.008, (0, s * (HWB + 0.04), CEIL_Z - 0.004), M['zinc'], col, verts=12, parent=root)
root['rod_top_z'] = CEIL_Z
finish_piece(root, 'WB_H', FILE, stats)

bpy.ops.wm.save_as_mainfile(filepath=BLEND)
export_all(FILE, stats)

if DO_RENDER:
    PP = {r.name: r for r, t in PIECES}
    for r, t in PIECES:
        for o in [r] + list(r.children_recursive):
            o.hide_render = True
    dup(PP['Basket_Straight_3m'], (-1.8, 0, 0))
    dup(PP['Basket_Tee'], (0.0, 0, 0))
    dup(PP['Basket_Elbow90'], (0.6, 0, 0))
    dup(PP['Basket_Hanger'], (-1.2, 0, 0))
    dup(PP['Basket_Hanger'], (-2.9, 0, 0))
    context_racks([-2.7 + i * 0.6 for i in range(5)], -0.535, facing=-1)
    studio(6.0, (0, 0, 2.8))
    add_sun(1.0)
    render_views(FILE, {
        'run':  ((-4.2, -3.6, 4.4), (-0.6, 0.0, 3.4), 30),
        'tee':  ((0.9, -1.3, 4.3), (0.2, 0.15, 3.45), 30),
        'below': ((-1.0, -1.1, 2.7), (-1.6, 0.0, 3.45), 30),
    })
