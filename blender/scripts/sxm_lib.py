"""Extra helpers for SXM module modelling (V100 SXM2, A100 SXM4).

Load after hw.py:
    exec(open(r'C:\\laragon\\www\\scaling-law\\blender\\lib\\hw.py', encoding='utf-8').read())
    exec(open(r'C:\\laragon\\www\\scaling-law\\blender\\scripts\\sxm_lib.py', encoding='utf-8').read())
Conventions (SXM modules lie flat):
  - metres; module PCB top surface = z 0; heatsink grows toward +Z
  - X = module long side, Y = short side, origin at module centre
"""
import bpy, bmesh, math, mathutils, random

H = bpy.app.driver_namespace['HW']
mm = 0.001


def mesh_from_quads(name, quads, material, col, parent):
    """quads: list of 4- or 3-tuples of (x,y,z) points (already in metres)."""
    bm = bmesh.new()
    for q in quads:
        bm.faces.new([bm.verts.new(p) for p in q])
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-7)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me)
    me.materials.append(material)
    col.objects.link(o)
    if parent:
        o.parent = parent
    return o


def boxes(name, specs, material, col, parent):
    """specs: iterable of (centre_mm(x,y,z), size_mm(sx,sy,sz)) -> one merged mesh (metres)."""
    lst = [(tuple(c * mm for c in ce), tuple(s * mm for s in si)) for ce, si in specs]
    return H['slat_array'](name, lambda: iter(lst), material, col, parent)


def lens_pts(cx, cy, a, b, n, sharp=0.35):
    """Pointed-ellipse (eye) outline, n points, in mm."""
    pts = []
    for i in range(n):
        t = 2 * math.pi * i / n
        s = math.sin(t)
        pts.append((cx + a * math.cos(t), cy + b * s * (abs(s) ** sharp)))
    return pts


def nv_logo(name, cx, cy, z, s, dark, light, col, parent, rotz=0.0):
    """Approximate NVIDIA eye mark (s = square side, mm). Left eye outline dark on the
    surface, black square on the right with the eye continuing as a light cut-out."""
    sq_l = cx - 0.5 * s + 0.18 * s          # square left edge
    sq_r = sq_l + s
    eye_cx = sq_l + 0.12 * s                # eye centre slightly inside the square
    rings = [((eye_cx, cy, 0.78 * s, 0.40 * s), (eye_cx + 0.04 * s, cy, 0.62 * s, 0.27 * s)),
             ((eye_cx + 0.05 * s, cy, 0.42 * s, 0.20 * s), (eye_cx + 0.08 * s, cy, 0.28 * s, 0.10 * s))]
    n = 48
    dq, lq = [], []
    c, sn = math.cos(rotz), math.sin(rotz)

    def P(x, y, zz):
        x0, y0 = x - cx, y - cy
        return ((cx + x0 * c - y0 * sn) * mm, (cy + x0 * sn + y0 * c) * mm, zz * mm)
    for (o, i) in rings:
        po = lens_pts(*o, n); pi = lens_pts(*i, n)
        for k in range(n):
            j = (k + 1) % n
            xm = (po[k][0] + po[j][0] + pi[k][0] + pi[j][0]) / 4
            inside = xm > sq_l and xm < sq_r
            zz = z + (0.25 if inside else 0.12)
            q = (P(*po[k], zz), P(*po[j], zz), P(*pi[j], zz), P(*pi[k], zz))
            (lq if inside else dq).append(q)
    zq = z + 0.12
    dq.append((P(sq_l, cy - s / 2, zq), P(sq_r, cy - s / 2, zq), P(sq_r, cy + s / 2, zq), P(sq_l, cy + s / 2, zq)))
    a = mesh_from_quads(name + '_Dark', dq, dark, col, parent)
    b = mesh_from_quads(name + '_Cut', lq, light, col, parent)
    return a, b


def label_text(name, body, size_mm, loc_mm, material, col, parent, rotz=0.0, font=r'C:\Windows\Fonts\ariblk.ttf', extrude_mm=0.1, scale=(1, 1, 1)):
    t = H['text_mesh'](name, body, font, size_mm * mm, material, col, parent,
                       tuple(v * mm for v in loc_mm), (0, 0, rotz), extrude=extrude_mm * mm, scale=scale)
    return t


