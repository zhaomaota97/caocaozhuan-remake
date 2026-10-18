/** Original selectors 0x43E572 and 0x43E515; verified against 512 native cases. */
export function idleFrame(direction: number, actorFlags: number, statusFlags: number, phase: number, injured = false): number {
  const bank = [1, 2, 0, 2][direction] ?? 0;
  const special = Boolean(actorFlags & 6);
  const base = injured ? 9 : special ? bank + 6 : bank * 2;
  return base + (special ? 0 : (statusFlags & 2) ? Number((phase >> 2) !== 0) : phase & 1);
}
