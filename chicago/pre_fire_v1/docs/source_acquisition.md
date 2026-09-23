# Source and media acquisition notes

## Core text sources reviewed

- A. T. Andreas, *History of Chicago*, volumes I and II (1884–1885), Internet Archive identifiers `historyofchicago01andr` and `historyofchicago02andr`. Public domain scans and OCR were searched locally; OCR-sensitive names are flagged for scan review.
- The 1844 and 1846 Chicago directories and retrospective city narratives used by the decade researchers.
- National Park Service designation material, City of Chicago landmark records, Library of Congress catalog records, and institutional reference essays listed row-by-row in `data/sources.csv`.
- The supplied Chicago source guide, chronology, schema PDF, Word list, Numbers file, and workbook already present elsewhere in the repository. These were treated as guides and lead lists, not automatic evidence. Suspect dates or unsupported rows were independently checked or excluded.

## Map images

Local images are practical-size derivatives for the viewer. `maps/map_references.csv` records the canonical source page, rights statement, credit line, dimensions, and whether the item is a contemporary survey, pictorial view, engineering plan, or later reconstruction.

Library of Congress Geography and Map Division items are credited as requested by the catalog and were downloaded from records that state digitized collection content is free to use and reuse absent a contrary rights advisory. Wikimedia Commons items are limited to files marked public domain on their item pages.

For archival or georeferencing work, retrieve the highest-resolution master from the recorded source URL instead of upscaling the included derivative.

## Building images

Building images are stored in `media/images/buildings/` and indexed by `data/media.csv`. Creation date and depicted date are separate, and `representation_type` distinguishes photographs from retrospective lithographs, illustrations, postcards, and imagined reconstructions. `data/media_buildings.csv` is the subject join; its confidence belongs to the claimed building-image relationship rather than to the underlying building record.

The first building-image pass traced a Wolf Point blog article back to New York Public Library, Newberry/CARLI, *Chicago Magazine*, Andreas, Illinois Digital Archives, and Wikimedia Commons records. No Blogger-hosted file was copied. The modern George Yelich Wolf Point painting and Google Maps relocation graphic were excluded because no suitable reuse license was established.
