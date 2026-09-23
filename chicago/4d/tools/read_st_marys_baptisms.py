#!/usr/bin/env python3
"""Read St Mary's baptismal register 1833-1835 off its eleven deposited page images.

WHAT THIS IS. `chicago/reference/catholic-baptisms-1833-1835/` holds eleven
FamilySearch page images (`S3HT-DHG9-*.jpg`) of the register Father John Mary
Irenaeus St. Cyr opened at Chicago in May 1833. They are the ONLY primary record
this project has that names a family together — a child, two parents and two
sponsors on one dated line — and until T-0503 nothing had been read out of them.

The deposit is READ-ONLY and no scan or render is ever committed. What is committed
is this file: the reading itself, held as a table, with `--build` emitting the
records and the claims and `--check` proving the emitted JSON is still exactly what
this table says. A hand-edit of the JSON is therefore a gate failure, which is the
point — the transcription and the artifact cannot drift apart.

THE CROSSWALK HAS A SECOND INPUT and it moves: `data/residents/`. The records and
the claims are this table alone, but the crosswalk holds the reading against the
town, so it goes stale whenever the town gains people — which it did, 849 to 1,308,
between T-0503 and T-1110. That is not a hand edit and not a changed tool, and
`--check` now says which of the three it is (`_why_it_differs`) instead of naming two
and leaving the reader to guess. Staleness is answered by `--build`; a hand edit
would be a ruling a rebuild erases.

THE GRADE. Every row here is `scan_verified`: read off the page image, not out of a
transcription. That is the higher of the two readings this project recognises and it
is why these rows outrank the marriage register's, which came through the Illinois
Catholic Historical Review by way of Genealogy Trails.

`as_read` keeps the clerk's own spelling, his Latin and French forms, his
abbreviations (`8bre` October, `9bre` November, `10bre` December) and his
inconsistencies. An unread letter is `[?]`; a word read with real doubt carries the
doubt in `notes` and drops the row's confidence to `inferred`. `normalized` is this
project's spelling of the same person and is never merged back into `as_read`.

WHAT THE REGISTER IS NOT. A baptism documents a person at a font on a day. It is not
a residence, not an address and not an occupation. Nothing here mints or regrades a
resident; T-0514 and T-0515 do that, from the consolidation.

AND IT IS NOT ALL CHICAGO. Entries 1-11 of 1834 were written on St. Cyr's journey
back from St. Louis, at Bear Creek, the South Fork of the Sangamon and Springfield,
in Sangamon County. Those rows carry `at_chicago: false` themselves — the same trap
the marriage page set, and the reason `data/research/church/README.md` warns about it.
"""

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOMAIN = ROOT / "data" / "research" / "church"
RECORDS = DOMAIN / "records" / "st_marys_baptisms_1833_1835.json"
CLAIMS = DOMAIN / "claims" / "st_marys_baptisms_town_findings.json"
CROSSWALK = DOMAIN / "st_marys_baptisms_crosswalk.json"

SOURCE_ID = "st_marys_baptismal_register_1833_1835"
LIST_ID = "st_marys_baptisms_1833_1835"

PRIEST = "J. M. I. Saint Cyr"

# The eleven images, in the order the book runs. Each carries a two-page opening;
# the page numbers are the ones written in the book's own top corners. The order was
# established by reading the entry numbers and the catchwords across the openings —
# the deposit's filenames carry no order at all.
IMAGES = [
    ("S3HT-DHG9-SLR", ["flyleaf", "title"],
     "The flyleaf (blank) and the title page: 'Actus Baptismi. 1833, 1834. Baptisms "
     "& marriages', with a hue-and-cry note below it in the same hand."),
    ("S3HT-DHG9-SKB", ["stray", "1"],
     "A stray later leaf (entries 130-133, 1837-1838, faded almost to nothing) "
     "opposite PAGE 1, which carries the first four baptisms ever entered at Chicago."),
    ("S3HT-DHG9-SK8", ["2", "3"], "Pages 2-3: 1833 entries 4-10."),
    ("S3HT-DHG9-S1B", ["4", "5"], "Pages 4-5: 1833 entries 11-17."),
    ("S3HT-DHG9-SKM", ["6", "7"],
     "Page 6: 1833 entries 18-19, the year's own tally, and one 1849 entry (no. 40) "
     "in Father O'Meara's later hand. Page 7 opens the 1834 Sangamon County journey."),
    ("S3HT-DHG9-9YM", ["8", "9"], "Pages 8-9: 1834 entries 5-11, Sangamon County."),
    ("S3HT-DHG9-SKW", ["10", "11"], "Pages 10-11: 1834 entries 11-17, Chicago from entry 12."),
    ("S3HT-DHG9-S1C", ["12", "13"], "Pages 12-13: 1834 entries 18-23."),
    ("S3HT-DHG9-ST3", ["14", "15"], "Pages 14-15: 1834 entries 23-24 and its tally; 1835 entries 1-4."),
    ("S3HT-DHG9-SJ8", ["16", "17"], "Pages 16-17: 1835 entries 5-9."),
    ("S3HT-DHG9-926", ["18", "19"], "Pages 18-19: 1835 entries 10-14, and the year's tally."),
]

CHI = "Chicago, Cook County, Illinois"

# --------------------------------------------------------------------------- #
# THE READING. One dict is one entry of the register.
#
#   no        the number the clerk wrote beside the entry (he restarts each year)
#   img/page  where it stands
#   date      ISO, as far as the entry itself fixes it; `dp` is the precision
#   dc        the date's confidence — `inferred` where the day had to be reasoned
#   place     the place the entry is written under
#   chi       True when that place is Chicago
#   lang      the language the entry is written in
#   read      the entry read out, in the clerk's own words, lightly lineated
#   ppl       (role, as_read, normalized, confidence, note) — one per named person
#   note      what the entry does not say, and what a later reader must not assume
# --------------------------------------------------------------------------- #

D = "documented"
I = "inferred"

