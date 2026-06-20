# Prompts for Development

## Prompt for Creating Bible Skill and /bible Command

```
Create a new skill and a new slash command / workflow, to retrieve bible verses:

skill name should be simply bible

slash command should be simply /bible

bible databases are in sqlite format, stored either in ~/biblemate/data/bibles or ~/biblemate/data_custom/bibles

Remember use home variable instead of hardcoding absolute paths, to make this repository portable.

Valid bible database filenames are ended with *.bible

retrieve from table `Verses`

NET.bible is the default bible if no bible version is specified

the command `/bible` can take both bible version(s) and bible reference(s)

if bible version is not specified, NET.bible is the default database for retrieval.  If a specified version, use that version, If more than one version is specified, all specified versions are retrieved with each verse display line by line comparison of the specified versions.

bible references can be single or multiple verse(s), e.g. John 3:16-18; Rm 5-8

bible references can also be a chapter a verse or multiple verse range

examples for use: 

/bible John 3:16 # use NET.bible as default

/bible John 3 # retrieve the whole chapter from the first verse to the last

/bible John 3:16-18; Deut 6:4; Rom 5-8 # retrieve multiple verses from different books.

/bible CUV John 3:16-18 # use CUV.bible as it is specified

/bible NET CUV John 3:16-18 # compare NET CUV every single verse, line by line, from John 3:16 to 3:18

make sure you don't hardcode bible version list available in ~/biblemate/data/bibles and ~/biblemate/data_custom/bibles , as users can dynamatically add or remove bible databases into or from this folder.  Instead of hardcoding a static bible version list, you should always check if bible version specified is a valid name in those folder.
```

```
Should you further improve the bible skill?  Right now, verse comparison like:

John 3:16 [NET] For this is the way God loved the world: He gave his one and only Son, so that everyone who believes in him will not perish but have eternal life. [CUV] 「上帝愛世人，甚至將他的獨生子賜給〔他們〕，叫一切信他的，不致滅亡，反得永生。 [OHGBI] ΟὕτωςThus γὰρfor ἠγάπησενloved ὁ- ΘεὸςGod τὸνthe κόσμονworld, ὥστεthat τὸνthe ΥἱὸνSon, τὸνthe μονογενῆonly begotten, ἔδωκενHe gave, ἵναso that πᾶςeveryone ὁ- πιστεύωνbelieving εἰςin αὐτὸνHim μὴnot ἀπόληταιshould perish, ἀλλ᾽but ἔχῃshould have ζωὴνlife αἰώνιονeternal. ...

The markdown display show all different versions for a single verse on a single line, which makes uers different to read.  Can you make the markdown display for version comparison better, with each version display on a single line.  For example, you may consider prefix each version with `\n* ` or `\n- ` or better alternatives?
```

```
I noted an issue.  Whenever you or agents, specified in [agents.md](.agents/agents.md) , quote bible verse content in their responses.  They use different bible versions, out of their memory, inconsistently.  Can you make sure whenever you or other agents need to quote bible verse content, always use the skill `bible`, so that bible verse content is retrieved from solid local database.
```

## Prompt for Creating Original Skill and /original Command

Create a new skill `original` and a new slash command `/original`, that will retrieve the original language of a given Bible verse in Greek or Hebrew, with the full text in the original language.  It is essentially an alias to the `/bible` command, but with default bible version set to OHGB (Open Hebrew Greek Bible).  When users run `/original`, they are essentially running `/bible OHGB`. So the `original` skill is actually the bible skill taking `OHGB` as the first parameter.  All other parameters are passed to the bible skill directly.  You should leverage the `bible` skill to implement the `original` skill.

## Prompt for Creating Interlinear Skill and /interlinear Command

Create a new skill `interlinear` and a new slash command `/interlinear`, that will retrieve the interlinear version of a given Bible verse in Greek or Hebrew, with the full text in the original language.  It is essentially an alias to the `/bible` command, but with default bible version set to OHGBi (Open Hebrew Greek Bible Interlinear).  When users run `/interlinear`, they are essentially running `/bible OHGBi`. So the `interlinear` skill is actually the bible skill taking `OHGBi` as the first parameter.  All other parameters are passed to the bible skill directly.  You should leverage the `bible` skill to implement the `interlinear` skill.

## Prompt for Creating Search Skill and /search Command

