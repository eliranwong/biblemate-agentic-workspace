# Characters

```
Create a new skill characters and slash command workflow /characters, to retrieve bible characters/people data.

This skill work with [exlbp_dict.py](file;file:///Users/admin/dev/antigravity-biblemate-workspace/data/exlbp_dict.py) and ~/biblemate/data/data/exlb3.data

remember:
* not to hardcode absolute path, to make this repository portable.
* copy the content of the file [exlbp_dict.py](file;file:///Users/admin/dev/antigravity-biblemate-workspace/data/exlbp_dict.py) , if you need them, into the skill folder.  Do not make the skill dependent on this file after the skill is created.

When a bible person name is given, you try to find the best match at [exlbp_dict.py](file;file:///Users/admin/dev/antigravity-biblemate-workspace/data/exlbp_dict.py) .  I says best match, coz user spelling may vary from the names in this file, as it is not uncommon for name spellings varies slightly.  So, make sure the searching is flexible enough for you to handle.

when a key is find, its values contain a list of content lookup entries.  some keys may have multiple entries.

when entries are found, retrieve their content from ~/biblemate/data/data/exlb3.data , particularly table `exlbp`, column `path` contains the entries, column `content` contains the content for corresponding paths / entries
```

```
Merge the skill `character` and slash command `/character` into the newly built the skill `characters` and slash command `/characters` and keep the later only.
```

# Bible Topics

```
Along the same line, create a new skill 'topics' with slash command workflow '/topics', to retrieve bible topics data.

This skill work with ... and ~/biblemate/data/data/exlb3.data

remember:
* not to hardcode absolute path, to make this repository portable.
* copy the content of the file ..., if you need them, into the skill folder.  Do not make the skill dependent on this file after the skill is created.

When a bible topic is given, you try to find the best match at ... .  I says best match, coz user spelling may vary from the topics in this file, as it is not uncommon for topics spelling varies slightly.  So, make sure the searching is flexible enough for you to handle.

when a key is find, its values contain a list of content lookup entries.  some keys may have multiple entries.

when entries are found, retrieve their content from ~/biblemate/data/data/exlb3.data , particularly table `exlbt`, column `path` contains the entries, column `content` contains the content for corresponding paths / entries
```

```
Merge the skill `topic` and slash command `/topic` into the newly built the skill `topics` and slash command `/topics` and keep the later only.
```

# Bible Promises

```
Enhance the existing `/promises` skill to also retrieve bible promises data, to enrich its content.

This skill work with ... and ~/biblemate/data/collections3.sqlite

remember:
* not to hardcode absolute path, to make this repository portable.
* copy the content of the file ..., if you need them, into the skill folder.  Do not make the skill dependent on this file after the skill is created.

When a bible query is given, you try to find the best match at ... .  I says best match, coz user spelling may vary from the promise entries in this file, as it is not uncommon for description or entries spellings varies.  So, make sure the searching is flexible enough for you to handle.

when a key is find, its values contain a list of content lookup entries.  some keys may have multiple entries.  Each entry is a list of two numbers, e.g. [0, 1], which corresponds to `Tool` and `Number` columns in `PROMISES` table in `~/biblemate/data/collections3.sqlite`.  e.g. [0, 1] corresponds to Tool=0 and Number=1.  

when entries are found, retrieve their content from ~/biblemate/data/collections3.sqlite , particularly table `PROMISES`, column `Tool` and column `Number` corresponds respectively the two numbers in each entries mentioned above. Passages contains the corresponding content.
```

# Bible Parallels

Along the logic of the promises skill and slash command workflow, create a new skill `parallels` with slash command `/parallels` to retrieve bible parallels passages, and explain their theological significances, and what are the similarities and differences between them, and how they relate to each other, and their applications to our lives. Sometimes, authors use similarities among differences to higligh different empahsis in different passages. This skill work with ... and ~/biblemate/data/collections3.sqlite

# Chapter Summary

Integrate data retrieval into the exisiting skill of `chapter-summary`:

* enhance the original skill with extra data not to replace it
* retrive chapter data in the sqlite file ~/biblemate/data/data/chapter_summary.data table `Summary`
* data retriveal is the basis for enhancing the exisiting skill. Fully expound the data that are relevant to resolve users original requests. Provide full detail as much as possible.

Remember, do not hardcode absolute path, to make this repository portable.

# Book Analysis

Integrate data retrieval into the exisiting skill of `book-analysis`:

* enhance the original skill with extra data not to replace it
* retrive chapter data in the sqlite file ~/bib
lemate/data/data/book_analysis.data table `Introduction`.
* the table has columns `Book`, `Section` and `Content`.
* `Book` is the book number from 1-66, according to cannonical order.
* there are multiple entries for each book, each entry has a `Section` and `Content`.
* `Section` is the section number.  There are 9 sections, numbered from 0-9.
* 0-9 represents the following book sections:

0: Overview
1: Structural Outline
2: Logical Flow
3: Historical Setting
4: Themes
5: Keywords
6: Theology
7: Canonical Placement
8: Practical Living
9: Summary

* `Content` is the content for the corresponding section.
* data retriveal is the starting point to resolve users original requests. Fully expound the data that are relevant to resolve users original requests. Provide full detail as much as possible.

Remember, do not hardcode absolute path, to make this repository portable.

# People relationship

Integrate people relationship data into the existing skill of `characters` with additional data retrieval:

* this is additional data not to replace the original skill, do not skip the original data retrieval step the are currently exist in the skill.  integrate the additional data into the exisiting skill, do not overwrite it.  

* work with the sqlite file ~/biblemate/data/data/biblePeop
le.data tables `PEOPLE` and `PEOPLERELATIONSHIP`

* In table `PEOPLE` column `PersonID` is the primary connected point with the entries you can find in the characters skill current data `exlbp_dict.py` by prefixing the `PersonID` with "BP" (e.g. "John" in `exlbp_dict.py` will correspond to `PersonID` "BP1658")

* In table `PEOPLERELATIONSHIP` column `FromPersonID`, `ToPersonID`, `ToPersonID` are the connected points with the entries in `PEOPLE` table.  So you can find the relationship between `FromPersonID` and `ToPersonID` by looking up the `PersonID` in the `PEOPLE` table.

* When a character is given, retrieve their relationship from `PEOPLERELATIONSHIP` table

* Then retrieve the content from `PEOPLE` table based on the `PersonID`.

* I want you to present the relationship as a family tree, or relationship tree, as part of the characters skill.  Make the output visually appealing.  Use the markdown tree format to present the relationship.  The tree should start from the user requested character and expand outward to their relationships.  Do not output the entire tree, only the part of the tree that is relevant to the user requested character.  

* The depth of the tree should at least include parents, spouse, siblings, children.  Expand the tree reasonably based according to users request or the complexity of the character's relationships.

* Fully expound the data that are relevant to resolve users original requests. Provide full detail as much as possible.

Remember, do not hardcode absolute path, to make this repository portable.
