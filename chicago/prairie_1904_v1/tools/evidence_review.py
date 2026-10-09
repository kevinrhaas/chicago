"""Glessner's 1904 source-use contract (T-2198), applied to canonical streams.

Review state records what was actually inspected; rights remain an independent
restriction. No source in this audit authorizes geometry without dated corroboration.
"""
BUILDING = 'pa-1800-22'
EXCLUDED = {'disputed attribution', 'rejected design', 'unbuilt or preliminary design', 'interior context'}
USES = {'excluded', 'unreviewed', 'context only', 'corroborate with dated evidence'}
STATES = {'visually inspected', 'written document reviewed', 'text metadata inventoried',
          'unavailable image: catalog only', 'excluded: interior detail, metadata screened'}
ROLES = EXCLUDED | {'exterior reference', 'design documentation', 'measured documentation',
                   'streetscape or site context', 'text context', 'written documentation', 'secondary reconstruction'}
REQUIRED = ('ticket', 'reviewed_on', 'review_state', 'target_date', 'phase', 'date_basis',
            'evidence_role', 'geometry_use', 'reason', 'source_url', 'family_relationship')

def validate_reviews(records):
    errors, numbers = [], []
    by_id = {r['id']: r for r in records}
    for r in records:
        if BUILDING not in r.get('building_ids', []):
            continue
        rid, review = r['id'], r.get('evidence_review')
        def fail(message): errors.append(f'{rid}: evidence review {message}')
        if not isinstance(review, dict):
            fail('missing'); continue
        for field in REQUIRED:
            if not isinstance(review.get(field), str) or not review[field].strip(): fail(f'missing {field}')
        if review.get('review_state') not in STATES: fail('unknown review state')
        if review.get('evidence_role') not in ROLES: fail('unknown evidence role')
        if review.get('geometry_use') not in USES: fail('unknown geometry use')
        if review.get('target_date') != '1904-07-01': fail('wrong target date')
        if review.get('audit_number') is not None: numbers.append(review['audit_number'])
        if review.get('evidence_role') in EXCLUDED and review.get('geometry_use') != 'excluded': fail('excluded role permits geometry')
        if review.get('review_state', '').startswith('unavailable') and review.get('geometry_use') not in {'excluded', 'unreviewed'}: fail('unseen image permits geometry')
        if review.get('evidence_role') in {'secondary reconstruction', 'text context', 'streetscape or site context'} and review.get('geometry_use') not in {'context only', 'unreviewed'}: fail('context permits geometry')
        family = review.get('family')
        if family:
            members = review.get('family_members', [])
            if rid not in members or len(set(members)) < 2: fail('family needs this record and a related record')
            for member in members:
                other = by_id.get(member, {}).get('evidence_review', {})
                if other.get('family') != family or other.get('family_members') != members or other.get('family_relationship') != review.get('family_relationship'):
                    fail(f'inconsistent family member {member}')
    if sorted(numbers) != list(range(1, 169)):
        errors.append('Glessner evidence review must preserve all 168 original audit numbers exactly once')
    # These two determinations are hard exclusions, even if a future edit changes the role.
    for rid, role in [('a18-rba-lowe-glessner-stable-18th-c1900', 'disputed attribution'),
                      ('a18-rba-mf-glessner-f69', 'rejected design')]:
        review = by_id.get(rid, {}).get('evidence_review', {})
        if review.get('evidence_role') != role or review.get('geometry_use') != 'excluded':
            errors.append(f'{rid}: T-2198 quarantine must be retained pending a documented superseding review')
    return errors
