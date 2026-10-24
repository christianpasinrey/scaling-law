"""Shared helpers for hardware modelling in Blender.

Load inside Blender with:
    exec(open(r'C:\\laragon\\www\\scaling-law\\blender\\lib\\hw.py', encoding='utf-8').read())
Everything is also published in bpy.app.driver_namespace['HW'].

Conventions (all cards):
  - units: metres, 1 BU = 1 m
  - X: card length, bracket at x≈0, card grows toward +X
  - Z: height, PCIe finger bottom ≈ -0.0125, shroud top ≈ 0.1085
  - Y: thickness, PCB at y≈0, cooler/front toward -Y, backplate toward +Y
  - empties named SOCKET_* mark gameplay attach points (power_in, pcie)
"""
import bpy, bmesh, math, mathutils


def mat(name, base, metal=0.0, rough=0.5, emit=None, emit_str=0.0, alpha=1.0, aniso=0.0, spec=None):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    b = next(n for n in m.node_tree.nodes if n.type == 'BSDF_PRINCIPLED')
    b.inputs['Base Color'].default_value = (*base, 1)
    b.inputs['Metallic'].default_value = metal
    b.inputs['Roughness'].default_value = rough
    if emit:
        b.inputs['Emission Color'].default_value = (*emit, 1)
        b.inputs['Emission Strength'].default_value = emit_str
    if alpha < 1.0:
        b.inputs['Alpha'].default_value = alpha
        try:
            m.surface_render_method = 'BLENDED'
        except Exception:
            pass
    if aniso:
        b.inputs['Anisotropic'].default_value = aniso
    if spec is not None:
        b.inputs['Specular IOR Level'].default_value = spec
    m.diffuse_color = (*base, alpha)
    return m


def base_materials():
    return {
        'alu':       mat('HW_Aluminium', (0.62, 0.63, 0.65), 1.0, 0.32),
        'black_dc':  mat('HW_BlackDiecast', (0.008, 0.008, 0.009), 0.25, 0.30, spec=0.35),
        'black_gl':  mat('HW_BlackGloss', (0.006, 0.006, 0.007), 0.3, 0.18),
        'black_mt':  mat('HW_BlackMatte', (0.006, 0.006, 0.007), 0.0, 0.7, spec=0.15),
        'black_st':  mat('HW_BlackSteel', (0.02, 0.02, 0.022), 0.8, 0.4),
        'plastic':   mat('HW_BlackPlastic', (0.006, 0.006, 0.007), 0.0, 0.45, spec=0.35),
        'pcb':       mat('HW_PCB_Black', (0.03, 0.035, 0.03), 0.0, 0.45),
        'gold':      mat('HW_Gold', (1.0, 0.78, 0.34), 1.0, 0.22),
        'steel':     mat('HW_NickelSteel', (0.7, 0.7, 0.72), 1.0, 0.28),
        'port':      mat('HW_PortInner', (0.01, 0.01, 0.01), 0.0, 0.8),
        'fin_dark':  mat('HW_FinDark', (0.015, 0.016, 0.018), 0.6, 0.45, spec=0.35),
    }


def coll(name):
    c = bpy.data.collections.get(name)
    if not c:
        c = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(c)
    return c


def _link(o, col, parent):
    for c in list(o.users_collection):
        c.objects.unlink(o)
    col.objects.link(o)
    if parent:
        o.parent = parent
    return o


def box(name, size, loc, material, col, bevel=0.0, segs=2, parent=None):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.active_object
    o.name = name
    o.scale = size
    bpy.ops.object.transform_apply(scale=True)
    o.data.materials.append(material)
    if bevel > 0:
        b = o.modifiers.new('Bevel', 'BEVEL')
        b.width = bevel; b.segments = segs; b.limit_method = 'ANGLE'
    return _link(o, col, parent)


def cyl(name, r, depth, loc, material, col, verts=48, rot=(0, 0, 0), bevel=0.0, parent=None):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=r, depth=depth, location=loc, rotation=rot)
    o = bpy.context.active_object
    o.name = name
    o.data.materials.append(material)
    if bevel > 0:
        b = o.modifiers.new('Bevel', 'BEVEL')
        b.width = bevel; b.segments = 2; b.limit_method = 'ANGLE'
    return _link(o, col, parent)


