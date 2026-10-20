"""Differential-check original deterministic magnitude and target-terrain qualification."""
import json
from pathlib import Path
import frida
from verify_effect_terrain_native import GROUPS
from game_rng import GameRng

ROOT = Path(__file__).resolve().parents[1]
COEFFICIENTS = {0:7, 1:9, 2:5, 3:7, 4:9, 12:4, 14:2, 19:12, 22:5, 65:10, 66:0}
MAGNITUDE_EFFECTS = set(range(22)) | {22,33,34,35,36,38,64,65}


def power(value, tier):
    value = min(value, 400)
    if tier < 3:
        value = value * 7 // 10
    elif tier >= 4:
        value = value * 12 // 10
    return min(value, 400)


def expected(case):
    if case['effect'] not in MAGNITUDE_EFFECTS:
        return 0
    if case['effect'] < 20 and case['terrain'] not in GROUPS[case['effect']//5]:
        return 0
    if case['effect'] in (9, 21):
        return case['health']
    a = power(case['attack'], case['attack_tier'])
    d = power(case['defend'], case['defend_tier'])
    base = case['level'] + 25
    base = max(0, base - (d-a)//3) if a < d else base + (a-d)//3
    value = base * COEFFICIENTS[case['effect']] // 10
    if case['target_class'] in (39, 42, 43):
        value = value * 11 // 10
    elif case['target_class'] in (49, 50):
        value = value * 13 // 10
    return min(max(value, 1), case['resource'] if case['effect'] == 22 else case['health'])


def main():
    cases = []
    scenarios = [(60,40,30,3,3,100,50), (40,60,30,3,3,100,50),
                 (1,255,1,2,4,100,50), (255,1,50,4,2,3,2),
                 (100,100,10,3,3,0,0), (200,200,25,4,4,500,250)]
    for effect in [*COEFFICIENTS, 9, 21]:
        for a, d, level, at, dt, hp, mp in scenarios:
            for cls in (0,39,49):
                terrains=[min(GROUPS[effect//5]),255] if effect<20 else [0]
                for terrain in terrains:
                    cases.append(dict(effect=effect,attack=a,defend=d,level=level,
                                      attack_tier=at,defend_tier=dt,health=hp,resource=mp,
                                      target_class=cls,terrain=terrain))
    for effect in (0,1,3,4):
        for seed in range(32):
            for terrain in (0,255):
                cases.append(dict(effect=effect,attack=60,defend=40,level=30,
                                  attack_tier=3,defend_tier=3,health=100,resource=50,
                                  target_class=0,terrain=terrain,live=True,seed=seed))
    device = frida.get_local_device()
    lab = ROOT / 'analysis/runtime-game'
    pid = device.spawn([str(lab / 'Ekd5.exe')], cwd=str(lab))
    session = None
    try:
        session = device.attach(pid)
        script = session.create_script('''
rpc.exports = {verify(cases) {
  const b = Process.mainModule.base;
  const magnitude = new NativeFunction(b.add(0x3bfaa), 'uint',
      ['pointer','pointer','pointer','uint8','int'], 'thiscall');
  const attacker = b.add(0xb2c50), target = attacker.add(0x24);
  const map = Memory.alloc(0x641);map.writeByteArray(new Uint8Array(0x641));
  const view = b.add(0xaeb38);view.add(4).writeU32(0x641);
  view.add(12).writePointer(map);view.add(16).writeU8(1);
  b.add(0xb422c).writeU8(1);b.add(0xb422d).writeU8(1);
  const unitA = b.add(0xa1b68), unitD = unitA.add(0x48);
  return cases.map(t => {
    for (const unit of [unitA,unitD]) {
      unit.writeByteArray(new Uint8Array(0x48));
      for (const offset of [0x2e,0x31,0x34]) unit.add(offset).writeU8(255);
    }
    unitA.add(0x17).writeU8(t.attack); unitD.add(0x17).writeU8(t.defend);
    unitA.add(0x2c).writeU8(t.level); unitD.add(0x2b).writeU8(t.target_class);
    unitA.add(0x20).writeU8(50);
    unitA.add(0x19).writeU8(t.attack);unitD.add(0x19).writeU8(t.defend);
    attacker.writeByteArray(new Uint8Array(0x24));
    target.writeByteArray(new Uint8Array(0x24)); target.writeU32(1);
    target.add(4).writeU8(1);
    map.add(0x640).writeU8(t.terrain);
    attacker.add(0x1a).writeU8(t.attack_tier);
    target.add(0x1a).writeU8(t.defend_tier);
    attacker.add(0x1c).writeU8(3);target.add(0x1c).writeU8(3);
    target.add(0x10).writeU32(t.health); target.add(0x14).writeU32(t.resource);
    b.add(0xaf4c0 + t.effect * 70 + 15).writeU8(1);
    b.add(0x8ecd4).writeU32(t.seed || 0);
    const value=magnitude(attacker, target, unitD, t.effect, t.live ? 0 : 1);
    return {value,state:b.add(0x8ecd4).readU32()};
  });
}};
''')
        script.load()
        actual = script.exports_sync.verify(cases)
        if len(actual) != len(cases):
            raise ValueError('Native result count mismatch')
        rows=[]
        for case,native in zip(cases,actual):
            value=expected(case);rng=GameRng(case.get('seed',0))
            if case.get('live'):
                numerator,denominator={0:(1,1),1:(9,10),3:(4,5),4:(3,5)}[case['effect']]
                probability=95*numerator//denominator if case['terrain']==0 else 0
                if rng.chance(probability):
                    jitter=rng.bounded(7)
                    value=min(max(value+(-jitter if jitter<3 else jitter-2),1),case['health'])
                else:value=0
            rows.append(dict(**case,expected=value,actual=native['value'],
                expected_seed=rng.state,actual_seed=native['state'],
                match=value==native['value'] and rng.state==native['state']))
        (ROOT / 'analysis/native-combat-magnitude-validation.json').write_text(
            json.dumps(rows, indent=2), encoding='utf-8')
        print(f'Native combat magnitude: {sum(r["match"] for r in rows)}/{len(rows)}')
        if not all(r['match'] for r in rows):
            raise SystemExit(1)
    finally:
        device.kill(pid)
        if session is not None:
            try:
                session.detach()
            except frida.InvalidOperationError:
                pass


if __name__ == '__main__':
    main()