ENTRIES = [
    # ------------------------------ 1833 ------------------------------------
    dict(year=1833, no=1, img="S3HT-DHG9-SKB", page="1", date="1833-05-22", dp="day",
         dc=D, place=CHI, chi=True, lang="fr",
         read="Le 22 de mai mil huit [cent] trente trois, je soussigné ai baptisé George "
              "Beaubien fils de Mark Beaubien et de Monique Nadeau, né le 19 août 1832. "
              "Parrain a été Mark Beaubien père de l'enfant baptisé; marraine Archange "
              "Beaubien nièce du père de l'enfant. J. M. I. Saint Cyr, prêtre.",
         ppl=[("child", "George Beaubien", "George Beaubien", D, "Born 19 August 1832."),
              ("father", "Mark Beaubien", "Mark Beaubien", D, ""),
              ("mother", "Monique Nadeau", "Monique Nadeau", D, ""),
              ("godfather", "Mark Beaubien", "Mark Beaubien", D,
               "The entry says he stood as godfather to his own child: 'parrain a été "
               "Mark Beaubien père de l'enfant baptisé'."),
              ("godmother", "Archange Beaubien", "Archange Beaubien", D,
               "Named as 'nièce du père de l'enfant' — niece of the child's father.")],
         note="THE FIRST BAPTISM ENTERED IN THE BOOK, and the first Catholic baptism "
              "recorded at Chicago. The page is headed '1er Page' and the margin reads "
              "'Chicago, Cook Co.'"),
    dict(year=1833, no=2, img="S3HT-DHG9-SKB", page="1", date="1833-05-26", dp="day",
         dc=D, place=CHI, chi=True, lang="en",
         read="On the 26th of may eighteen hundred thirty three I, the undersigned, "
              "baptised Joseph son of Michel Mayo and of Marguerit Malore[?] born the "
              "5[?] of 9ber 1832. Sponsors were Joseph Laframboise and Archange Beaubien.",
         ppl=[("child", "Joseph", "Joseph Mayo", I,
               "The child is entered by forename only; the surname is taken from the "
               "father in the same line and is therefore inferred, not read."),
              ("father", "Michel Mayo", "Michel Mayo", I,
               "The surname is struck through and rewritten; 'Mayo' is the legible form."),
              ("mother", "Marguerit Malore[?]", "Marguerite Malore", I,
               "The surname is written over an erasure and the last two letters are not "
               "certain."),
              ("sponsor", "Joseph Laframboise", "Joseph Laframboise", D, ""),
              ("sponsor", "Archange Beaubien", "Archange Beaubien", D, "")],
         note="The birth date is written over a struck passage and reads as the 5th of a "
              "month abbreviated 9ber (November) 1832; neither figure is certain and the "
              "date of birth is not carried forward."),
    dict(year=1833, no=3, img="S3HT-DHG9-SKB", page="1", date="1833-06-03", dp="day",
         dc=D, place=CHI, chi=True, lang="fr",
         read="Le 3 juin mil huit cent trente trois, je soussigné ai baptisé Augustin "
              "Pottier fils de Jean Potier et de Victoire Madera, né le 26 de mai 1832. "
              "Parrain a été Augustin Bonné, marraine Monique Nadeau.",
         ppl=[("child", "Augustin Pottier", "Augustin Pottier", D, "Born 26 May 1832."),
              ("father", "Jean Potier", "Jean Pottier", D,
               "The clerk spells the child 'Pottier' and the father 'Potier' in the same "
               "sentence; both spellings are kept."),
              ("mother", "Victoire Madera", "Victoire Madera", D, ""),
              ("godfather", "Augustin Bonné", "Augustin Bonné", D, ""),
              ("godmother", "Monique Nadeau", "Monique Nadeau", D, "")],
         note=""),
    dict(year=1833, no=4, img="S3HT-DHG9-SKB", page="1", date="1833-06-05", dp="day",
         dc=D, place=CHI, chi=True, lang="en",
         read="On the fifth June eighteen hundred and thirty three I, the undersigned, "
              "baptised Caroline daughter of Baptist Beaubien and Josette Laframboise, "
              "born the tenth of August eighteen hundred thirty two. Sponsors were John "
              "Whistler and Esther Bailly.",
         ppl=[("child", "Caroline", "Caroline Beaubien", I,
               "Forename only in the entry; the surname is the father's and is inferred."),
              ("father", "Baptist Beaubien", "Jean Baptiste Beaubien", D, ""),
              ("mother", "Josette Laframboise", "Josette Laframboise", D, ""),
              ("sponsor", "John Whistler", "John Whistler", D, ""),
              ("sponsor", "Esther Bailly", "Esther Bailly", D, "")],
         note="The entry begins at the foot of page 1 and finishes at the head of page 2."),
    dict(year=1833, no=5, img="S3HT-DHG9-SK8", page="2", date="1833-06-05", dp="day",
         dc=D, place=CHI, chi=True, lang="en",
         read="On [the] fifth of June eighteen hundred and thirty three, I the "
              "undersigned, baptised Marguerit daughter of Salomon Juneau and Josette "
              "Vieau, born the 25th of December 1832. Sponsors were Louis Franchère and "
              "Elozina[?] Bailly.",
         ppl=[("child", "Marguerit", "Marguerite Juneau", I,
               "Forename only; the surname is the father's and is inferred."),
              ("father", "Salomon Juneau", "Solomon Juneau", D, ""),
              ("mother", "Josette Vieau", "Josette Vieau", D, ""),
              ("sponsor", "Louis Franchère", "Louis Franchère", D, ""),
              ("sponsor", "Elozina[?] Bailly", "Elozina Bailly", I,
               "The forename is written small and the middle letters are not certain.")],
         note="Salomon Juneau of Milwaukee stands here as a father, not a sponsor; he "
              "sponsors three later entries."),
    dict(year=1833, no=6, img="S3HT-DHG9-SK8", page="2", date="1833-06-05", dp="day",
         dc=D, place=CHI, chi=True, lang="en",
         read="On the fifth of June eighteen hundred and thirty [three] I, the "
              "undersigned [baptised] John David son of William Dird[?] and [of] "
              "Lieu[?] born the twentieth of October 1832. Sponsors were Mathias Smith. "
              "There was no godmother.",
         ppl=[("child", "John David", "John David Dird", I,
               "Two forenames and no surname; the surname is the father's and is inferred."),
              ("father", "William Dird[?]", "William Dird", I,
               "The surname is four letters and the middle two are not certain; 'Dird', "
               "'Bird' and 'Died' are all readable from the hand."),
              ("mother", "Lieu[?]", "Lieu", I,
               "One short word, heavily abbreviated, and the reading is not secure. It is "
               "recorded as it stands rather than guessed at."),
              ("sponsor", "Mathias Smith", "Mathias Smith", D, "")],
         note="THE ENTRY SAYS THERE WAS NO GODMOTHER, in those words. An absent sponsor "
              "is a fact the register states here, not a hole in the reading."),
    dict(year=1833, no=7, img="S3HT-DHG9-SK8", page="2", date="1833-06", dp="month",
         dc=I, place="Ottawa", chi=False, lang="en",
         read="On the [twenty?] seventh of June eighteen hundred and thirty three, I the "
              "undersigned, performed the ceremonies of baptism on Francise son of "
              "Francise Nowbonnois and Josette Ashkam, of Ottaway, born in the year "
              "eighteen hundred and twenty seventh. Sponsors were Augustin Bonné and "
              "Monique Nadeau.",
         ppl=[("child", "Francise", "François Nowbonnois", I,
               "Forename only; the surname is the father's and is inferred. The clerk "
               "writes the same form for father and son."),
              ("father", "Francise Nowbonnois", "François Nowbonnois", D, ""),
              ("mother", "Josette Ashkam", "Josette Ashkam", D,
               "The clearest of this surname's several spellings in the book; the same "
               "family is written Aspam on pages 4-5 and in 1835."),
              ("sponsor", "Augustin Bonné", "Augustin Bonné", D, ""),
              ("sponsor", "Monique Nadeau", "Monique Nadeau", D, "")],
         note="THE DAY IS NOT SETTLED. The figure is written over itself and reads as "
              "either the seventh or the twenty-seventh; the entries either side are the "
              "5th and the 17th of June, which favours the seventh but does not settle "
              "it, because this book is not strictly chronological. The margin reads "
              "'Ottawa' and the entry 'of Ottaway' — which may be the Odawa nation or the "
              "place on the Illinois; the entry does not say, and this row does not "
              "choose. Not counted as a Chicago entry."),
    dict(year=1833, no=8, img="S3HT-DHG9-SK8", page="3", date="1833-06-17", dp="day",
         dc=D, place=CHI, chi=True, lang="fr",
         read="Le 17 juin mil huit cent trente trois, je soussigné ai baptisé Marie "
              "Josette fille de Jacob Vieau et de Matanacqua, née aux environs du 16 de "
              "février mil huit cent trente trois. Parrain et marraine furent Solomon "
              "Juneau et Monique Nadeau.",
         ppl=[("child", "Marie Josette", "Marie Josette Vieau", I,
               "Two forenames and no surname; the surname is the father's and is inferred."),
              ("father", "Jacob Vieau", "Jacob Vieau", D, ""),
              ("mother", "Matanacqua", "Matanacqua", D,
               "A single Indigenous name, written without a surname and without a "
               "baptismal forename."),
              ("godfather", "Solomon Juneau", "Solomon Juneau", D, ""),
              ("godmother", "Monique Nadeau", "Monique Nadeau", D, "")],
         note="The birth is given as 'aux environs du 16 de février' — about the 16th — "
              "and the approximation is the clerk's own."),
    dict(year=1833, no=9, img="S3HT-DHG9-SK8", page="3", date="1833-07-14", dp="day",
         dc=D, place=CHI, chi=True, lang="en",
         read="On the fourteenth of July eighteen hundred & thirty three I, the "
              "undersigned, baptised Mary and Catherine daughters of John Wode and "
              "Mariana Kamenwith[?] born the 16th July 1833. Sponsors were Jacob Jolly "
              "and Catherine Harrington.",
         ppl=[("child", "Mary", "Mary Wode", I,
               "Forename only; the surname is the father's and is inferred. One of two "
               "children baptised in this single entry."),
              ("child", "Catherine", "Catherine Wode", I,
               "Forename only; the surname is the father's and is inferred. The second of "
               "the two."),
              ("father", "John Wode", "John Wode", D, ""),
              ("mother", "Mariana Kamenwith[?]", "Mariana Kamenwith", I,
               "The surname is long, unfamiliar and the last syllable is not certain."),
              ("sponsor", "Jacob Jolly", "Jacob Jolly", D, ""),
              ("sponsor", "Catherine Harrington", "Catherine Harrington", D, "")],
         note="TWO CHILDREN IN ONE ENTRY — 'Mary and Catherine daughters of' — which is "
              "why the margin of page 6 totals twenty where the year's own pencil tally "
              "counts nineteen entries. The birth is written as the 16th of July, two "
              "days AFTER the baptism; the entry contradicts itself and the birth date is "
              "not carried forward."),
    dict(year=1833, no=10, img="S3HT-DHG9-SK8", page="3", date="1833-07-26", dp="day",
         dc=D, place=CHI, chi=True, lang="fr",
         read="Le 26 juillet mil huit cent trente trois, je soussigné ai baptisé Joseph "
              "Létendre fils de Baptiste Létendre et [de] O'Waichiquoi, né le vingt huit "
              "de mai mil huit cent trente [trois]. Parrain et marraine ont été Solomon "
              "Juneau et Josette Vieau.",
         ppl=[("child", "Joseph Létendre", "Joseph Létendre", D, "Born 28 May 1833."),
              ("father", "Baptiste Létendre", "Baptiste Létendre", D, ""),
              ("mother", "O'Waichiquoi", "O'Waichiquoi", D,
               "A single Indigenous name, written without a surname."),
              ("godfather", "Solomon Juneau", "Solomon Juneau", D, ""),
              ("godmother", "Josette Vieau", "Josette Vieau", D, "")],
         note=""),
    dict(year=1833, no=11, img="S3HT-DHG9-S1B", page="4", date="1833-08-18", dp="day",
         dc=D, place=CHI, chi=True, lang="en",
         read="On the eighteenth of August eighteen hundred and thirty three, I the "
              "undersigned, baptised Louis son of Andrew and of Adelaide Bouchard born "
              "the 4th December 1830. Sponsors were Augustin Bonné and Josette Chevalier.",
         ppl=[("child", "Louis", "Louis Bouchard", I,
               "Forename only; the surname is the father's and is inferred."),
              ("father", "Andrew [Bouchard]", "Andrew Bouchard", D,
               "The clerk writes 'Andrew and of Adelaide Bouchard', carrying the surname "
               "once for both parents."),
              ("mother", "Adelaide Bouchard", "Adelaide Bouchard", D, ""),
              ("sponsor", "Augustin Bonné", "Augustin Bonné", D, ""),
              ("sponsor", "Josette Chevalier", "Josette Chevalier", D, "")],
         note="The margin reads '8th august 1833' against a text reading 'the eighteenth "
              "of August'; the text is followed."),
    dict(year=1833, no=12, img="S3HT-DHG9-S1B", page="4", date="1833-08-18", dp="day",
         dc=D, place=CHI, chi=True, lang="en",
         read="On the same day eighteen hundred and thirty three I, the undersigned, "
              "baptised Isabelle[?] daughter of Andrew and Adelaide Bouchard, born the "
              "eighth of May eighteen hundred & thirty three. Sponsors were Augustin "
              "Bonné and Josette Chevalier.",
         ppl=[("child", "Isabelle[?]", "Isabelle Bouchard", I,
               "The forename is written small and the first syllable is not certain; the "
               "surname is the father's and is inferred."),
              ("father", "Andrew [Bouchard]", "Andrew Bouchard", D, ""),
              ("mother", "Adelaide Bouchard", "Adelaide Bouchard", D, ""),
              ("sponsor", "Augustin Bonné", "Augustin Bonné", D, ""),
              ("sponsor", "Josette Chevalier", "Josette Chevalier", D, "")],
         note="'On the same day' — the day of entry 11, 18 August 1833. Two children of "
              "one household baptised together."),
    dict(year=1833, no=13, img="S3HT-DHG9-S1B", page="4", date="1833-08", dp="month",
         dc=I, place=CHI, chi=True, lang="fr",
         read="Le trente [unième] d'août mil huit cent trente trois, je soussigné ai "
              "baptisé François Lafambise fils de Joseph Laframboise et de Jacquet "
              "Peltier, né le 1er août mil huit cent trente trois. Parrain et marraine "
              "ont été Mark Beaubien et Josette Laframboise.",
         ppl=[("child", "François Lafambise", "François Laframboise", D,
               "The clerk contracts the surname to 'Lafambise' for the child and writes "
               "it out for the father in the next line. Born 1 August 1833."),
              ("father", "Joseph Laframboise", "Joseph Laframboise", D, ""),
              ("mother", "Jacquet Peltier", "Jacquette Peltier", D,
               "Written 'Jacquet'; the same woman is 'Thérèse Jacquet Peltier' in 1834 "
               "entry 15 and 'Thérèse Peltier Laframboise' in 1834 entry 23."),
              ("godfather", "Mark Beaubien", "Mark Beaubien", D,
               "Signs the entry in his own hand in the margin: 'M. Beaubien'."),
              ("godmother", "Josette Laframboise", "Josette Laframboise", D,
               "Signs the entry in her own hand in the margin: 'Jose Laframboise'.")],
         note="THE DAY IS NOT SETTLED: the ordinal is written as 'trente' with a "
              "superscript that reads as 'unième' but is smudged, so the entry is dated "
              "to the month only. Two of the town's own people SIGN this entry — Mark "
              "Beaubien and Josette Laframboise — which is the earliest autograph in the "
              "book after the priest's."),
    dict(year=1833, no=14, img="S3HT-DHG9-S1B", page="4", date="1833-10", dp="month",
         dc=I, place=CHI, chi=True, lang="fr",
         read="Le [quatre?] octobre mil huit cent trente trois, je soussigné ai baptisé "
              "Jean Baptiste fils d'Antoine Aspam et de Marianne (sauvage) né le 15 "
              "octobre 1831. Parrain et marraine ont été Augustin Bonné et Monique Nodeau.",
         ppl=[("child", "Jean Baptiste", "Jean Baptiste Aspam", I,
               "Two forenames and no surname; the surname is the father's and is inferred."),
              ("father", "Antoine Aspam", "Antoine Aspam", I,
               "The surname's second letter is an s or an sh ligature and its fourth is a "
               "p or a k: the same family is written 'Ashkam' on page 2. The reading is "
               "recorded as it stands and no spelling is preferred."),
              ("mother", "Marianne (sauvage)", "Marianne", D,
               "The clerk's own parenthesis. 'Sauvage' is his word for an Indigenous "
               "woman and it is kept in as_read because it is the register's own "
               "vocabulary; it is not this project's."),
              ("sponsor", "Augustin Bonné", "Augustin Bonné", D,
               "Signs in the margin: 'Aug. Bonné'."),
              ("sponsor", "Monique Nodeau", "Monique Nadeau", D,
               "Signs in the margin: 'Mo. Nodeau'. Written 'Nodeau' here and 'Nadeau' "
               "elsewhere in the same hand.")],
         note="The day figure runs into the month word and is not legible; the entry is "
              "dated to October 1833 only. It begins at the foot of page 4 and its "
              "sponsors are at the head of page 5."),
    dict(year=1833, no=15, img="S3HT-DHG9-S1B", page="5", date="1833-10-04", dp="day",
         dc=D, place=CHI, chi=True, lang="fr",
         read="Le 4 octobre mil huit cent trente trois, je soussigné ai baptisé Catherine "
              "fille d'Alexis Gagnier et d'Angel[ique] Aspam, née le 1er décembre mil "
              "huit cent trente. Parrain et marraine ont été Augustin Bonné et Monique "
              "Nodeau.",
         ppl=[("child", "Catherine", "Catherine Gagnier", I,
               "Forename only; the surname is the father's and is inferred."),
              ("father", "Alexis Gagnier", "Alexis Gagnier", D, ""),
              ("mother", "Angel[ique] Aspam", "Angélique Aspam", I,
               "The forename is abbreviated and the surname is the family written "
               "'Ashkam' on page 2; neither spelling is preferred here."),
              ("sponsor", "Augustin Bonné", "Augustin Bonné", D, "Signs in the margin."),
              ("sponsor", "Monique Nodeau", "Monique Nadeau", D, "Signs in the margin.")],
         note=""),
    dict(year=1833, no=16, img="S3HT-DHG9-S1B", page="5", date="1833-10-08", dp="day",
         dc=D, place=CHI, chi=True, lang="fr",
         read="Le huit octobre mil huit cent trente trois, je soussigné ai baptisé "
              "Susanne fille de François Tranche[?] et de Josette Aspam, née [le] 15 "
              "octobre 1831. Parrain et marraine ont été Jean Baptiste Lavigne et "
              "Monique Beaubien.",
         ppl=[("child", "Susanne", "Susanne Tranche", I,
               "Forename only; the surname is the father's and is inferred."),
              ("father", "François Tranche[?]", "François Tranche", I,
               "The surname is written over a struck word and is not certain; the same "
               "man appears again in 1835 entry 6 with the same wife and the same "
               "difficulty."),
              ("mother", "Josette Aspam", "Josette Aspam", I,
               "The family written 'Ashkam' on page 2."),
              ("godfather", "Jean Baptiste Lavigne", "Jean Baptiste Lavigne", D,
               "Signs in the margin: 'J. B. Lavigne'."),
              ("godmother", "Monique Beaubien", "Monique Beaubien", D,
               "Signs in the margin. Monique Nadeau, wife of Mark Beaubien, is written "
               "under her married name here; the merge is not made in this file.")],
         note=""),
    dict(year=1833, no=17, img="S3HT-DHG9-S1B", page="5", date="1833-10-08", dp="day",
         dc=D, place=CHI, chi=True, lang="fr",
         read="Le huit october mil huit cent trente trois, je soussigné ai baptisé "
              "Magdelene fille d'Antoine Aspam et de Marianne (sauvage) née le vingt neuf "
              "mars[?] mil huit cent trente trois. Parrain et marraine ont été Jean "
              "Baptiste Lavigne et Josette Aspam.",
         ppl=[("child", "Magdelene", "Magdeleine Aspam", I,
               "Forename only; the surname is the father's and is inferred."),
              ("father", "Antoine Aspam", "Antoine Aspam", I,
               "The same father as entry 14; the same uncertain surname."),
              ("mother", "Marianne (sauvage)", "Marianne", D, "The clerk's own parenthesis."),
              ("godfather", "Jean Baptiste Lavigne", "Jean Baptiste Lavigne", D, ""),
              ("godmother", "Josette Aspam", "Josette Aspam", I,
               "The same woman who is a mother in entry 16, standing as godmother here.")],
         note="The clerk writes the month in English — 'october' — inside a French entry."),
    dict(year=1833, no=18, img="S3HT-DHG9-SKM", page="6", date="1833-10-10", dp="day",
         dc=D, place=CHI, chi=True, lang="fr",
         read="Le 10 d'octobre mil huit cent trente trois, je soussigné ai baptisé "
              "Susanne fille de Paul Vieaux et de Jaespquaa (sauvage de Green Bay), née "
              "le dix mai mil huit cent trente un. Parrain et marraine ont été Joseph "
              "Beaubien et Monique Nadeau.",
         ppl=[("child", "Susanne", "Susanne Vieaux", I,
               "Forename only; the surname is the father's and is inferred."),
              ("father", "Paul Vieaux", "Paul Vieau", D,
               "Written 'Vieaux' here and 'Vieau' for Jacob and Josette elsewhere."),
              ("mother", "Jaespquaa (sauvage de Green Bay)", "Jaespquaa", I,
               "An Indigenous name written phonetically by a French speaker; the middle "
               "letters are not certain. The parenthesis is the clerk's."),
              ("godfather", "Joseph Beaubien", "Joseph Beaubien", D, "Signs in the margin."),
              ("godmother", "Monique Nadeau", "Monique Nadeau", D, "Signs in the margin.")],
         note="THE ONLY ORIGIN THE BOOK EVER GIVES FOR A MOTHER: 'sauvage de Green Bay'. "
              "It places her, not the household, and no residence follows from it."),
    dict(year=1833, no=19, img="S3HT-DHG9-SKM", page="6", date="1833-10-20", dp="day",
         dc=D, place=CHI, chi=True, lang="fr",
         read="Le vingt d'octobre mil huit cent trente trois, je soussigné ai baptisé "
              "Joseph Chevalier né dans le mois de mai mil huit cent trente [?] à la "
              "rivière au Sable. J. M. I. Saint Cyr, prêtre. À Chicago.",
         ppl=[("child", "Joseph Chevalier", "Joseph Chevalier", D,
               "Born in May, at the Rivière au Sable; the year's last figure is struck "
               "through and unread.")],
         note="NO PARENTS AND NO SPONSORS ARE NAMED — the only entry of the year that "
              "names nobody but the child and the priest. It closes 1833; the margin "
              "reads 'total 20' and a later pencil hand has written '1833: 19 Bapt' "
              "beneath. Both are right: nineteen entries, twenty children, because entry "
              "9 baptised two. THE PLACE OF BIRTH — 'à la rivière au Sable', the Sable "
              "River — is a place named by the register and is filed as a town finding."),
    # ------------------------------ 1834 ------------------------------------
    dict(year=1834, no=1, img="S3HT-DHG9-SKM", page="7", date="1834-05", dp="month",
         dc=I, place="Bear Creek, Sangamon County, Illinois", chi=False, lang="en",
         read="On the fifth of mai eighteen hundred and thirty four I the undersigned, "
              "baptised John son of Matthew and Elisabeth Logdson three months old. "
              "Sponsors were John Durbin and Louisa Simps[on].",
         ppl=[("child", "John", "John Logdson", I,
               "Forename only; the surname is the parents' and is inferred. Three months old."),
              ("father", "Matthew [Logdson]", "Matthew Logdson", D, ""),
              ("mother", "Elisabeth Logdson", "Elisabeth Logdson", D, ""),
              ("sponsor", "John Durbin", "John Durbin", D, ""),
              ("sponsor", "Louisa Simps[on]", "Louisa Simpson", I,
               "The surname runs off the ruled line and its ending is not legible.")],
         note="NOT CHICAGO. The page is headed 'Bear Creek, State of Illinois, Sangamon "
              "Co. 1834. 15 mai' and this is the first of eleven entries St. Cyr wrote in "
              "Sangamon County on his way back from St. Louis. The heading says 15 May "
              "and the entry says the fifth; the two are not reconciled here and the "
              "entry is dated to the month."),
    dict(year=1834, no=2, img="S3HT-DHG9-SKM", page="7", date="1834-05", dp="month",
         dc=I, place="Bear Creek, Sangamon County, Illinois", chi=False, lang="en",
         read="On the same day, I the undersigned baptised Elisabette daughter of "
              "Sylvester and of Ann Vinter, three months old. Sponsors were Philipp "
              "Durbin and Elis[abeth] Logdson.",
         ppl=[("child", "Elisabette", "Elisabeth Vinter", I,
               "Forename only; the surname is the parents' and is inferred."),
              ("father", "Sylvester [Vinter]", "Sylvester Vinter", D, ""),
              ("mother", "Ann Vinter", "Ann Vinter", D, ""),
              ("sponsor", "Philipp Durbin", "Philipp Durbin", D, ""),
              ("sponsor", "Elis[abeth] Logdson", "Elisabeth Logdson", D, "Abbreviated by the clerk.")],
         note="NOT CHICAGO — Bear Creek, Sangamon County."),
    dict(year=1834, no=3, img="S3HT-DHG9-SKM", page="7", date="1834-05", dp="month",
         dc=I, place="Bear Creek, Sangamon County, Illinois", chi=False, lang="en",
         read="On the same day I the undersigned, baptised Marguerit daughter of Philipp "
              "Durbin and of Elisabeth Durbin four months old. Sponsors were James "
              "Logdson and Marguerit Durbin.",
         ppl=[("child", "Marguerit", "Marguerite Durbin", I,
               "Forename only; the surname is the parents' and is inferred."),
              ("father", "Philipp Durbin", "Philipp Durbin", D, ""),
              ("mother", "Elisabeth Durbin", "Elisabeth Durbin", D, ""),
              ("sponsor", "James Logdson", "James Logdson", D, ""),
              ("sponsor", "Marguerit Durbin", "Marguerite Durbin", D, "")],
         note="NOT CHICAGO — Bear Creek, Sangamon County."),
    dict(year=1834, no=4, img="S3HT-DHG9-SKM", page="7", date="1834-05", dp="month",
         dc=I, place="Bear Creek, Sangamon County, Illinois", chi=False, lang="en",
         read="On the same day I the undersigned baptised Patience daughter of John Meeds "
              "and of Oro[?] Durbin three months old. Sponsors were —",
         ppl=[("child", "Patience", "Patience Meeds", I,
               "Forename only; the surname is the father's and is inferred."),
              ("father", "John Meeds", "John Meeds", D, ""),
              ("mother", "Oro[?] Durbin", "Oro Durbin", I,
               "The forename is three or four letters and is not certain.")],
         note="TRUNCATED BY THE DEPOSIT. The entry runs to the foot of page 7 and stops at "
              "'Sponsors were'; page 8 opens with entry 5. The sponsors' names stood on "
              "the last ruled line of page 7, which the scan's frame cuts off. They are "
              "not illegible — they are NOT IN THE DEPOSIT, and this is the one place in "
              "the eleven images where the reading is incomplete. NOT CHICAGO."),
    dict(year=1834, no=5, img="S3HT-DHG9-9YM", page="8", date="1834-05", dp="month",
         dc=I, place="Bear Creek, Sangamon County, Illinois", chi=False, lang="en",
         read="On the same day I, the undersigned, baptised Ann daughter of Thomas Durbin "
              "and of Susanna Johnson, nine months old. Sponsors were William Durbin and "
              "Ann Durbin.",
         ppl=[("child", "Ann", "Ann Durbin", I,
               "Forename only; the surname is the father's and is inferred."),
              ("father", "Thomas Durbin", "Thomas Durbin", D, ""),
              ("mother", "Susanna Johnson", "Susanna Johnson", D, ""),
              ("sponsor", "William Durbin", "William Durbin", D, "Signs in the margin: 'W. Durbin'."),
              ("sponsor", "Ann Durbin", "Ann Durbin", D, "Signs in the margin: 'A. Durbin'.")],
         note="NOT CHICAGO — Bear Creek, Sangamon County."),
    dict(year=1834, no=6, img="S3HT-DHG9-9YM", page="8", date="1834-05-25", dp="day",
         dc=D, place="South Fork of the Sangamon, Sangamon County, Illinois",
         chi=False, lang="en",
         read="On the twenty fifth of May eighteen hundred and thirty four I, the "
              "undersigned baptised Isaak son of John Johnson and of Marguerit Durbin, "
              "born the thirtieth of November eighteen hundred and thirty three. Sponsors "
              "were Philipp Durbin and Elisabeth Durbin.",
         ppl=[("child", "Isaak", "Isaac Johnson", I,
               "Forename only; the surname is the father's and is inferred. Born 30 "
               "November 1833."),
              ("father", "John Johnson", "John Johnson", D, ""),
              ("mother", "Marguerit Durbin", "Marguerite Durbin", D, ""),
              ("sponsor", "Philipp Durbin", "Philipp Durbin", D, "Signs in the margin."),
              ("sponsor", "Elisabeth Durbin", "Elisabeth Durbin", D, "Signs in the margin.")],
         note="NOT CHICAGO. A new heading stands above this entry: 'South Fork of "
              "Sangamon Co. State of Illinois. 1834.'"),
    dict(year=1834, no=7, img="S3HT-DHG9-9YM", page="8", date="1834-05-25", dp="day",
         dc=D, place="South Fork of the Sangamon, Sangamon County, Illinois",
         chi=False, lang="en",
         read="On the same day, I the undersigned, baptised Thomas Kinkie son of Henry "
              "Winkie and of Ana Cery, born the eighth of april 1834. Sponsors were "
              "Samuel Hendriks and Cicily McKinzie.",
         ppl=[("child", "Thomas Kinkie", "Thomas Kinkie", D, "Born 8 April 1834."),
              ("father", "Henry Winkie", "Henry Kinkie", I,
               "The clerk writes the child 'Kinkie' and the father 'Winkie' in the same "
               "sentence, and signs the margin of entry 8 'H. Kinkie'; the initial letter "
               "is the same shape both times and one of the two readings is wrong."),
              ("mother", "Ana Cery", "Ana Cery", I,
               "The surname is short and its first letter could be a C or an E."),
              ("sponsor", "Samuel Hendriks", "Samuel Hendriks", D, ""),
              ("sponsor", "Cicily McKinzie", "Cicily McKinzie", I,
               "Written 'Cicily' here, 'Cicey' in entry 8, and the surname 'McKinzie' and "
               "'MacKinzie'.")],
         note="NOT CHICAGO. Begins at the foot of page 8 and ends at the head of page 9."),
    dict(year=1834, no=8, img="S3HT-DHG9-9YM", page="9", date="1834-05-25", dp="day",
         dc=D, place="South Fork of the Sangamon, Sangamon County, Illinois",
         chi=False, lang="en",
         read="On the same day, I the undersigned Baptised Marguerit daughter of Samuel "
              "Henriks and of Mary Durbin, born the thirteenth of December 1833. Sponsors "
              "were Henry Kinkie and Cicey MacKinzie.",
         ppl=[("child", "Marguerit", "Marguerite Henriks", I,
               "Forename only; the surname is the father's and is inferred. Born 13 "
               "December 1833."),
              ("father", "Samuel Henriks", "Samuel Hendriks", I,
               "Written 'Hendriks' as a sponsor in entry 7 and 'Henriks' as a father here."),
              ("mother", "Mary Durbin", "Mary Durbin", D, ""),
              ("sponsor", "Henry Kinkie", "Henry Kinkie", D, "Signs in the margin: 'H. Kinkie'."),
              ("sponsor", "Cicey MacKinzie", "Cicily McKinzie", I,
               "Signs in the margin: 'C. McKinzie'.")],
         note="NOT CHICAGO — South Fork of the Sangamon."),
    dict(year=1834, no=9, img="S3HT-DHG9-9YM", page="9", date="1834-05-29", dp="day",
         dc=D, place="Springfield, Sangamon County, Illinois", chi=False, lang="en",
         read="On twenty ninth of may eighteen hundred and thirty four I the undersigned "
              "Baptised Elisabeth daughter of Thomas Potts and of [blank] Meskal, three "
              "months old. Sponsors were William Alvey and Catherine Trewin.",
         ppl=[("child", "Elisabeth", "Elisabeth Potts", I,
               "Forename only; the surname is the father's and is inferred."),
              ("father", "Thomas Potts", "Thomas Potts", D, ""),
              ("mother", "[blank] Meskal", "Meskal", I,
               "THE CLERK LEFT THE FORENAME BLANK — a gap of about an inch is ruled and "
               "never filled. The surname alone stands, and a surname alone is not a "
               "person here."),
              ("sponsor", "William Alvey", "William Alvey", D, "Signs in the margin: 'W. Alvey'."),
              ("sponsor", "Catherine Trewin", "Catherine Trewin", I,
               "Signs in the margin: 'C. Trewin'. The surname could be Trewin or Irewin.")],
         note="NOT CHICAGO. A third heading stands above this entry: 'Springfield "
              "Sangamon Co. 1834.'"),
    dict(year=1834, no=10, img="S3HT-DHG9-9YM", page="9", date="1834-05-29", dp="day",
         dc=D, place="Springfield, Sangamon County, Illinois", chi=False, lang="en",
         read="On the same I the undersigned baptised William son of William Alvey and of "
              "Magdlen Lawton, three months old. Sponsors were John Mary Saint Cyr and "
              "Emelie Potts.",
         ppl=[("child", "William", "William Alvey", I,
               "Forename only; the surname is the father's and is inferred."),
              ("father", "William Alvey", "William Alvey", D, ""),
              ("mother", "Magdlen Lawton", "Magdalen Lawton", D, ""),
              ("sponsor", "John Mary Saint Cyr", "John Mary Irenaeus Saint Cyr", D,
               "THE PRIEST STANDS AS SPONSOR TO A CHILD HE IS BAPTISING — the first of "
               "three times he does so in this book."),
              ("sponsor", "Emelie Potts", "Emelie Potts", D, "")],
         note="NOT CHICAGO — Springfield."),
    dict(year=1834, no=11, img="S3HT-DHG9-9YM", page="9", date="1834-05-29", dp="day",
         dc=D, place="Springfield, Sangamon County, Illinois", chi=False, lang="en",
         read="On the same day I the undersigned baptised Aline Florille[?] daughter of "
              "John Louis [?] and of Sohibie Rountry[?], six months old. Godfather was "
              "William Alvey and there was no godmother.",
         ppl=[("child", "Aline Florille[?]", "Aline Florille", I,
               "The second forename is not certain."),
              ("father", "John Louis [?]", "John Louis", I,
               "The surname is at the page turn and is not legible; only the two "
               "forenames can be read."),
              ("mother", "Sohibie Rountry[?]", "Sohibie Rountry", I,
               "Neither name is certain; both are read letter by letter and neither is a "
               "form this project has seen elsewhere."),
              ("godfather", "William Alvey", "William Alvey", D, "Signs in the margin: 'W. Alvey'.")],
         note="NOT CHICAGO. The entry runs across the page turn from 9 to 10 and its worst "
              "reading is at the break. THE ENTRY SAYS THERE WAS NO GODMOTHER. This is the "
              "last of the eleven Sangamon County entries; the next entry is headed "
              "'Chicago Cook County State of Ill.'"),
    dict(year=1834, no=12, img="S3HT-DHG9-SKW", page="10", date="1834-06-16", dp="day",
         dc=D, place=CHI, chi=True, lang="fr",
         read="Le seize juin mil huit cent trente quatre, je soussigné ai baptisé Joseph "
              "Pottier fils de Jean Pottier et de Victoire Medero, né [le] huit de mars "
              "mil huit [cent] trente quatre. Parrain et marraine ont été Joseph Pallet "
              "et Josette Chevalier.",
         ppl=[("child", "Joseph Pottier", "Joseph Pottier", D, "Born 8 March 1834."),
              ("father", "Jean Pottier", "Jean Pottier", D,
               "The same father as 1833 entry 3, where he is written 'Potier'."),
              ("mother", "Victoire Medero", "Victoire Madera", I,
               "Written 'Madera' in 1833 entry 3 and 'Medero' here, in the same hand."),
              ("godfather", "Joseph Pallet", "Joseph Pallet", I,
               "The surname's double letter is not certain; 'Pallet' and 'Pillet' are "
               "both readable."),
              ("godmother", "Josette Chevalier", "Josette Chevalier", D, "")],
         note="THE RETURN TO CHICAGO. A heading in the priest's hand stands above this "
              "entry: 'Chicago Cook County State of Ill.' Everything from here to the end "
              "of 1835 is Chicago."),
    dict(year=1834, no=13, img="S3HT-DHG9-SKW", page="10", date="1834-06-28", dp="day",
         dc=D, place=CHI, chi=True, lang="fr",
         read="Le vingt huit juin mil huit cent trente quatre, je soussigné ai baptisé "
              "Josette Beaubien femme de Jean Baptiste Beaubien, âgée de 38 ans.",
         ppl=[("subject", "Josette Beaubien", "Josette Laframboise Beaubien", D,
               "AN ADULT, not a child: 'femme de Jean Baptiste Beaubien, âgée de 38 ans' "
               "— wife of Jean Baptiste Beaubien, aged 38. A birth year of about 1796 "
               "follows from the age and is not asserted here."),
              ("spouse", "Jean Baptiste Beaubien", "Jean Baptiste Beaubien", D,
               "Named as the subject's husband, not as a parent.")],
         note="AN ADULT BAPTISM AND NO SPONSOR IS NAMED. The entry gives an AGE — 38 — "
              "which is the only age this register ever gives for an adult woman of "
              "Chicago. It is the same day her son Alexander was baptised (entry 14)."),
    dict(year=1834, no=14, img="S3HT-DHG9-SKW", page="10", date="1834-06-28", dp="day",
         dc=D, place=CHI, chi=True, lang="fr",
         read="Le même jour, je soussigné ai conféré les cérémonies du baptême à "
              "Alexander fils de Jean Baptiste Beaubien et de Josette Laframboise, âgé "
              "environ de 12 ans.",
         ppl=[("child", "Alexander", "Alexander Beaubien", I,
               "Forename only; the surname is the father's and is inferred. Aged about "
               "twelve, so born about 1822."),
              ("father", "Jean Baptiste Beaubien", "Jean Baptiste Beaubien", D, ""),
              ("mother", "Josette Laframboise", "Josette Laframboise", D,
               "The same woman baptised as an adult in the entry immediately above, "
               "written there under her married name.")],
         note="No sponsors are named. The words are 'conféré les cérémonies du baptême' — "
              "the supplying of ceremonies to someone already baptised privately — not "
              "'baptisé'; the distinction is the clerk's and it is kept."),
    dict(year=1834, no=15, img="S3HT-DHG9-SKW", page="11", date="1834-06-28", dp="day",
         dc=D, place=CHI, chi=True, lang="fr",
         read="Le même jour mil huit cent trente quatre, je soussigné ai conféré les "
              "cérémonies du baptême à Thérèse fille de Joseph Laframboise et de Thérèse "
              "Jacquet Peltier, âgée de onze ans.",
         ppl=[("child", "Thérèse", "Thérèse Laframboise", I,
               "Forename only; the surname is the father's and is inferred. Aged eleven, "
               "so born about 1823."),
              ("father", "Joseph Laframboise", "Joseph Laframboise", D, ""),
              ("mother", "Thérèse Jacquet Peltier", "Jacquette Peltier", D,
               "Written 'Jacquet Peltier' in 1833 entry 13 and 'Thérèse Jacquet Peltier' "
               "here; the child is named for her.")],
         note="No sponsors are named."),
    dict(year=1834, no=16, img="S3HT-DHG9-SKW", page="11", date="1834-06-29", dp="day",
         dc=D, place=CHI, chi=True, lang="fr",
         read="Le vingt neuf juin, je soussigné ai conféré les cérémonies du baptême à "
              "Joseph fils de John Welsh et de Marie Louise Wimette né le dix huit mars "
              "mil huit cent trente trois. Parrain et marraine ont été N. Thob[?] et "
              "Louise Caroline Choulet.",
         ppl=[("child", "Joseph", "Joseph Welsh", I,
               "Forename only; the surname is the father's and is inferred. Born 18 March 1833."),
              ("father", "John Welsh", "John Welsh", D,
               "The clerk underlines the name, which he does nowhere else."),
              ("mother", "Marie Louise Wimette", "Marie Louise Ouilmette", I,
               "'Wimette' is the phonetic form of Ouilmette; the normalization is this "
               "project's spelling and the merge to any particular Ouilmette is NOT made "
               "here — see the crosswalk."),
              ("godfather", "N. Thob[?]", "N. Thob", I,
               "An initial and a four-letter surname, and neither is secure."),
              ("godmother", "Louise Caroline Choulet", "Louise Caroline Choulet", D, "")],
         note=""),
    dict(year=1834, no=17, img="S3HT-DHG9-SKW", page="11", date="1834-06-29", dp="day",
         dc=D, place=CHI, chi=True, lang="en",
         read="On the same day eighteen hundred and thirty four I, the undersigned "
              "baptised Cattarine daughter of John Welsh and of Mary Louis Wimette, born "
              "the ninth of June. Sponsors were Salomon Juneau and Claudia Pierrette "
              "Choulet.",
         ppl=[("child", "Cattarine", "Catharine Welsh", I,
               "Forename only; the surname is the father's and is inferred. Born the "
               "ninth of June, twenty days before her baptism."),
              ("father", "John Welsh", "John Welsh", D, ""),
              ("mother", "Mary Louis Wimette", "Marie Louise Ouilmette", I,
               "The English form of the name written 'Marie Louise Wimette' in the entry "
               "above."),
              ("sponsor", "Salomon Juneau", "Solomon Juneau", D, ""),
              ("sponsor", "Claudia Pierrette Choulet", "Claudia Pierrette Choulet", D, "")],
         note="Two children of the same household on one day, one entry in French and one "
              "in English."),
    dict(year=1834, no=18, img="S3HT-DHG9-S1C", page="12", date="1834-07-16", dp="day",
         dc=D, place=CHI, chi=True, lang="en",
         read="On the 16th of July eighteen hundred and thirty four I the undersigned "
              "conferred the ceremonies of Baptism according to the rites of the holy "
              "Catholic church to Cicely daughter of Patrick Wagon[?] and of Mary Duggan, "
              "born the 15th of July 1834. Sponsors were Doctor Egan and Josette Beaubien.",
         ppl=[("child", "Cicely", "Cicely Wagon", I,
               "Forename only; the surname is the father's and is inferred. Born the day "
               "before her baptism."),
              ("father", "Patrick Wagon[?]", "Patrick Wagon", I,
               "The surname is five letters and the first is not certain; 'Wagon' and "
               "'Nagon' are both readable."),
              ("mother", "Mary Duggan", "Mary Duggan", D, ""),
              ("sponsor", "Doctor Egan", "Doctor Egan", D,
               "Entered by title and surname, with no forename — which is how the town's "
               "papers print him too."),
              ("sponsor", "Josette Beaubien", "Josette Laframboise Beaubien", D,
               "Baptised herself as an adult eighteen days before, in entry 13.")],
         note="THE ONLY ENTRY THAT NAMES A PROFESSION: 'Doctor Egan'. It is a title inside "
              "the name and not an occupation the register states, and it mints nothing."),
    dict(year=1834, no=19, img="S3HT-DHG9-S1C", page="12", date="1834-08-06", dp="day",
         dc=D, place=CHI, chi=True, lang="fr",
         read="Le 6 d'août mil huit cent trente quatre, je soussigné ai baptisé Eléonore "
              "Beaubien fille de Mark Beaubien et de Monique Nodou, née le vingt deux de "
              "juillet 1834. Parrain et marraine ont été Jean Marie Irénée Saint Cyr et "
              "Archange Beaubien.",
         ppl=[("child", "Eléonore Beaubien", "Eléonore Beaubien", D, "Born 22 July 1834."),
              ("father", "Mark Beaubien", "Mark Beaubien", D, ""),
              ("mother", "Monique Nodou", "Monique Nadeau", I,
               "A third spelling of the same woman's surname in the same hand — Nadeau, "
               "Nodeau, Nodou."),
              ("godfather", "Jean Marie Irénée Saint Cyr", "John Mary Irenaeus Saint Cyr", D,
               "THE PRIEST AS GODFATHER, and here he writes out his own three forenames "
               "in full — the only place in the book he does."),
              ("godmother", "Archange Beaubien", "Archange Beaubien", D, "")],
         note="The margin carries a running total, 'total 19', and a note that reads 'a "
              "[?] Creek, Flat Branche' — a hand later than the entry and not part of it."),
    dict(year=1834, no=20, img="S3HT-DHG9-S1C", page="12", date="1834-12-10", dp="day",
         dc=D, place=CHI, chi=True, lang="en",
         read="On the 10th December eighteen hundred and thirty four I, the undersigned, "
              "baptised Elisabeth daughter of Godfrey Coslet and of Marian Eberling, born "
              "the 9th of December eighteen hundred and thirty four. Godmother was Marian "
              "Mouch[?]; no godfather.",
         ppl=[("child", "Elisabeth", "Elisabeth Coslet", I,
               "Forename only; the surname is the father's and is inferred. Born the day "
               "before her baptism."),
              ("father", "Godfrey Coslet", "Godfrey Coslet", I,
               "The surname's middle letters are crossed by the line below and the "
               "reading is not secure."),
              ("mother", "Marian Eberling", "Marian Eberling", I,
               "A German form written by a French speaker; the ending is not certain."),
              ("godmother", "Marian Mouch[?]", "Marian Mouch", I,
               "The surname is short and its final letters run into the signature.")],
         note="THE ENTRY SAYS THERE WAS NO GODFATHER. The margin reads '10. 10bre 1834 "
              "Chicago'."),
    dict(year=1834, no=21, img="S3HT-DHG9-S1C", page="13", date="1834-12-24", dp="day",
         dc=D, place=CHI, chi=True, lang="en",
         read="On the twenty fourth of 10ber eighteen hundred and thirty four I, the "
              "undersigned, baptised Susan daughter of Charles Beaubien and of Lucy "
              "Kennedy, born sixteenth of 10ber eighteen hundred thirty four. Sponsors "
              "were John Mary I. Saint Cyr and Monique Nadeau Beaubien.",
         ppl=[("child", "Susan", "Susan Beaubien", I,
               "Forename only; the surname is the father's and is inferred. Born 16 "
               "December 1834."),
              ("father", "Charles Beaubien", "Charles Beaubien", D, ""),
              ("mother", "Lucy Kennedy", "Lucy Kennedy", I,
               "The surname is struck through once and rewritten; the rewritten form is "
               "what is read."),
              ("sponsor", "John Mary I. Saint Cyr", "John Mary Irenaeus Saint Cyr", D,
               "The priest as sponsor for the third and last time in this book."),
              ("sponsor", "Monique Nadeau Beaubien", "Monique Nadeau", D,
               "Under her married name, which is how the crosswalk reaches her.")],
         note="'10ber' is December. The entry stands before entry 22, which is dated the "
              "22nd — the book is two days out of order here, and neither date is "
              "adjusted."),
    dict(year=1834, no=22, img="S3HT-DHG9-S1C", page="13", date="1834-12-22", dp="day",
         dc=D, place=CHI, chi=True, lang="en",
         read="On the 22d of 10ber eighteen hundred and thirty [four] I, the undersigned "
              "baptised Robert Jerome Beaubien son of J. Bap[tis]t Beaubien and of "
              "Josette Laframboise, born nineteenth december eighteen hundred and thirty "
              "four. Godfather and godmother were Mr Robert Kinzie and Gwinthlean "
              "Whistler.",
         ppl=[("child", "Robert Jerome Beaubien", "Robert Jerome Beaubien", D,
               "Born 19 December 1834, and named for his godfather."),
              ("father", "J. Bap[tis]t Beaubien", "Jean Baptiste Beaubien", D,
               "SIGNS THE ENTRY IN HIS OWN HAND: 'J. B. Beaubien'."),
              ("mother", "Josette Laframboise", "Josette Laframboise", D, ""),
              ("godfather", "Mr Robert Kinzie", "Robert Allen Kinzie", D,
               "SIGNS THE ENTRY IN HIS OWN HAND: 'Robt A. Kinzie'. The margin repeats "
               "'Robert A. Kinzie' in the priest's hand."),
              ("godmother", "Gwinthlean Whistler", "Gwinthlean Whistler", D,
               "SIGNS THE ENTRY IN HER OWN HAND, and signs it 'Gwin[thlean] H. Kinzie' — "
               "her married name, beside her maiden name in the body of the entry.")],
         note="THE MOST WITNESSED ENTRY IN THE BOOK: three of the town's own people sign "
              "it under the priest — J. B. Beaubien, Robert A. Kinzie and the godmother "
              "in her married name. Her signature and the entry's own text give the same "
              "woman two surnames on one page, which is a documented marriage and not an "
              "inference."),
    dict(year=1834, no=23, img="S3HT-DHG9-S1C", page="13", date="1834-12-29", dp="day",
         dc=D, place=CHI, chi=True, lang="fr",
         read="Le 29 10bre mil huit cent trente quatre, je soussigné ai baptisé Noel "
              "Bourassa fils de Léon Bourassa et de Marguerite Laframboise, âgé de deux "
              "ans. Parrain et marraine ont été M. Rowe[?] et Thérèse Peltier Laframboise.",
         ppl=[("child", "Noel Bourassa", "Noel Bourassa", D, "Aged two, so born about 1832."),
              ("father", "Léon Bourassa", "Léon Bourassa", D, ""),
              ("mother", "Marguerite Laframboise", "Marguerite Laframboise", D, ""),
              ("godfather", "M. Rowe[?]", "M. Rowe", I,
               "A title and a four-letter surname; the reading is not secure and the same "
               "name stands as godfather to entry 24."),
              ("godmother", "Thérèse Peltier Laframboise", "Jacquette Peltier", I,
               "A third form of the woman written 'Jacquet Peltier' in 1833 entry 13 and "
               "'Thérèse Jacquet Peltier' in 1834 entry 15.")],
         note="Runs across the page turn from 13 to 14."),
    dict(year=1834, no=24, img="S3HT-DHG9-ST3", page="14", date="1834-12-29", dp="day",
         dc=D, place=CHI, chi=True, lang="fr",
         read="Le vingt neuf 10bre mil huit cent trente quatre, je soussigné ai baptisé "
              "Cécile fille de Claude Laframboise et de Manqua Masqua[?], âgée de 4 ans. "
              "Parrain et marraine ont été M. Rowe[?] et Thérèse Laframboise.",
         ppl=[("child", "Cécile", "Cécile Laframboise", I,
               "Forename only; the surname is the father's and is inferred. Aged four, so "
               "born about 1830."),
              ("father", "Claude Laframboise", "Claude Laframboise", D, ""),
              ("mother", "Manqua Masqua[?]", "Manqua Masqua", I,
               "An Indigenous name written phonetically; the second element is not certain."),
              ("godfather", "M. Rowe[?]", "M. Rowe", I, "The same uncertain name as entry 23."),
              ("godmother", "Thérèse Laframboise", "Jacquette Peltier", I,
               "A fourth form of the same woman; see entry 23.")],
         note="CLOSES 1834. A pencil hand beneath the entry has written '1834: 24 Bapt' — "
              "the year's own tally, and it agrees exactly with the twenty-four entries "
              "read here."),
    # ------------------------------ 1835 ------------------------------------
    dict(year=1835, no=1, img="S3HT-DHG9-ST3", page="14", date="1835-02-23", dp="day",
         dc=D, place=CHI, chi=True, lang="en",
         read="On twenty third of February eighteen hundred thirty five I, the "
              "undersigned, baptised Mary Elisabeth daughter of Thomas Forester and of "
              "Brigitt Finegan, born the twenty first of instant 1835. Sponsors were "
              "Patrick Carroll and Mary Murphy.",
         ppl=[("child", "Mary Elisabeth", "Mary Elisabeth Forester", I,
               "Two forenames and no surname; the surname is the father's and is "
               "inferred. Born 21 February 1835."),
              ("father", "Thomas Forester", "Thomas Forester", D,
               "The surname is written over a struck word and rewritten clearly."),
              ("mother", "Brigitt Finegan", "Bridget Finegan", D, ""),
              ("sponsor", "Patrick Carroll", "Patrick Carroll", D, ""),
              ("sponsor", "Mary Murphy", "Mary Murphy", D, "")],
         note="THE FIRST ENTRY OF THE SCENE YEAR, and the first of six Irish households "
              "the register reaches in it. The margin carries one word in the priest's "
              "hand: 'Irish'."),
    dict(year=1835, no=2, img="S3HT-DHG9-ST3", page="15", date="1835-04-05", dp="day",
         dc=D, place=CHI, chi=True, lang="en",
         read="On the fifth of April eighteen hundred & thirty five, I the undersigned "
              "baptized Catherine Henrietta Bousque daughter of Bernard Bousque & of "
              "Catherine Preman, born the fifth of march 1835. Sponsors were Henry Stone "
              "& Catherine Debert[?].",
         ppl=[("child", "Catherine Henrietta Bousque", "Catherine Henrietta Bousque", D,
               "Born 5 March 1835."),
              ("father", "Bernard Bousque", "Bernard Bousque", D, ""),
              ("mother", "Catherine Preman", "Catherine Preman", I,
               "The surname's first letter could be a P or a B."),
              ("sponsor", "Henry Stone", "Henry Stone", I,
               "The surname is short and could be Stone or Stove."),
              ("sponsor", "Catherine Debert[?]", "Catherine Debert", I,
               "The surname is crossed by the flourish of the signature below it.")],
         note="The heading is 'Chicago Ill.' and the priest signs 'Cath. priest'."),
    dict(year=1835, no=3, img="S3HT-DHG9-ST3", page="15", date="1835-06-06", dp="day",
         dc=D, place=CHI, chi=True, lang="fr",
         read="Le six juin mil huit cent trente cinq, je soussigné ai baptisé Geneviève "
              "Medera fille de Miranda et de [blank] âgée d'environ vingt ans. Témoins: "
              "L. Chevalier, Bourrasso.",
         ppl=[("subject", "Geneviève Medera", "Geneviève Medera", D,
               "AN ADULT: 'âgée d'environ vingt ans' — about twenty years old, so born "
               "about 1815."),
              ("father", "Miranda", "Miranda", I,
               "One name, and the entry gives no more of it."),
              ("witness", "L. Chevalier", "L. Chevalier", I,
               "An initial and a surname. The word the clerk uses is 'témoins' — "
               "witnesses — not 'parrain et marraine'."),
              ("witness", "Bourrasso", "Bourrasso", I,
               "A surname alone, and a surname alone is not a person here: Léon Bourassa "
               "and his son Jean Baptiste are both in this book and neither is merged to "
               "this name.")],
         note="THE MOTHER'S NAME IS LEFT BLANK — a ruled gap the clerk never filled. The "
              "second adult baptism in the register and the only one of the scene year."),
    dict(year=1835, no=4, img="S3HT-DHG9-ST3", page="15", date="1835-06-29", dp="day",
         dc=D, place=CHI, chi=True, lang="fr",
         read="Le vingt neuf juin mil huit cent trente cinq, je soussigné ai baptisé Jean "
              "Baptiste fils de Léon Bourrasso et de Marguerite [Laframboise]. Né the "
              "quatre juin 1835. Parrain et marraine ont été Jean Baptiste Derocher et "
              "Louise Caroline Choutet.",
         ppl=[("child", "Jean Baptiste", "Jean Baptiste Bourassa", I,
               "Two forenames and no surname; the surname is the father's and is "
               "inferred. Born 4 June 1835 — a scene-year birth."),
              ("father", "Léon Bourrasso", "Léon Bourassa", I,
               "Written 'Bourassa' in 1834 entry 23 and 'Bourrasso' here."),
              ("mother", "Marguerite", "Marguerite Laframboise", I,
               "The forename alone; the surname is taken from 1834 entry 23, where the "
               "same father's wife is 'Marguerite Laframboise', and is therefore inferred."),
              ("godfather", "Jean Baptiste Derocher", "Jean Baptiste Derocher", D, ""),
              ("godmother", "Louise Caroline Choutet", "Louise Caroline Choulet", I,
               "Written 'Choulet' in 1834 entry 16 and 'Choutet' here.")],
         note="The margin names the child in full — 'Jean Baptiste Bourasso 1835 29 juin' "
              "— which is where the child's surname is actually written. The clerk mixes "
              "his languages in one line: 'Né the quatre juin 1835.'"),
    dict(year=1835, no=5, img="S3HT-DHG9-SJ8", page="16", date="1835-07-05", dp="day",
         dc=D, place=CHI, chi=True, lang="fr",
         read="Le cinq juillet mil huit cent trente cinq, je soussigné ai administré les "
              "cérémonies du baptême à Joseph Arquat fils de Michel Arquot et de "
              "Marguerite Robi, âgé de 16 mois. Parrain a été Louis Trombere[?].",
         ppl=[("child", "Joseph Arquat", "Joseph Arquette", I,
               "Sixteen months old, so born about March 1834. The surname is spelt two "
               "ways in one sentence."),
              ("father", "Michel Arquot", "Michel Arquette", I,
               "Written 'Arquat' for the child and 'Arquot' for the father; the "
               "normalization to 'Arquette' is this project's spelling of the French form "
               "and is inferred."),
              ("mother", "Marguerite Robi", "Marguerite Robi", I,
               "The surname is four letters and its ending is not certain."),
              ("godfather", "Louis Trombere[?]", "Louis Trombere", I,
               "The surname runs off the line; 'Trombere' and 'Tremblay' are both "
               "readable from the hand.")],
         note="NO GODMOTHER IS NAMED — the entry names a 'parrain' and stops."),
    dict(year=1835, no=6, img="S3HT-DHG9-SJ8", page="16", date="1835-07-05", dp="day",
         dc=D, place=CHI, chi=True, lang="fr",
         read="Le cinq juillet mil huit cent trente cinq, je soussigné ai administré les "
              "cérémonies du baptême à Marguerite [struck: Lafambre] fille de François "
              "Tranche[?] et de Josette Aspam, âgée d'un an. Parrain a été Michel Choulet.",
         ppl=[("child", "Marguerite", "Marguerite Tranche", I,
               "Forename only — a surname was written after it and struck out. The "
               "surname is the father's and is inferred. Aged one, so born about 1834."),
              ("father", "François Tranche[?]", "François Tranche", I,
               "The same uncertain surname as 1833 entry 16, with the same wife."),
              ("mother", "Josette Aspam", "Josette Aspam", I,
               "The family written 'Ashkam' on page 2 and 'Aspam' here and on page 5."),
              ("godfather", "Michel Choulet", "Michel Choulet", D, "")],
         note="A SURNAME WAS STRUCK OUT after the child's forename and the struck word "
              "reads as 'Lafambre' — the contraction of Laframboise the clerk used in "
              "1833 entry 13. He appears to have begun the wrong family and corrected "
              "himself. NO GODMOTHER IS NAMED."),
    dict(year=1835, no=7, img="S3HT-DHG9-SJ8", page="16", date="1835-08-20", dp="day",
         dc=D, place=CHI, chi=True, lang="en",
         read="On the twentieth of August 1835 I, the undersigned baptized Brigitt "
              "O'Marra daughter of James O'Marra and Cierno Ann, born the nineteenth of "
              "August eighteen hundred thirty five. Sponsors were John Murphy and "
              "Brigitte his wife.",
         ppl=[("child", "Brigitt O'Marra", "Bridget O'Marra", D,
               "Born 19 August 1835 — a scene-year birth, the day before her baptism."),
              ("father", "James O'Marra", "James O'Marra", D, ""),
              ("mother", "Cierno Ann", "Cierno Ann", I,
               "Read as written; it may be a forename pair rather than a surname and the "
               "entry does not say."),
              ("sponsor", "John Murphy", "John Murphy", D, ""),
              ("sponsor", "Brigitte [Murphy]", "Bridget Murphy", I,
               "Named only as 'Brigitte his wife'. The surname is her husband's and is "
               "inferred; a wife named by her husband's entry is still a named person.")],
         note="The margin reads 'Brigitte O'Marra 1835 August 20'. The entry documents a "
              "MARRIED COUPLE at Chicago on 20 August 1835 — John Murphy and his wife "
              "Brigitte — which is a marriage the register states in passing."),
    dict(year=1835, no=8, img="S3HT-DHG9-SJ8", page="17", date="1835-08-24", dp="day",
         dc=D, place=CHI, chi=True, lang="fr",
         read="Le 24 août 1835, je soussigné ai administré les cérémonies du baptême à "
              "Pierre Adam Schwartz fils de Adam Schwartz et de Marie Dalbau[?], âgé de "
              "six mois. Parrain et marraine ont été M. Pierre Riffe et Marie Delacher[?].",
         ppl=[("child", "Pierre Adam Schwartz", "Pierre Adam Schwartz", D,
               "Six months old, so born about February 1835 — a scene-year birth."),
              ("father", "Adam Schwartz", "Adam Schwartz", D,
               "The child's second forename is struck through in the entry and rewritten "
               "as the father's name."),
              ("mother", "Marie Dalbau[?]", "Marie Dalbau", I,
               "The surname's ending is not certain."),
              ("godfather", "M. Pierre Riffe", "Pierre Riffe", D,
               "SIGNS THE ENTRY IN HIS OWN HAND: 'P. Riffe'."),
              ("godmother", "Marie Delacher[?]", "Marie Delacher", I,
               "The surname is crossed by the signature flourish below it.")],
         note="A GERMAN HOUSEHOLD with French sponsors — the register's only Schwartz."),
    dict(year=1835, no=9, img="S3HT-DHG9-SJ8", page="17", date="1835-09-25", dp="day",
         dc=D, place=CHI, chi=True, lang="en",
         read="On the 25 of 7ber eighteen hundred & thirty five I the undersigned "
              "administered the ceremonies of Baptism to Martha daughter of John Murray & "
              "Mary Brenin, fifteen days old. Godfather & Godmother were Catherine Murray "
              "& J. M. I. St Cyr.",
         ppl=[("child", "Martha", "Martha Murray", I,
               "Forename only; the surname is the father's and is inferred. Fifteen days "
               "old, so born about 10 September 1835 — a scene-year birth."),
              ("father", "John Murray", "John Murray", D, ""),
              ("mother", "Mary Brenin", "Mary Brenin", I,
               "The surname could be Brenin or Brennan."),
              ("godmother", "Catherine Murray", "Catherine Murray", D, ""),
              ("godfather", "J. M. I. St Cyr", "John Mary Irenaeus Saint Cyr", D,
               "The priest as godfather. The clerk writes 'Godfather & Godmother were "
               "Catherine Murray & J. M. I. St Cyr' — the names in the reverse order of "
               "the roles, and they are assigned by sex here.")],
         note="'7ber' is September. The roles are written in the order godfather, "
              "godmother and the names in the order Catherine Murray, St Cyr; the priest "
              "is a man and Catherine Murray a woman, so the pairing is read across."),
    dict(year=1835, no=10, img="S3HT-DHG9-926", page="18", date="1835-10-04", dp="day",
         dc=D, place=CHI, chi=True, lang="fr",
         read="Chicago. Le quatre octobre mil huit cent trente cinq, je soussigné ai "
              "baptisé Joseph Claude Roi fils de George David Roi, et d'Anne Françoise "
              "Apolline Bruno, âgé de [?] jours. Ses parrain et marraine ont été Jean "
              "Baptiste Bruno et Joséphine Guy.",
         ppl=[("child", "Joseph Claude Roi", "Joseph Claude Roi", D,
               "Aged some days — the figure is struck through and unread — so born in "
               "1835, a scene-year birth."),
              ("father", "George David Roi", "George David Roi", D, ""),
              ("mother", "Anne Françoise Apolline Bruno", "Anne Françoise Apolline Bruno", D, ""),
              ("godfather", "Jean Baptiste Bruno", "Jean Baptiste Bruno", D,
               "Shares the mother's surname; the register does not say how they are related."),
              ("godmother", "Joséphine Guy", "Joséphine Guy", D, "")],
         note="The entry is headed 'Chicago' in the priest's hand and the margin reads "
              "'1835. 4 8bre'. '8bre' is October."),
    dict(year=1835, no=11, img="S3HT-DHG9-926", page="18", date="1835-10-04", dp="day",
         dc=D, place=CHI, chi=True, lang="fr",
         read="Chicago. Le quatre d'octobre mil huit cent trente cinq, je soussigné ai "
              "baptisé Anne Françoise Virginie Roy fille de George David Roi et de Anne "
              "Françoise Apolline Bruno, âgée d'un an. Alexis Thomas Blanchemontagne et "
              "Marie Louise Mallet l'ont tenue sur les fonts.",
         ppl=[("child", "Anne Françoise Virginie Roy", "Anne Françoise Virginie Roi", D,
               "Aged one, so born about 1834. The clerk writes the child 'Roy' and the "
               "father 'Roi' in the same sentence."),
              ("father", "George David Roi", "George David Roi", D, ""),
              ("mother", "Anne Françoise Apolline Bruno", "Anne Françoise Apolline Bruno", D, ""),
              ("godfather", "Alexis Thomas Blanchemontagne", "Alexis Thomas Blanchemontagne", D,
               "The entry says the sponsors 'l'ont tenue sur les fonts' — held her at the "
               "font — rather than naming them parrain and marraine."),
              ("godmother", "Marie Louise Mallet", "Marie Louise Mallet", D, "")],
         note="A sister of entry 10, baptised the same day. Two children of one household "
              "on one day, as in 1833 entries 11-12 and 1834 entries 16-17."),
    dict(year=1835, no=12, img="S3HT-DHG9-926", page="18", date="1835-10-18", dp="day",
         dc=D, place=CHI, chi=True, lang="en",
         read="Chicago. On the eighteenth of October eighteen hundred & thirty five I, "
              "the undersigned, administered the ceremonies of Baptism to Catherine "
              "Duplar two months old daughter of Joseph Duplas & Catherine Miller. "
              "Sponsors were Frederick Daniel and Barbery Judar.",
         ppl=[("child", "Catherine Duplar", "Catherine Duplas", I,
               "Two months old, so born about August 1835 — a scene-year birth. The "
               "surname is written 'Duplar' for the child and 'Duplas' for the father."),
              ("father", "Joseph Duplas", "Joseph Duplas", D, ""),
              ("mother", "Catherine Miller", "Catherine Miller", D, ""),
              ("sponsor", "Frederick Daniel", "Frederick Daniel", D, ""),
              ("sponsor", "Barbery Judar", "Barbery Judar", D,
               "Stands again three weeks later in entry 13.")],
         note="Begins at the foot of page 18 and finishes at the head of page 19."),
    dict(year=1835, no=13, img="S3HT-DHG9-926", page="19", date="1835-11-09", dp="day",
         dc=D, place=CHI, chi=True, lang="en",
         read="On the nineth of November eighteen hundred and thirty five I, the "
              "undersigned, baptized Louisa born the thirtieth of October, daughter of "
              "Jacob Tony and Catherine Chandler. Godfather and godmother were Joseph "
              "Chandler and Barbery Judar.",
         ppl=[("child", "Louisa", "Louisa Tony", I,
               "Forename only in the body; the margin heads the entry 'Baptism of Louisa "
               "Tony'. Born 30 October 1835 — a scene-year birth."),
              ("father", "Jacob Tony", "Jacob Tony", D, ""),
              ("mother", "Catherine Chandler", "Catherine Chandler", D, ""),
              ("godfather", "Joseph Chandler", "Joseph Chandler", D,
               "Shares the mother's surname; the register does not say how they are related."),
              ("godmother", "Barbery Judar", "Barbery Judar", D, "")],
         note=""),
    dict(year=1835, no=14, img="S3HT-DHG9-926", page="19", date="1835-12-25", dp="day",
         dc=D, place=CHI, chi=True, lang="en",
         read="Chicago, Illinois. On the twenty five of december eighteen hundred and "
              "thirty five I the undersigned baptized Denis Molony born the twentieth of "
              "december 1835, son of John Molony and Honour Casy, & sponsors were Edward "
              "Daly and Brigitte Forster.",
         ppl=[("child", "Denis Molony", "Denis Molony", D,
               "Born 20 December 1835 — a scene-year birth, five days before his baptism."),
              ("father", "John Molony", "John Molony", D, ""),
              ("mother", "Honour Casy", "Honora Casy", D, ""),
              ("sponsor", "Edward Daly", "Edward Daly", D, ""),
              ("sponsor", "Brigitte Forster", "Bridget Forster", D, "")],
         note="THE LAST ENTRY OF 1835 AND OF THE READING, written on Christmas Day. A "
              "pencil hand beneath it gives the year's tally, '1835: 14 B', which agrees "
              "exactly with the fourteen entries read here. The margin reads 'Chicago "
              "Illinois'."),
]

