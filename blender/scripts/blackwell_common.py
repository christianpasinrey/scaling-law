"""Extra helpers shared by gpu_14a_b200_sxm.py and gpu_14b_gb200_superchip.py.

Loaded with exec() after hw.py; expects `H` (the hw.py helper dict) in globals.
Does not modify hw.py.
"""
import bpy, bmesh, math, mathutils, random
from mathutils import Vector

FONT = r'C:\Windows\Fonts\arialbd.ttf'
FONT_LOGO = r'C:\Windows\Fonts\bahnschrift.ttf'


def extra_materials():
    m = H['mat']
    return {
        'copper':    m('BW_Copper', (0.93, 0.50, 0.32), 1.0, 0.28),
        'copper_dk': m('BW_CopperDark', (0.62, 0.30, 0.17), 1.0, 0.38),
        'nickel':    m('BW_NickelLid', (0.80, 0.80, 0.79), 1.0, 0.34),
        'substrate': m('BW_SubstrateTeal', (0.002, 0.032, 0.033), 0.0, 0.5, spec=0.25),
        'die':       m('BW_DieSilicon', (0.012, 0.012, 0.016), 0.6, 0.12, spec=0.8),
        'hbm':       m('BW_HBM', (0.012, 0.012, 0.014), 0.2, 0.22, spec=0.5),
        'mold':      m('BW_Mold', (0.006, 0.006, 0.007), 0.0, 0.5, spec=0.3),
        'choke':     m('BW_Choke', (0.10, 0.10, 0.105), 0.2, 0.55),
        'print':     m('BW_WhitePrint', (0.85, 0.85, 0.85), 0.0, 0.6),
        'anod':      m('BW_BlackAnodised', (0.008, 0.008, 0.009), 0.0, 0.62, spec=0.18),
        'pcb_mod':   m('BW_PCB_Module', (0.018, 0.03, 0.026), 0.0, 0.45),
        'hose':      m('BW_HoseEPDM', (0.015, 0.015, 0.016), 0.0, 0.62, spec=0.25),
        'qd_blue':   m('BW_QD_Blue', (0.02, 0.18, 0.75), 0.3, 0.35),
        'qd_red':    m('BW_QD_Red', (0.75, 0.04, 0.03), 0.3, 0.35),
        'cable_red': m('BW_CableRed', (0.7, 0.03, 0.02), 0.0, 0.5),
        'tin':       m('BW_Tin', (0.72, 0.72, 0.70), 1.0, 0.30),
        'smd':       m('BW_SMD', (0.06, 0.055, 0.05), 0.1, 0.5),
        'smd_cap':   m('BW_SMD_Cap', (0.28, 0.22, 0.14), 0.0, 0.5),
        'pcb_board': m('BW_PCB_Board', (0.010, 0.012, 0.011), 0.0, 0.62, spec=0.3),
        'green_ring': m('BW_TorqueGreen', (0.15, 0.85, 0.12), 0.0, 0.45),
    }


def look_at(cam, loc, target, lens=50.0, ortho=None):
    cam.location = loc
    d = Vector(target) - Vector(loc)
    cam.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    if ortho:
        cam.data.type = 'ORTHO'; cam.data.ortho_scale = ortho
    else:
        cam.data.type = 'PERSP'; cam.data.lens = lens
    cam.data.clip_start = 0.005


def setup_render(floor_z=-0.03):
    s = bpy.context.scene
    s.render.resolution_x = 1280; s.render.resolution_y = 720; s.render.resolution_percentage = 100
    s.camera = bpy.data.objects['Camera']
    fl = bpy.data.objects.get('Floor')
    if fl:
        fl.location = (0, 0, floor_z)


def render(path):
    bpy.context.scene.render.filepath = path
    bpy.ops.render.render(write_still=True)


