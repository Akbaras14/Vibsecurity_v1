'use client';

import Link from 'next/link';
import { useParams } from 'next/navigation';
import { useResource } from '../../../../components/api';
import { findingText } from '../../../../components/finding-language.mjs';
import FindingDetail from '../../../../components/finding-detail';
import { ErrorBox, Loading, PageHead } from '../../../../components/ui';

export default function Finding() {
  const { id, findingId } = useParams();
  const data = useResource(`/scans/${encodeURIComponent(id)}/findings/${encodeURIComponent(findingId)}`);
  return <><Link className="back-link" href={`/scans/${id}`}>← Hasil pemindaian</Link><PageHead eyebrow="FINDING DETAILS" title={data.result ? findingText(data.result.data).title : 'Detail temuan'} />{data.error && <ErrorBox message={data.error} retry={data.reload} />}{data.loading && <Loading />}{data.result && <FindingDetail key={findingId} finding={data.result.data} scanId={id} reload={data.reload} />}</>;
}