def scatter_smd(name, rects, count, material, col, parent, seed=1, avoid=(), sizes=((1.0, 0.5), (1.6, 0.8), (2.0, 1.25), (3.2, 1.6)), h=(0.4, 0.9), z0=0.0):
    """Random small SMD parts inside rects [(x0,x1,y0,y1) mm], avoiding rects in `avoid`."""
    rnd = random.Random(seed)
    specs = []; tries = 0
    while len(specs) < count and tries < count * 40:
        tries += 1
        x0, x1, y0, y1 = rnd.choice(rects)
        w, d = rnd.choice(sizes)
        if rnd.random() < 0.5:
            w, d = d, w
        x = rnd.uniform(x0 + w / 2, x1 - w / 2); y = rnd.uniform(y0 + d / 2, y1 - d / 2)
        if any(ax0 - w / 2 < x < ax1 + w / 2 and ay0 - d / 2 < y < ay1 + d / 2 for ax0, ax1, ay0, ay1 in avoid):
            continue
        if any(abs(x - sx) < (w + sw) / 2 + 0.25 and abs(y - sy) < (d + sd) / 2 + 0.25 for (sx, sy, _), (sw, sd, _) in specs):
            continue
        hh = rnd.uniform(*h)
        specs.append(((x, y, z0 + (hh / 2 if z0 >= 0 else -hh / 2)), (w, d, hh)))
    return boxes(name, specs, material, col, parent)


def rings_mesh(name, centres_mm, r_out, r_in, z_mm, material, col, parent, verts=20):
    """Flat annuli (plated mounting-hole rings) at given XY centres, facing +Z (or -Z if z<0)."""
    quads = []
    for cx, cy in centres_mm:
        for k in range(verts):
            a0 = 2 * math.pi * k / verts; a1 = 2 * math.pi * (k + 1) / verts
            p = lambda r, a: ((cx + r * math.cos(a)) * mm, (cy + r * math.sin(a)) * mm, z_mm * mm)
            q = (p(r_out, a0), p(r_out, a1), p(r_in, a1), p(r_in, a0))
            quads.append(q if z_mm >= 0 else tuple(reversed(q)))
    return mesh_from_quads(name, quads, material, col, parent)


def discs(name, centres_mm, r, z_mm, material, col, parent, verts=16):
    tris = []
    for cx, cy in centres_mm:
        for k in range(verts):
            a0 = 2 * math.pi * k / verts; a1 = 2 * math.pi * (k + 1) / verts
            t = ((cx * mm, cy * mm, z_mm * mm), ((cx + r * math.cos(a0)) * mm, (cy + r * math.sin(a0)) * mm, z_mm * mm),
                 ((cx + r * math.cos(a1)) * mm, (cy + r * math.sin(a1)) * mm, z_mm * mm))
            tris.append(t if z_mm >= 0 else tuple(reversed(t)))
    return mesh_from_quads(name, tris, material, col, parent)


def cyls(name, specs, material, col, parent, verts=16):
    """specs: [(x,y,z_centre,r,depth) mm] -> one merged mesh of Z-aligned cylinders."""
    bm = bmesh.new()
    for x, y, z, r, d in specs:
        bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=verts, radius1=r * mm, radius2=r * mm, depth=d * mm,
                              matrix=mathutils.Matrix.Translation((x * mm, y * mm, z * mm)))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me); me.materials.append(material); col.objects.link(o)
    if parent:
        o.parent = parent
    return o


def sxm_sockets(root, col, power_in, mezz, extra=()):
    s = bpy.data.objects.new('SOCKET_power_in', None); s.empty_display_type = 'SINGLE_ARROW'; s.empty_display_size = 0.02
    s.location = power_in; s.rotation_euler = (math.pi, 0, 0); col.objects.link(s); s.parent = root
    m = bpy.data.objects.new('SOCKET_mezzanine', None); m.empty_display_type = 'ARROWS'; m.empty_display_size = 0.015
    m.location = mezz; col.objects.link(m); m.parent = root
    for nm, loc in extra:
        e = bpy.data.objects.new(nm, None); e.empty_display_type = 'PLAIN_AXES'; e.empty_display_size = 0.01
        e.location = loc; col.objects.link(e); e.parent = root


def look_at(cam, eye, target, roll_up=(0, 0, 1)):
    cam.location = eye
    d = mathutils.Vector(target) - mathutils.Vector(eye)
    cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()


def render_views(prefix, views, out_dir=r'C:\laragon\www\scaling-law\blender\renders'):
    """views: {name: (eye, target, lens, hide_floor, under_light)}"""
    sc = bpy.context.scene
    sc.render.resolution_x = 1280; sc.render.resolution_y = 720; sc.render.resolution_percentage = 100
    cam = bpy.data.objects['Camera']; sc.camera = cam
    floor = bpy.data.objects.get('Floor')
    for vname, (eye, target, lens, hide_floor, under) in views.items():
        look_at(cam, eye, target)
        cam.data.lens = lens
        if floor:
            floor.hide_render = hide_floor
        tmp = None
        if under:
            ld = bpy.data.lights.new('UnderLight', 'AREA'); ld.energy = 4; ld.size = 0.5
            tmp = bpy.data.objects.new('UnderLight', ld); sc.collection.objects.link(tmp)
            look_at(tmp, (0.1, -0.15, -0.35), (0, 0, 0))
        sc.render.filepath = out_dir + '\\' + prefix + '_' + vname + '.png'
        bpy.ops.render.render(write_still=True)
        if tmp:
            bpy.data.objects.remove(tmp, do_unlink=True)
    if floor:
        floor.hide_render = False
