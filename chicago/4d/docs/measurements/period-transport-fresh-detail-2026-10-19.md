# Complete split fresh pricing diagnostic

Split diagnostic runs using forced two production steps and GPU finish, keep-geometry=1. Initial run timed out after27 rows; continuation supplies9. Not one completed CI smoke run; no claim of exact causality relative to normal unforced CI samples.

Validated **36 unique finite rows**, exactly2 viewports ×3 tiers ×6 stands.

|Tier|Worst triangles|Triangle location(s)|Worst calls|Call location(s)|Current cap|Candidate cap|Candidate headroom|
|---|---:|---|---:|---|---:|---:|---:|
|full|3,449,919|desktop 1280x800 / prairie_west|319|desktop 1280x800 / lake_and_market|3,400,000|3,470,000|20,081|
|balanced|2,607,952|desktop 1280x800 / prairie_west|314|desktop 1280x800 / lake_and_market|2,535,000|2,625,000|17,048|
|light|1,154,091|desktop 1280x800 / prairie_west|89|desktop 1280x800 / lake_and_market|1,190,000|1,190,000|35,909|

Arithmetic candidates preserve18,059 full /16,806 balanced headroom before rounding up to5,000. Light remains 1,190,000. General calls cap remains 330; the separate light-tier 90-call floor also remains unchanged (measured worst 89, only 1 call of headroom). Full/balanced retain 330. No constants are changed.

|Viewport|Tier|Stand|Triangles|Calls|Split|
|---|---|---|---:|---:|---|
|desktop 1280x800|full|lake_at_canal|3,076,607|306|initial480s_partial|
|desktop 1280x800|full|the_forks|2,709,399|259|initial480s_partial|
|desktop 1280x800|full|from_above|2,249,867|228|initial480s_partial|
|desktop 1280x800|full|lake_and_market|2,846,348|319|initial480s_partial|
|desktop 1280x800|full|prairie_west|3,449,919|301|initial480s_partial|
|desktop 1280x800|full|sauganash_26|2,094,094|229|initial480s_partial|
|desktop 1280x800|balanced|lake_at_canal|2,416,472|278|initial480s_partial|
|desktop 1280x800|balanced|the_forks|2,103,992|232|initial480s_partial|
|desktop 1280x800|balanced|from_above|1,764,711|223|initial480s_partial|
|desktop 1280x800|balanced|lake_and_market|2,299,343|314|initial480s_partial|
|desktop 1280x800|balanced|prairie_west|2,607,952|271|initial480s_partial|
|desktop 1280x800|balanced|sauganash_26|1,688,562|226|initial480s_partial|
|desktop 1280x800|light|lake_at_canal|1,010,661|61|initial480s_partial|
|desktop 1280x800|light|the_forks|939,454|64|initial480s_partial|
|desktop 1280x800|light|from_above|655,344|55|initial480s_partial|
|desktop 1280x800|light|lake_and_market|831,667|89|initial480s_partial|
|desktop 1280x800|light|prairie_west|1,154,091|85|initial480s_partial|
|desktop 1280x800|light|sauganash_26|648,718|75|initial480s_partial|
|mobile 390x780|full|lake_at_canal|2,640,406|283|initial480s_partial|
|mobile 390x780|full|the_forks|2,199,247|240|initial480s_partial|
|mobile 390x780|full|from_above|2,097,244|210|initial480s_partial|
|mobile 390x780|full|lake_and_market|2,257,978|274|initial480s_partial|
|mobile 390x780|full|prairie_west|3,030,587|300|initial480s_partial|
|mobile 390x780|full|sauganash_26|1,489,688|181|initial480s_partial|
|mobile 390x780|balanced|lake_at_canal|2,113,887|254|initial480s_partial|
|mobile 390x780|balanced|the_forks|1,739,296|208|initial480s_partial|
|mobile 390x780|balanced|from_above|1,632,084|208|initial480s_partial|
|mobile 390x780|balanced|lake_and_market|1,853,041|270|mobile_continuation|
|mobile 390x780|balanced|prairie_west|2,313,680|246|mobile_continuation|
|mobile 390x780|balanced|sauganash_26|1,239,846|178|mobile_continuation|
|mobile 390x780|light|lake_at_canal|845,506|56|mobile_continuation|
|mobile 390x780|light|the_forks|756,763|55|mobile_continuation|
|mobile 390x780|light|from_above|593,542|72|mobile_continuation|
|mobile 390x780|light|lake_and_market|656,037|85|mobile_continuation|
|mobile 390x780|light|prairie_west|977,672|74|mobile_continuation|
|mobile 390x780|light|sauganash_26|422,840|63|mobile_continuation|

Source receipt verifies trees.js and tree-model.js match frozen e5; main.js differs only by the human role-card import/listener, with no human actors placed. No attestation that all rendering modules match. Aggregator validates numeric coverage only, not source hashes.

Arithmetic candidate only; no app/budget change. Full/balanced preserve original absolute margins; light remains1190000. Actual scene/period/photographic acceptance is separate.
