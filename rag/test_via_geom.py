import math
from via_geom import find_via_position
VIA_R, CLR, BOUNDS = 0.225, 0.09, (20.0, 20.0, 45.0, 45.0)

def lattice(cx, cy, n, pitch, r, target_ij, target_net="GND", other="OTHER"):
    obs, tgt = [], None
    for i in range(-n, n+1):
        for j in range(-n, n+1):
            x, y = cx + i*pitch, cy + j*pitch
            if (i, j) == target_ij:
                tgt = (x, y)
            else:
                obs.append((x, y, r, other))
    return tgt, obs

print("case 1  isolated 0805 GND pad (r=0.6), no neighbours")
print("        ->", find_via_position((30.0,30.0), 0.6, "GND", [], VIA_R, CLR, BOUNDS))

print("case 2  INTERIOR ball of a 0.4mm-pitch array (r=0.1125)")
t, obs = lattice(32.0, 32.0, 2, 0.4, 0.1125, (0,0))
p = find_via_position(t, 0.1125, "GND", obs, VIA_R, CLR, BOUNDS)
print("        ->", p, "" if p is None else "dist=%.3f" % math.hypot(p[0]-t[0], p[1]-t[1]))

print("case 3  EDGE ball (left column) of the same array")
t3, obs3 = lattice(32.0, 32.0, 2, 0.4, 0.1125, (-2,0))
p3 = find_via_position(t3, 0.1125, "GND", obs3, VIA_R, CLR, BOUNDS)
print("        ->", p3, "" if p3 is None else "dist=%.3f" % math.hypot(p3[0]-t3[0], p3[1]-t3[1]))

print("case 4  CORNER ball")
t4, obs4 = lattice(32.0, 32.0, 2, 0.4, 0.1125, (-2,-2))
p4 = find_via_position(t4, 0.1125, "GND", obs4, VIA_R, CLR, BOUNDS)
print("        ->", p4, "" if p4 is None else "dist=%.3f" % math.hypot(p4[0]-t4[0], p4[1]-t4[1]))

print("case 5  one ring inside (like H8) - the real question")
t5, obs5 = lattice(32.0, 32.0, 3, 0.4, 0.1125, (-2,-2))   # 7x7 array, target 1 ring in
p5 = find_via_position(t5, 0.1125, "GND", obs5, VIA_R, CLR, BOUNDS)
print("        ->", p5, "" if p5 is None else "dist=%.3f" % math.hypot(p5[0]-t5[0], p5[1]-t5[1]))
