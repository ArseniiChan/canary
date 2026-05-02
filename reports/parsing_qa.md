# Parsing QA

**Overall:** 73/78 filings successfully parsed (**93.6%** success). Hard gate: >= 80%.

## Success rate by fraud/peer status

| Kind | Successful | Total | Rate |
|---|---|---|---|
| fraud | 6 | 6 | 100.0% |
| peer | 67 | 72 | 93.1% |

## Success rate by period year

| Year | Successful | Total | Rate |
|---|---|---|---|
| 2000 | 9 | 13 | 69.2% |
| 2001 | 38 | 39 | 97.4% |
| 2007 | 13 | 13 | 100.0% |
| 2014 | 13 | 13 | 100.0% |

## Per-cohort detail

### ENE cohort

- 9/13 parsed successfully (69.2%)

| Kind | CIK | Accession | Method | Chars | Sentences | Error |
|---|---|---|---|---|---|---|
| fraud | 0001024401 | `0001024401-01-500010` | first_item7_after_toc__last_item7a | 42,579 | 211 |  |
| peer | 0000745774 | `0000912057-01-007737` | first_item7_after_toc__last_item7a | 19,731 | 123 |  |
| peer | 0000888165 | `0000950135-01-000998` | first_item7_after_toc__last_item7a | 23,613 | 145 |  |
| peer | 0000922575 | `0000950137-01-500580` | first_item7_after_toc__last_item8 | 15,919 | 83 |  |
| peer | 0000922811 | `0000922811-01-500021` | first_item7_after_toc__last_item7a | 14,175 | 93 |  |
| peer | 0001023844 | `0001015769-00-000348` | missing_primary_document | 0 | 0 | raw filing not found at data/raw/edgar/filings/000101576900000348/0001.txt |
| peer | 0001033926 | `0001068800-01-500094` | no_end_boundary | 0 | 0 | Could not locate Item 7A / Item 8 / financial-statements anchor |
| peer | 0001085095 | `0000950123-01-000629` | first_item7_after_toc__last_item7a | 43,355 | 202 |  |
| peer | 0001103945 | `0000912057-01-506021` | first_mdna_anchor_after_toc__last_item7a | 53,891 | 386 |  |
| peer | 0001105018 | `0000950123-01-002844` | first_item7_after_toc__last_item7a | 31,663 | 203 |  |
| peer | 0000038777 | `0000038777-00-000380` | missing_primary_document | 0 | 0 | raw filing not found at data/raw/edgar/filings/000003877700000380/0001.txt |
| peer | 0000052234 | `0000052234-01-000044` | missing_primary_document | 0 | 0 | raw filing not found at data/raw/edgar/filings/000005223401000044/0001.txt |
| peer | 0000065100 | `0000950130-01-500261` | first_mdna_anchor_after_toc__last_item7a | 74,328 | 356 |  |

### HRC cohort

- 12/13 parsed successfully (92.3%)

| Kind | CIK | Accession | Method | Chars | Sentences | Error |
|---|---|---|---|---|---|---|
| fraud | 0000785161 | `0001005150-02-000448` | first_item7_after_toc__last_item8 | 43,013 | 268 |  |
| peer | 0000820474 | `0000892569-02-000552` | first_item7_after_toc__last_item7a | 11,263 | 87 |  |
| peer | 0000893949 | `0000950144-02-003022` | first_item7_after_toc__last_item7a | 39,487 | 189 |  |
| peer | 0000005197 | `0001116502-02-000019` | first_item7_after_toc__last_item8 | 11,270 | 70 |  |
| peer | 0000022872 | `0000950144-01-506401` | first_item7_after_toc__last_item8 | 26,614 | 132 |  |
| peer | 0000070318 | `0000912057-01-529717` | first_mdna_anchor_after_toc__last_item7a | 89,337 | 414 |  |
| peer | 0000096793 | `0000950144-01-504160` | first_item7_after_toc__last_item7a | 21,753 | 108 |  |
| peer | 0000352915 | `0000928385-02-001053` | first_item7_after_toc__last_item7a | 65,936 | 329 |  |
| peer | 0000720847 | `0000720847-01-500009` | no_anchor_pair | 0 | 0 | no candidate pair produced a usable body |
| peer | 0000731012 | `0000950116-02-000413` | first_item7_after_toc__last_item8 | 24,536 | 132 |  |
| peer | 0000732247 | `0001142207-04-000098` | first_item7_after_toc__last_item7a | 18,106 | 98 |  |
| peer | 0000737561 | `0000737561-02-000002` | first_item7_after_toc__last_item7a | 26,092 | 138 |  |
| peer | 0000739944 | `0000739944-02-000006` | first_item7_after_toc__last_item7a | 31,592 | 167 |  |