```
Create a new skill and a new slash command / workflow, to search for given words or phrases in a bible or multiple bibles, with search wildcards supported: `*` and `?`, `*` matches zero or more characters, `?` matches a single character.

skill name should be simply `search`

slash command should be simply `/search`

bible databases are in sqlite format, stored either in ~/biblemate/data/bibles or ~/biblemate/data_custom/bibles

Remember use home variable instead of hardcoding absolute paths, to make this repository portable.

Valid bible database filenames are ended with *.bible

search and retrieve matches from table `Verses`, return each verse content as a markdown line, with each version on a single line.

NET.bible is the default bible if no bible version is specified

the command `/search` can take both bible version(s) and bible reference(s)

if bible version is not specified, NET.bible is the default database for retrieval.  If a specified version, use that version, If more than one version is specified, all specified versions are searched and retrieved with each verse display line by line. search results are grouped by book and chapter, with each book and chapter on a separate line.  Different bible versions results are separated with different blocks, as some matches in a particular version may not exist in another version.  For example, if user search for 'love' and there are 10 matches in NET.bible, 5 matches in CUV.bible and 8 matches in KJV.bible, then the output should be in 10 blocks, with each block containing the verse content for NET.bible, CUV.bible and KJV.bible if the verse exists in that version. Also, tell the total number of matches for each version, and in each book.

examples for use: 

/search love*God # search in NET.bible as default

when a `+` sign is used to search for word combination, it means `AND` regardless of sequence.

e.g. /search love*God # means love, followed by God, with `*` as wildcard character

/search love+God+Jesus # means love AND God AND Jesus, regardless of sequence

when a `|` sign is used to search for multiple words or phrases, it means `OR`

e.g. /search Holy Spirit|the Spirit|Spirit of God # means Holy Spirit OR the Spirit OR Spirit of God

the search can be very complex, e.g.

/search love+God|sin # means love AND God OR sin

To specify search version(s), e.g.

/search NET love*God

/search NET KJV love*God

make sure you don't hardcode bible version list available in ~/biblemate/data/bibles and ~/biblemate/data_custom/bibles , as users can dynamatically add or remove bible databases into or from this folder.  Instead of hardcoding a static bible version list, you should always check if bible version specified is a valid name in those folder.
```

## Prompt for Creating Search Skills and Command for Searching Individual Books

Now, along the same search, retrieval and display logic as the previous search skill, but for individual book only.

Create 66 new skilla and 66 new slash commands / workflows, to search for given words or phrases in a bible or multiple bibles, limiting the search to a single book only, and with search wildcards supported: `*` and `?`, `*` matches zero or more characters, `?` matches a single character.

Skill names are:

Gen
Exod
Lev
Num
Deut
Josh
Judg
Ruth
1Sam
2Sam
1Kgs
2Kgs
1Chr
2Chr
Ezra
Neh
Esth
Job
Ps
Prov
Eccl
Song
Isa
Jer
Lam
Ezek
Dan
Hos
Joel
Amos
Obad
Jonah
Mic
Nah
Hab
Zeph
Hag
Zech
Mal
Matt
Mark
Luke
John
Acts
Rom
1Cor
2Cor
Gal
Eph
Phil
Col
1Thess
2Thess
1Tim
2Tim
Titus
Phlm
Heb
Jas
1Pet
2Pet
1John
2John
3John
Jude
Rev

Command names are:

/Gen
/Exod
/Lev
/Num
/Deut
/Josh
/Judg
/Ruth
/1Sam
/2Sam
/1Kgs
/2Kgs
/1Chr
/2Chr
/Ezra
/Neh
/Esth
/Job
/Ps
/Prov
/Eccl
/Song
/Isa
/Jer
/Lam
/Ezek
/Dan
/Hos
/Joel
/Amos
/Obad
/Jonah
/Mic
/Nah
/Hab
/Zeph
/Hag
/Zech
/Mal
/Matt
/Mark
/Luke
/John
/Acts
/Rom
/1Cor
/2Cor
/Gal
/Eph
/Phil
/Col
/1Thess
/2Thess
/1Tim
/2Tim
/Titus
/Phlm
/Heb
/Jas
/1Pet
/2Pet
/1John
/2John
/3John
/Jude
/Rev

The search logic, supported symbols (`+`, `|`, `*`, `?`), retrieval and display all are same as how /search skill works, but for each book only.

For example, we use the same examples used above, but /search searches the whole bible, /Matt , for example, search the book of Matthew ONLY.

/Matt love*God # search in NET.bible as default

when a `+` sign is used to search for word combination, it means `AND` regardless of sequence.

e.g. /Matt love*God # means love, followed by God, with `*` as wildcard character

/Matt love+God+Jesus # means love AND God AND Jesus, regardless of sequence

when a `|` sign is used to search for multiple words or phrases, it means `OR`

e.g. /Matt Holy Spirit|the Spirit|Spirit of God # means Holy Spirit OR the Spirit OR Spirit of God

the search can be very complex, e.g.

/Matt love+God|sin # means love AND God OR sin

To specify search version(s), e.g.

/Matt NET love*God

/Matt NET KJV love*God