# Entries the deposit carries that fall OUTSIDE 1833-1835. They are declared, not
# transcribed person by person: they are later evidence about a later town, and the
# ticket's window is the scene. Recording them is what stops a later run reading
# these two page-sides again and finding them "unread".
OUT_OF_WINDOW = [
    dict(img="S3HT-DHG9-SKM", page="6", what="entry 40",
         date="1849-10-15",
         note="A single entry in Father O'Meara's later hand, written into the foot of "
              "page 6 fifteen years after the page around it: 'October 15th 1849 I the "
              "undersigned baptized Catherine daughter of Peter Gale and Marie Malen. "
              "Sponsors Fernandus Lebuke and Catherine Mattea. Child aged 11 dys. F. "
              "O'Meara.' Read and declared; not transcribed into records, because 1849 is "
              "fourteen years past the scene and nothing here may reach a resident."),
    dict(img="S3HT-DHG9-SKB", page="stray", what="entries 130-133",
         date="1837-1838",
         note="A stray leaf bound out of place, faded almost past reading, carrying four "
              "entries numbered 130-133 and dated August 1837 to January 1838 — the "
              "Short, Burke, Halligan and Donnelly households, with Patrick Murphy, Honor "
              "Foley, Patrick McCabe, Mary Halligan, David Burke, Mary Burke, William "
              "Fanning and John Fitzpatrick standing as sponsors. A pencil line beneath "
              "reads 'same as p. 107 & 108'. Read and declared; not transcribed into "
              "records: the ink is too far gone for a name to be given a confidence, and "
              "1837-38 is past the scene."),
]


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def slug(text):
    out = []
    for ch in text.lower():
        out.append(ch if ch.isalnum() else "_")
    s = "".join(out)
    while "__" in s:
        s = s.replace("__", "_")
    return s.strip("_")