def _new_obj(name, bm, material, col, parent):
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me); bm.free()
    o = bpy.data.objects.new(name, me)
    me.materials.append(material)
    col.objects.link(o)
    if parent:
        o.parent = parent
    return o


def prism(name, pts, plane, d0, depth, material, col, parent=None, bevel=0.0):
    """Extrude a (possibly concave) 2D polygon.
    plane 'xz': pts are (x,z), extruded along Y from d0 by depth (signed).
    plane 'xy': pts are (x,y), extruded along Z.
    plane 'yz': pts are (y,z), extruded along X."""
    def P(a, b, d):
        return {'xz': (a, d, b), 'xy': (a, b, d), 'yz': (d, a, b)}[plane]
    bm = bmesh.new()
    v0 = [bm.verts.new(P(a, b, d0)) for a, b in pts]
    v1 = [bm.verts.new(P(a, b, d0 + depth)) for a, b in pts]
    f0 = bm.faces.new(v0); f1 = bm.faces.new(list(reversed(v1)))
    n = len(pts)
    for k in range(n):
        j = (k + 1) % n
        bm.faces.new((v0[k], v0[j], v1[j], v1[k]))
    if n > 4:
        bmesh.ops.triangulate(bm, faces=[f0, f1])
    o = _new_obj(name, bm, material, col, parent)
    if bevel:
        b = o.modifiers.new('Bevel', 'BEVEL'); b.width = bevel; b.segments = 2; b.limit_method = 'ANGLE'
    return o


def ring(name, outer, inner, plane, d0, depth, material, col, parent=None):
    """Frame between two loops of equal vertex count (same plane conventions as prism)."""
    def P(a, b, d):
        return {'xz': (a, d, b), 'xy': (a, b, d), 'yz': (d, a, b)}[plane]
    bm = bmesh.new(); n = len(outer)
    L = lambda pts, d: [bm.verts.new(P(a, b, d)) for a, b in pts]
    o0, i0, o1, i1 = L(outer, d0), L(inner, d0), L(outer, d0 + depth), L(inner, d0 + depth)
    for k in range(n):
        j = (k + 1) % n
        bm.faces.new((o1[k], o1[j], i1[j], i1[k]))
        bm.faces.new((o0[k], o0[j], o1[j], o1[k]))
        bm.faces.new((i0[k], i1[k], i1[j], i0[j]))
    return _new_obj(name, bm, material, col, parent)


def loft(name, sections, material, col, parent=None):
    """sections: list of (x, [(y,z),...]) with equal point counts; caps both ends."""
    bm = bmesh.new(); rings = []
    for x, sec in sections:
        rings.append([bm.verts.new((x, y, z)) for y, z in sec])
    n = len(sections[0][1])
    for a, b in zip(rings[:-1], rings[1:]):
        for k in range(n):
            j = (k + 1) % n
            bm.faces.new((a[k], a[j], b[j], b[k]))
    bm.faces.new(list(reversed(rings[0]))); bm.faces.new(rings[-1])
    return _new_obj(name, bm, material, col, parent)


def slat_array(name, count_fn, material, col, parent=None):
    """count_fn yields (centre(x,y,z), size(sx,sy,sz)) boxes merged into one mesh."""
    bm = bmesh.new()
    for c, s in count_fn():
        bmesh.ops.create_cube(bm, size=1, matrix=mathutils.Matrix.Translation(c) @ mathutils.Matrix.Diagonal((*s, 1)))
    return _new_obj(name, bm, material, col, parent)


def text_mesh(name, body, font, size, material, col, parent, loc, rot, extrude=0.0002, shear=0.0, scale=(1, 1, 1)):
    bpy.ops.object.text_add(location=(0, 0, 0))
    t = bpy.context.active_object
    t.name = name
    t.data.body = body; t.data.align_x = 'CENTER'; t.data.align_y = 'CENTER'
    t.data.font = bpy.data.fonts.load(font, check_existing=True)
    t.data.size = size; t.data.extrude = extrude; t.data.shear = shear
    for c in list(t.users_collection):
        c.objects.unlink(t)
    col.objects.link(t)
    t.data.materials.append(material)
    bpy.context.view_layer.objects.active = t
    bpy.ops.object.select_all(action='DESELECT'); t.select_set(True)
    bpy.ops.object.convert(target='MESH')
    t.parent = parent; t.matrix_parent_inverse.identity()
    t.location = loc; t.rotation_euler = rot; t.scale = scale
    return t


