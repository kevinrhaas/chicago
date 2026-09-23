1840 Chicago IPUMS name crosswalk — current validated tranche

Scope
- H_1840_chicago.csv contains 964 Chicago household records.
- The currently available name-bearing census scans are printed pages 234 and 235.
- Those two pages contain 55 head-of-household names.
- The remaining 909 IPUMS households are intentionally left unnamed rather than guessed.

How serials were attached
- The 1840 census left sheet records the head of household plus age-band tally marks.
- Each scan row was converted into a 26-column free-white age-band occupancy fingerprint.
- That fingerprint was compared with the corresponding IPUMS household variables.
- Page 234 resolves to the contiguous IPUMS serial block 5102083–5102113.
- Page 235 resolves to the contiguous IPUMS serial block 5102114–5102137.
- Census row order is not the same as IPUMS SERIAL order, so the crosswalk retains both census page/row and SERIAL.
- Most rows are exact fingerprint matches. A few have 1–2 image-cell mismatches but are resolved by block continuity. Page 234 row 31 is sequence-derived because the bottom total line contaminates the image.

Name confidence and serial-mapping confidence are separate:
- name_confidence = confidence reading the handwriting.
- serial_mapping_confidence = confidence attaching that census row to the IPUMS SERIAL.

Next step for all 964
Obtain either (a) the remaining Chicago 1840 name-bearing census left-sheet scans, or (b) a bulk/exported head-of-household index for Chicago from FamilySearch/Ancestry/AmericanAncestors. The same fingerprint/block method can then attach the remaining names without relying on OCR alone.