## Prompt for Creating Commentary Skill and /commentary Command

```
Now, along a similar line, create a new skill and a new slash command workflow, to retrieve bible commentary:

skill name should be simply `commentary`

slash command should be simply `/commentary`

commentaries are in sqlite format, stored either in `~/biblemate/data/commentaries` or `~/biblemate/data_custom/commentaries`

Note: make sure you don't hardcode commentary version list available in `~/biblemate/data/commentaries` and `~/biblemate/data_custom/commentaries` , because users can dynamatically add or remove commentary databases into or from this folder.  Instead of hardcoding a static commentary version list, you should always check if commentary version specified is a valid name in those folder.

Remember use home variable instead of hardcoding absolute paths, to make this repository portable.

Valid commentary filenames are formatted like `c<commentary_version>.commentary`, so each commentary filename starts with `c` followed by the commentary version abbreviation, then `.commentary`. for example:
`cAIC.commentary`, `cBI.commentary`, etc. and each is its own commentary database.

retrieve from table `Commentary`, the `Scripture` column contains the commentary text content that is intended to be retrieved. 

Note: there may be a challenge for you, some Commentary table, like the one in `cAIC.commentary` contains Book, Chapter, and Verse entries, but most of the others have Book, Chapter entries only.  In the latter case, the `Scripture` column contains the commentary text content for the whole chapter.  You need a further step to retrieve only the relevant verses/verse range sections from the commentary text content, based on the given verse range.  For example, if verse range is John 3:16-18, and the commentary text content is for the whole chapter, you need to retrieve only the sections relevant to John 3:16-18.  You should use text processing, and natural language understanding techniques to achieve this goal or any better alternatives.

`cAIC.commentary` is the default commentary if no commentary version is specified

the command `/commentary` can take both commentary version(s) and bible reference(s)

if commentary version is not specified, `cAIC.commentary` is the default database for retrieval.  If a specified version, use that version, If more than one version is specified, all specified versions are retrieved for comparison for each given bible reference.

bible references can be single or multiple verse(s), e.g. John 3:16-18; Rm 5-8

bible references can also be a chapter a verse or multiple verse range

examples for use: 

/commentary John 3:16 # use `cAIC.commentary` as default

/commentary John 3 # retrieve the whole chapter from the first verse to the last

/commentary John 3:16-18; Deut 6:4; Rom 5-8 # retrieve multiple commentaries for the given verses from different books.

/commentary BI John 3:16-18 # use `cBI.commentary` as it is specified

/commentary AIC BI John 3:16-18 # compare `cAIC.commentary` and `cBI.commentary` for the given bible references
```

## Prompt for Creating Lexicon Skill and /lexicon Command

```
Now, along a similar line, create a new skill and a new slash command workflow, to retrieve original language or Strong Number lexicon content:

skill name should be simply `lexicon`

slash command should be simply `/lexicon`

lexicon contents are in sqlite format, stored either in `~/biblemate/data/lexicons` or `~/biblemate/data_custom/lexicons`

Note: make sure you don't hardcode lexicon version list available in `~/biblemate/data/lexicon` and `~/biblemate/data_custom/lexicon` , because users can dynamatically add or remove lexicon databases into or from this folder.  Instead of hardcoding a static lexicon version list, you should always check if lexicon version specified is a valid name in those folder.

Remember use home variable instead of hardcoding absolute paths, to make this repository portable.

Valid lexicon filenames are formatted like `<lexicon_version>.lexicon`, so each lexicon filename starts with the lexicon version abbreviation, then ends with `.lexicon`. for example:
`SECE.lexicon`, `BDB.lexicon`, `LSJ.lexicon`, etc. and each is its own lexicon database.

work with table `Lexicon` for lexicon entries `Topic` and content `Definition`. 

`SECE.lexicon` is the default lexicon if no lexicon version is specified

the command `/lexicon` can take both lexicon version(s) and lexicon entries

if lexicon version is not specified, `SECE.lexicon` is the default database for retrieval.  If a specified version, use that version, If more than one version is specified, all specified versions are retrieved for comparison for each given entry.

examples for use: 

/lexicon H148 G2479 # use `SECE.lexicon` as default

/lexicon H148 G2479; G5547; G5590 # retrieve multiple lexicon entries

/lexicon BDB SECE H148 # use `BDB.lexicon` and `SECE.lexicon` for comparison

/lexicon BDB SECE H148; H1933-H1935 # compare `BDB.lexicon` and `SECE.lexicon` for the given lexicon entries
```

## Prompt for Creating Xrefs Skill and /xrefs Command