def triangle_vent_bracket(name, material, col, parent, ports=(), bx=-0.0030, t=0.0009, s=0.0072, web=0.00085):
    """PCIe dual-slot bracket in the YZ plane with a triangular vent mesh.
    ports: list of (y, z, half_w, half_h) rectangles kept solid."""
    br = box(name, (t, 0.0400, 0.1180), (bx, -0.0170, 0.0530), material, col, parent=parent)
    h = s * 0.866

    def blocked(y0, y1, z0, z1):
        for (py, pz, hw, hh) in ports:
            if y1 > py - hw - 0.0012 and y0 < py + hw + 0.0012 and z1 > pz - hh - 0.0012 and z0 < pz + hh + 0.0012:
                return True
        return False
    bm = bmesh.new()

    def tri(yc, zc, up):
        if up:
            pts = [(yc - s / 2, zc - h / 3), (yc + s / 2, zc - h / 3), (yc, zc + 2 * h / 3)]
        else:
            pts = [(yc - s / 2, zc + h / 3), (yc + s / 2, zc + h / 3), (yc, zc - 2 * h / 3)]
        inr = h / 3; f = (inr - web / 2) / inr
        pts = [(yc + (y - yc) * f, zc + (z - zc) * f) for y, z in pts]
        ys = [p[0] for p in pts]; zs = [p[1] for p in pts]
        if min(ys) < -0.0360 or max(ys) > -0.0012 or min(zs) < -0.0035 or max(zs) > 0.1085:
            return
        if blocked(min(ys), max(ys), min(zs), max(zs)):
            return
        v0 = [bm.verts.new((bx - 0.003, y, z)) for y, z in pts]
        v1 = [bm.verts.new((bx + 0.003, y, z)) for y, z in pts]
        bm.faces.new(v0); bm.faces.new(list(reversed(v1)))
        for i in range(3):
            j = (i + 1) % 3
            bm.faces.new((v0[i], v0[j], v1[j], v1[i]))
    row = 0; zb = -0.0035
    while zb < 0.109:
        i = 0; yc = -0.0360
        while yc < 0.0:
            up = (i + row) % 2 == 0
            tri(yc, zb + (h / 3 if up else 2 * h / 3), up)
            yc += s / 2; i += 1
        zb += h; row += 1
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name + '_Cutter'); bm.to_mesh(me); bm.free()
    cut = bpy.data.objects.new(name + '_Cutter', me); col.objects.link(cut)
    mod = br.modifiers.new('Vent', 'BOOLEAN'); mod.object = cut; mod.operation = 'DIFFERENCE'; mod.solver = 'EXACT'
    bpy.context.view_layer.objects.active = br
    bpy.ops.object.select_all(action='DESELECT'); br.select_set(True)
    bpy.ops.object.modifier_apply(modifier='Vent')
    bpy.data.objects.remove(cut, do_unlink=True)
    box(name + '_Tab', (0.0110, 0.0190, t), (bx - 0.0055 + t / 2, -0.0080, 0.1120), material, col, parent=parent)
    box(name + '_Tongue', (t, 0.0080, 0.0120), (bx, -0.0060, -0.0100), material, col, parent=parent)
    return br


def pcie_edge(root, col, M, x0=0.026):
    """PCB edge fingers + gold pads (x16) under the PCB (PCB plane y∈[0,0.0016])."""
    T = 0.0016
    box('PCIe_Edge', (0.0820, T, 0.0085), (x0 + 0.041 + 0.0115, T / 2, -0.0040), M['pcb'], col, parent=root)
    box('PCIe_Edge_Key', (0.0110, T, 0.0085), (x0 + 0.0055, T / 2, -0.0040), M['pcb'], col, parent=root)

    def pads():
        for start, n in ((x0 + 0.0005, 11), (x0 + 0.0125, 81)):
            for i in range(n):
                for y in (-0.00002, T + 0.00002):
                    yield (start + i * 0.001 + 0.0005, y, -0.0050), (0.0007, 0.00004, 0.0065)
    return slat_array('PCIe_Gold', pads, M['gold'], col, root)