def build_records():
    rows = []
    for e in ENTRIES:
        for i, (role, as_read, norm, conf, pnote) in enumerate(e["ppl"], start=1):
            rid = "st_marys_bapt_%d_%02d_%d_%s" % (e["year"], e["no"], i, slug(role))
            bits = ["%s of baptism entry %d of %d, %s." % (
                role.capitalize(), e["no"], e["year"], e["place"])]
            if pnote:
                bits.append(pnote)
            if not e["chi"]:
                bits.append("NOT A CHICAGO ENTRY: written at %s. A reader who takes this "
                            "book as a Chicago roll plants a household in the wrong "
                            "town." % e["place"])
            bits.append("A baptism documents a person at a font on a day; it is not a "
                        "residence, an address or an occupation, and this row asserts none.")
            rows.append({
                "id": rid,
                "as_read": as_read,
                "normalized": norm,
                "locator": {
                    "image": e["img"],
                    "page": e["page"],
                    "entry": e["no"],
                    "year_series": e["year"],
                    "role": role,
                    "position": i,
                },
                "reading": "scan_verified",
                "confidence": conf,
                "describes_date": e["date"],
                "cells": {
                    "role": role,
                    "date": e["date"],
                    "date_precision": e["dp"],
                    "date_confidence": e["dc"],
                    "place": e["place"],
                    "language": e["lang"],
                    "priest": PRIEST,
                    "entry_as_read": e["read"],
                },
                "at_chicago": e["chi"],
                "beyond_ticket_window": False,
                "adult": role not in ("child",),
                "notes": " ".join(bits) + (" " + e["note"] if e["note"] else ""),
            })
    return rows