### LEH cohort

- 13/13 parsed successfully (100.0%)

| Kind | CIK | Accession | Method | Chars | Sentences | Error |
|---|---|---|---|---|---|---|
| fraud | 0000806085 | `0001104659-08-005476` | first_item7_after_toc__last_item7a | 214,554 | 1051 |  |
| peer | 0000065100 | `0000950123-08-002050` | last_mdna_anchor__last_finstmt_anchor | 23,560 | 134 |  |
| peer | 0000316709 | `0001193125-08-039024` | first_item7_after_toc__last_item7a | 86,941 | 404 |  |
| peer | 0000350894 | `0001193125-08-038641` | first_item7_after_toc__last_item7a | 62,462 | 313 |  |
| peer | 0000718482 | `0001206774-07-001180` | first_item7_after_toc__last_item7a | 78,074 | 427 |  |
| peer | 0000720672 | `0000720672-08-000046` | first_item7_after_toc__last_item7a | 112,987 | 461 |  |
| peer | 0000815917 | `0001068800-08-000132` | first_item7_after_toc__last_item7a | 39,228 | 186 |  |
| peer | 0000878520 | `0001193125-07-199182` | last_mdna_anchor__last_quantitative_anchor | 81,685 | 414 |  |
| peer | 0000895421 | `0001193125-08-013719` | first_item7_after_toc__last_item7a | 199,534 | 1017 |  |
| peer | 0000920424 | `0001047469-08-002065` | first_item7_after_toc__last_item7a | 225,737 | 1034 |  |
| peer | 0000944696 | `0000944696-08-000006` | first_item7_after_toc__last_item7a | 25,484 | 150 |  |
| peer | 0001001871 | `0001001871-07-000006` | first_item7_after_toc__last_item7a | 79,555 | 387 |  |
| peer | 0001052100 | `0001047469-08-001998` | first_item7_after_toc__last_item7a | 185,708 | 836 |  |

### TYC cohort

- 13/13 parsed successfully (100.0%)

| Kind | CIK | Accession | Method | Chars | Sentences | Error |
|---|---|---|---|---|---|---|
| fraud | 0000833444 | `0000912057-01-544874` | last_mdna_anchor__last_quantitative_anchor | 59,159 | 296 |  |
| peer | 0000824142 | `0001026608-02-000004` | first_item7_after_toc__last_item7a | 12,350 | 78 |  |
| peer | 0000880591 | `0000880591-02-000004` | first_item7_after_toc__last_item8 | 46,719 | 234 |  |
| peer | 0001005272 | `0000912057-01-533690` | first_item7_after_toc__last_item7a | 25,612 | 149 |  |
| peer | 0001069202 | `0001116320-02-000064` | first_item7_after_toc__last_item7a | 38,640 | 231 |  |
| peer | 0000007623 | `0000007623-02-000002` | first_item7_after_toc__last_item7a | 18,028 | 119 |  |
| peer | 0000008146 | `0000927016-01-500246` | first_item7_after_toc__last_item7a | 14,263 | 108 |  |
| peer | 0000012355 | `0000012355-02-000007` | first_item7_after_toc__last_item7a | 52,127 | 221 |  |
| peer | 0000014930 | `0000950137-02-001164` | first_item7_after_toc__last_item7a | 56,962 | 314 |  |
| peer | 0000018061 | `0000912057-01-511762` | first_item7_after_toc__last_item7a | 21,132 | 127 |  |
| peer | 0000019871 | `0000950137-02-001604` | first_item7_after_toc__last_item7a | 19,460 | 119 |  |
| peer | 0000024008 | `0000950152-02-002538` | first_item7_after_toc__last_item7a | 18,628 | 103 |  |
| peer | 0000026324 | `0000950117-02-000522` | first_mdna_anchor_after_toc__last_item7a | 29,354 | 169 |  |

### VRX cohort

- 13/13 parsed successfully (100.0%)