def sockets(root, col, power_in, pcie=(0.067, 0.0008, -0.0085)):
    s = bpy.data.objects.new('SOCKET_power_in', None); s.empty_display_type = 'SINGLE_ARROW'; s.empty_display_size = 0.02
    s.location = power_in; col.objects.link(s); s.parent = root
    p = bpy.data.objects.new('SOCKET_pcie', None); p.empty_display_type = 'ARROWS'; p.empty_display_size = 0.015
    p.location = pcie; col.objects.link(p); p.parent = root


def export_glb(root_name, path):
    root = bpy.data.objects[root_name]
    bpy.ops.object.select_all(action='DESELECT')
    objs = [root] + list(root.children_recursive)
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = root
    dg = bpy.context.evaluated_depsgraph_get(); tris = 0
    for o in objs:
        if o.type == 'MESH':
            e = o.evaluated_get(dg); m = e.to_mesh(); m.calc_loop_triangles(); tris += len(m.loop_triangles); e.to_mesh_clear()
    # export_extras keeps custom props (flow_u_start/end, slot_type, led_role…) as glTF extras for the game
    bpy.ops.export_scene.gltf(filepath=path, use_selection=True, export_apply=True, export_extras=True)
    return tris


def new_card_scene(root_name):
    """Empty the scene except the Studio collection and create a root empty + collection."""
    studio = coll('Studio')
    for o in list(bpy.data.objects):
        if o.type in ('CAMERA', 'LIGHT'):
            if studio not in o.users_collection:
                studio.objects.link(o)
            continue
        if not any(c.name == 'Studio' for c in o.users_collection):
            bpy.data.objects.remove(o, do_unlink=True)
    for c in list(bpy.data.collections):
        if c.name != 'Studio' and not c.objects:
            bpy.data.collections.remove(c)
    col = coll(root_name)
    root = bpy.data.objects.new(root_name, None)
    root.empty_display_type = 'PLAIN_AXES'; root.empty_display_size = 0.05
    col.objects.link(root)
    return root, col


def apply_all(obj):
    """Apply every modifier on obj with an explicit context (plain modifier_apply can silently skip)."""
    with bpy.context.temp_override(object=obj, active_object=obj, selected_objects=[obj], selected_editable_objects=[obj]):
        for m in list(obj.modifiers):
            bpy.ops.object.modifier_apply(modifier=m.name)


def cut(obj, cutter, remove_cutter=True):
    """Boolean DIFFERENCE obj - cutter, applied immediately."""
    apply_all(obj)
    mod = obj.modifiers.new('Cut', 'BOOLEAN')
    mod.operation = 'DIFFERENCE'; mod.object = cutter
    # EXACT can return an empty mesh on bevelled bodies in Blender 5.2: probe each solver before applying
    for solver in ('EXACT', 'MANIFOLD', 'FLOAT'):
        mod.solver = solver
        dg = bpy.context.evaluated_depsgraph_get()
        if len(obj.evaluated_get(dg).data.polygons) > 0:
            break
    else:
        raise RuntimeError(f'cut({obj.name}, {cutter.name}) empties the mesh with every solver')
    apply_all(obj)
    if remove_cutter:
        bpy.data.objects.remove(cutter, do_unlink=True)
    return obj


HW = dict(apply_all=apply_all, cut=cut, mat=mat, base_materials=base_materials, coll=coll, box=box, cyl=cyl, prism=prism, ring=ring, loft=loft,
          slat_array=slat_array, text_mesh=text_mesh, triangle_vent_bracket=triangle_vent_bracket,
          pcie_edge=pcie_edge, sockets=sockets, export_glb=export_glb, new_card_scene=new_card_scene)
bpy.app.driver_namespace['HW'] = HW