TOWN_FINDINGS = [
    dict(id="st_marys_town_01", kind="building",
         quote="Le 22 de mai mil huit [cent] trente trois, je soussigné ai baptisé George "
               "Beaubien fils de Mark Beaubien et de Monique Nadeau",
         normalized="A Catholic priest was baptising at Chicago from 22 May 1833, and the "
                    "register he opened that day is headed '1er Page' — so the parish's "
                    "own recordkeeping begins on that date and not before.",
         img="S3HT-DHG9-SKB", page="1", entry=1, date="1833-05-22",
         entities=["Mark Beaubien", "Monique Nadeau", "John Mary Irenaeus Saint Cyr"],
         note="THE REGISTER DOES NOT NAME A CHURCH BUILDING — not on this page and not on "
              "any of the eleven. It heads its entries 'Chicago', 'Chicago Cook Co.' and "
              "'Chicago Ill.' and never a street, a chapel or a house. What the book "
              "establishes is a DATE, and the date is what this finding carries. Where "
              "the first church stood is NOT read out of these scans and must not be "
              "taken from them."),
    dict(id="st_marys_town_02", kind="landscape",
         quote="né dans le mois de mai mil huit cent trente [?] à la rivière au Sable",
         normalized="The Rivière au Sable — the Sable River — is named by the register as "
                    "a place a child was born, in or about May 1830.",
         img="S3HT-DHG9-SKM", page="6", entry=19, date="1833-10-20",
         entities=["Joseph Chevalier"],
         note="The only PLACE OUTSIDE A TOWN NAME the register ever gives. It is a "
              "birthplace, not a residence, and it is 1830, not 1835. The identification "
              "of this stream is NOT made here: the entry says 'rivière au Sable' and "
              "stops."),
    dict(id="st_marys_town_03", kind="appearance",
         quote="Enquiry to be made for Malachi Bacon, left Peru in the beginning of "
               "April. — aged 24 years. Swarthy complexion — 5 feet 10 — black eyes — "
               "hair black — Dress — white pea coat — gray pants, fur cap",
         normalized="A hue and cry written on the register's title page describes a "
                    "missing man of twenty-four: swarthy, five feet ten, black eyes and "
                    "black hair, wearing a white pea coat, gray trousers and a fur cap.",
         img="S3HT-DHG9-SLR", page="title", entry=None, date="1833-1834",
         entities=["Malachi Bacon"],
         note="WHAT A YOUNG MAN OF THE ILLINOIS COUNTRY WORE, written down by somebody "
              "who had seen him: a white pea coat, gray pants, a fur cap. The whole "
              "value of this note to the town is the CLOTHING; the man himself left Peru, "
              "not Chicago, and no residence is claimed for him. The surname is read "
              "'Bacon' with the middle letters uncertain."),
    dict(id="st_marys_town_04", kind="person",
         quote="Sponsors were Doctor Egan and Josette Beaubien",
         normalized="A man entered only as 'Doctor Egan' stood as sponsor at Chicago on "
                    "16 July 1834 — the register's single naming of a profession.",
         img="S3HT-DHG9-S1C", page="12", entry=18, date="1834-07-16",
         entities=["Doctor Egan", "Josette Laframboise Beaubien"],
         note="A TITLE INSIDE A NAME, not an occupation the register states, and it mints "
              "nothing and merges to nobody here — the crosswalk refuses it, because a "
              "title and a surname are not a forename."),
    dict(id="st_marys_town_05", kind="person",
         quote="Josette Beaubien femme de Jean Baptiste Beaubien, âgée de 38 ans",
         normalized="Josette Laframboise, wife of Jean Baptiste Beaubien, was baptised as "
                    "an adult at Chicago on 28 June 1834 and the register gives her age "
                    "as thirty-eight.",
         img="S3HT-DHG9-SKW", page="10", entry=13, date="1834-06-28",
         entities=["Josette Laframboise Beaubien", "Jean Baptiste Beaubien"],
         note="THE ONLY AGE THE REGISTER GIVES FOR AN ADULT WOMAN OF CHICAGO. A birth "
              "year of about 1796 follows from it and is not asserted here; the age is "
              "the reading and the arithmetic belongs to whoever spends it."),
    dict(id="st_marys_town_06", kind="civic",
         quote="Godfather and godmother were Mr Robert Kinzie and Gwinthlean Whistler",
         normalized="Robert A. Kinzie and Gwinthlean Whistler stood as godparents at "
                    "Chicago on 22 December 1834, and she signed the entry herself under "
                    "the name Kinzie.",
         img="S3HT-DHG9-S1C", page="13", entry=22, date="1834-12-22",
         entities=["Robert Allen Kinzie", "Gwinthlean Whistler", "Jean Baptiste Beaubien"],
         note="THREE OF THE TOWN'S OWN PEOPLE SIGN THIS ENTRY IN THEIR OWN HANDS — 'J. B. "
              "Beaubien', 'Robt A. Kinzie' and the godmother, who signs 'Gwin[thlean] H. "
              "Kinzie' beside a body text that calls her Whistler. Her two surnames on "
              "one page are a documented marriage, and it is the register that documents "
              "it. Autographs are the strongest thing in this book: they place a named "
              "person at a named place on a named day in their own hand."),
    dict(id="st_marys_town_07", kind="person",
         quote="Sponsors were John Murphy and Brigitte his wife",
         normalized="John Murphy and his wife Brigitte were both at Chicago on 20 August "
                    "1835 and the register names them as a married couple.",
         img="S3HT-DHG9-SJ8", page="16", entry=7, date="1835-08-20",
         entities=["John Murphy", "Bridget Murphy"],
         note="A MARRIAGE STATED IN PASSING, inside the scene year. Her surname is her "
              "husband's and is inferred; the marriage is not."),
    dict(id="st_marys_town_08", kind="person",
         quote="fille de Paul Vieaux et de Jaespquaa (sauvage de Green Bay)",
         normalized="A mother of a child baptised at Chicago on 10 October 1833 is "
                    "recorded as coming from Green Bay.",
         img="S3HT-DHG9-SKM", page="6", entry=18, date="1833-10-10",
         entities=["Paul Vieau", "Jaespquaa"],
         note="THE ONLY ORIGIN THE REGISTER EVER GIVES ANYONE. It is the clerk's "
              "parenthesis, it places a person and not a household, and no residence at "
              "Chicago follows from it. 'Sauvage' is his word and is kept in the quote "
              "because a quote is a quote; it is not this project's vocabulary."),
]


