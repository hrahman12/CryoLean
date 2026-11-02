import type { EvidenceRecord } from '../types/backend';
import { safeUrl, humanize } from '../services/format';
import { ExternalLink } from 'lucide-react';

export function Evidence({ records }: { records: EvidenceRecord[] }) {
  if (!records.length) return <p className="muted">No source record supplied for this item.</p>;
  return <div className="evidence-list">{records.map((record, index) => <article key={`${record.id}-${index}`} className="evidence-record">
    <span className="eyebrow">{humanize(record.evidence_status ?? 'source record')}</span>
    <h4>{record.document_title || record.id}</h4>
    {record.location && <p className="muted">{record.location}</p>}
    {record.quote && <blockquote>{record.quote}</blockquote>}
    {safeUrl(record.source_url) && <a href={safeUrl(record.source_url)} target="_blank" rel="noreferrer">Open source <ExternalLink size={13} /></a>}
  </article>)}</div>;
}
