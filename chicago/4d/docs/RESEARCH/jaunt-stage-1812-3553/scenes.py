# SPDX-License-Identifier: GPL-3.0-or-later
"""T-3553: who stands where at each staged stop of the two 1812 story jaunts, and what they do.

Read by build.py (`battle(b)` and `lalime(b)` take the build module for its helpers). Marks are
local ENU metres. Each scene follows its stop's own text and sources; who stands exactly where,
when they move, the unnamed figures' dress and every pose is reconstruction
(L-1812-staged-jaunts-3553). The owner's ruling for students, 2026-11-14, "Build-up and
aftermath": the lead-up is played and the fallen are shown lying still afterwards; no blow, shot
or blood is staged, and no child is shown dead.
"""
import math
import re

# ── shared ground ───────────────────────────────────────────────────────────────────────────
GATE_OUT = (1149.0, 198.2)          # just outside the fort's south gate
GATE_IN = (1149.0, 204.5)           # just inside it
IRWIN_WATCH = (1125.0, 193.0)       # "from twenty or thirty yards"
SOLDIERS = ['hays_otho', 'crozier_john', 'griffith_william', 'forth_thomas', 'bowen_joseph', 'allin_john', 'adams_george',
            'andrews_prestly', 'corbin_james', 'campbell_asa', 'dyer_dyson', 'draper_stephen', 'daugherty_daniel',
            'denison_micajah', 'edson_nathan', 'fury_john', 'garner_richard', 'hunt_william_n', 'hurtt_nathan_a',
            'jones_rodias', 'kennison_david', 'kilpatrick_samuel', 'landon_jacob', 'latta_james', 'lynch_michael',
            'logan_hugh', 'locker_frederick', 'mortt_august', 'miller_peter', 'mccarty_duncan', 'moffett_william',
            'mills_elias', 'noles_joseph', 'poindexter_thomas', 'prickett_william', 'peterson_frederick',
            'sherror_david', 'suttenfield_john', 'smith_john_sr', 'starr_james', 'vanhorn_james', 'simmons_john',
            'corbin_fielding', 'holt_isaac', 'needs_john']
MUSIC = ['burnett_george', 'smith_john_jr', 'hamilton_john', 'mcpherson_hugh']
LEADERS = ['topenebe', 'black_partridge', 'blackbird', 'waubansee', 'keepotah', 'naunongee', 'nuscotnemeg',
           'peesotum', 'waubeeneemah', 'winnemeg']
MIAMI = [f'miami_escort_1812_{i:02d}' for i in range(1, 28)]


def fates(b):
    """Heald's men by what the company's own cards say became of them on 15 August: killed in the
    action (Quaife's count, mostly by elimination) or alive at the surrender."""
    import json
    h = json.loads((b.ROOT / 'data/residents_1812/households/hh_heald_company_1812.json').read_text())
    killed = {p['id'] for p in h['persons'] if re.search(r'Killed in (battle|a bayonet)|among the 26', p.get('note') or '')}
    return killed, {p['id'] for p in h['persons'] if p['id'] not in killed}


# The beach at the eighteenth-street stop, read off the app's view from above: the waterline
# runs south by a little east; `shore(u, v)` is u metres along it (south positive) and v metres
# in from the water (west), from the waterline abreast of the stop's anchor.
SHORE0 = (1551.0, -3262.0)
SHORE_S = (0.220, -0.975)
SHORE_W = (-0.975, -0.220)


def shore(u, v):
    return (SHORE0[0] + u * SHORE_S[0] + v * SHORE_W[0], SHORE0[1] + u * SHORE_S[1] + v * SHORE_W[1])


def drop_drivers(b):
    """The men who drive the town's wagons (data/transport/driven/loops.json) are drawn on their
    wagons all day, so they are never cast: a person is drawn once."""
    text = (b.ROOT / 'data/transport/driven/loops.json').read_text()
    SOLDIERS[:] = [w for w in SOLDIERS if f'"{w}"' not in text]


def soldiers(b, n, skip=()):
    out = [s for s in SOLDIERS if s not in skip and b.castable(s)]
    return out[:n]


def polyline(pts):
    """[(s, e, n)] cumulative arc length along a path."""
    out, s = [(0.0, pts[0][0], pts[0][1])], 0.0
    for a, z in zip(pts, pts[1:]):
        s += math.hypot(z[0] - a[0], z[1] - a[1]); out.append((s, z[0], z[1]))
    return out


def along(line, s, side=0.0):
    """The point `s` metres along a polyline, `side` metres to its right."""
    s = max(0.0, min(s, line[-1][0]))
    for (s0, e0, n0), (s1, e1, n1) in zip(line, line[1:]):
        if s <= s1 or (s1, e1, n1) == line[-1]:
            k = 0 if s1 == s0 else (s - s0) / (s1 - s0)
            de, dn = e1 - e0, n1 - n0; L = math.hypot(de, dn) or 1
            return (e0 + de * k + side * dn / L, n0 + dn * k - side * de / L)


def sub(line, s0, s1, side=0.0):
    """The way from s0 to s1 along a polyline, `side` to its right, as marks."""
    pts = [along(line, s0, side)] + [along(line, s, side) for s, _, _ in line if s0 < s < s1] + [along(line, s1, side)]
    return pts