def build_claims():
    claims = []
    for c in TOWN_FINDINGS:
        loc = {"image": c["img"], "page": c["page"]}
        if c["entry"] is not None:
            loc["entry"] = c["entry"]
        claims.append({
            "id": c["id"],
            "kind": c["kind"],
            "reading": "scan_verified",
            "quote": c["quote"],
            "normalized": c["normalized"],
            "locator": loc,
            "describes_date": c["date"],
            "entities": c["entities"],
            "town_finding": True,
            "notes": c["note"],
        })
    return claims


def tallies():
    out = {}
    for e in ENTRIES:
        out.setdefault(e["year"], 0)
        out[e["year"]] += 1
    return out


# The book's OWN arithmetic, written into it in pencil beneath each year's last
# entry. It is the one independent check a reading of these scans can have, and a
# reading that does not meet it has lost or invented an entry.
BOOK_TALLY = {1833: 19, 1834: 24, 1835: 14}


def records_doc():
    rows = build_records()
    t = tallies()
    return {
        "schema": 1,
        "_doc": "GENERATED by tools/read_st_marys_baptisms.py --build out of the eleven "
                "deposited page images of St Mary's baptismal register. One row is one "
                "NAMED PERSON: an entry naming a child, two parents and two sponsors "
                "carries five readings, not one. Hand-edit and --check says so.",
        "generated_by": "tools/read_st_marys_baptisms.py",
        "source_id": SOURCE_ID,
        "describes_date": "1833-1835",
        "list": {
            "id": LIST_ID,
            "title": "St Mary's baptismal register, Chicago, 1833-1835, read off the "
                     "eleven deposited FamilySearch page images",
            "date": "1833-1835",
            "date_confidence": "documented",
            "entries": len(ENTRIES),
        },
        "the_ladder": "Under the ratified ladder a baptism parent or godparent of "
                      "1833-35 reaches `inferred`, and `attested` only where another "
                      "source corroborates. NOTHING IS MINTED OR REGRADED HERE. This "
                      "file is a reading; T-0514 and T-0515 spend it.",
        "counts": {
            "entries": len(ENTRIES),
            "entries_by_year": {str(k): v for k, v in sorted(t.items())},
            "book_tally_by_year": {str(k): v for k, v in sorted(BOOK_TALLY.items())},
            "readings": len(rows),
            "chicago_entries": sum(1 for e in ENTRIES if e["chi"]),
            "sangamon_county_entries": sum(1 for e in ENTRIES if not e["chi"]),
            "images_declared": len(IMAGES),
            "out_of_window_page_sides_declared": len(OUT_OF_WINDOW),
        },
        "images": [{"image": i, "pages": p, "what": w} for i, p, w in IMAGES],
        "out_of_window": OUT_OF_WINDOW,
        "records": rows,
    }


def claims_doc():
    return {
        "schema": 1,
        "_doc": "GENERATED by tools/read_st_marys_baptisms.py --build. TOWN FINDINGS — "
                "what the register says about the place rather than about a person's "
                "kinship. The quote is the page as read; there is no committed text file "
                "for a manuscript this project may not republish, so the quote is the "
                "reading itself and its locator is the image and the entry.",
        "generated_by": "tools/read_st_marys_baptisms.py",
        "source_id": SOURCE_ID,
        "describes_date": "1833-1835",
        "claims": build_claims(),
    }



# --------------------------------------------------------------------------- #
# THE CROSSWALK. Every ADULT the register names, held against `data/residents/`.
#
# The rules are `data/research/newspapers/identity.json`'s, which this domain's
# `crosswalk.json` restates: a merge needs a written rule; the rule names BOTH
# spellings verbatim; a surname-only merge is ALWAYS a refusal however good the
# rule reads; and a refusal is declared as explicitly as a merge, because the
# absence of a merge is indistinguishable from a pair nobody has looked at.
#
# Nothing here mints, regrades or edits a resident. The crosswalk DECLARES; T-0514
# and T-0515 spend it.
# --------------------------------------------------------------------------- #

RESIDENTS = ROOT / "data" / "residents" / "households"

