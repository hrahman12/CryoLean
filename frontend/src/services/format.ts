import type { Constraint, Quantity, Requirement } from '../types/backend';
export function quantity(q?: Quantity | null): string { return q ? `${q.value} ${q.unit}` : 'Not supplied'; }
export function constraintText(c: Constraint): string {
  switch (c.kind) {
    case 'at_least': return `At least ${quantity(c.q)}`;
    case 'at_most': return `At most ${quantity(c.q)}`;
    case 'point_within': return `Must include ${quantity(c.q)}`;
    case 'range_within': return `${quantity(c.lo)} to ${quantity(c.hi)}`;
    case 'count_at_least': return `At least ${c.n}`;
    case 'count_equals': return `Exactly ${c.n}`;
    case 'flag_is': return c.b ? 'Required' : 'Must be absent';
    case 'present': return 'Must be present';
    case 'absent': return 'Must be absent';
    case 'enum_in': return `One of: ${c.allowed?.join(', ')}`;
    case 'set_contains': return `Requires: ${c.needed?.join(', ')}`;
    default: return c.kind.replaceAll('_', ' ');
  }
}
export const requirementKey = (r: Requirement) => r.keys?.join('|') ?? r.key ?? '';
export const humanize = (s: string) => s.replaceAll('_', ' ').replaceAll('.', ' · ');
export function safeUrl(url?: string): string | undefined {
  try { const u = new URL(url ?? ''); return ['https:', 'http:'].includes(u.protocol) ? u.href : undefined; } catch { return undefined; }
}
export const decimalPattern = /^[+-]?(?:\d+(?:\.\d*)?|\.\d+)$/;
