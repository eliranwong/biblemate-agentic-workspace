Currently, both the skills `biblemate` and `biblemate-super` create study folders and save the outputs for a single study in the same folder.  That's very good, keep it as it is right now, no need to change.

However, for other bible-related skills, excluding those `Workspace & Repository Commands` as in ..., i.e. biblemate, biblemate-super, image, data, sync, md, docx, and zip, the outputs for a single study not saved at all, if running them on Antigravity platform instead of web app. They are sometimes not even visible as they are saved as artifacts.  This is very bad.

For the web app, we have successfully solved this issue, as stated in ... 

Particularly,

```
                "\n- Save ALL study outputs (outlines, sermons, devotionals, analyses, etc.) to the"
                " `biblemate/` subdirectory."
                "\n- Every output filename MUST be prefixed with a timestamp in the format"
                " `YYYY-MM-DD-HH-MM-SS_` followed by a short descriptive name ending in `.md`."
```

Individual study outputs are saved in the `biblemate` directory without creating new folders.  They are just saved to the root `biblemate` directory.  I.e. if I run a skill twice, there will be two files in the root `biblemate` directory. but it won't be a problem as the timestamp will be different.  

I want you to apply the same logic to all the other bible-related skills, even I am not running them on the web app, but on Antigravity platform.