```
Create a new skill and a new slash command / workflow, to retrieve bible cross-references:

skill name should be simply `xrefs`

slash command should be simply `/xrefs`

bible cross-reference database are in sqlite format, stored as `~/biblemate/data/cross-reference.sqlite`

Remember use home variable instead of hardcoding absolute paths, to make this repository portable.

The retrieval involves two steps, in which the second step needs to work with the `bible` skill.

Step 1: retrieve cross reference verses information from table `ScrollMapper`

Step 2: use the retrieved information to invoke `bible` skill to retrieve the actual cross reference verses content in different versions.

An important note: before proceeding to step 2, prefix the cross reference verses information retrieved from Step 1 with the given verse range information retrieved from Step 1 in the format: `[given_verse_range] [cross_reference_verses_information]`, and pass this new formatted string to `bible` skill.

For example, for `/xrefs John 3:16-18`, in step 1 you retrieve cross reference verses information for `John 3:16-18`, then in step 2, you invoke `bible` skill with the string `/bible John 3:16-18 [cross_reference_verses_information]`.

As a result, the given bible reference content will be displayed at the top, then each of the cross reference verses content will be displayed line by line with each version on a single line.  

About the use of bible version, there should already be mentioned in the bible skill.  just brief information here.

NET.bible is the default bible if no bible version is specified

the command `/xrefs` can take both bible version(s) and bible reference(s)

if bible version is not specified, NET.bible is the default database for retrieval.  If a specified version, use that version, If more than one version is specified, all specified versions are retrieved with each verse display line by line comparison of the specified versions.

bible references can be single or multiple verse(s), e.g. John 3:16-18; Rm 5-8

bible references can also be a chapter a verse or multiple verse range

examples for use: 

/xrefs John 3:16 # use NET.bible for step 2 as default

/xrefs John 3 # retrieve the whole chapter cross-references from the first verse to the last

/xrefs John 3:16-18; Deut 6:4; Rom 5-8 # retrieve multiple verses cross-references from different books.

/xrefs CUV John 3:16-18 # use CUV.bible for step 2 as it is specified

/xrefs NET CUV John 3:16-18 # compare NET CUV every single cross-reference, line by line.

Make the markdown display for version comparison better, for each verse with each version, make sure the whole version content for a single verse is displayed on a single line.  For example, you may consider prefix each version with `\n- `.  I think this is already in place in the bible skill.

Update the root README.md file and the files in docs directory to reflect the new skills.
```

## Prompt for Creating Data Skill and /data Command

```
Now, create a new skill and a new slash command workflow, to list available resources.

skill name: `data`

slash command: `/data`

Currently, this skill and command work with three main resources:

> /data bible # list all available bible versions.

as mentioned, bible databases are in sqlite format, stored either in ~/biblemate/data/bibles or ~/biblemate/data_custom/bibles

> /data commentary # list all available commentary versions.

as mentioned, commentaries are in sqlite format, stored either in `~/biblemate/data/commentaries` or `~/biblemate/data_custom/commentaries`

> /data lexicon # list all available lexicon versions.

as mentioned, lexicon contents are in sqlite format, stored either in `~/biblemate/data/lexicons` or `~/biblemate/data_custom/lexicons`

Note: make sure you don't hardcode available versions.  Instead of hardcoding a static version list, you should always check afresh the available versions in the mentioned folders.  Each folder has its own list of versions.  so you need to check both folders.
```

## Prompt for Creating Morphology Skill and /morphology Command

```
Create a new skill and a new slash command / workflow, to retrieve bible morphology data:

skill name should be simply `morphology`

slash command should be simply `/morphology`

sqlite database is located at `~/biblemate/data/morphology.sqlite`

works mainly on the table `morphology` in the sqlite file for morphology data

though you may work with all columns, results mainly shows: 

Verse Reference in readable format (Book Chapter:Verse), WordID, Word, LexicalEntry, MorphologyCode, Morphology, Lexeme, Transliteration, Pronunciation, Interlinear, Translation, Gloss

1. Works with bible references

/morphology accepts bible reference(s), single or multiple, and can be separated by ;

examples for use:

/morphology John 3:16 # retrieve morphology data for John 3:16

/morphology John 3:16-18 # retrieve morphology data for John 3:16-18

/morphology John 3:16-18; Deut 6:4; Rom 5-8 # retrieve morphology data for John 3:16-18; Deut 6:4; Rom 5-8

2. Works with specific word(s) or phrases

/morphology also support queries with specific word(s) or phrases, to limit the scope in particular verses.

In this case, users have to specify the verse range(s) along with the word(s) or phrases.

examples for use:

/morphology create in Genesis 1:1

/morphology love the world in John 3:16

Important for your reasoning: The words or phrases provided by users may not exactly match the words in the morphology data rows, you should try your best to match in a reasonable way. Retrieve the best relevant data for results.

If the queries and bible references does not make sense at all, clarify with user and ask for clarification.
```