def battle(b):
    drop_drivers(b)
    P, member, bearing = b.P, b.member, b.bearing
    st = {}

    # 1 — Lee's place, 6 April, a little before sunset. Eleven men come to the cabin; White
    # meets them and goes in with them; the soldier and the boy slip down to the canoes, cross,
    # are seen on this bank making for the haystacks, look back, and run. The killing is the
    # stop's text: White and Cardin are last seen going in.
    door = (-1649.0, -4237.5); landing = (-1641.0, -4254.0)
    cast = []
    donors = b.take(b.MEN, 11, stride=37, offset=3)
    approach = [(-1702.0, -4196.0), (-1681.0, -4214.0), (-1660.0, -4231.0)]
    sit_at = [(-1655.5, -4241.0), (-1653.0, -4242.5), (-1645.0, -4242.0), (-1642.5, -4240.5)]
    for i, d in enumerate(donors):
        start = (approach[0][0] - 2.0 * i * 0.75, approach[0][1] + 2.0 * i * 0.65)
        path = [P(*approach[1]), P(*approach[2])]
        beats = []
        if i < len(sit_at):
            beats = [{'t': 0.8 * i, 'walk': path + [P(*sit_at[i])]}, {'t': 0.8 * i + 52, 'heading': bearing(sit_at[i], door)},
                     {'t': 0.8 * i + 54, 'pose': 'sit', 'ease': 1.2}]
        else:
            beats = [{'t': 0.8 * i, 'walk': path + [P(*door)], 'hide': True}]
        cast.append(member(f'extra:winnebago_{i + 1:02d}', P(*start), heading=bearing(start, approach[1]),
                           dress='potawatomi_man_1812', dress_of=d, beats=beats, tier='desktop' if i in (5, 7, 9) else None,
                           name="One of the eleven men Heald took for Winnebagoes (Ho-Chunk); name not recorded"))
    cast.append(member('white_liberty', P(-1651.5, -4239.8), face=approach[2], beats=[
        {'t': 26, 'greet': True}, {'t': 28, 'talk': True}, {'t': 44, 'talk': False}, {'t': 46, 'walk': [P(*door)], 'hide': True}]))
    cast.append(member('cardin_john_b', P(-1638.0, -4233.0), heading=300, beats=[
        {'t': 24, 'face': 'winnebago_01'}, {'t': 50, 'walk': [P(-1645.0, -4236.0), P(*door)], 'hide': True}]))
    flee = [{'t': 34, 'face': 'winnebago_02'}, {'t': 40, 'face': 'lee_son'}]
    cast.append(member('kelso_john', P(-1644.5, -4244.5), heading=300, beats=flee + [
        {'t': 46, 'walk': [P(-1643.0, -4249.0), P(*landing)], 'pace': 'brisk', 'hide': True},
        {'t': 62, 'place': P(-1641.5, -4293.5), 'show': True, 'heading': 120},
        {'t': 63, 'walk': [P(-1626.0, -4297.5), P(-1613.0, -4304.0)], 'pace': 'brisk'},
        {'t': 78, 'face': P(-1649.0, -4237.0)},
        {'t': 82, 'walk': [P(-1590.0, -4296.0), P(-1545.0, -4292.0)], 'pace': 'hurry', 'hide': True}]))
    cast.append(member('lee_son', P(-1643.0, -4245.5), heading=300, beats=[{'t': 34, 'face': 'winnebago_03'}, {'t': 40, 'face': 'kelso_john'},
        {'t': 47, 'walk': [P(-1642.0, -4249.5), P(landing[0] + 1.2, landing[1] - 0.4)], 'pace': 'brisk', 'hide': True},
        {'t': 62, 'place': P(-1640.0, -4294.6), 'show': True, 'heading': 120},
        {'t': 63, 'walk': [P(-1625.0, -4299.0), P(-1611.5, -4305.5)], 'pace': 'brisk'},
        {'t': 78, 'face': P(-1649.0, -4237.0)},
        {'t': 82.5, 'walk': [P(-1589.0, -4297.5), P(-1545.0, -4293.5)], 'pace': 'hurry', 'hide': True}]))
    st['hardscrabble'] = {'caption': "Watch the eleven men come to the cabin, and the soldier and the boy slip away across the river.", 'cast': cast}

    # 2 — the Burns house, 6 April, dusk. The children come out at the shouting from the far
    # bank and run in to their mother (a day after her baby, abed). Ronan's party lands from the
    # scow, goes in, and carries her down to the boat, the children after.
    door = (798.5, 103.6); boat = (806.5, 93.4)
    cast = [
        member('burns_child_a', P(797.2, 102.4), heading=180, hidden=True, beats=[
            {'t': 2, 'show': True}, {'t': 3, 'face': P(797.0, 40.0)}, {'t': 9, 'walk': [P(*door)], 'pace': 'brisk', 'hide': True},
            {'t': 48, 'place': P(799.6, 102.6), 'show': True, 'heading': 160}, {'t': 66, 'walk': [P(803.5, 96.0), P(boat[0] - 1.5, boat[1] + 0.8)], 'hide': True}]),
        member('burns_child_b', P(799.4, 102.2), heading=190, hidden=True, beats=[
            {'t': 3, 'show': True}, {'t': 4, 'face': P(799.0, 40.0)}, {'t': 12, 'walk': [P(*door)], 'hide': True},
            {'t': 48, 'place': P(797.5, 102.3), 'show': True, 'heading': 160}, {'t': 67, 'walk': [P(802.5, 96.5), P(boat[0] - 2.5, boat[1] + 1.0)], 'hide': True}]),
    ]
    party = ['ronan_george'] + soldiers(b, 5, skip=('kelso_john',))
    for i, who in enumerate(party):
        land = (boat[0] + 0.9 * (i % 3), boat[1] - 0.2 + 0.9 * (i // 3))
        stand = (795.8 + 1.4 * (i % 3), 100.4 + 0.9 * (i // 3))
        beats = [{'t': 18 + 0.6 * i, 'show': True}, {'t': 19 + 0.6 * i, 'walk': [P(804.0, 99.0), P(*stand)], 'heading': bearing(stand, door)}]
        if who == 'ronan_george':
            beats += [{'t': 32, 'walk': [P(door[0] + 0.6, door[1] - 1.3)], 'heading': 0}, {'t': 36, 'talk': True}, {'t': 44, 'talk': False},
                      {'t': 46, 'walk': [P(*door)], 'hide': True}, {'t': 58, 'show': True}, {'t': 59, 'walk': [P(*boat)], 'pace': 'slow', 'hide': True}]
        elif i <= 4:
            # four go in, and come out together carrying her bed, slowly, to the boat
            beats += [{'t': 40 + i, 'walk': [P(*door)], 'hide': True}, {'t': 56, 'place': P(door[0] - 0.8 + 0.8 * (i % 2), door[1] - 1.0 - 1.4 * ((i - 1) // 2)), 'show': True, 'heading': 160},
                      {'t': 57, 'walk': [P(boat[0] - 0.8 + 0.8 * (i % 2), boat[1] + 1.6 - 1.4 * ((i - 1) // 2))], 'pace': 0.7, 'hide': True}]
        else:
            beats += [{'t': 60, 'walk': [P(*land)], 'hide': True}]
        cast.append(member(who, P(*land), heading=bearing(land, door), hidden=True, beats=beats))
    st['burns'] = {'caption': "Watch the Burns children answer the shouting, and Ensign Ronan's party carry their mother down to the boat.", 'cast': cast}

    # 3 — the parade, 10 August, morning. Heald reads Hull's order to the company drawn up in
    # two ranks; the officers come to him to argue for staying; he holds to it.
    # In the stop's own view (from the parade's north side, looking east): the company in two
    # ranks across it with their backs to the visitor, Heald before them under the commanding
    # officer's gallery.
    heald = (1160.4, 223.2)
    cast = [member('heald_nathan', P(*heald), heading=270, beats=[{'t': 1, 'talk': True}, {'t': 22, 'talk': False},
            {'t': 34, 'face': 'helm_linai'}, {'t': 42, 'talk': True}, {'t': 52, 'talk': False}, {'t': 53, 'heading': 270}]),
            member('winnemeg', P(1160.4, 220.4), heading=250, beats=[{'t': 30, 'face': 'heald_nathan'}])]
    for i, (who, at) in enumerate([('helm_linai', (1158.8, 230.6)), ('ronan_george', (1160.0, 231.2)), ('van_voorhis_isaac', (1161.0, 231.8))]):
        to = (heald[0] - 0.6 + 1.0 * i, heald[1] + 1.5 + 0.2 * i)
        cast.append(member(who, P(*at), heading=180, beats=[{'t': 24 + i, 'walk': [P(*to)], 'heading': bearing(to, heald)},
                                                             {'t': 30 + 2 * i, 'talk': True}, {'t': 38 + 2 * i, 'talk': False}]))
    ranks = soldiers(b, 18, skip=('kelso_john',))
    for i, who in enumerate(ranks):
        row, k = divmod(i, 9)
        at = (1156.0 - 1.2 * row, 218.8 + 1.05 * k)
        cast.append(member(who, P(*at), heading=90, tier='desktop' if row == 1 and k % 2 else None,
                           beats=[{'t': 40 + (k % 5) * 0.7, 'face': 'heald_nathan'}] if k in (2, 6) else None))
    st['the-order'] = {'caption': "Watch Captain Heald read the order to the company, and his officers come to argue against it.", 'cast': cast}

    # 4 — the council on the esplanade, 12 August, afternoon. Heald alone, the leaders seated
    # before him, the people of the gathering standing round.
    centre = (1119.0, 222.0)
    cast = [member('heald_nathan', P(centre[0] + 3.8, centre[1]), heading=270, beats=[{'t': 2, 'talk': True}, {'t': 18, 'talk': False},
            {'t': 34, 'talk': True}, {'t': 48, 'talk': False}])]
    seats = b.ring(centre, 3.0, len(LEADERS), start=200, span=140)
    for i, (who, at) in enumerate(zip(LEADERS, seats)):
        beats = [{'t': 20, 'talk': True}, {'t': 31, 'talk': False}] if who == 'topenebe' else None
        if who == 'black_partridge': beats = [{'t': 40, 'face': 'heald_nathan'}]
        cast.append(member(who, at, face=(centre[0] + 3.8, centre[1]), pose='sit', beats=beats))
    crowd = b.take(b.MEN, 30, stride=11, offset=1) + b.take(b.WOMEN, 8, stride=5, offset=2)
    outer = b.ring(centre, 6.5, 14, start=15, span=150) + b.ring(centre, 8.3, 14, start=12, span=156) + b.ring(centre, 10.0, 10, start=25, span=130)
    for i, (who, at) in enumerate(zip(crowd, outer)):
        cast.append(member(who, at, face=centre, tier='desktop' if i % 3 == 2 else None))
    st['council'] = {'caption': "Watch the council: Heald alone before the leaders, the gathering standing round, the blockhouse guns above.", 'cast': cast}

    # 5 — the factory, 13 August, early afternoon. Soldiers carry the goods out to a pile on
    # the grass; the gathering stands round it to receive them; Heald looks on.
    door = (1071.6, 218.0); pile = (1079.0, 215.5)
    cast = [member('heald_nathan', P(1086.5, 221.5), face=pile)]
    carriers = soldiers(b, 6, skip=('kelso_john',))
    for i, who in enumerate(carriers):
        a = (door[0] + 0.6, door[1] - 1.6 + 1.1 * (i % 3)); z = (pile[0] - 1.2, pile[1] - 1.5 + 0.9 * (i % 4))
        beats, t = [], 1.5 * i
        for k in range(5):
            beats += [{'t': t, 'walk': [P(*z)]}, {'t': t + 10, 'walk': [P(*a)], 'hide': True}, {'t': t + 17, 'show': True}]
            t += 20
        cast.append(member(who, P(*a), heading=bearing(a, z), beats=beats))
    crowd = b.take(b.MEN, 18, stride=13, offset=4) + b.take(b.WOMEN, 12, stride=3, offset=6)
    spots = b.ring(pile, 4.2, 12, start=40, span=200) + b.ring(pile, 6.5, 12, start=30, span=220) + b.ring(pile, 8.8, 6, start=60, span=160)
    for i, (who, at) in enumerate(zip(crowd, spots)):
        cast.append(member(who, at, face=pile, tier='desktop' if i % 3 == 1 else None))
    st['factory'] = {'caption': "Watch the goods come out of the factory to the people of the gathering, while Heald looks on.", 'cast': cast}

    # 6 — the covered way, 13 August, evening, from above. Men carry the powder and the
    # liquor down the covered way; at the river end they stave in the barrels and pour.
    top = (1165.4, 236.5); end = (1166.0, 262.0)
    cast = []
    for i, who in enumerate(soldiers(b, 9, skip=('kelso_john',))):
        if i < 3:
            at = (end[0] - 1.2 + 1.2 * i, end[1] + 0.8)
            cast.append(member(who, P(*at), heading=0, pose='crouch', beats=[{'t': 12 + 9 * i, 'pose': 'stand', 'ease': 0.8}, {'t': 16 + 9 * i, 'pose': 'crouch', 'ease': 0.8}]))
            continue
        beats, t = [], 2.5 * (i - 3)
        for k in range(4):
            beats += [{'t': t, 'walk': [P(top[0], top[1] + 4), P(end[0], end[1] - 1.2)]}, {'t': t + 26, 'walk': [P(top[0], top[1] + 4), P(*top)]}]
            t += 50
        cast.append(member(who, P(top[0] + 0.2 * (i % 2), top[1] + 0.6 * (i - 3)), heading=0, beats=beats))
    st['covered-way'] = {'caption': "Watch the soldiers carry the powder and the whiskey down the covered way to the river.", 'cast': cast}

    # 7 — the gate, 14 August, sunset. Wells comes in at the head of his Miamis (on foot here;
    # no horse is drawn), his niece and Heald meet him; later Black Partridge comes to give back
    # his medal, and goes in with Heald.
    cast = [member('heald_nathan', P(GATE_OUT[0] + 0.4, GATE_OUT[1] + 0.6), heading=250, beats=[
                {'t': 17, 'face': 'wells_william'}, {'t': 19, 'greet': True}, {'t': 21, 'talk': True}, {'t': 30, 'talk': False},
                {'t': 44, 'face': 'black_partridge'}, {'t': 52, 'talk': True}, {'t': 60, 'talk': False},
                {'t': 62, 'walk': [P(*GATE_IN)], 'hide': True}]),
            member('heald_rebekah', P(GATE_OUT[0] + 1.6, GATE_OUT[1] + 1.0), heading=240, beats=[{'t': 16, 'face': 'wells_william'}, {'t': 18, 'greet': True},
                {'t': 34, 'walk': [P(*GATE_IN)], 'hide': True}]),
            member('wells_william', P(1117.0, 191.5), heading=80, beats=[{'t': 1, 'walk': [P(1132.0, 194.0), P(GATE_OUT[0] - 1.5, GATE_OUT[1] - 0.6)], 'heading': 70},
                {'t': 20, 'greet': True}, {'t': 22, 'talk': True}, {'t': 31, 'talk': False}, {'t': 35, 'walk': [P(*GATE_IN)], 'hide': True}])]
    for i, who in enumerate(MIAMI[:12]):
        row, k = divmod(i, 3)
        start = (1113.5 - 1.6 * row, 191.0 + 1.0 * k)
        stop = (1144.4 + 1.1 * (i % 6) + (3.6 if i % 6 >= 3 else 0.0), 196.6 + 1.3 * (i // 6))
        cast.append(member(who, P(*start), heading=80, tier='desktop' if i % 3 == 2 else None,
                           beats=[{'t': 1.5 + 0.4 * i, 'walk': [P(1128.0 - 1.6 * row, 193.4 + 1.0 * k), P(*stop)], 'heading': 60}]))
    cast.append(member('black_partridge', P(1112.0, 186.5), heading=80, hidden=True, beats=[
        {'t': 36, 'show': True}, {'t': 37, 'walk': [P(1135.0, 192.0), P(GATE_OUT[0] - 1.4, GATE_OUT[1] - 1.0)], 'heading': 60},
        {'t': 52, 'face': 'heald_nathan'}, {'t': 54, 'talk': True}, {'t': 61, 'talk': False}, {'t': 63, 'walk': [P(*GATE_IN)], 'hide': True}]))
    st['the-gate'] = {'caption': "Watch Wells come in with his Miami escort, and Black Partridge come to hand back his medal.", 'cast': cast}

    # 8 — the river's mouth, 15 August, nine in the morning: the column, from the north,
    # passes the visitor and goes on south along the beach (see column() below).
    st['river-mouth'] = column(b)

    # 9 — the sand bank, 15 August, about ten. The column comes down the beach and halts; the
    # warriors wait behind the bank, lying, kneeling, crouched; Wells comes hurrying back from the
    # front; the warriors rise and the soldiers turn to face the bank. Nothing further is staged.
    east = (bearing(shore(0, 30), shore(0, 0)))
    walking = ['heald_rebekah', 'helm_margaret', 'holt_mrs', 'needs_mrs', 'cooper_isabella', 'simmons_susan_millhouse', 'lee_mrs', 'cicely', 'lee_son']
    order = (['heald_nathan', 'kinzie_john_elder', 'helm_linai', 'ronan_george', 'van_voorhis_isaac'] + MUSIC
             + soldiers(b, 60, skip=('fury_john',))
             + [('WAGON', 0, walking[:4]), ('WAGON', 1, walking[4:8])] + walking[8:]
             + ['burns_thomas', 'lee_charles', 'simmons_david', 'cooper_joseph'] + [f'chicago_militia_unnamed_{i}' for i in range(1, 7)])
    order = [w for w in order if isinstance(w, tuple) or b.castable(w)]
    cast, teams, slot, i = [], [], 0, 0
    for who in order:
        if isinstance(who, tuple):
            _, k, beside = who
            team, riders = WAGONS[k]
            slot += slot % 2
            rank = slot // 2
            u_end = -9.0 - 1.7 * rank - TEAM_AHEAD; u0 = u_end - 34.0
            a, z = shore(u0, 9.6), shore(u_end, 9.6)
            t, seated = wagon(b, team, riders, a, [z], bearing(a, z))
            teams.append(t); cast += seated
            for j, w in enumerate(x for x in beside if b.castable(x)):
                du = TEAM_AHEAD - 1.2 - 1.7 * j
                wa, wz = shore(u0 + du, 11.0), shore(u_end + du, 11.0)
                beats = [{'t': 0.0, 'walk': [P(*wz)], 'pace': MARCH}]
                if w in ('heald_rebekah', 'helm_margaret') or j % 2 == 0:
                    beats += [{'t': 41 + 0.2 * j, 'face': P(*shore(u_end - 8, 40))}]
                cast.append(member(w, P(*wa), heading=bearing(wa, wz), tier='desktop' if j % 2 else None, beats=beats))
            slot += 2 * TEAM_RANKS
            continue
        rank, file = divmod(slot, 2)
        slot += 1
        u_end = -9.0 - 1.7 * rank; u0 = u_end - 34.0
        v = 9.0 + 1.2 * file
        a, z = shore(u0, v), shore(u_end, v)
        beats = [{'t': 0.0, 'walk': [P(*z)], 'pace': MARCH}]
        regular = who in SOLDIERS or who in ('ronan_george', 'helm_linai', 'heald_nathan')
        if regular:
            beats += [{'t': 40 + 0.15 * (i % 9), 'heading': bearing(z, shore(u_end, v + 20))},
                      {'t': 43 + 0.1 * (i % 7), 'walk': [P(*shore(u_end + 0.4 * (i % 3), v + 6.0))], 'heading': bearing(z, shore(u_end, v + 20))}]
        elif who in ('heald_rebekah', 'helm_margaret') or rank % 3 == 0:
            beats += [{'t': 41 + 0.2 * (i % 5), 'face': P(*shore(u_end - 8, 40))}]
        if who == 'heald_nathan':
            beats += [{'t': 30, 'face': 'wells_william'}, {'t': 33, 'talk': True}, {'t': 38, 'talk': False}]
        cast.append(member(who, P(*a), heading=bearing(a, z), tier='desktop' if i % 3 == 2 and who != 'heald_nathan' else None, beats=beats))
        i += 1
    w0 = shore(26.0, 10.0)
    cast.append(member('wells_william', P(*w0), heading=bearing(w0, shore(60, 10)), beats=[
        {'t': 0.0, 'walk': [P(*shore(34.0, 10.0))], 'pace': MARCH}, {'t': 14, 'face': P(*shore(10, 40))},
        {'t': 18, 'walk': [P(*shore(-7.5, 12.0))], 'pace': 'hurry'}, {'t': 30, 'face': 'heald_nathan'}, {'t': 31, 'talk': True}, {'t': 38, 'talk': False},
        {'t': 40, 'heading': bearing(shore(0, 12), shore(0, 30))}]))
    for i, who in enumerate(MIAMI[:6]):
        at = shore(30.0 + 1.6 * (i // 2), 9.0 + 1.3 * (i % 2))
        cast.append(member(who, P(*at), heading=bearing(at, shore(60, 10)), tier='desktop' if i % 2 else None,
                           beats=[{'t': 0.0, 'walk': [P(*shore(38.0 + 1.6 * (i // 2), 9.0 + 1.3 * (i % 2)))], 'pace': MARCH}, {'t': 20 + i, 'face': P(*shore(10, 40))}]))
    waiting = b.take(b.MEN, 72, stride=19, offset=7)
    poses = ['prone', 'kneel', 'crouch', 'prone', 'kneel2', 'kneel', 'crouch', 'prone', 'sit', 'kneel']
    for i, who in enumerate(waiting):
        u = -58.0 + 66.0 * ((i * 0.618) % 1.0)
        v = 30.0 + 3.5 * (i % 5) + 3.0 * ((i * 0.382) % 1.0)
        at = shore(u, v)
        pose = poses[i % len(poses)]
        cast.append(member(who, P(*at), heading=(east + (i % 7) * 4 - 12) % 360, pose=pose, tier='desktop' if i % 3 else None,
                           beats=[{'t': 36 + 0.25 * (i % 13), 'pose': 'stand', 'ease': 1.1 + 0.1 * (i % 4)},
                                  {'t': 41 + 0.2 * (i % 9), 'walk': [P(*shore(u + (i % 3) - 1, v - 6.0))], 'heading': east}]))
    st['the-bank'] = {'caption': "Watch the column come down the beach and halt, the wagons with it, the warriors waiting behind the bank, and Wells hurry back.", 'cast': cast, 'teams': teams}

    # 10 — the small elevation, about half past ten. Heald's men who are left, standing,
    # kneeling, sitting with their wounds; Black Bird walks out to Heald and they shake hands;
    # back towards the bank, the dead lie still.
    killed, alive = fates(b)
    heald = (1167.5, -3465.0)
    cast = [member('heald_nathan', P(*heald), heading=55, beats=[{'t': 18, 'face': 'blackbird'}, {'t': 31, 'greet': True},
                                                                 {'t': 40, 'talk': True}, {'t': 46, 'talk': False}]),
            member('helm_linai', P(heald[0] - 1.6, heald[1] - 1.0), heading=60, pose='kneel', beats=[{'t': 20, 'face': 'blackbird'}, {'t': 50, 'pose': 'stand', 'ease': 1.4}])]
    left = [w for w in SOLDIERS if w in alive and w not in ('kelso_john', 'fury_john') and b.castable(w)][:20]
    spots = b.ring((heald[0] - 0.5, heald[1] - 2.0), 4.0, 10, start=290, span=250) + b.ring((heald[0] - 0.5, heald[1] - 2.0), 6.8, 10, start=280, span=270)
    pose_of = ['kneel', None, 'sit', None, None, 'kneel2', None, 'sit', None, 'kneel']
    for i, (who, at) in enumerate(zip(left, spots)):
        pose = pose_of[i % len(pose_of)]
        beats = [{'t': 52 + 0.4 * (i % 6), 'pose': 'stand', 'ease': 1.4}] if pose in ('kneel', 'kneel2') else None
        cast.append(member(who, at, heading=(40 + 13 * i) % 80 + 20, pose=pose, tier='desktop' if i % 3 == 2 else None, beats=beats))
    bb0 = (1201.0, -3436.0)
    cast.append(member('blackbird', P(*bb0), heading=bearing(bb0, heald), beats=[
        {'t': 4, 'walk': [P(heald[0] + 1.3, heald[1] + 1.0)], 'heading': bearing((heald[0] + 1.3, heald[1] + 1.0), heald)},
        {'t': 31, 'greet': True}, {'t': 33, 'talk': True}, {'t': 40, 'talk': False}]))
    for i, d in enumerate(b.take(b.MEN, 3, stride=23, offset=5)):
        a = (bb0[0] + 2.0 + 1.5 * i, bb0[1] + 1.0 + 1.2 * i); z = (heald[0] + 5.0 + 1.4 * i, heald[1] + 4.0 + 1.0 * i)
        cast.append(member(d, P(*a), heading=bearing(a, heald), beats=[{'t': 5 + 0.6 * i, 'walk': [P(*z)], 'heading': bearing(z, heald)}]))
    fallen = ['ronan_george', 'van_voorhis_isaac', 'wells_william'] + [w for w in SOLDIERS if w in killed and w != 'kelso_john' and b.castable(w)][:8] \
        + [w for w in ['chicago_militia_unnamed_1', 'chicago_militia_unnamed_2', 'chicago_militia_unnamed_3'] if b.castable(w)]
    for i, who in enumerate(fallen):
        r = 42.0 + 6.0 * i + 4.0 * ((i * 0.618) % 1.0)
        ang = math.radians(30.0 + 40.0 * ((i * 0.382) % 1.0))
        at = (heald[0] + r * math.sin(ang), heald[1] + r * math.cos(ang))
        cast.append(member(who, P(*at), heading=(i * 67) % 360, pose='lie', tier='desktop' if i % 3 == 2 else None))
    st['cottonwoods'] = {'caption': "Watch Black Bird come out to Heald's last men and take his hand; behind, the dead lie still.", 'cast': cast}

    # 11 — the Kinzie house, 15 August, sunset: the family on the green under guard; Kinzie
    # kneels to Mrs. Heald's arm; the guards stand round, facing out.
    cast = [
        member('heald_rebekah', P(1148.0, 323.0), heading=90, pose='sit'),
        member('kinzie_john_elder', P(1150.0, 323.2), heading=270, pose='kneel', beats=[{'t': 6, 'talk': True}, {'t': 16, 'talk': False}]),
        member('kinzie_eleanor', P(1146.6, 325.6), face=(1148.0, 323.0)),
        member('kinzie_john_h_1812', P(1143.4, 330.0), heading=160),
        member('kinzie_ellen_marion', P(1144.8, 331.2), heading=170),
        member('kinzie_maria_indiana', P(1142.6, 331.6), heading=150),
        member('kinzie_robert_allen', P(1145.6, 329.4), heading=200),
        member('black_partridge', P(1139.8, 319.8), heading=225, beats=[{'t': 20, 'heading': 200}]),
        member('waubansee', P(1157.0, 320.5), heading=135),
        member('keepotah', P(1156.0, 331.0), heading=90, beats=[{'t': 30, 'face': 'kinzie_john_elder'}]),
        member('topenebe', P(1139.0, 330.0), heading=270),
    ]
    st['kinzie-house'] = {'caption': "Watch the Kinzies on their green under guard, Kinzie kneeling to Mrs. Heald's wounded arm.", 'cast': cast}

    # 12 — the Ouilmette house, 16 August, morning. Searchers come; some go in, the rest wait
    # at the door; they come out and go. Mrs. Helm is under the feather bed inside, not shown.
    door = (1119.0, 344.4)
    cast = [member('ouilmette_antoine', P(door[0] + 0.9, door[1] - 1.0), heading=240, beats=[{'t': 14, 'talk': True}, {'t': 22, 'talk': False}]),
            member('ouilmette_archange', P(door[0] - 0.9, door[1] - 0.6), heading=200),
            member('black_partridge', P(1126.5, 340.0), heading=250, beats=[{'t': 14, 'face': P(1112.0, 339.0)}])]
    for i, d in enumerate(b.take(b.MEN, 6, stride=29, offset=9)):
        start = (1089.0 - 1.4 * (i // 2), 337.0 + 1.3 * (i % 2)); wait = (1115.0 + 1.0 * (i % 3), 340.0 + 1.2 * (i // 3))
        beats = [{'t': 0.5 * i, 'walk': [P(*wait)], 'heading': bearing(wait, door)}]
        if i < 3:
            beats += [{'t': 22 + i, 'walk': [P(*door)], 'hide': True}, {'t': 42 + i, 'show': True}, {'t': 43 + i, 'walk': [P(*wait)]}]
        beats += [{'t': 50 + 0.5 * i, 'walk': [P(*start), P(start[0] - 12, start[1])], 'hide': True}]
        cast.append(member(f'extra:wabash_searcher_{i + 1}', P(*start), heading=80, dress='potawatomi_man_1812', dress_of=d,
                           name='One of the searchers, a war party from the Wabash; names not recorded', beats=beats))
    st['ouilmette'] = {'caption': "Watch the searchers come to the Ouilmette house and go in, while Mrs. Helm lies hidden.", 'cast': cast}

    return st


# The trail along the river's channel above its mouth, north to south (from the app's own view
# from above): the column walks it at a march, two abreast, past the visitor.
TRAIL = [(1148.0, -300.0), (1148.0, -370.0), (1139.0, -412.0), (1141.0, -433.0), (1149.0, -450.0),
         (1151.0, -475.0), (1149.0, -496.0), (1144.0, -527.0), (1143.0, -540.0), (1141.0, -600.0), (1140.0, -640.0)]
MARCH = 1.3

# The column's wagons (T-3553): the town's own two teams (data/transport/driven/loops.json),
# driven by the men who drive them every day, Mills and Moffett, walking at the near horse.
# The accounts (Helm's narrative, Wau-Bun) put the children and some of the women in the baggage wagons. Who sits in which is
# reconstruction (L-1812-staged-jaunts-3553). Seats are vehicle-local metres on the farm box's
# bed (farm-box-near.glb: bed boards top 0.955 m, sides to 1.5 m, inside x within 0.48 m,
# z within 1.5 m): two across, four rows, all facing ahead, sitting on the baggage with their legs out.
WAGONS = [
    ('fort_wagon_loop_1812', ['burns_mrs', 'burns_child_a', 'burns_child_b', 'holt_child', 'needs_child',
                              'garrison_child_unnamed_1', 'garrison_child_unnamed_2']),
    ('shore_road_wagon_haul_1812', ['corbin_mrs', 'lee_daughter', 'garrison_child_unnamed_3', 'garrison_child_unnamed_4',
                                    'garrison_child_unnamed_5', 'garrison_child_unnamed_6', 'garrison_child_unnamed_7']),
]
RIDERS = {w for _, riders in WAGONS for w in riders}
SEAT_Y = 1.15  # the bed boards (0.955 m) and the bundles they sit on: 'sit' puts the hips at its foot
SEATS = [(0.24, SEAT_Y, 1.05), (-0.24, SEAT_Y, 1.05), (0.24, SEAT_Y, 0.35), (-0.24, SEAT_Y, 0.35),
         (0.24, SEAT_Y, -0.35), (-0.24, SEAT_Y, -0.35), (0.24, SEAT_Y, -1.05), (-0.24, SEAT_Y, -1.05)]
TEAM_AHEAD = 4.8   # the lead horses' noses ahead of the vehicle root, near enough (envelope 5.1 m)
TEAM_RANKS = 5     # the ranks of two a team and its wagon take in the column


def wagon(b, team, riders, start, way, heading, pace=MARCH):
    """A town team taken for the column, and the people sitting in it."""
    P, member = b.P, b.member
    t = {'team': team, 'at': P(*start), 'heading': round(heading % 360, 1),
         'beats': [{'t': 0.0, 'walk': [P(*p) for p in way], 'pace': pace}]}
    seated = [member(who, P(*start), heading=heading, pose='sit', ride={'team': team, 'seat': list(SEATS[k])})
              for k, who in enumerate(w for w in riders if b.castable(w))]
    return t, seated


def column(b):
    P, member = b.P, b.member
    line = polyline(TRAIL)
    walking = ['heald_rebekah', 'helm_margaret', 'holt_mrs', 'needs_mrs', 'cicely', 'cooper_isabella', 'simmons_susan_millhouse', 'lee_mrs', 'lee_son']
    order = (['wells_william'] + MIAMI[:14] + MUSIC + ['heald_nathan', 'kinzie_john_elder', 'helm_linai', 'ronan_george', 'van_voorhis_isaac']
             + soldiers(b, 60)
             + [('WAGON', 0, walking[:4]), ('WAGON', 1, walking[4:8])] + walking[8:]
             + ['burns_thomas', 'lee_charles', 'simmons_david', 'cooper_joseph'] + [f'chicago_militia_unnamed_{i}' for i in range(1, 7)]
             + MIAMI[14:])
    order = [w for w in order if isinstance(w, tuple) or b.castable(w)]
    s_vis = min(line, key=lambda p: math.hypot(p[1] - 1150.0, p[2] + 490.0))[0]
    head0 = s_vis - 50.0  # the head starts about 45 m north of the visitor
    head_end = line[-1][0] - 2.0
    cast, teams, slot, i = [], [], 0, 0
    for who in order:
        if isinstance(who, tuple):
            _, k, beside = who
            team, riders = WAGONS[k]
            slot += slot % 2
            rank = slot // 2
            s0 = head0 - 1.7 * (rank + 2) - TEAM_AHEAD
            s1 = head_end - 1.7 * (rank + 2) - TEAM_AHEAD
            start = along(line, s0, 3.3)
            way = sub(line, s0, s1, 3.3)[1:]
            t, seated = wagon(b, team, riders, start, way, b.bearing(start, way[0]))
            teams.append(t); cast += seated
            # The rest of the women walk beside it, on the side away from the teamster.
            for j, w in enumerate(x for x in beside if b.castable(x)):
                a0 = s0 + TEAM_AHEAD - 1.2 - 1.7 * j
                a = along(line, a0, 4.9)
                cast.append(member(w, P(*a), heading=b.bearing(a, way[0]), tier='desktop' if j % 2 else None,
                                   beats=[{'t': 0.0, 'walk': [P(*p) for p in sub(line, a0, s1 + TEAM_AHEAD - 1.2 - 1.7 * j, 4.9)[1:]], 'pace': MARCH}]))
            slot += 2 * TEAM_RANKS
            continue
        rank, file = divmod(slot, 2) if slot else (0, 0)
        if who == 'wells_william': rank, file = -2, 0.5
        slot += 1
        s0 = head0 - 1.7 * (rank + 2)
        s1 = head_end - 1.7 * (rank + 2)
        side = (4.0 if file == 0 else 2.6) if file != 0.5 else 3.3
        start = along(line, s0, side)
        way = sub(line, s0, s1, side)[1:]
        tier = 'desktop' if (i % 3 == 2 and who not in ('heald_nathan', 'wells_william', 'kinzie_john_elder')) else None
        i += 1
        cast.append(member(who, P(*start), heading=b.bearing(start, way[0]), tier=tier, beats=[{'t': 0.0, 'walk': [P(*p) for p in way], 'pace': MARCH}]))
    # The Potawatomi escort walks with them out on the prairie, at a distance.
    for i, who in enumerate(b.take(b.MEN, 24, stride=17, offset=11)):
        rank, k = divmod(i, 4)
        s0 = head0 - 10.0 - 6.0 * rank - 1.5 * k
        s1 = s0 + 150.0
        side = 42.0 + 3.0 * k + (i % 3)
        start = along(line, s0, side)
        way = sub(line, s0, min(s1, line[-1][0]), side)[1:]
        cast.append(member(who, P(*start), heading=b.bearing(start, way[0]), tier='desktop' if i % 6 else None,
                           beats=[{'t': 0.0, 'walk': [P(*p) for p in way], 'pace': MARCH}]))
    return {'caption': "Watch the column come down from the fort and pass you: Wells and the Miamis, the band, the regulars, the wagons with the children, the families, the militia.", 'cast': cast, 'teams': teams}


def lalime(b):
    drop_drivers(b)
    P, member, bearing = b.P, b.member, b.bearing
    st = {}
    body = (1146.4, 194.6)

    # 0 — the cold open: Lalime lies outside the gate; Kinzie walks away, bleeding; Helm and the
    # girl at the gate; Irwin where he watched from.
    away = [P(1158.0, 195.0), P(1171.0, 198.0), P(1176.0, 212.0), P(1180.0, 236.0)]
    st['cold-open'] = {'caption': "Lalime lies where he fell; Kinzie walks away.", 'cast': [
        member('lalime_john', P(*body), heading=250, pose='lie'),
        member('kinzie_john_elder', P(1150.5, 195.2), heading=95, beats=[{'t': 1, 'walk': away, 'pace': 'slow', 'hide': True}]),
        member('helm_linai', P(GATE_OUT[0] - 0.2, GATE_OUT[1] + 0.8), face=body),
        member('mirandeau_victoire_1812', P(GATE_OUT[0] + 1.4, GATE_OUT[1] + 1.6), face=body),
        member('irwin_matthew', P(*IRWIN_WATCH), face=body),
    ]}

    # 1 — May 1804, the du Sable house: the Kinzies and their men bring their things up from the
    # river and go in; Lalime watches from the west, then walks off along the bank.
    door = (1150.5, 339.5)
    cast = [member('kinzie_john_elder', P(1160.0, 304.0), heading=340, beats=[{'t': 1, 'walk': [P(1152.0, 318.0), P(door[0] + 0.6, door[1] - 1.6)], 'heading': 0},
                                                                              {'t': 24, 'face': 'lalime_john'}, {'t': 30, 'walk': [P(*door)], 'hide': True}]),
            member('kinzie_eleanor', P(1161.4, 302.6), heading=340, beats=[{'t': 2, 'walk': [P(1153.4, 317.0), P(*door)], 'hide': True}])]
    for i, who in enumerate(['kinzie_engage_1812', 'kinzie_boatman_1812', 'kinzie_servant_second']):
        a = (1163.0 + 1.2 * i, 301.0 - 0.8 * i)
        cast.append(member(who, P(*a), heading=330, beats=[{'t': 6 + 4 * i, 'walk': [P(1154.0 + 0.8 * i, 317.0), P(*door)], 'hide': True},
                                                            {'t': 34 + 4 * i, 'show': True}, {'t': 35 + 4 * i, 'walk': [P(*a)]},
                                                            {'t': 58 + 4 * i, 'walk': [P(1154.0 + 0.8 * i, 317.0), P(*door)], 'hide': True}]))
    cast.append(member('lalime_john', P(1143.0, 329.0), face=door, beats=[{'t': 26, 'face': 'kinzie_john_elder'}, {'t': 40, 'walk': [P(1130.0, 330.0), P(1102.0, 331.0), P(1080.0, 333.0)], 'hide': True}]))
    st['du-sable-house'] = {'caption': "Watch the Kinzies move into the du Sable house, and Lalime look on from along the bank.", 'cast': cast}

    # 2 — May 1811, Lalime's house: he sits at his door with his letter; a neighbour passes.
    st['lalime-house'] = {'caption': "Lalime at his own door, writing to Governor Clark.", 'cast': [
        member('lalime_john', P(1101.2, 341.8), heading=170, pose='sit', beats=[{'t': 18, 'face': 'ouilmette_antoine'}, {'t': 21, 'greet': True}, {'t': 28, 'heading': 170}]),
        member('ouilmette_antoine', P(1128.0, 333.5), heading=270, beats=[{'t': 4, 'walk': [P(1106.0, 337.8), P(1088.0, 336.0)]}, {'t': 19, 'greet': True}]),
    ]}

    # 3 — 10 March 1812, the factory: Irwin at his door with his two allies; Kinzie and Helm
    # look on from the path.
    door = (1072.0, 218.0)
    st['factory'] = {'caption': "Irwin at his factory door with Van Voorhis and Lalime; Kinzie and Helm watching from the path.", 'cast': [
        member('irwin_matthew', P(door[0] + 0.8, door[1]), heading=90, beats=[{'t': 2, 'talk': True}, {'t': 14, 'talk': False}, {'t': 30, 'face': 'kinzie_john_elder'}]),
        member('van_voorhis_isaac', P(door[0] + 3.0, door[1] - 1.4), face=(door[0] + 0.8, door[1]), beats=[{'t': 15, 'talk': True}, {'t': 24, 'talk': False}]),
        member('lalime_john', P(door[0] + 3.1, door[1] + 1.4), face=(door[0] + 0.8, door[1]), beats=[{'t': 25, 'talk': True}, {'t': 33, 'talk': False}]),
        member('kinzie_john_elder', P(1088.0, 208.0), face=(door[0] + 2.0, door[1]), beats=[{'t': 10, 'talk': True}, {'t': 16, 'talk': False}]),
        member('helm_linai', P(1089.4, 209.6), face=(door[0] + 2.0, door[1]), beats=[{'t': 12, 'face': 'kinzie_john_elder'}]),
    ]}

    # 4 — 16 April 1812, before the officers' barracks: Helm, Kinzie and Ronan in hot talk;
    # Irwin and Lalime pass; Ronan turns on Lalime.
    st['bad-blood'] = {'caption': "Helm, Kinzie and Ronan talking hot; Ronan turns on Lalime as he passes with Irwin.", 'cast': [
        member('helm_linai', P(1146.2, 221.8), heading=110, beats=[{'t': 1, 'talk': True}, {'t': 12, 'talk': False}]),
        member('kinzie_john_elder', P(1148.6, 223.0), heading=220, beats=[{'t': 12, 'talk': True}, {'t': 20, 'talk': False}]),
        member('ronan_george', P(1148.4, 220.6), heading=300, beats=[{'t': 24, 'face': 'lalime_john'}, {'t': 26, 'talk': True}, {'t': 34, 'talk': False}]),
        member('irwin_matthew', P(1138.6, 209.4), heading=40, beats=[{'t': 2, 'walk': [P(1143.0, 214.0), P(1151.0, 213.0)]}, {'t': 26, 'face': 'ronan_george'}]),
        member('lalime_john', P(1137.6, 208.4), heading=40, beats=[{'t': 2.5, 'walk': [P(1142.4, 212.6), P(1149.8, 211.8)]}, {'t': 27, 'face': 'ronan_george'}]),
    ]}

    # 5 — 17 June, six in the evening, the parade: the quarrel. Helm rails against the
    # factory, Kinzie backs him, Lalime answers for it; Kinzie and Lalime walk out together.
    # In the stop's own view (the parade's north side, looking east), clear of the flagstaff.
    out_k = [P(1154.0, 216.0), P(GATE_IN[0] + 0.4, GATE_IN[1]), P(GATE_OUT[0] + 0.4, GATE_OUT[1] + 1.4)]
    out_l = [P(1152.6, 216.4), P(GATE_IN[0] - 0.4, GATE_IN[1]), P(GATE_OUT[0] - 0.4, GATE_OUT[1] + 1.4)]
    st['the-quarrel'] = {'caption': "Watch the quarrel on the parade: Helm, then Lalime, then Kinzie; then Kinzie and Lalime walk out together.", 'cast': [
        member('helm_linai', P(1157.0, 222.6), heading=285, beats=[{'t': 1, 'talk': True}, {'t': 12, 'talk': False}, {'t': 26, 'face': 'kinzie_john_elder'}]),
        member('kinzie_john_elder', P(1157.6, 224.8), heading=265, beats=[{'t': 22, 'talk': True}, {'t': 30, 'talk': False},
            {'t': 32, 'walk': out_k, 'hide': True}]),
        member('lalime_john', P(1153.2, 223.6), heading=95, beats=[{'t': 12, 'talk': True}, {'t': 21, 'talk': False}, {'t': 22, 'face': 'kinzie_john_elder'},
            {'t': 32.5, 'walk': out_l, 'hide': True}]),
        member('irwin_matthew', P(1152.4, 221.6), heading=80),
        member('van_voorhis_isaac', P(1152.8, 226.0), heading=110, beats=[{'t': 14, 'face': 'helm_linai'}]),
        member('mirandeau_victoire_1812', P(1150.5, 220.2), heading=70),
    ] + [member(w, P(*at), face=(1155.2, 223.6), tier='desktop' if i % 2 else None)
         for i, (w, at) in enumerate(zip(soldiers(b, 4, skip=('kelso_john',)), [(1159.4, 227.0), (1159.2, 219.8), (1151.0, 226.8), (1156.0, 218.6)]))]}

    # 6 — sunset, outside the gate: the argument, Helm's warning, then (no blow shown) the two
    # go down together; Kinzie gets up and goes; Lalime does not.
    st['the-gate'] = {'caption': "Watch Kinzie and Lalime outside the gate at sunset, and what is left when it is over.", 'cast': [
        member('kinzie_john_elder', P(GATE_OUT[0] + 0.4, GATE_OUT[1] + 0.6), heading=200, beats=[
            {'t': 1, 'walk': [P(body[0] + 1.3, body[1] + 0.1)]}, {'t': 5, 'face': 'lalime_john'}, {'t': 6, 'talk': True}, {'t': 15, 'talk': False},
            {'t': 20, 'pose': 'kneel2', 'ease': 1.4}, {'t': 25, 'pose': 'stand', 'ease': 1.4},
            {'t': 28, 'walk': away, 'pace': 'slow', 'hide': True}]),
        member('lalime_john', P(GATE_OUT[0] - 0.6, GATE_OUT[1] + 0.4), heading=200, beats=[
            {'t': 1.2, 'walk': [P(body[0] - 0.2, body[1] - 0.2)]}, {'t': 5, 'face': 'kinzie_john_elder'}, {'t': 9, 'talk': True}, {'t': 17, 'talk': False},
            {'t': 20, 'heading': 250}, {'t': 20.2, 'pose': 'lie', 'ease': 2.2}]),
        member('helm_linai', P(GATE_IN[0], GATE_IN[1] - 1.5), heading=180, beats=[{'t': 10, 'walk': [P(GATE_OUT[0] + 0.2, GATE_OUT[1] + 1.2)]},
            {'t': 13, 'face': 'kinzie_john_elder'}, {'t': 14, 'talk': True}, {'t': 18, 'talk': False}, {'t': 32, 'walk': [P(body[0] + 0.6, body[1] + 1.6)], 'heading': 200}]),
        member('mirandeau_victoire_1812', P(GATE_IN[0] + 1.3, GATE_IN[1] - 0.6), heading=190, beats=[{'t': 12, 'walk': [P(GATE_OUT[0] + 1.5, GATE_OUT[1] + 1.8)]}, {'t': 16, 'face': 'lalime_john'}]),
        member('irwin_matthew', P(*IRWIN_WATCH), face=body, beats=[{'t': 34, 'walk': [P(1137.0, 194.0)], 'heading': 90}]),
    ]}

    # 7 — 11:20 at night, the river's edge before the fort: Helm walks Kinzie down to the
    # water, shakes his hand and lets him go (Irwin's account); Ronan watches from the fort.
    edge = (1140.4, 254.2)  # straight ahead of the visitor at the stop (1140, 250, looking north)
    far = (1145.5, 297.5)
    st['the-flight'] = {'caption': "In the dark: Helm walks Kinzie down to the water, shakes his hand, and lets him go across the river.", 'cast': [
        member('kinzie_john_elder', P(1147.0, 238.0), heading=350, beats=[{'t': 0.5, 'walk': [P(1144.4, 248.6), P(edge[0] + 0.4, edge[1] + 0.2)]},
            {'t': 15, 'face': 'helm_linai'}, {'t': 17, 'greet': True}, {'t': 24, 'walk': [P(edge[0] + 0.2, edge[1] + 1.2)], 'hide': True},
            {'t': 44, 'place': P(*far), 'show': True, 'heading': 5}, {'t': 45, 'walk': [P(1149.0, 312.0), P(1150.0, 338.6)], 'pace': 'slow', 'hide': True}]),
        member('helm_linai', P(1148.4, 237.2), heading=350, beats=[{'t': 0.7, 'walk': [P(1146.0, 248.0), P(edge[0] + 1.6, edge[1] - 1.0)]},
            {'t': 15, 'face': 'kinzie_john_elder'}, {'t': 17, 'greet': True}, {'t': 30, 'face': P(*far)}, {'t': 60, 'walk': [P(1148.0, 238.0)], 'hide': True}]),
        member('ronan_george', P(1137.5, 241.0), heading=40),
    ]}

    # 8 — 18 June, morning, two hundred yards west of the Kinzie house: soldiers headed by Helm
    # bring the body to the grave; the townspeople who wanted an inquest stand by.
    grave = (991.0, 344.0)
    cast = [member('lalime_john', P(*grave), heading=95, pose='lie', hidden=True, beats=[{'t': 34, 'show': True}])]
    bearers = soldiers(b, 6, skip=('kelso_john',))
    for i, who in enumerate(bearers):
        start = (1040.0 + 1.0 * (i // 2), 364.0 + 1.0 * (i % 2)); stand = (grave[0] - 2.0 + 2.0 * (i % 3), grave[1] - 1.8 + 3.6 * (i // 3))
        via = (grave[0] + 2.0 + 1.0 * (i // 2), grave[1] - 0.6 + 1.0 * (i % 2))
        beats = [{'t': 2 + 0.3 * i, 'walk': [P(1008.0 + 1.0 * (i // 2), 356.0 + 1.0 * (i % 2)), P(*via)], 'pace': 0.8}, {'t': 36, 'walk': [P(*stand)], 'heading': bearing(stand, grave)}]
        if i in (0, 3): beats += [{'t': 44, 'pose': 'crouch', 'ease': 1.0}]
        cast.append(member(who, P(*start), heading=270, beats=beats))
    cast.append(member('helm_linai', P(1044.0, 362.0), heading=250, beats=[{'t': 1, 'walk': [P(1010.0, 354.0), P(grave[0] + 4.4, grave[1] - 2.6)], 'pace': 0.8}, {'t': 40, 'face': 'irwin_matthew'}]))
    for i, who in enumerate(['irwin_matthew', 'van_voorhis_isaac', 'ouilmette_antoine', 'leclerc_pierre', 'mirandeau_jean_baptiste']):
        start = (1052.0 + 1.6 * i, 370.0 + 1.0 * (i % 2)); stand = (grave[0] + 6.0 + 1.4 * i, grave[1] + 4.0 + 0.8 * (i % 2))
        beats = [{'t': 6 + 0.6 * i, 'walk': [P(*stand)], 'heading': bearing(stand, grave)}]
        if who == 'irwin_matthew': beats += [{'t': 40, 'face': 'helm_linai'}, {'t': 41, 'talk': True}, {'t': 50, 'talk': False}]
        cast.append(member(who, P(*start), heading=270, beats=beats))
    st['the-grave'] = {'caption': "Watch Helm's file of soldiers bring Lalime to his grave, while the townspeople who wanted an inquest look on.", 'cast': cast}
    return st