| Kind | CIK | Accession | Method | Chars | Sentences | Error |
|---|---|---|---|---|---|---|
| fraud | 0000885590 | `0000885590-15-000015` | first_item7_after_toc__last_item7a | 153,830 | 566 |  |
| peer | 0000001800 | `0001047469-15-001377` | first_item7_after_toc__last_item7a | 81,198 | 434 |  |
| peer | 0000014272 | `0000014272-15-000055` | first_item7_after_toc__last_item7a | 116,705 | 515 |  |
| peer | 0000025743 | `0001387131-15-000875` | first_item7_after_toc__last_item7a | 51,212 | 257 |  |
| peer | 0000034956 | `0001354488-14-003782` | first_item7_after_toc__last_item7a | 27,077 | 108 |  |
| peer | 0000057725 | `0001104659-14-063906` | first_item7_after_toc__last_item7a | 57,488 | 318 |  |
| peer | 0000059478 | `0000059478-15-000100` | first_item7_after_toc__last_item7a | 74,241 | 402 |  |
| peer | 0000072170 | `0001144204-15-022924` | first_item7_after_toc__last_item7a | 10,089 | 66 |  |
| peer | 0000078003 | `0000078003-15-000014` | last_mdna_anchor__last_finstmt_anchor__outside_ideal | 7,082 | 25 |  |
| peer | 0000200406 | `0000200406-15-000004` | first_mdna_anchor_after_toc__last_item7a | 31,732 | 160 |  |
| peer | 0000275053 | `0001104659-15-019269` | first_item7_after_toc__last_item7a | 78,959 | 397 |  |
| peer | 0000310158 | `0000310158-15-000005` | first_item7_after_toc__last_item7a | 201,614 | 1034 |  |
| peer | 0000318306 | `0001144204-15-020126` | first_item7_after_toc__last_item7a | 19,664 | 106 |  |

### WCOM cohort

- 13/13 parsed successfully (100.0%)

| Kind | CIK | Accession | Method | Chars | Sentences | Error |
|---|---|---|---|---|---|---|
| fraud | 0000723527 | `0001005477-02-001226` | first_item7_after_toc__last_item7a | 120,724 | 685 |  |
| peer | 0000011107 | `0000950109-02-001581` | first_item7_after_toc__last_item7a | 28,929 | 158 |  |
| peer | 0000018926 | `0000018926-02-000003` | first_item7_after_toc__last_item7a | 79,095 | 325 |  |
| peer | 0000019719 | `0000950109-02-001582` | first_item7_after_toc__last_item7a | 26,979 | 148 |  |
| peer | 0000019722 | `0000950109-02-001580` | first_item7_after_toc__last_item7a | 27,774 | 151 |  |
| peer | 0000019724 | `0000950109-02-001584` | first_item7_after_toc__last_item7a | 27,793 | 150 |  |
| peer | 0000019725 | `0000950109-02-001590` | first_item7_after_toc__last_item7a | 28,306 | 156 |  |
| peer | 0000028729 | `0000950109-02-001585` | first_item7_after_toc__last_item7a | 28,361 | 155 |  |
| peer | 0000040864 | `0000950109-02-001593` | first_item7_after_toc__last_item7a | 27,635 | 146 |  |
| peer | 0000040865 | `0000950109-02-001594` | first_item7_after_toc__last_item7a | 28,452 | 154 |  |
| peer | 0000040867 | `0000950109-02-001586` | first_item7_after_toc__last_item7a | 30,361 | 163 |  |
| peer | 0000040874 | `0000950109-02-001579` | first_item7_after_toc__last_item7a | 30,045 | 165 |  |
| peer | 0000040877 | `0000950109-02-001591` | first_item7_after_toc__last_item7a | 28,263 | 152 |  |

## Failures (for manual review)

- `0001015769-00-000348`  (ENE/peer)  method=missing_primary_document  chars=0  error=raw filing not found at data/raw/edgar/filings/000101576900000348/0001.txt
- `0001068800-01-500094`  (ENE/peer)  method=no_end_boundary  chars=0  error=Could not locate Item 7A / Item 8 / financial-statements anchor
- `0000038777-00-000380`  (ENE/peer)  method=missing_primary_document  chars=0  error=raw filing not found at data/raw/edgar/filings/000003877700000380/0001.txt
- `0000052234-01-000044`  (ENE/peer)  method=missing_primary_document  chars=0  error=raw filing not found at data/raw/edgar/filings/000005223401000044/0001.txt
- `0000720847-01-500009`  (HRC/peer)  method=no_anchor_pair  chars=0  error=no candidate pair produced a usable body

