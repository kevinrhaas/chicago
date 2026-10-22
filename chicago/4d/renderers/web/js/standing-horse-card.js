// SPDX-License-Identifier: GPL-3.0-or-later
// Modern asset credit is separate from historically graded animal claims.
export function standingHorseCard(row, spec) {
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
          ? 'Gentle head/tail idle is reconstructed; no independent ear, body weight shift, walking, halter, tie rope, harness, rider, driver, boarding, route or physical coupling is enabled.'
          : 'Idle activation awaits qualification; no halter, tie rope, harness, rider, driver, boarding, route or physical coupling is enabled.' },
    },
    citations: [...row.source_ids, spec.source.id].map(source_id => ({ source_id })),
    research_note: `${row.note} Modern model credit (${spec.source.publication_date.slice(0, 4)}): ${spec.source.credit} Model adaptations: uniform reconstructed metre scale, source-origin wrapper,
      declared whole-root support rotation, yard placement and source-derived reconstructed head/tail idle. Original six clips never autoplay. ${spec.material_variants[row.material_variant].change_notice}`,
  } };
}