def tube(name, ctrl, radius, material, col, parent, u0=0.0, res=10, ring=12):
    """Bezier curve through ctrl points (AUTO handles), converted to mesh.
    UVs: u = metres along the tube starting at u0 (continuous along the flow), v = 0..1 around.
    Returns (object, end_u)."""
    cu = bpy.data.curves.new(name, 'CURVE'); cu.dimensions = '3D'
    cu.resolution_u = res; cu.bevel_depth = radius; cu.bevel_resolution = max(1, (ring - 4) // 2)
    cu.use_fill_caps = False
    sp = cu.splines.new('BEZIER'); sp.bezier_points.add(len(ctrl) - 1)
    for bp, p in zip(sp.bezier_points, ctrl):
        bp.co = p; bp.handle_left_type = 'AUTO'; bp.handle_right_type = 'AUTO'
    ob = bpy.data.objects.new(name, cu); col.objects.link(ob)
    # sample the same curve for UV projection
    pts = []
    bps = sp.bezier_points
    for a, b in zip(bps[:-1], bps[1:]):
        seg = mathutils.geometry.interpolate_bezier(a.co, a.handle_right, b.handle_left, b.co, 64)
        pts.extend(seg if not pts else seg[1:])
    with bpy.context.temp_override(object=ob, active_object=ob, selected_objects=[ob], selected_editable_objects=[ob]):
        bpy.ops.object.convert(target='MESH')
    ob = bpy.data.objects[name]
    me = ob.data
    me.materials.clear(); me.materials.append(material)
    cum = [0.0]
    for p, q in zip(pts[:-1], pts[1:]):
        cum.append(cum[-1] + (q - p).length)
    L = cum[-1]

    def proj(v):
        best = (1e9, 0.0, 0)
        for i in range(len(pts) - 1):
            p, q = pts[i], pts[i + 1]; d = q - p; ll = d.length_squared
            t = 0.0 if ll == 0 else max(0.0, min(1.0, (v - p).dot(d) / ll))
            c = p + d * t; dist = (v - c).length_squared
            if dist < best[0]:
                best = (dist, cum[i] + t * math.sqrt(ll), i)
        i = best[2]; tang = (pts[i + 1] - pts[i]).normalized()
        c = pts[i] + tang * (best[1] - cum[i])
        ref = Vector((0, 0, 1)) if abs(tang.z) < 0.9 else Vector((1, 0, 0))
        n1 = (ref - tang * ref.dot(tang)).normalized(); n2 = tang.cross(n1)
        r = v - c
        ang = (math.atan2(r.dot(n2), r.dot(n1)) / (2 * math.pi)) % 1.0
        return best[1], ang
    vu = [proj(v.co) for v in me.vertices]
    uvl = me.uv_layers.get('UVMap') or me.uv_layers.new(name='UVMap')
    for poly in me.polygons:
        vs = [vu[me.loops[li].vertex_index][1] for li in poly.loop_indices]
        wrap = max(vs) - min(vs) > 0.5
        for li in poly.loop_indices:
            s, a = vu[me.loops[li].vertex_index]
            if wrap and a < 0.5:
                a += 1.0
            uvl.data[li].uv = (u0 + s, a)
    for p in me.polygons:
        p.use_smooth = True
    ob.parent = parent
    ob['flow_u_start'] = u0; ob['flow_u_end'] = u0 + L
    return ob, u0 + L


def empty(name, loc, col, parent, kind='SINGLE_ARROW', size=0.02, rot=(0, 0, 0)):
    e = bpy.data.objects.new(name, None); e.empty_display_type = kind; e.empty_display_size = size
    e.location = loc; e.rotation_euler = rot; col.objects.link(e); e.parent = parent
    return e


def frame_rect(name, cx, cy, w, h, t, z0, depth, material, col, parent):
    """Rectangular frame (outer w x h, wall t) in XY extruded along Z."""
    o = [(cx - w / 2, cy - h / 2), (cx + w / 2, cy - h / 2), (cx + w / 2, cy + h / 2), (cx - w / 2, cy + h / 2)]
    i = [(cx - w / 2 + t, cy - h / 2 + t), (cx + w / 2 - t, cy - h / 2 + t), (cx + w / 2 - t, cy + h / 2 - t), (cx - w / 2 + t, cy + h / 2 - t)]
    return H['ring'](name, o, i, 'xy', z0, depth, material, col, parent)


def corner_marks(cx, cy, w, h, z, arm=0.004, wid=0.0006, th=0.00006):
    """L-shaped printed corner marks just outside a rectangle (as on the HGX bolster plates)."""
    for sx in (-1, 1):
        for sy in (-1, 1):
            x = cx + sx * w / 2; y = cy + sy * h / 2
            yield (x - sx * arm / 2 + sx * wid / 2, y, z), (arm, wid, th)
            yield (x, y - sy * arm / 2 + sy * wid / 2, z), (wid, arm, th)


def tri_count(objs):
    dg = bpy.context.evaluated_depsgraph_get(); n = 0
    for o in objs:
        if o.type == 'MESH':
            e = o.evaluated_get(dg); m = e.to_mesh(); m.calc_loop_triangles(); n += len(m.loop_triangles); e.to_mesh_clear()
    return n
