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