MERGES = [
    ("Mark Beaubien", "Mark Beaubien",
     ["st_marys_bapt_1833_01_2_father", "st_marys_bapt_1833_13_4_godfather"],
     "The register writes \"Mark Beaubien\" and the residents layer writes \"Mark "
     "Beaubien\": forename and surname agree exactly. Three further agreements, from "
     "sources that did not copy each other: he is at Chicago on 22 May 1833 and again "
     "in August 1833 in the register, and the resident record has him keeping the "
     "Sauganash and holding the incorporation election at his house on 10 August 1833; "
     "his wife is Monique Nadeau in the register and the resident record documents his "
     "marriage; and he SIGNS the register in his own hand in 1833 entry 13."),
    ("Jean Baptiste Beaubien", "Col. Jean Baptiste Beaubien",
     ["st_marys_bapt_1834_13_2_spouse", "st_marys_bapt_1834_22_2_father"],
     "The register writes \"Jean Baptiste Beaubien\" and the residents layer writes "
     "\"Col. Jean Baptiste Beaubien\": three forenames and a surname agree exactly and "
     "the layer's form adds only a rank. Two independent agreements beyond the name: "
     "the register makes him the husband of Josette Laframboise, and the resident "
     "record documents that marriage out of Andreas; and he SIGNS the register in his "
     "own hand, 'J. B. Beaubien', on 22 December 1834, which is a named man at a named "
     "place on a named day in his own writing."),
    ("Josette Laframboise Beaubien", "Josette LaFramboise Beaubien",
     ["st_marys_bapt_1834_13_1_subject", "st_marys_bapt_1834_18_5_sponsor"],
     "The register writes \"Josette Laframboise Beaubien\" and the residents layer "
     "writes \"Josette LaFramboise Beaubien\": the same three name-parts, differing "
     "only in the capital inside Laframboise. Two agreements beyond the name: the "
     "register calls her 'femme de Jean Baptiste Beaubien' and the resident record has "
     "her married to J. B. Beaubien; and the register's age of 38 in June 1834 is "
     "consistent with the 1812 marriage the resident record documents. THE AGE IS NOT "
     "WRITTEN INTO HER RECORD BY THIS PASS."),
    ("Robert Allen Kinzie", "Robert Allen Kinzie",
     ["st_marys_bapt_1834_22_4_godfather"],
     "The register writes \"Robert Allen Kinzie\" — as 'Mr Robert Kinzie' in the body "
     "and 'Robt A. Kinzie' in his own signature — and the residents layer writes "
     "\"Robert Allen Kinzie\". The AUTOGRAPH is the merge: a signature is the strongest "
     "identification a manuscript can offer, and it agrees with a resident record that "
     "has him at Chicago as a merchant through 1834."),
    ("John Mary Irenaeus Saint Cyr", "Rev. John Mary Irenaeus St Cyr",
     ["st_marys_bapt_1834_10_4_sponsor", "st_marys_bapt_1834_19_4_godfather",
      "st_marys_bapt_1835_09_5_godfather"],
     "The register writes \"John Mary Irenaeus Saint Cyr\" — he writes out his own "
     "three forenames in full in 1834 entry 19 — and the residents layer writes \"Rev. "
     "John Mary Irenaeus St Cyr\", differing only in the style of the surname and the "
     "style of address. He is the officiant of every entry in this book and the "
     "resident record names him first priest of St Mary's from May 1833. This is the "
     "one identity in the domain that cannot be doubted."),
    ("Doctor Egan", "Dr William Bradshaw Egan",
     ["st_marys_bapt_1834_18_4_sponsor"],
     "The register writes \"Doctor Egan\" and the residents layer writes \"Dr William "
     "Bradshaw Egan\". THIS MERGE IS MADE ON A TITLE, NOT A FORENAME, and it is made "
     "only because the title is itself an attribute that agrees: three independent "
     "agreements stand behind it — the surname Egan; the medical title, which matches "
     "the resident record's occupation of physician and Andreas' count of him among "
     "the eight physicians at the close of 1833; and the place and time, Chicago in "
     "July 1834, against a resident record that has him arriving in the fall of 1833 "
     "and on the South Division health committee in August 1834. A fourth agreement "
     "is the confession itself: he was born in County Kerry and the sponsor at a "
     "Catholic font is a Catholic. THE RESIDUAL RISK IS STATED: a second Doctor Egan "
     "at Chicago in 1834 would break this, and the layer's only other Egan, Emeline "
     "Egan, is separated by the title."),
    ("John Murphy", "John Murphy",
     ["st_marys_bapt_1835_07_4_sponsor"],
     "The register writes \"John Murphy\" and the residents layer writes \"John "
     "Murphy\": forename and surname agree exactly, and the name is a common one, so "
     "the merge rests on what stands beside it. The register names him with a WIFE — "
     "'John Murphy and Brigitte his wife' — at Chicago on 20 August 1835; the resident "
     "record is built on Andreas' 'Mr. and Mrs. Murphy took charge of this new hotel' "
     "and has the couple keeping the Exchange Coffee House from August 1834 until "
     "1836. A married couple of that name, at Chicago, in that window, in two sources "
     "that did not copy each other, is three agreements. WHAT THIS PASS DOES NOT DO is "
     "write 'Brigitte' into Mrs Murphy's record; that is T-0515's to spend, and it is "
     "the forename of a woman the resident layer holds without one."),
    ("Joseph Chandler", "Joseph Chandler",
     ["st_marys_bapt_1835_13_4_godfather"],
     "The register writes \"Joseph Chandler\" and the residents layer writes \"Joseph "
     "Chandler\": forename and surname agree exactly. The resident is known from one "
     "return of uncalled-for letters at the Chicago post office in April 1834, printed "
     "'Joveph Chandler'; the register puts a Joseph Chandler at a Chicago font on 9 "
     "November 1835 as godfather to the daughter of Catherine Chandler, which "
     "establishes a Chandler household in the town and is exactly the second source a "
     "letter-list name has always lacked. Two independent agreements — the name and "
     "the town — plus a household the letter list could not show. THE RESIDUAL RISK IS "
     "STATED: the name is not rare and no third attribute agrees."),
    ("Solomon Juneau", "Solomon Juneau",
     ["st_marys_bapt_1833_05_2_father", "st_marys_bapt_1833_08_4_godfather",
      "st_marys_bapt_1833_10_4_godfather", "st_marys_bapt_1834_17_4_sponsor"],
     "The register writes \"Salomon Juneau\" in 1833 entry 5 and 1834 entry 17 and "
     "\"Solomon Juneau\" in 1833 entries 8 and 10 \u2014 the French and the English form "
     "of one forename, in one hand \u2014 and the residents layer writes \"Solomon "
     "Juneau\". THE SURNAME IS RARE HERE: one Juneau among the people the layer holds "
     "and one across every adult reading of this book. Three agreements stand beyond "
     "the name, and the two sources did not copy each other. FIRST, THE FAMILY THE "
     "REGISTER ITSELF GIVES HIM: he is the father of Marguerite by 'Josette Vieau' "
     "(1833 entry 5), he stands godfather WITH Josette Vieau (1833 entry 10), and he "
     "stands godfather to the daughter of Jacob Vieau (1833 entry 8). A husband, his "
     "wife and her kin named together across three entries is not a surname match. "
     "SECOND, THE TRADE AND THE TWO TOWNS: the resident card is minted from the "
     "Chicago Democrat, and the newspaper gazetteer's entity for this name carries "
     "the occupation merchant and the associated places Chicago AND Milwaukee \u2014 "
     "while this book's own reading notes name him 'Salomon Juneau of Milwaukee'. "
     "Milwaukee is the agreement; it is the one attribute that would separate a "
     "second Solomon Juneau and instead it joins them. THIRD, THE WINDOW CLOSES: his "
     "last reading here is 29 June 1834, and his advertisement is dated over his own "
     "name 'Chicago, July 2, 1834' \u2014 three days later. RESIDENCE IS NOT CLAIMED "
     "AND IS NOT IMPLIED. Sponsorship at a font is not residence, and `at_chicago` on "
     "a reading is about the ENTRY, not the man: he had every reason to stand "
     "godfather at Chicago and the record gives him none to sleep there. His own "
     "advertisement is the proof of it \u2014 he offers a corner parcel of Block 18 on "
     "South Water Street to lease and sends enquiries 'to the Printing office', which "
     "is how an owner lets ground he is not in the town to show. The resident card "
     "already carries present_on_scene_date 'uncertain'; THIS PASS DOES NOT DISTURB "
     "IT, and what is merged is an IDENTITY, not a residence."),
]

REFUSALS = [
    ("Archange Beaubien", "Col. Jean Baptiste Beaubien",
     "\"Archange Beaubien\" and \"Col. Jean Baptiste Beaubien\" share a surname and "
     "nothing else. The register calls her the niece of Mark Beaubien; the layer holds "
     "four Beaubiens and none of them is an Archange. A surname match inside a large "
     "family is the emptiest evidence there is."),
    ("Monique Nadeau", "Josette LaFramboise Beaubien",
     "\"Monique Nadeau\" is Mark Beaubien's wife in the register and \"Josette "
     "LaFramboise Beaubien\" is Jean Baptiste's in the layer. Two different women "
     "married to two different Beaubien brothers, and the register writes Monique "
     "under her married name — 'Monique Beaubien', 'Monique Nadeau Beaubien' — often "
     "enough that a careless pass would fold them. It is refused."),
    ("Joseph Beaubien", "Madore Benjamin Beaubien",
     "\"Joseph Beaubien\" stands as godfather in 1833 entry 18 and \"Madore Benjamin "
     "Beaubien\" is in the residents layer. The forenames disagree outright. No merge, "
     "on a surname that four resident records already share."),
    ("Charles Beaubien", "Col. Jean Baptiste Beaubien",
     "\"Charles Beaubien\" is a father in 1834 entry 21 and no \"Col. Jean Baptiste "
     "Beaubien\" forename reaches him. He is a fifth Beaubien the layer does not hold, "
     "and that is the finding, not a merge."),
    ("Esther Bailly", "Joseph Bailly",
     "\"Esther Bailly\" and \"Joseph Bailly\" share a surname and disagree on the "
     "forename and the sex. The Bailly family of the Calumet is large and this project "
     "holds one of them; a surname is a clue about the family and says nothing about "
     "the person."),
    ("Elozina Bailly", "Joseph Bailly",
     "\"Elozina Bailly\" and \"Joseph Bailly\" share a surname only, and \"Elozina\" is "
     "itself an uncertain reading. Refused twice over."),
    ("Mathias Smith", "Elded Smith",
     "\"Mathias Smith\" and \"Elded Smith\" share the commonest surname in the "
     "language and disagree on the forename. There is no evidence here at all."),
    ("Mary Murphy", "Harriet Murphy",
     "\"Mary Murphy\" sponsors 1835 entry 1 and \"Harriet Murphy\" is in the layer. "
     "The forenames disagree. That the layer's John Murphy IS the register's is no "
     "argument for folding a second Murphy into a third."),
    ("Bridget Murphy", "Harriet Murphy",
     "\"Bridget Murphy\" is named in the register only as 'Brigitte his wife' and "
     "\"Harriet Murphy\" is a distinct forename in the layer. The register's Mrs "
     "Murphy is the wife of the merged John Murphy, and the right home for her "
     "forename is HIS household record — a job for T-0515, not a merge to a different "
     "woman here."),
    ("John Murray", "Alonzo Murray",
     "\"John Murray\" and \"Alonzo Murray\" share a surname and disagree on the "
     "forename. Murray and Murphy are also close enough in this priest's hand to be "
     "worth saying: they are read as written and neither is folded into the other."),
    ("Catherine Murray", "Alonzo Murray",
     "\"Catherine Murray\" and \"Alonzo Murray\" share a surname only."),
    ("Catherine Miller", "John Miller",
     "\"Catherine Miller\" and \"John Miller\" share a surname only, and Miller is a "
     "common one in a town this German and this Irish."),
    ("Catherine Chandler", "Joseph Chandler",
     "\"Catherine Chandler\" is the mother of 1835 entry 13 and \"Joseph Chandler\" is "
     "the resident merged above. They plainly belong to one household — he stands as "
     "godfather to her child — but a household is not a person, and no source read "
     "here gives Catherine Chandler a place in the residents layer. She is a woman the "
     "register adds, not a woman it identifies."),
    ("Bridget Forster", "Jane Forster",
     "\"Bridget Forster\" sponsors the last entry of 1835 and \"Jane Forster\" is in "
     "the layer. The forenames disagree."),
    ("Marie Louise Ouilmette", "Antoine Ouilmette",
     "\"Marie Louise Ouilmette\" is read from the register's 'Wimette' and \"Antoine "
     "Ouilmette\" is the man the name calls to mind. He is not in the residents layer "
     "at all, and even if he were, the register gives her only a husband, John Welsh, "
     "and no father. A famous surname is the most dangerous kind of surname match and "
     "this one is refused explicitly so the next pass does not make it."),
    ("Bourrasso", "Léon Bourassa",
     "\"Bourrasso\" stands alone as a witness in 1835 entry 3 and \"Léon Bourassa\" is "
     "a father in the same book. A surname with no forename is always a refusal, and "
     "this book holds at least two Bourassas — Léon and his son Jean Baptiste — so the "
     "bare surname does not even narrow to one of them."),
    ("L. Chevalier", "Josette Chevalier",
     "\"L. Chevalier\" is an initial and a surname and \"Josette Chevalier\" is a "
     "sponsor elsewhere in the same book. An initial that does not match a forename is "
     "one step below a surname match, not one above it."),
    ("Doctor Egan", "Emeline Egan",
     "\"Doctor Egan\" is merged above to Dr William Bradshaw Egan and is here refused "
     "against \"Emeline Egan\", the layer's only other Egan. The refusal is written "
     "down because the merge above depends on it: the title separates them, and if it "
     "did not, neither identification could stand."),
    ("Josette Chevalier", "Josette Chevalier",
     "\"Josette Chevalier\" sponsors 1833 entries 11 and 12 and stands godmother at "
     "1834 entry 12, and \"Josette Chevalier\" is in the residents layer as the bride "
     "of Mark Bourassa, married at Chicago in March 1835. THE NAMES AGREE EXACTLY AND "
     "THAT IS THE WHOLE OF WHAT AGREES. Everything else the pair shares \u2014 the "
     "parish, the priest, the town, the nineteen months \u2014 is a restatement of WHERE "
     "BOTH READINGS WERE FOUND, because both sides are ONE MANUSCRIPT: the layer's "
     "person is minted from st_cyr_marriage_005_2, the marriage list of the same "
     "Father St Cyr whose baptism book this is. That fails the test every merge above "
     "passes, which is two sources that did not copy each other. And this book holds a "
     "SECOND Chevalier presence \u2014 Joseph Chevalier, a child born at the Rivi\u00e8re au "
     "Sable and baptised at Chicago on 20 October 1833, and 'L. Chevalier', a witness "
     "of 6 June 1835 who is refused above \u2014 so a Chevalier kin group stands at "
     "Chicago from which a second Josette is not excluded by anything read here. SHE "
     "IS VERY PROBABLY ONE WOMAN. Probably is not a confidence grade, and writing the "
     "merge would put the word 'documented' over an inference. WHAT WOULD OVERTURN "
     "THIS: a source outside St Cyr's own register that names her, or an entry naming "
     "the same husband or household on both sides."),
    ("Patrick Carroll", "Patrick Carroll",
     "\"Patrick Carroll\" sponsors 1835 entry 1, the first entry of the scene year, and "
     "\"Patrick Carroll\" is in the residents layer as the groom of Mary Hogan, married "
     "at Chicago on 21 April 1835. Refused on the ground that refuses Josette "
     "Chevalier above, and more heavily. The names agree exactly and nothing else "
     "agrees that is independent of where the readings were found: the layer's person "
     "is minted from st_cyr_marriage_007_1, the marriage list of this book's own "
     "priest, so the shared parish and the eight weeks between 23 February and 21 "
     "April are ONE FACT and not two agreements. THE NAME IS ALSO A COMMON ONE: the "
     "layer holds six Patricks, and the priest's margin against this very entry reads "
     "one word, 'Irish' \u2014 this register exists to show that the Irish and French "
     "Catholic town was larger than the poll books knew, which is exactly why a "
     "second Patrick Carroll in it cannot be ruled out. John Murphy is MERGED above "
     "because a wife and a hotel stand beside his equally common name. Nothing stands "
     "beside this one."),
    ("Mary Durbin", "Mary Durbin",
     "\"Mary Durbin\" is the mother of 1834 entry 8 and \"Mary Durbin\" is in the "
     "residents layer. The names agree exactly and the two records CONTRADICT each "
     "other on the single attribute both carry \u2014 a husband. The register makes her "
     "the mother of Marguerite, daughter of Samuel Henriks, born 13 December 1833 and "
     "baptised on 25 May 1834; this register writes mothers under their MAIDEN names "
     "throughout (Josette Vieau, Adelaide Bouchard, Monique Nadeau), so its Mary "
     "Durbin is Samuel Henriks' wife. The layer's Mary Durbin is minted from "
     "st_cyr_marriage_002_2: the bride of JOHN SIMMONS, married five days earlier on "
     "20 May 1834. One woman does not marry two men in five days and nothing read "
     "here widows her. NEITHER READING IS AT CHICAGO: the baptism is written at the "
     "South Fork of the Sangamon and the marriage at Bear Creek, Sangamon County, in "
     "the house the article's footnote calls Hy Durbin's \u2014 central Illinois, not "
     "Cook County. AND THE SURNAME IS THAT SETTLEMENT'S, NOT A PERSON'S: one week of "
     "the priest's journey names John, Philipp, Thomas, William, Elisabeth, "
     "Marguerite, Ann, Oro and Mary Durbin across six entries, and it repeats its "
     "forenames across generations \u2014 a Marguerite Durbin is BAPTISED AS A CHILD in "
     "1834 entry 3 and a Marguerite Durbin stands as a MOTHER in 1834 entry 6. An "
     "exact name inside a clan that reuses its names, disagreeing on the husband, in "
     "a county this town is not in, is a refusal three times over. A SEPARATE FINDING, "
     "not this crosswalk's to fix: the layer's card reads that the church list 'names "
     "this person at Chicago by 20 May 1834' while the marriage record it cites says "
     "in capitals that it is not Chicago and 'is not evidence of anybody standing in "
     "Chicago'. That is a defect in the residents layer and it is filed as its own "
     "ticket."),
]


