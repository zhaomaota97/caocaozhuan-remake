import type { Unit } from '../model/battle';

export interface AttackResult { supported: false; reason: string; }

export function resolveAttack(_attacker: Unit, _defender: Unit, _criticalChance = 0): AttackResult {
  return { supported: false, reason: 'verified native combat pipeline has not yet been migrated into the standalone runtime' };
}

export function adjacent(a: Unit, b: Unit): boolean {
  return Math.max(Math.abs(a.x - b.x), Math.abs(a.y - b.y)) <= 1;
}
