#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""T-3553: the adults tellings of the two 1812 story jaunts, with the fighting staged.

The owner, 2026-11-15: "add a jaunt for the 1812 thst shows battle of fort Dearborn with more of
the actual conflicts in place, the knifing of la lime, people being attacked, tomahawks, this one
is targeted at adults and shows everything incredibly graphically"; "Both the murder and battle
jaunts"; "We can alter some of these internal rules to accomplish this goal".

Each adults jaunt is a `version_of` its students' jaunt (audience 'adults', a content_warning,
hidden until the visitor says they are 18 or over), and plays the students' scenes (scenes.py,
built here in the same order, so every donor is the same) with the fighting added from the
accounts Kirkland (1893) prints: weapons in the hand (`arm`) and what is done with them (`act`:
strike, stab, aim, fire, lower, struck), the fallen going down where they are hit. Held even
here: no child is shown struck (the young man who climbs into the baggage wagon is shown
reaching it; the wagon's children stay seated), and what was done to the dead (White's wounds,
Wells's heart) is told, not shown. Who strikes whom, and when, beyond the accounts is
reconstruction (L-1812-adult-jaunts).

    python3 docs/RESEARCH/jaunt-stage-1812-3553/adults.py           # write both adults jaunts
    python3 docs/RESEARCH/jaunt-stage-1812-3553/adults.py --check   # the adults jaunts are as built
"""
import copy
import json
import math
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import build as b  # noqa: E402  (the helpers and the casting pools; importing writes nothing)
import scenes  # noqa: E402
from adult_texts import BATTLE, LALIME  # noqa: E402

ROOT = b.ROOT
LIBERTY = 'L-1812-adult-jaunts'
P, bearing = b.P, b.bearing
STRIKE_HIT, STAB_HIT = 0.6, 0.44           # human-fight.js MOTIONS: when a blow lands
SHOT = {'pistol': 0.7, 'musket': 0.8, 'rifle': 0.8}
HURRY = 2.2                                 # jaunt-stage.js PACES.hurry, m/s
WEST = scenes.SHORE_W                       # inland from the beach, toward the bank


# ── reading a scene ─────────────────────────────────────────────────────────────────────────
def key(c):
    return c.get('person') or c.get('extra')


def by_id(cast):
    return {key(c): c for c in cast}


def add(c, *beats):
    c.setdefault('beats', []).extend(beats)
    c['beats'].sort(key=lambda x: x['t'])


def drop(c, pred):
    c['beats'] = [x for x in c.get('beats', []) if not pred(x)]


def rest(c, t):
    """Where a castmate stands at `t`: the end of the last walk or place begun before it."""
    at = tuple(c['at'])
    for x in sorted(c.get('beats', []), key=lambda y: y['t']):
        if x['t'] > t: break
        if x.get('place'): at = tuple(x['place'])
        if x.get('walk'): at = tuple(x['walk'][-1])
    return at


def toward(a, z, gap):
    """The point `gap` metres short of z on the way from a."""
    d = math.hypot(z[0] - a[0], z[1] - a[1]) or 1.0
    return (z[0] + (a[0] - z[0]) * gap / d, z[1] + (a[1] - z[1]) * gap / d)


def dist(a, z):
    return math.hypot(z[0] - a[0], z[1] - a[1])


def r1(t):
    return round(t, 2)


# ── what a fight is made of ─────────────────────────────────────────────────────────────────
def falls(c, t, pose='fallen', ease=0.7, drop_arm=True):
    """Hit at `t`: the hands to the wound, then down."""
    hit = {'t': r1(t), 'act': 'struck'}
    if drop_arm: hit['arm'] = 'none'
    add(c, hit, {'t': r1(t + 0.35), 'pose': pose, 'ease': ease})


def wounded(c, t, pose=None, ease=0.9):
    """Hit at `t` and kept up (or down on a knee)."""
    add(c, {'t': r1(t), 'act': 'struck'})
    if pose: add(c, {'t': r1(t + 0.3), 'pose': pose, 'ease': ease})


def shoot(c, victim, t, gun='musket'):
    """`c` turns to `victim` (an id or a mark) and fires at `t`; returns when the ball lands."""
    add(c, {'t': r1(t - 0.6), 'face': victim, 'arm': gun}, {'t': r1(t), 'act': 'fire'}, {'t': r1(t + 1.5), 'act': 'lower'})
    return t + SHOT[gun] + 0.05


def close(att, victim_at, t, gap=1.05, pace='hurry', arm=None):
    """`att` runs from where he stands at `t` to `gap` short of `victim_at`; returns his arrival."""
    a = rest(att, t)
    spot = toward(a, victim_at, gap)
    beat = {'t': r1(t), 'walk': [P(*spot)], 'pace': pace}
    if arm: beat['arm'] = arm
    add(att, beat)
    return t + dist(a, spot) / (HURRY if pace == 'hurry' else 1.75) + 0.4


def blow(att, victim, t, kind='strike'):
    """`att` (already there) turns to `victim` and strikes or stabs at `t`; returns when it lands."""
    add(att, {'t': r1(t), 'face': key(victim), 'act': kind})
    return t + (STRIKE_HIT if kind == 'strike' else STAB_HIT)


def scalp(att, victim, t, side=(0.7, 0.3)):
    """The owner, 2026-11-15: "Yes scalpings did occur so we want to be honest about it". `att`
    goes to the fallen `victim` with his knife, kneels at him and cuts, and gets up; seen from the
    stop, not close to. Returns when he stands."""
    at = rest(victim, t)
    spot = (at[0] + side[0], at[1] + side[1])
    a = rest(att, t)
    add(att, {'t': r1(t), 'walk': [P(*spot)], 'pace': 'brisk', 'arm': 'knife'})
    there = t + dist(a, spot) / 1.75 + 0.5
    add(att, {'t': r1(there), 'face': key(victim), 'pose': 'kneel2', 'ease': 0.6})
    for j in range(3):
        add(att, {'t': r1(there + 0.9 + 0.8 * j), 'act': 'stab'})
    add(att, {'t': r1(there + 4.2), 'pose': 'stand', 'ease': 0.9})
    return there + 4.2


def nearest(pool, used, at, t=50, ok=lambda w: True):
    """The free fighter nearest `at` (at `t`), taken."""
    w = min((w for w in pool if key(w) not in used and ok(w)), key=lambda w: dist(rest(w, t), at))
    used.add(key(w))
    return w


def extra(name, at, heading, dress_of, beats=None, tier='desktop', pose=None, label=None):
    return b.member(f'extra:{name}', P(*at), heading=heading, pose=pose, dress='potawatomi_man_1812', dress_of=dress_of,
                    beats=beats, tier=tier, name=label or 'One of the warriors; name not recorded')


# ── the battle ──────────────────────────────────────────────────────────────────────────────
def hardscrabble(st):
    """Lee's place, 6 April: White and the Canadian come out, two of the men come out after
    them and shoot them down; one kneels over White with his knife (Heald: 'nine stabs with a
    knife in his breast'). The scalping and the rest are told."""
    cast = by_id(st['cast'])
    door = (-1649.0, -4237.5)
    white, cardin = cast['white_liberty'], cast['cardin_john_b']
    w_at, c_at = (-1653.6, -4233.4), (-1645.0, -4233.0)
    add(white, {'t': 66, 'place': P(*door), 'show': True}, {'t': 66.3, 'walk': [P(*w_at)]})
    add(cardin, {'t': 67, 'place': P(*door), 'show': True}, {'t': 67.3, 'walk': [P(*c_at)]})
    s1, s2 = cast['winnebago_05'], cast['winnebago_06']
    add(s1, {'t': 68.5, 'place': P(*door), 'show': True, 'arm': 'musket'}, {'t': 68.8, 'walk': [P(-1650.4, -4235.6)]})
    add(s2, {'t': 69.2, 'place': P(*door), 'show': True, 'arm': 'musket'}, {'t': 69.5, 'walk': [P(-1647.4, -4235.4)]})
    falls(white, shoot(s1, 'white_liberty', 74.5), pose='kneel2', ease=0.5)
    falls(cardin, shoot(s2, 'cardin_john_b', 76.0))
    add(white, {'t': 76.4, 'pose': 'fallen', 'ease': 0.8})
    # The four who sat by the door get up with their weapons; one goes to White with his knife.
    for i, arm in enumerate(('knife', 'tomahawk', 'club', 'tomahawk')):
        c = cast[f'winnebago_{i + 1:02d}']
        add(c, {'t': 70 + 0.3 * i, 'pose': 'stand', 'ease': 0.8, 'arm': arm})
    k = cast['winnebago_01']
    t = close(k, w_at, 77.5, gap=0.9, pace='brisk')
    add(k, {'t': r1(t), 'face': 'white_liberty', 'pose': 'kneel2', 'ease': 0.6})
    for j in range(4):
        blow(k, white, t + 0.8 + 1.0 * j, 'stab')
    close(cast['winnebago_02'], w_at, 78.5, gap=1.6, pace='brisk')
    # Heald: the Frenchman 'was only shot through the neck and scalped.'
    scalp(cast['winnebago_03'], cardin, 78.6)
    st['caption'] = "Watch the eleven men come to the cabin, the soldier and the boy slip away, and White and the Canadian shot down at the door."
    return st


def bank(st, killed):
    """The sand bank, 15 August: the volley from the bank, the company's one round and its
    charge with the bayonet, the fighting hand to hand, Hays and Nau-non-gee, Ronan on one knee,
    Van Voorhis, Mrs. Helm and Black Partridge, the militia cut down at the wagons and a young
    man reaching the baggage wagon."""
    cast = st['cast']
    ids = by_id(cast)
    regulars = [c for c in cast if key(c) in scenes.SOLDIERS]
    warriors = [c for c in cast if key(c) in b.MEN]
    # The warriors take up their weapons as they rise: one in three a gun (the volley), the rest
    # tomahawks and war clubs, a few knives.
    kinds = ['musket', 'tomahawk', 'club', 'musket', 'tomahawk', 'knife', 'musket', 'tomahawk', 'club']
    arm_of = {}
    for i, c in enumerate(warriors):
        arm_of[key(c)] = kinds[i % len(kinds)]
        add(c, {'t': r1(36.4 + 0.25 * (i % 13)), 'arm': arm_of[key(c)]})
    # 'Scarcely were the words uttered when a volley was showered from among the sand-hills.'
    guns = [c for c in warriors if arm_of[key(c)] == 'musket']
    for i, c in enumerate(guns):
        t = 46.0 + 0.23 * (i % 11)
        add(c, {'t': r1(t), 'act': 'fire'}, {'t': r1(t + 1.6), 'act': 'lower'})
    regs = [c for c in cast if key(c) in scenes.SOLDIERS]
    for i, c in enumerate(guns):
        mark = rest(c, 50)
        aim = min(regs, key=lambda s: dist(rest(s, 58), mark))
        t = 59.0 + 1.37 * (i % 13)
        add(c, {'t': r1(t - 0.6), 'face': key(aim)}, {'t': r1(t), 'act': 'fire'}, {'t': r1(t + 1.6), 'act': 'lower'})
    # The company: muskets up as they face the bank, 'after firing one round, we charged'.
    vet = None
    for i, c in enumerate(regulars):
        add(c, {'t': r1(40.5 + 0.1 * (i % 7)), 'arm': 'musket'})
        if vet is None and key(c) in killed and i > 6:
            vet = c  # 'One man, a veteran of seventy winters, fell as they ascended.'
            falls(c, 47.4)
            continue
        t = 49.2 + 0.17 * (i % 9)
        add(c, {'t': r1(t), 'act': 'fire'}, {'t': r1(t + 1.4), 'act': 'lower'})
        up = rest(c, 48)
        charge = (up[0] + 8.0 * WEST[0], up[1] + 8.0 * WEST[1])
        add(c, {'t': r1(52.2 + 0.1 * (i % 5)), 'walk': [P(*charge)], 'pace': 'hurry'})
    heald = ids['heald_nathan']
    add(heald, {'t': 40.5, 'arm': 'pistol'})
    shoot(heald, P(*scenes.shore(-12, 36)), 49.4, 'pistol')
    hp = rest(heald, 48)
    add(heald, {'t': 52.4, 'walk': [P(hp[0] + 7.0 * WEST[0], hp[1] + 7.0 * WEST[1])], 'pace': 'hurry'})
    # Wells fires his pistols into the bank, and one of the men there falls.
    wells = ids['wells_william']
    add(wells, {'t': 40.2, 'arm': 'pistol'})
    near = sorted(guns, key=lambda c: dist(rest(c, 47), rest(wells, 41)))
    target = near[0]
    shoot(wells, P(*rest(target, 47)), 46.5, 'pistol')
    falls(target, shoot(wells, key(target), 52.0, 'pistol'))
    add(wells, {'t': 56.0, 'walk': [P(*scenes.shore(-36.0, 16.0))], 'pace': 'hurry'})

    # Hand to hand where the charge meets the bank: each charging man meets the nearest of the
    # tomahawks and clubs who runs down at him. A man whose card says he was killed in the action
    # goes down; a man who lived puts his man down with the bayonet (Heald gives the warriors' loss
    # as 'about fifteen').
    used = {key(target)}
    melee = [c for c in warriors if arm_of[key(c)] in ('tomahawk', 'club', 'knife')]
    hays = ids.get('hays_otho')
    fights, scalpers = 0, []
    for i, s in enumerate(regulars):
        if s is vet or s is hays or fights >= 16: continue
        end = rest(s, 60)
        phone = s.get('tier') != 'desktop'
        pool = [w for w in melee if key(w) not in used and (w.get('tier') != 'desktop') == phone and dist(rest(w, 50), end) < 26]
        if not pool: continue
        w = min(pool, key=lambda w: dist(rest(w, 50), end))
        used.add(key(w)); fights += 1
        arrive = max(close(w, end, 52.6 + 0.2 * (fights % 4), gap=1.1), 52.2 + 8.0 / HURRY + 0.4) + 0.3 + 0.55 * (fights % 7)
        if key(s) in killed:
            falls(s, blow(w, s, arrive, 'strike'))
            if len(scalpers) < 6: scalpers.append((w, s, arrive + 2.5))
        else:
            blow(w, s, arrive, 'strike')
            add(s, {'t': r1(arrive + 0.9), 'face': key(w)})
            falls(w, blow(s, w, arrive + 1.2, 'stab'))
    # Sergeant Hays and Nau-non-gee: 'After Hays had received a ball through the body, this Indian
    # ran up to tomahawk him, when the Sergeant ... pierced him through the body with his bayonet.
    # They fell together. Other Indians running up soon dispatched Hays'.
    if hays:
        hp = rest(hays, 60)
        wounded(hays, 56.2)
        nau_at = (hp[0] + 14.0 * WEST[0], hp[1] + 14.0 * WEST[1])
        nau = b.member('naunongee', P(*nau_at), heading=bearing(nau_at, hp), pose='kneel', tier='desktop', beats=[
            {'t': 37.0, 'pose': 'stand', 'ease': 1.1, 'arm': 'tomahawk'}])
        t = close(nau, hp, 55.0, gap=1.05)
        add(nau, {'t': r1(t), 'face': 'hays_otho', 'act': 'strike'})
        add(hays, {'t': r1(t + 0.05), 'face': 'naunongee', 'act': 'stab'})
        falls(nau, t + 0.05 + STAB_HIT, ease=0.9)
        add(hays, {'t': r1(t + 0.9), 'pose': 'kneel2', 'ease': 0.8})
        finisher = nearest(melee, used, hp, ok=lambda w: w.get('tier') == 'desktop')
        t2 = close(finisher, hp, t + 0.6, gap=1.05)
        falls(hays, blow(finisher, hays, t2, 'strike'))
        cast.append(nau)
    # Ensign Ronan, 'mortally wounded and nearly down, was still fighting with desperation on one knee'.
    ronan = ids['ronan_george']
    wounded(ronan, 58.5, pose='kneel')
    rp = rest(ronan, 60)
    foe = nearest(melee, used, rp)
    t = close(foe, rp, 60.0, gap=1.1)
    add(ronan, {'t': r1(t - 0.4), 'face': key(foe), 'act': 'stab'})
    blow(foe, ronan, t + 1.0, 'strike')
    falls(ronan, blow(foe, ronan, t + 2.6, 'strike'))
    # Van Voorhis: 'His horse was shot under him and he had received a ball in his leg.' Then
    # 'Some murderous tomahawk had stretched him upon the very spot'.
    vv = ids['van_voorhis_isaac']
    wounded(vv, 48.6, pose='kneel2')
    vp = rest(vv, 50)
    foe = nearest(melee, used, vp, ok=lambda w: arm_of[key(w)] == 'tomahawk')
    falls(vv, blow(foe, vv, close(foe, vp, 64.0, gap=1.05), 'strike'))

    # The rear: the militia and the families. 'a deadlier combat ... was raging around the wagons';
    # the militia 'were cut down to a man'.
    rear = [c for c in cast if key(c) in ('burns_thomas', 'lee_charles', 'simmons_david', 'cooper_joseph') or key(c).startswith('chicago_militia_unnamed')]
    tail = sorted([w for w in melee if key(w) not in used], key=lambda w: scenes.SHORE_S[0] * rest(w, 50)[0] + scenes.SHORE_S[1] * rest(w, 50)[1])
    for i, m in enumerate(rear):
        add(m, {'t': r1(44.0 + 0.3 * i), 'arm': 'musket'})
        mp = rest(m, 50)
        phone = m.get('tier') != 'desktop'
        pool = [w for w in tail if key(w) not in used and (w.get('tier') != 'desktop') == phone] or [w for w in tail if key(w) not in used]
        w = min(pool, key=lambda w: dist(rest(w, 50), mp))
        used.add(key(w))
        t = close(w, mp, 50.0 + 1.3 * i, gap=1.1)
        shoot(m, P(*rest(w, 50)), max(50.5 + 1.3 * i, t - 2.2), 'musket')
        falls(m, blow(w, m, t + 0.3, 'strike'))
        if key(m) == 'cooper_joseph' or i % 3 == 1: scalpers.append((w, m, t + 3.0))
        if i % 2 == 0: blow(w, m, t + 2.1, 'strike')
    # The dead are scalped where they fall: the British commander at Malden 'bought the scalps of
    # our murdered garrison'; Cooper's daughter 'saw her father's scalp in the hands of an Indian
    # afterward'.
    for w, v, t in scalpers:
        scalp(w, v, t)
    # Cicely, 'Mrs. Heald's negro serving-woman', among the dead.
    cic = ids.get('cicely')
    if cic:
        w = nearest(tail, used, rest(cic, 50))
        falls(cic, blow(w, cic, close(w, rest(cic, 50), 63.0, gap=1.05), 'strike'))
    # Mrs. Helm: 'a young Indian raised his tomahawk at me ... which alighted on my shoulder. I
    # seized him around the neck ... I was dragged from his grasp by another and an older Indian.
    # The latter bore me struggling and resisting toward the lake.' It was Black Partridge.
    helm = ids['helm_margaret']
    mp = rest(helm, 50)
    young = nearest(melee, used, mp, ok=lambda w: arm_of[key(w)] == 'tomahawk' and w.get('tier') == helm.get('tier'))
    t = close(young, mp, 61.0, gap=1.0)
    wounded(helm, blow(young, helm, t, 'strike'))
    add(helm, {'t': r1(t + 1.0), 'face': key(young)})
    bp_at = (mp[0] + 16.0 * WEST[0] - 3.0 * scenes.SHORE_S[0], mp[1] + 16.0 * WEST[1] - 3.0 * scenes.SHORE_S[1])
    bp = b.member('black_partridge', P(*bp_at), heading=bearing(bp_at, mp), pose='kneel', tier='desktop', beats=[
        {'t': 37.5, 'pose': 'stand', 'ease': 1.1}])
    t2 = close(bp, mp, t - 2.0, gap=0.8)
    add(young, {'t': r1(t2 + 0.6), 'walk': [P(mp[0] - 5.0 * scenes.SHORE_S[0], mp[1] - 5.0 * scenes.SHORE_S[1])], 'pace': 'brisk'})
    lake = (mp[0] - 9.5 * WEST[0], mp[1] - 9.5 * WEST[1])   # the waterline, abreast of where she was
    add(bp, {'t': r1(t2 + 1.0), 'walk': [P(lake[0] + 0.7, lake[1])], 'pace': 'brisk'})
    add(helm, {'t': r1(t2 + 1.1), 'walk': [P(*lake)], 'pace': 'brisk'}, {'t': r1(t2 + 8.0), 'pose': 'kneel', 'ease': 1.0},
        {'t': r1(t2 + 8.2), 'face': 'black_partridge'})
    add(bp, {'t': r1(t2 + 8.4), 'face': 'helm_margaret'})
    cast.append(bp)
    # The baggage wagon with the children: one young man reaches its tail with his tomahawk. What
    # he did is the stop's text (Mrs. Helm: 'tomahawked the children of the entire group'); no
    # child is shown struck.
    team = st['teams'][1]
    tail_at = tuple(team['beats'][0]['walk'][-1])
    ahead = math.radians(team['heading'])
    behind = (tail_at[0] - 2.6 * math.sin(ahead), tail_at[1] - 2.6 * math.cos(ahead))
    w = nearest(tail, used, behind, ok=lambda w: arm_of[key(w)] == 'tomahawk')
    t = close(w, behind, 66.0, gap=0.2)
    add(w, {'t': r1(t), 'heading': round(math.degrees(ahead) % 360, 1)})
    st['caption'] = ("Watch the volley from the bank, the soldiers fire and charge, the fighting hand to hand, "
                     "Mrs. Helm carried to the lake, and the militia cut down at the wagons.")
    return st


def cottonwoods(st):
    """Half past ten: Wells comes to his niece, takes her hand, is pinned, fires, and is shot;
    Mrs. Heald is hit; then (the students' scene, later) Black Bird comes out to Heald."""
    cast = st['cast']
    cast[:] = [c for c in cast if key(c) != 'wells_william']
    DT = 44.0
    for c in cast:
        for x in c.get('beats', []):
            x['t'] = r1(x['t'] + DT)
    heald = (1167.5, -3465.0)
    W = (heald[0] + 18.0, heald[1] + 14.0)
    mrs = b.member('heald_rebekah', P(*W), heading=50)
    w0 = (W[0] + 15.0, W[1] + 9.0)
    wells = b.member('wells_william', P(*w0), face=W, beats=[{'t': 0.0, 'arm': 'pistol'}])
    hand = (W[0] + 0.9, W[1] + 0.5)
    add(wells, {'t': 1.0, 'walk': [P(*hand)], 'pace': 'slow'})
    there = 1.0 + dist(w0, hand) / 0.9 + 0.5
    add(wells, {'t': r1(there), 'face': 'heald_rebekah'}, {'t': r1(there + 0.6), 'greet': True},
        {'t': r1(there + 1.6), 'talk': True}, {'t': r1(there + 9.0), 'talk': False})
    add(mrs, {'t': r1(there - 1.0), 'face': 'wells_william'}, {'t': r1(there + 0.6), 'greet': True})
    down = there + 10.0
    add(wells, {'t': r1(down), 'pose': 'kneel2', 'ease': 0.6, 'heading': 50})
    men = b.take(b.MEN, 4, stride=31, offset=13)
    foes = []
    for i, d in enumerate(men):
        a = (W[0] + 34.0 + 2.0 * i, W[1] + 26.0 - 2.5 * i)
        z = (W[0] + 10.0 + 1.6 * i, W[1] + 7.0 - 1.2 * i)
        arm = 'musket' if i in (0, 3) else 'tomahawk'
        c = extra(f'wells_foe_{i + 1}', a, bearing(a, z), d, tier=None if i < 2 else 'desktop',
                  beats=[{'t': 0.0, 'arm': arm}, {'t': r1(there - 4.0 + 0.6 * i), 'walk': [P(*z)]}])
        foes.append(c)
    # 'He took aim and fired, killing one of them.'
    falls(foes[1], shoot(wells, 'wells_foe_2', down + 2.0, 'pistol'))
    # 'Captain Wells put his hand back and held up his head that better aim might be taken, and
    # then cried "Shoot away!" The Indian fired, the shot being fatal.'
    falls(wells, shoot(foes[0], 'wells_william', down + 8.0, 'musket'), pose='fallen', ease=0.9)
    # They close round him; what was done is the stop's text.
    add(foes[0], {'t': r1(down + 11.0), 'walk': [P(hand[0] - 1.1, hand[1] + 0.6)]}, {'t': r1(down + 14.0), 'face': 'wells_william', 'pose': 'crouch', 'ease': 0.9})
    # Mrs. Helm later saw 'a scalp which, by the black ribbon around the queue,' she knew for Wells's.
    scalp(foes[2], wells, down + 10.5, side=(0.6, -0.5))
    # Mrs. Heald 'got up in range of the bullets coming from Indians on both sides of her ... she
    # was wounded in six places'.
    wounded(mrs, shoot(foes[3], 'heald_rebekah', down + 12.0, 'musket'), pose='kneel2', ease=0.7)
    add(mrs, {'t': r1(down + 18.0), 'pose': 'sit', 'ease': 1.4})
    cast.extend([mrs, wells] + foes)
    st['caption'] = "Watch Wells come to his niece and take her hand, and fall; then Black Bird come out to Heald's last men."
    return st


# ── the murder ──────────────────────────────────────────────────────────────────────────────
def the_gate(st):
    """Sunset, outside the gate (Porthier: 'We heard the pistol go off and saw the smoke. Then
    they fell down together.' Mrs. Kinzie via Hubbard: the ball cut the side of Kinzie's neck;
    'Mr. Kinzie, closing with Lalime, stabbed him'. Porthier: 'he (Lalime) pulled out his dirk,
    and as they fell he was stabbed with his own knife.')"""
    cast = by_id(st['cast'])
    k, l = cast['kinzie_john_elder'], cast['lalime_john']
    away = next(x for x in k['beats'] if x['t'] == 28)
    drop(k, lambda x: x['t'] >= 19)
    drop(l, lambda x: x['t'] >= 19)
    add(l, {'t': 17.4, 'arm': 'pistol'})
    hit = shoot(l, 'kinzie_john_elder', 18.2, 'pistol')
    l['beats'] = [x for x in l['beats'] if x.get('act') != 'lower']
    wounded(k, hit)
    lp = rest(l, 18)
    add(k, {'t': r1(hit + 0.5), 'walk': [P(*toward(rest(k, 18), lp, 0.62))], 'pace': 'brisk'})
    add(l, {'t': r1(hit + 0.9), 'arm': 'knife'})
    # the knife changes hands as they close: Lalime's dirk, in Kinzie's fist
    add(l, {'t': r1(hit + 2.1), 'arm': 'none', 'act': 'struck'})
    add(k, {'t': r1(hit + 2.1), 'arm': 'knife', 'face': 'lalime_john'})
    for j in range(3):
        blow(k, l, hit + 2.3 + 0.95 * j, 'stab')
    down = hit + 5.2
    add(k, {'t': r1(down), 'pose': 'kneel2', 'ease': 0.9})
    add(l, {'t': r1(down), 'pose': 'kneel2', 'ease': 0.8}, {'t': r1(down + 1.2), 'heading': 250}, {'t': r1(down + 1.4), 'pose': 'lie', 'ease': 1.8})
    add(k, {'t': r1(down + 5.0), 'pose': 'stand', 'ease': 1.4, 'arm': 'none'}, dict(away, t=r1(down + 7.0)))
    for c in (cast['helm_linai'], cast['irwin_matthew']):
        for x in c.get('beats', []):
            if x['t'] >= 30: x['t'] = r1(x['t'] + 4.0)
    st['caption'] = "Watch Kinzie and Lalime outside the gate at sunset: the pistol, the knife, and the two men going down together."
    return st


# ── the documents ───────────────────────────────────────────────────────────────────────────
def on_dev(path):
    try:
        raw = subprocess.run(['git', 'show', f'origin/dev:chicago/4d/{b.rel(path)}'], cwd=ROOT, capture_output=True, text=True, check=True).stdout
        return json.loads(raw)['content_version']
    except Exception:
        return None


def adult_doc(base_name, stages, texts):
    base = json.loads((ROOT / f'data/jaunts/{base_name}.json').read_text())
    doc = copy.deepcopy(base)
    doc['id'] = texts['id']
    doc['version_of'] = base['id']
    doc['audience'] = 'adults'
    doc['content_warning'] = texts['content_warning']
    doc['featured'] = False
    doc.pop('menu_rank', None)
    doc['title'] = texts['title']
    doc['premise'] = texts['premise']
    if texts.get('opening'):
        doc['opening']['text'] = texts['opening']
    else:
        paras = base['opening']['text'].split('\n\n')
        doc['opening']['text'] = '\n\n'.join(paras[:-1] + [texts['opening_add'], paras[-1]])
    doc['opening']['read_s'] = round(len(doc['opening']['text'].split()) / 3.5)
    doc['grade_band'] = texts['grade_band']
    claims = {c['id'] for c in doc['evidence']}
    for c in texts['evidence']:
        if c['id'] in claims: raise SystemExit(f"{doc['id']}: claim {c['id']} already in the base jaunt")
        doc['evidence'].append(c)
    for stop in doc['stops']:
        t = texts['stops'].get(stop['id'])
        if t:
            stop['text'] = t['text']
            stop['read_s'] = t.get('read_s', stop['read_s'])
            stop['evidence'] = stop['evidence'] + [e for e in t.get('evidence', []) if e not in stop['evidence']]
        stop.pop('stage', None)
        if stop['id'] in stages:
            s = stages[stop['id']]
            for c in s['cast']:
                who = c.get('person')
                if who and not b.castable(who):
                    raise SystemExit(f'{doc["id"]}/{stop["id"]}: {who} has no figure in 1812')
            stop['stage'] = {'caption': s['caption'], 'liberty': LIBERTY, 'cast': s['cast']}
            if s.get('teams'): stop['stage']['teams'] = s['teams']
    doc['liberties'] = [x for x in doc['liberties'] if x != b.LIBERTY] + [b.LIBERTY, LIBERTY]
    path = ROOT / f'data/jaunts/{doc["id"]}.json'
    v = on_dev(path)
    doc['content_version'] = 1 if v is None else v + 1
    order = ['schema_version', 'content_version', 'category', 'menu_group', 'grade_band', 'featured', 'review_required', 'id',
             'version_of', 'audience', 'content_warning']
    out = {k: doc[k] for k in order if k in doc}
    out.update({k: v for k, v in doc.items() if k not in out})
    return path, out


def write(check=False):
    battle = scenes.battle(b)
    lalime = scenes.lalime(b)          # the students' order: every donor as in their jaunts
    killed, _ = scenes.fates(b)
    hardscrabble(battle['hardscrabble'])
    bank(battle['the-bank'], killed)
    cottonwoods(battle['cottonwoods'])
    the_gate(lalime['the-gate'])
    stale = []
    for name, stages, texts in (('battle-of-fort-dearborn', battle, BATTLE), ('killing-of-jean-lalime', lalime, LALIME)):
        path, doc = adult_doc(name, stages, texts)
        body = json.dumps(doc, indent=2, ensure_ascii=False) + '\n'
        if check:
            if not path.exists() or path.read_text() != body: stale.append(b.rel(path))
        else:
            path.write_text(body)
            print(f'wrote {b.rel(path)}: {sum(len(s["cast"]) for s in stages.values())} castmates on {len(stages)} stops')
    if stale:
        raise SystemExit('stale: ' + ', '.join(stale) + '; run adults.py')


if __name__ == '__main__':
    write('--check' in sys.argv)