def _resident_people():
    people = []
    for path in sorted(RESIDENTS.glob("*.json")):
        doc = load(path)
        for person in doc.get("persons") or []:
            people.append({
                "name": person.get("name") or "",
                "person_id": person.get("id"),
                "household": doc.get("id"),
                "grade": person.get("grade"),
            })
    return people


def _fold(name):
    out = name.lower().replace(".", "").replace(",", "")
    return " ".join(out.split())


def _surname(name):
    parts = [p for p in _fold(name).split()
             if p not in ("mr", "mrs", "miss", "dr", "doctor", "rev", "col", "m")]
    return parts[-1] if parts else ""


def crosswalk_doc():
    rows = build_records()
    people = _resident_people()
    by_surname = {}
    for person in people:
        by_surname.setdefault(_surname(person["name"]), []).append(person)

    merged = {frm for frm, _, _, _ in MERGES}
    refused = set()
    for a, b, _ in REFUSALS:
        refused.add(a)

    adults, seen = [], {}
    for row in rows:
        if not row["adult"]:
            continue
        seen.setdefault(row["normalized"], []).append(row)

    outcomes = []
    for name in sorted(seen):
        rowset = seen[name]
        at_chicago = any(r["at_chicago"] for r in rowset)
        candidates = by_surname.get(_surname(name), [])
        # An EXACT name is not the surname-only case and must not be filed under its
        # rule, whose whole ground is that no forename agrees. See T-1110: the
        # residents layer grew from 849 people to over 1,300 after this pass was
        # written, and four adults it had found no candidate for now have a namesake
        # in it who folds identically. Saying "no forename agrees" over those would
        # be a false statement in a provenance artifact.
        exact = [c["name"] for c in candidates if _fold(c["name"]) == _fold(name)]
        if name in merged:
            outcome = "merged"
        elif name in refused:
            outcome = "refused"
        elif exact:
            outcome = "exact_name_unruled"
        elif candidates:
            outcome = "refused_surname_only"
        else:
            outcome = "no_candidate"
        outcomes.append({
            "name": name,
            "readings": len(rowset),
            "at_chicago": at_chicago,
            "roles": sorted({r["cells"]["role"] for r in rowset}),
            "entries": sorted({"%s/%s" % (r["locator"]["year_series"], r["locator"]["entry"])
                               for r in rowset}),
            "resident_surname_candidates": [c["name"] for c in candidates],
            "resident_exact_name_matches": exact,
            "adjudication": outcome,
        })

    counted = {"merged": 0, "refused": 0, "exact_name_unruled": 0,
               "refused_surname_only": 0, "no_candidate": 0}
    chicago_counted = dict(counted)
    for o in outcomes:
        counted[o["adjudication"]] += 1
        if o["at_chicago"]:
            chicago_counted[o["adjudication"]] += 1

    nowhere = sorted(o["name"] for o in outcomes
                     if o["at_chicago"] and o["adjudication"] == "no_candidate")

    # The pairs the next pass owes a ruling. Listed by name so it is a worklist and
    # not a count somebody has to go and reconstruct.
    exact_unruled = [
        {"register_name": o["name"], "resident_names": o["resident_exact_name_matches"],
         "readings": o["readings"], "at_chicago": o["at_chicago"], "entries": o["entries"]}
        for o in outcomes if o["adjudication"] == "exact_name_unruled"
    ]

    # ONE RULING PER READING, anchored to the row it rules on. The summary above is
    # by NAME, and a name read in three entries is three readings; the spend gate
    # measures readings, and a reading nobody has ruled on is exactly what it exists
    # to find. A child gets a ruling too, and the ruling says why it is not
    # crosswalked — the absence of one is indistinguishable from an oversight.
    by_name = {o["name"]: o for o in outcomes}
    rulings = []
    for row in rows:
        if row["adult"]:
            o = by_name[row["normalized"]]
            verdict = o["adjudication"]
            why = {
                "merged": "Merged to a person in the residents layer; the rule is in "
                          "merges[] and names both spellings verbatim.",
                "refused": "Refused against a named rival in the residents layer; the "
                           "rule is in refusals[].",
                "refused_surname_only": "REFUSED ON THE STANDING RULE: the residents "
                                        "layer holds this surname and no forename "
                                        "agrees, and a surname-only merge is always a "
                                        "refusal.",
                "exact_name_unruled": "AN EXACT NAME, AND NOBODY HAS RULED ON IT. The "
                                      "residents layer holds a person whose name folds "
                                      "identically to this one, and neither merges[] nor "
                                      "refusals[] names the pair. It is NOT the standing "
                                      "surname-only refusal, whose ground is that no "
                                      "forename agrees — here one does. It is not merged "
                                      "either: a merge needs a written rule naming both "
                                      "spellings, and there is none. The pair is listed "
                                      "in exact_name_unruled[] for the pass that rules "
                                      "on it; until then this reading is crosswalked to "
                                      "nobody.",
                "no_candidate": "NO CANDIDATE AT ALL — the residents layer holds no "
                                "person of this surname. This is the finding, not a "
                                "failure: it is the Catholic town the poll books and "
                                "the letter lists never reached.",
            }[verdict]
        else:
            verdict = "child_not_crosswalked"
            why = ("A CHILD, and this pass does not crosswalk children. A child "
                   "baptised in 1833-35 is named by no other source this project "
                   "holds, so there is nothing to match against, and minting one off "
                   "a baptism alone is precisely what the ratified ladder forbids. "
                   "Ruled on so the next sweep does not read this row as unexamined.")
        rulings.append({
            "record_id": row["id"],
            "name": row["normalized"],
            "role": row["cells"]["role"],
            "at_chicago": row["at_chicago"],
            "outcome": verdict,
            "rule": why,
        })
    for claim in build_claims():
        rulings.append({
            "claim_id": claim["id"],
            "name": claim["normalized"][:80],
            "role": "town_finding",
            "at_chicago": True,
            "outcome": "not_a_person",
            "rule": "A TOWN FINDING, not a reading of a person: it says something about "
                    "the place, the date or the clothing and there is nobody in it to "
                    "crosswalk. Ruled on so it is not counted as a name nobody has "
                    "looked at.",
        })

    return {
        "schema": 1,
        "_doc": "GENERATED by tools/read_st_marys_baptisms.py --build. The scene-year "
                "pass of St Mary's baptismal register against data/residents/. The "
                "merges and refusals are hand-authored in the tool and adjudicated one "
                "by one; the COUNTS and the outcome of every other adult are derived, so "
                "an adult nobody has ruled on cannot hide. Hand-edit and --check says so.",
        "generated_by": "tools/read_st_marys_baptisms.py",
        "domain": "church",
        "source_id": SOURCE_ID,
        "pass": "T-0503",
        "what": "Every ADULT named in the eleven page images — parents, godparents, "
                "sponsors, witnesses, spouses and the officiant — held against the %d "
                "people data/residents/ holds today. That count is DERIVED and it "
                "moves: the layer stood at 849 when T-0503 wrote this pass, and a "
                "crosswalk built against a layer that has since grown is stale rather "
                "than wrong — which is what T-1110 found and why --check now says "
                "which of the three it is." % len(people),
        "the_rule": "A merge needs a written rule naming BOTH spellings verbatim; a "
                    "surname-only merge is always a refusal; an EXACT name with no "
                    "written rule is neither, and is held in exact_name_unruled[] "
                    "rather than filed under a refusal whose stated ground is untrue "
                    "of it; a refusal is declared as explicitly as a merge. Nothing "
                    "here mints or regrades a resident — T-0514 and T-0515 spend this "
                    "file.",
        "counts": {
            "adult_readings": sum(1 for r in rows if r["adult"]),
            "distinct_adult_names": len(outcomes),
            "residents_examined": len(people),
            "all_places": counted,
            "chicago_entries_only": chicago_counted,
            "chicago_adults_present_nowhere_else": len(nowhere),
        },
        "the_finding": "Of the %d distinct adults the register names in its CHICAGO "
                       "entries, %d reach no surname in the residents layer at all. They "
                       "are the French, Métis, Irish and German Catholic town that the "
                       "poll books (which recorded only men who voted) and the post "
                       "office's letter lists do not reach — and they are what the "
                       "owner's ask was for."
                       % (sum(1 for o in outcomes if o["at_chicago"]), len(nowhere)),
        "chicago_adults_present_nowhere_else": nowhere,
        "exact_name_unruled": exact_unruled,
        "counts_by_ruling": {k: sum(1 for r in rulings if r["outcome"] == k)
                             for k in sorted({r["outcome"] for r in rulings})},
        "merges": [
            {"into": into, "from": frm, "rule": rule, "evidence": ev}
            for frm, into, ev, rule in MERGES
        ],
        "refusals": [
            {"a": a, "b": b, "rule": rule,
             "evidence": ["data/research/church/records/st_marys_baptisms_1833_1835.json",
                          "data/residents/households/"]}
            for a, b, rule in REFUSALS
        ],
        "adults": outcomes,
        "rulings": rulings,
    }


def write(path, doc):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def cmd_build():
    write(RECORDS, records_doc())
    write(CLAIMS, claims_doc())
    write(CROSSWALK, crosswalk_doc())
    t = tallies()
    print("  built %s — %d entries, %d readings"
          % (RECORDS.relative_to(ROOT), len(ENTRIES), len(build_records())))
    print("  built %s — %d town findings" % (CLAIMS.relative_to(ROOT), len(TOWN_FINDINGS)))
    xw = crosswalk_doc()
    print("  built %s — %d merges, %d refusals, %d Chicago adults present nowhere else"
          % (CROSSWALK.relative_to(ROOT), len(MERGES), len(REFUSALS),
             xw["counts"]["chicago_adults_present_nowhere_else"]))
    for y in sorted(t):
        print("    %d: %d entries (the book's own pencil tally: %d)" % (y, t[y], BOOK_TALLY[y]))


def _why_it_differs(path):
    """Say WHICH of the three it is, rather than name two and leave the reader to guess.

    T-1110 is the reason this exists. The old message offered a hand edit or a tool
    change and could tell them apart from neither — and the actual cause was a THIRD
    thing it did not name: the crosswalk's INPUT, data/residents/, had grown from 849
    people to over 1,300 since the pass was written, while neither the file nor the
    tool had been touched since the commit that landed both. That is staleness, and it
    is answered by a rebuild that costs nothing; a hand edit is a ruling somebody made
    that a rebuild would erase, and the two must not read alike.

    The committed file records the count it was built against, so the input case can
    be recognised for what it is instead of inferred.
    """
    if path != CROSSWALK:
        return "It has been hand-edited or the tool has changed."
    try:
        was = json.loads(path.read_text(encoding="utf-8"))["counts"]["residents_examined"]
    except Exception:
        return "It has been hand-edited or the tool has changed."
    now = len(_resident_people())
    if was != now:
        return ("Its INPUT moved: it was built against %d people in data/residents/ and "
                "that layer holds %d today, so this is staleness and not a hand edit."
                % (was, now))
    return ("The residents layer still holds the %d people it was built against, so "
            "this is a hand edit or a change to the tool, not staleness." % now)


def cmd_check():
    bad = []
    for path, doc in ((RECORDS, records_doc()), (CLAIMS, claims_doc()),
                      (CROSSWALK, crosswalk_doc())):
        if not path.exists():
            bad.append("%s is missing — run --build" % path.relative_to(ROOT))
            continue
        want = json.dumps(doc, indent=2, ensure_ascii=False) + "\n"
        if path.read_text(encoding="utf-8") != want:
            bad.append("%s is not what tools/read_st_marys_baptisms.py says. %s Rebuild it."
                       % (path.relative_to(ROOT), _why_it_differs(path)))

    # The book's own arithmetic. A reading that misses it has lost or invented an entry.
    t = tallies()
    for year, want in BOOK_TALLY.items():
        got = t.get(year, 0)
        if got != want:
            bad.append("%d: %d entries read against the book's own pencil tally of %d"
                       % (year, got, want))

    # Every declared image must be reached by a record or a claim, and nothing may
    # reach an image the deposit does not hold.
    declared = {i for i, _, _ in IMAGES}
    reached = {r["locator"]["image"] for r in build_records()}
    reached |= {c["locator"]["image"] for c in build_claims()}
    reached |= {o["img"] for o in OUT_OF_WINDOW}
    for img in sorted(declared - reached):
        bad.append("image %s is declared and nothing in the reading reaches it" % img)
    for img in sorted(reached - declared):
        bad.append("image %s is reached and is not one of the eleven declared" % img)

    # Ids are the join key everything else uses; a duplicate silently drops a person.
    ids = [r["id"] for r in build_records()]
    if len(ids) != len(set(ids)):
        bad.append("duplicate record id in the reading")

    for b in bad:
        print("  FAIL  " + b)
    if not bad:
        # The exact-name bucket is a WORKLIST and it refills silently: the layer grows,
        # the rebuild that answers the staleness message quietly re-derives a new pair,
        # and nothing says so. T-1128 emptied it; this line is what keeps it visible.
        unruled = len(crosswalk_doc()["exact_name_unruled"])
        print("  st_marys_baptisms: %d entries, %d readings, %d town findings, %d images "
              "— and the book's own tallies agree"
              % (len(ENTRIES), len(ids), len(TOWN_FINDINGS), len(IMAGES)))
        print("  st_marys_baptisms: %d exact-name pair(s) awaiting a written ruling%s"
              % (unruled, "" if not unruled else
                 " — see exact_name_unruled[] in the crosswalk; each needs a rule in "
                 "MERGES or REFUSALS, never an edit to the JSON"))
    return bad


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    if args.build:
        cmd_build()
        return 0
    if args.check:
        return 1 if cmd_check() else 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
