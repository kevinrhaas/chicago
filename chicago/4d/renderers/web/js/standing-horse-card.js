// SPDX-License-Identifier: GPL-3.0-or-later
// Modern asset credit is separate from historically graded animal claims.
export function standingHorseCard(row, spec) {
  const citations = [...new Set([...row.source_ids, spec.source.id, ...(spec.anatomy?.source_ids ?? [])])].map(source_id => {
    const source = spec.citation_records?.[source_id];
    if (!source?.citation || !source.url) throw Error('Standing horse citation does not resolve: ' + source_id);
    return { ...source, source_id };
  });
  return { id: row.id, sidecar: {
    name: row.name, phase: null,
    change_note: `A reconstructed, unidentified horse in the 1835 Western Hotel yard. Modern model credit (published ${spec.source.publication_date.slice(0, 4)}): ${spec.source.credit} This modern asset credit is not evidence of a particular 1835 horse, breed or owner.`,
    placement: { symbolic_location: row.location, position_confidence: 'reconstructed',
      position_sources: row.source_ids, position_note: row.note },
    attributes: {
      animal: { value: 'Standing horse; individual unidentified', confidence: 'reconstructed',
        sources: row.source_ids, note: 'Yard context supports horsekeeping; this individual is a reconstruction.' },
      breed_owner: { value: 'Unidentified', confidence: 'reconstructed', sources: [],
        note: 'No historical breed, owner, measured stature, coat or grooming is attested for this model.' },
      state: { value: 'Standing, unhitched, untied and unmounted', confidence: 'reconstructed', sources: [],
        note: row.animation?.enabled
          ? 'Gentle body weight shifts are reconstructed; hooves stay planted. This horse is unhitched and unmounted; walking and riding are not available.'
          : 'Idle activation awaits qualification; no halter, tie rope, harness, rider, driver, boarding, route or physical coupling is enabled.' },
      anatomy: { value: 'Reconstructed working horse', confidence: 'reconstructed',
        sources: spec.anatomy?.source_ids ?? [],
        note: 'Cleared anatomical studies and living-animal references guide the head and hoof surfaces. They do not identify an 1835 individual, breed, coat or owner.' },
    },
    citations,
    research_note: `${row.note} Modern model credit (${spec.source.publication_date.slice(0, 4)}): ${spec.source.credit}
      Proportions, coat, markings, grooming and resting pose are reconstructed. Anatomical references guide the refined eyelid and rounded hoof surfaces.
      ${spec.material_variants[row.material_variant].change_notice}`,
  } };
}
