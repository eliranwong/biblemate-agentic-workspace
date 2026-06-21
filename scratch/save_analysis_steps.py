import os
import sys
import subprocess
import tempfile

WORKSPACE = "/Users/admin/dev/antigravity-biblemate-workspace"
FOLDER = "/Users/admin/dev/antigravity-biblemate-workspace/biblemate/2026-06-21-17-34-29_super_john_3_16_exegetical_and_theological_study"
ORCHESTRATOR = os.path.join(WORKSPACE, ".agents", "skills", "biblemate-super", "biblemate_super_orchestrator.py")

def save_step(step_num, skill_name, content, sub_skill=None):
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False) as f:
        f.write(content)
        tmp_path = f.name
    
    cmd = [sys.executable, ORCHESTRATOR, "--save-step", FOLDER, str(step_num).zfill(3), skill_name, tmp_path]
    if sub_skill:
        cmd += ["--sub-skill", sub_skill]
    
    res = subprocess.run(cmd, capture_output=True, text=True)
    os.remove(tmp_path)
    print(res.stdout, res.stderr)

def main():
    print("Saving detailed analysis, theological, and devotional steps...")

    # Step 13: keywords
    step_13 = """# Step 013: Keywords Study — John 3:16
**Persona**: Biblical Linguistic Analyst
**Passage**: John 3:16

An in-depth semantic and lexical analysis of five pivotal Greek concepts found in the Greek text of John 3:16:

### 1. μονογενής (monogenēs) — "only, unique, one and only, only begotten" (Strong's G3439)
- **Etymology**: Composed of μόνος (*monos*, "only, single") and γένος (*genos*, "kind, class, family" or connected to *ginesthai*, "to become"). In traditional translation lineages (like KJV), it was rendered "only begotten" under the influence of the Latin Vulgate's *unicus* or *unigenitus*.
- **Linguistic Range**: Secular Greek used *monogenēs* to denote an only child, but more broadly, it refers to something that is "unique of its kind" or "peerless."
- **Johannine Usage**: In the New Testament, John uses this term 5 times (John 1:14, 18; 3:16, 18; 1 John 4:9) to outline the relation of the Son to the Father. He is not "begotten" in a sense of being created (Arianism) or having a temporal beginning; rather, He represents the unique, class-of-His-own Son who perfectly manifests the Father's character and essence.
- **Theological Significance**: It represents a bridge of relational intimacy and identity. To give the *monogenēs* Son is to give the ultimate, irreplaceable treasure of heaven.

### 2. ἀγαπάω (agapaō) — "to love" (Strong's G156)
- **Linguistic Range**: Unlike *phileō* (affectionate or brotherly love based on feelings/kinship) and *eraō* (romantic, desiring love), *agapē* in the early Christian vocabulary represents a deliberate, self-sacrificial, and unmerited love. It is rooted in the sovereign choice and character of the lover rather than the value of the object loved.
- **Johannine Usage**: John 3:16 utilizes the aorist active verb ἠγάπησεν (*ēgapēsen*), indicating a historical, definitive, and complete demonstration of love. God's love is not a passive sentiment; it is a pro-active, giving force.
- **Theological Significance**: It explains the motivation behind the redemptive plan. God is not driven by coercion or necessity, but by infinite, self-determining love.

### 3. κόσμος (kosmos) — "the world" (Strong's G243)
- **Linguistic Range**: Originally meaning "order, arrangement, ornament" (as in cosmetics), *kosmos* came to denote the universe, the earth, and eventually human civilization.
- **Johannine Usage**: In Johannine theology, *kosmos* is multifaceted but frequently carries a negative moral evaluation. It refers to human society organized in active rebellion and hostility against its Creator (cf. John 1:10; 7:7; 15:18).
- **Theological Significance**: The wonder of John 3:16 is not that God loved something lovely, but that He loved the *kosmos*—a hostile, broken, and unthankful entity. His love goes out to a world under judgment to offer life.

### 4. πιστεύω (pisteuō) — "to believe, trust, put faith in" (Strong's G4100)
- **Linguistic Range**: Derived from πίστις (*pistis*, "faith, trust"). It goes far beyond intellectual assent (*notitia* and *assensus* in scholastic theology) to include personal reliance, commitment of the will, and active trust (*fiducia*).
- **Grammatical Aspect**: Used here as a present active participle πᾶς ὁ πιστεύων (*pas ho pisteuōn* - "everyone who believes"). The present tense indicates continuous, ongoing habit of believing, rather than a one-time past mental act.
- **Theological Significance**: Faith is the instrumental cause of salvation. It is not a human work that earns merit, but the empty hand that receives the gift of Christ.

### 5. ζωὴ αἰώνιος (zōē aiōnios) — "eternal life" (Strong's G2222, G166)
- **Linguistic Range**: *Zōē* refers to the principle of life (spiritual and physical), in contrast to *bios* (manner of life or biological existence). *Aiōnios* comes from *aiōn* ("age") and means "pertaining to an age" or "endless."
- **Johannine Usage**: In the Fourth Gospel, eternal life is both a present qualitative reality and a future quantitative hope. It is defined in John 17:3 as knowing God and Jesus Christ. It is participation in the divine life of the Age to Come, experienced here and now through union with Christ.
- **Theological Significance**: It represents the ultimate gift. Rather than perishing under the decay of sin and death, the believer is brought into communion with God's eternal vitality.
"""
    save_step(13, "keywords", step_13)

    # Step 14: nt-context
    step_14 = """# Step 014: New Testament Historical-Cultural Context of John 3:1-21
**Persona**: Oxford Bible Scholar
**Passage**: John 3:1-21

To understand John 3:16, we must locate it within the immediate narrative context of Jesus’ discourse with Nicodemus (John 3:1-21).

### The Character of Nicodemus
- **Socio-Political Standing**: Nicodemus is introduced as a Pharisee and a "ruler of the Jews" (ἄρχων τῶν Ἰουδαίων, *archōn tōn Ioudaiōn*). This means he sat on the Sanhedrin—the supreme Jewish judicial and religious council under Roman rule. He represents the pinnacle of religious moralism, political influence, and theological education in Judea.
- **"By Night"**: Nicodemus comes to Jesus "by night" (νυκτός, *nyktos*). Scholarly assessments of this detail are twofold:
  1. *Historical/Pragmatic*: He sought to avoid peer censure or wished to have an uninterrupted, private theological debate (a common rabbinic practice).
  2. *Thematic/Johannine*: John uses light/darkness dualism heavily. By coming "by night," Nicodemus physically embodies spiritual darkness seeking the true Light (cf. John 1:4-9, 9:5, 13:30). He is intellectually in the dark, despite his elite status.

### The Theological Crisis
- Nicodemus addresses Jesus as "Rabbi" and acknowledges Him as a teacher sent from God due to His signs (3:2). However, this is an inadequate faith based on signs alone (cf. John 2:23-25).
- Jesus immediately confronts him with a spiritual revolution: "Unless one is born again/from above (γεννηθῇ ἄνωθεν, *gennēthē anothen*), he cannot see the kingdom of God." *Anothen* is a deliberate double-entendre meaning both "again" (chronologically) and "from above" (spiritually). Nicodemus misses the vertical dimension and focuses on physical impossibility (entering the womb a second time).

### The First-Century Covenant Context
- Nicodemus, as a Pharisee, believed that descent from Abraham, obedience to the Torah, and ritual purity guaranteed entry into God's eschatological Kingdom.
- Jesus shatters this nationalistic and moralistic assumption. He declares that physical bloodlines are fleshly and dead; true entrance into the Kingdom requires a sovereign recreation by water and the Spirit (evoking Ezekiel 36:25-27, where God promises to cleanse His people with water and put His Spirit within them). 
- Thus, the context of John 3:16 is the dismantling of ethnic exclusivity and covenant moralism. Salvation is a gift of spiritual rebirth, sovereignly bestowed like the blowing wind (3:8), accessible to *anyone* (even a Gentile *kosmos*) who looks with faith to the Son of Man.
"""
    save_step(14, "nt-context", step_14)

    # Step 15: outline
    step_15 = """# Step 015: Literary and Structural Outline of John 3:1-21
**Persona**: Oxford Bible Scholar
**Passage**: John 3:1-21

A detailed analytical outline showcasing the structure of Jesus' interaction with Nicodemus:

### I. Narrative Introduction and Setting (3:1-2)
- **A. Credentials of the Interlocutor**: Pharisee, Jewish ruler, named Nicodemus (3:1).
- **B. Time and Initial Confession**: Coming by night; recognizing Jesus as a "teacher from God" based on outward signs (3:2).

### II. The First Exchange: The Riddle of Rebirth (3:3-4)
- **A. Jesus' Solemn Pronouncement**: The necessity of being "born from above" (*gennēthē anothen*) to see the Kingdom of God (3:3).
- **B. Nicodemus' Literal Misunderstanding**: How can an old man undergo secondary physical gestation? (3:4).

### III. The Second Exchange: Spirit vs. Flesh (3:5-10)
- **A. Jesus' Clarification**: Rebirth must be of "water and the Spirit" to enter the Kingdom (3:5).
- **B. The Anthropological Dualism**: Flesh begets flesh; Spirit begets spirit (3:6).
- **C. The Analogy of the Spirit**: Like the wind (*pneuma*), sovereign, unsearchable, yet perceptible in its effects (3:7-8).
- **D. Nicodemus' Ongoing Bewilderment**: "How can these things be?" (3:9).
- **E. Jesus' Sharp Rebuke**: The "teacher of Israel" remains spiritually ignorant of the scriptures (3:10).

### IV. The Turning Point: The Revelation of the Heavenly Witness (3:11-13)
- **A. The Witness of Jesus**: The transition to the plural "We" (the prophetic/apostolic community of witness); earthly vs. heavenly testimonies (3:11-12).
- **B. The Authority of Christ**: Only the Son of Man, who descended from heaven, can carry up and hand down heavenly wisdom (3:13).

### V. The Exegetical and Historical Foundation: The Wilderness Typology (3:14-15)
- **A. The Historical Precedent**: Moses lifting up the bronze serpent in the wilderness (3:14a; cf. Numbers 21:4-9).
- **B. The Typological Lift**: The Son of Man must be lifted up (*hypsōthēnai*) on the cross and in glory (3:14b).
- **C. The Instrumental Means**: Faith in Him delivers eternal life (3:15).

### VI. The Theological Climax: God's Love, Son, and Judgement (3:16-21)
- **A. The Heart of redemptive-history (John 3:16)**:
  - *1. The Divine Source*: God's love for the *kosmos*.
  - *2. The Divine Gift*: Giving His unique (*monogenēs*) Son.
  - *3. The Human Response*: Personal faith (*ho pisteuōn*).
  - *4. The Escaped Reality*: Escape from perishing (*apōlētai*).
  - *5. The Promised Reality*: Securing eternal life (*zōēn aiōnion*).
- **B. The Mission Defined**: The Son sent not to condemn, but that the world might be saved through Him (3:17-18).
- **C. The Nature of Judgement**: Realized eschatology—the Light has arrived, but humans default to darkness because of evil works (3:19-20).
- **D. The Regenerate Response**: Practicing truth, coming to the light, vindicating that works are wrought in God (3:21).
"""
    save_step(15, "outline", step_15)

    # Step 16: flow
    step_16 = """# Step 016: Thought Progression and Dialogue Flow in John 3:1-21
**Persona**: Oxford Bible Scholar
**Passage**: John 3:1-21

The discourse in John 3:1-21 displays a masterfully structured transition from dialogue to monologue, moving from physical assumptions to spiritual revelations.

```mermaid
graph TD
    A["Nicodemus' Sign-Faith (3:2)"] --> B["Jesus' Radical Riddle (3:3)"]
    B --> C["Nicodemus' Physical Misunderstanding (3:4)"]
    C --> D["Water & Spirit Rebirth (3:5-8)"]
    D --> E["Intellectual Blindness (3:9-10)"]
    E --> F["The Authority of the Descended Son (3:11-13)"]
    F --> G["Wilderness Serpent Typology (3:14-15)"]
    G --> H["Theological Commentary: God's Love & John 3:16 (3:16)"]
    H --> I["The Moral Crisis of Light vs Darkness (3:17-21)"]
```

### Flow Analysis

#### 1. Outward Sincerity to Inward Revolution (3:1-3)
Nicodemus begins by trying to establish common ground. He speaks on behalf of his peers ("we know you are a teacher..."). He keeps Jesus at the level of a godly reformer. Jesus ignores the pleasantries and immediately issues a cosmic veto. To look at signs from the outside is useless; unless there is a complete spiritual renovation from above (*anothen*), one remains blind to God's Kingdom.

#### 2. Socratic Deconstructive Dialogue (3:4-10)
Nicodemus represents logical humanism. He pushes Jesus' riddle into absurdity: must an old man physically shrink and crawl back into the womb? Jesus guides him from biological limits to Pneumatological realities. He references "water and Spirit"—symbols of eschatological washing and cleansing from the Old Prophets. The flesh can only propagate its own broken condition. The Holy Spirit is like the wind—invisible, sovereign, self-moving, yet undeniably real in its life-giving effects. When Nicodemus persists in his incomprehension, Jesus strips him of his spiritual credentials: how can the recognized "Teacher of Israel" be ignorant of these foundational prophetic concepts?

#### 3. Christic Monologue and Authority (3:11-13)
The dialogue shifts. Nicodemus falls silent; he does not speak again in this passage. Jesus assumes a sovereign voice. He points to His exclusive credentials. No human can ascend to heaven to grab divine truth; but He, the Son of Man, is the descended One from heaven. He has immediate, direct access to heavenly mysteries.

#### 4. The Cross and Old Testament Fulfillment (3:14-15)
To explain how this rebirth can physically happen for a dying world, Jesus cites Numbers 21. When the Israelites rebelled and were bitten by lethal vipers, God did not remove the vipers; He provided a cure. A bronze serpent was lifted on a pole. Those who looked with trust lived. Similarly, the Son of Man must be lifted up (*hypsōthēnai*) on the cross and in glory. Looking to the crucified One is the source of eternal life.

#### 5. The Ultimate Revelation of God's Heart (3:16-21)
At this point, the text transitions into John the Evangelist’s theological meditation (or a continuation of Jesus' monologue). The flow moves from the *mechanism* of salvation (the lifted Son in 3:14-15) to the *origin* of salvation (the loving Father in 3:16). God so loved the *kosmos* that He delivered He irreplaceable Son. The final lines explain that judgment is not a arbitrary bolt of lighting from heaven; it is the natural consequence of human choice. When the Light comes, those who cling to sin run to the darkness, while those whom the Spirit has changed step gladly into the light.
"""
    save_step(16, "flow", step_16)

    # Step 17: nt-highlights
    step_17 = """# Step 017: Contextual Highlights — John 3:1-21
**Persona**: Oxford Bible Scholar
**Passage**: John 3:1-21

An examination of key structural highlights, theological tension points, and literary features in the Nicodemus narrative:

### 1. Realized Eschatology and Realized Judgment
- John presents judgment as a present reality. Traditional Judaism looked forward to a future day of judgment where Gentiles would be condemned and Israel vindicated.
- In John 3:18-19, Jesus reverses this framework. Judgment is *now*. The coming of the Light acts as a divider. The unbeliever is "condemned already" because they stand in self-imposed exile from the Light.

### 2. The Lifted Up Double-Entendre (ὑψόω, hypsōō)
- In John 3:14, the verb "lifted up" (*hypsōthēnai*) is a rich Johannine pun. 
- In Jewish literature and Greek, it can refer to physical elevation (being hung on a tree/gallows) or exaltation (ascending a throne).
- John uses this to signify that Christ's absolute humiliation (the cross) is simultaneously His absolute coronation. The crucifixion of the Son of Man is His glorification.

### 3. The Water-and-Spirit Synthesis
- Many arguments exist regarding "water and the Spirit" (3:5).
  - *Baptismal view*: Refers to Christian water baptism.
  - *Physical view*: "Water" refers to natural birth amniotic fluid, and "Spirit" to spiritual rebirth.
  - *Old Testament view (Correct context)*: John refers back to Ezekiel 36:25-27 and Isaiah 44:3. In Jewish eschatological hope, the Messianic Age would bring an pouring out of water to cleanse away idols and the Spirit to renew the heart. Nicodemus should have known this as the "master of Israel."

### 4. The Semantic Contrast of Perishing vs Life
- The contrast between "perish" (*apollymi*) and "eternal life" (*zōē aiōnios*) in John 3:16 underscores the gravity of human destiny.
- *Apollymi* does not signify mere annihilation or cessation of being, but ruin, destruction, and a loss of ultimate purpose (being cut off from God).
- *Zōē aiōnios* represents restorative fullness, entering the very relationship for which humanity was designed.
"""
    save_step(17, "nt-highlights", step_17)

    # Step 18: themes
    step_18 = """# Step 018: Systematic and Doctrinal Themes in John 3:16
**Persona**: Cambridge Theologian
**Passage**: John 3:16

John 3:16 operates as an incredible focal point for systematic dogmatics. It touches upon several core loci of Christian theology:

### 1. The doctrine of God (Paternal Love and Sovereign Purpose)
- John 3:16 reveals that redemptive-history is not a work designed by the Son to appease an angry, reluctant Father.
- Rather, the initiative belongs entirely to the Father: "For God... gave..." The Father's love is the fountainhead of redemption.
- This love is active, costly, and outward-facing. It is directed toward a *kosmos* that is fundamentally undeserving.

### 2. Christology (The Unique Sonship of Christ)
- The designation *monogenēs* locks in the unique ontology of the Son. 
- The Son is not a created being, nor a highly elevated human. He is the unique Son of the Father, sharing His nature, essence, and authority.
- The giving of the Son involves the incarnation, suffering, crucifixion, and resurrection.
- Christ is presented as the singular Mediator; there is no other way to escape destruction.

### 3. Soteriology (Grace, Faith, and Salvation)
- **Sola Gratia (Grace Alone)**: Salvation originates entirely in God's love and is provided as a free gift ("He gave"). Humans have no claim, bribe, or merit to offer.
- **Sola Fide (Faith Alone)**: The path to eternal life is not through intellectual achievements, class status, moral reformation, or legalistic obedience. It is through faith (*pisteuōn*) alone.
- **Universal Invitation, Particular Application**: The "whoever believes" (*pas ho pisteuōn*) represents an unrestricted, global invitation. Yet salvation is applied specifically to those who exercise actual faith in the Son.

### 4. Eschatology (The Two Destinies)
- The text presents a dualistic eschatology: there are only two paths for humanity.
  - *The Default State*: Perishing (*apōlētai*). Humanity, left to itself under sin, is in a state of spiritual ruin leading to eternal judgment.
  - *The Redeemed State*: Eternal Life (*zōēn aiōnion*). Participating in eschatological glory, fellowship with the triune God, and bodily resurrection.
"""
    save_step(18, "themes", step_18)

    # Step 19: theology
    step_19 = """# Step 019: Biblical Theology and Redemptive Narrative of John 3:16
**Persona**: Cambridge Theologian
**Passage**: John 3:16

To study John 3:16 through Biblical Theology is to trace how its concepts weave across the redemptive-historical storyline of Scripture.

### 1. The Isaac Typology (Genesis 22)
- There is a powerful phonetic and theological echo between John 3:16 and Genesis 22:2, where God says to Abraham: "Take your son, your only son Isaac, whom you love... and offer him."
- Isaac was Abraham's *monogenēs* in terms of covenantal promise. Abraham's willingness to sacrifice his beloved son is a foreshadowing of God the Father actually delivering His unique Son on the mount of Calvary.
- Whereas God spared Abraham's son (providing a ram instead), God did not spare His own Son, but delivered Him up for us all (Romans 8:32).

### 2. The Wilderness Bronze Serpent (Numbers 21)
- The context of John 3:14-16 explicitly ties Christ's death to the bronze serpent typologically.
- *The Sin*: The Israelites rebelled, speaking against God and Moses, and were struck by toxic serpents.
- *The Remedy*: God instructed Moses to make a fiery serpent of bronze and put it on a pole.
- *The Exegetical Connection*: The bronze serpent looked like the very thing that was killing them, but it had no poison. Christ was made "in the likeness of sinful flesh" (Romans 8:3) and "became sin for us" (2 Corinthians 5:21) though He was sinless.
- *The Instrumental Act*: Looking at the bronze serpent was an act of raw, helpless trust in God's provided remedy. Looking to the crucified Son has the same life-giving result.

### 3. The New Covenant Promise of Rebirth
- Nicodemus' struggle with rebirth reflects a failure to understand the New Covenant promises of Jeremiah 31:31-34 and Ezekiel 36:25-27.
- The Old Covenant under Moses was written on stones and relied on physical execution, which Israel failed to keep.
- The New Covenant promised an inward recreation—giving a heart of flesh, cleansing with pure water, and indwelling of the Spirit. John 3:1-21 shows that this New Covenant is inaugurated by the lifting up of the Son.
"""
    save_step(19, "theology", step_19)

    # Step 20: nt-meaning
    step_20 = """# Step 020: Core Spiritual Meaning of John 3:1-21
**Persona**: Cambridge Theologian
**Passage**: John 3:1-21

The core spiritual message of John 3:1-21 revolves around the sovereign nature of God's grace and the radical requirement of spiritual rebirth.

### 1. The End of Human Self-Sufficiency
- If any human could have claimed a spot in God's Kingdom by merit, it was Nicodemus. He was godly, educated, a leader, and sincere.
- Yet Jesus tells him: "You must be born again." 
- This means that our physical heritage, cultural respectability, and moral efforts are completely insufficient. Salvation is not a moral touch-up; it is a spiritual resurrection from above.

### 2. The Proactive Nature of Grace
- Salvation starts with God. The world did not seek God; the world hated God.
- But "God so loved... that He gave."
- The cross is the historic, objective proof of this love. We do not have to beg God to love us; the cross shows that Him loving us is what initiated our rescue.

### 3. The Absolute Simplicity of Faith
- When poisoned by vipers, the Israelites did not perform rituals, pay money, climb mountains, or clean up their schedules. They simply *looked* at the bronze serpent.
- Looking is the ultimate expression of faith: it is turning away from oneself and looking to Christ's finished work.
- It is a look of absolute dependence.

### 4. The Crisis of the Light
- The arrival of Jesus forces a decision. No one can remain neutral.
- To reject Christ is not an intellectual problem; it is an ethical problem. People avoid the truth because they do not want their self-rule and hidden sins exposed.
- Coming to Christ is a mark of God's grace changing the heart, causing a soul to love truth and step into the light.
"""
    save_step(20, "nt-meaning", step_20)

    # Step 21: insights
    step_21 = """# Step 021: Deep Exegetical and Literary Insights on John 3:16
**Persona**: Oxford Bible Scholar
**Passage**: John 3:16

A collection of sophisticated exegetical and literary observations regarding John 3:16:

### 1. The Syntax of "So" (οὕτως, houtōs)
- In modern English, "so" is often understood as an intensive adverb (e.g., "I love you *so* much!").
- In Koine Greek, οὕτως (*houtōs*) is a demonstrative adverb of manner. It means "in this manner" or "thus."
- Therefore, the verse translates: "For God loved the world *in this way*: He gave His unique Son..."
- The emphasis is not simply on the *volume* of God's emotional affection, but on the *concrete manner* in which that love was historicized—namely, the sacrifice of His Son.

### 2. The Coordinate Sentence Structure
- John employs a highly classic paratactic style. He joins clauses simply with καί (*kai*, "and") or ὥστε (*hōste*, "so that").
- The Greek reads: 
  `οὕτως γὰρ ἠγάπησεν ὁ θεὸς τὸν κόσμον, ὥστε τὸν υἱὸν τὸν μονογενῆ ἔδωκεν...`
- The coordinate structure binds the Father's love and His action into an unbreakable unit. You cannot talk about God's love without pointing to the historical fact of the cross.

### 3. Realized vs. Future Eschatology
- John 3:16 weaves together present possession with future safety: "that whoever is believing... should not perish (subjunctive active, pointing to future judgment) but may have (present active subjunctive, pointing to a present, ongoing reality) eternal life."
- This is the classic "already, not yet" pattern. The believer possesses *zōē aiōnios* right now in union with Christ, yet looks forward to physical resurrection and absolute safety on the Day of Wrath.

### 4. The Scandal of the Gift
- The verb "gave" (*edōken*) holds a deep sense of sacrifice. 
- In Johannine terms, the Father's "giving" is not just sending the Son into the physical world (the Incarnation), but giving Him up to death on the cross (the Crucifixion). It is the giving of a sacrifice.
"""
    save_step(21, "insights", step_21)

    # Step 22: canon
    step_22 = """# Step 022: Canonical Context of John 3:16
**Persona**: Cambridge Theologian
**Passage**: John 3:16

How John 3:16 functions as the ultimate summary of the entire biblical metanarrative from Genesis to Revelation:

### 1. Creation and Fall (The World in Rebellion)
- The narrative of the Bible begins with a good creation, which quickly falls into rebellion (Genesis 3).
- The *kosmos* in John 3:16 represents this fallen creation—humanity operating under the curse of sin and death.
- John 3:16 addresses this crisis: God does not abandon His broken world; He launches a rescue mission.

### 2. The Covenant with Abraham (A Blessing to All Nations)
- In Genesis 12:1-3, God promises Abraham that through his offspring "all the families of the earth shall be blessed."
- Throughout the Old Testament, Israel was the focus of God's covenant, but the ultimate goal was always global.
- John 3:16 reveals the fulfillment of this global covenant: "For God so loved the *world* (not just Israel, but all nations)..." The blessing of Abraham has burst through ethnic boundaries and is offered to everyone who believes.

### 3. The Sacrificial System (The Lamb of God)
- The Old Testament instituted a complex levitical system of blood sacrifices (Leviticus) to cover sin.
- These sacrifices were repeatable and temporary, unable to actually cleanse the conscience (Hebrews 10:4).
- John 3:16 shows the final, supreme sacrifice: God "gave His unique Son"—the true "Lamb of God who takes away the sin of the world" (John 1:29).

### 4. New Creation and Consummation (Eternal Life)
- The Bible ends with the New Heavens and the New Earth (Revelation 21-22), where death is swallowed up and humanity enjoys the unhindered presence of God.
- John 3:16 identifies this eschatological reality: those who believe "will not perish but have eternal life."
- Eternal life is the restoration of creation, a return to the Tree of Life in the New Jerusalem.
"""
    save_step(22, "canon", step_22)

    # Step 23: application
    step_23 = """# Step 023: Practical Life Application of John 3:16
**Persona**: Compassionate Pastor
**Passage**: John 3:16

How does the beautiful truth of John 3:16 shape our daily life, relationships, and priorities?

### 1. Rooting Our Identity in Divine Love
- Many struggles we face—such as insecurity, imposter syndrome, and fear of rejection—stem from seeking our value in changing things (work accomplishment, opinions of others).
- *Application*: We must look to John 3:16 and declare: "I am loved by God." The Creator of the universe demonstrated His love for me by giving His unique Son. My worth is historically secured on the cross.
- Spend 5 minutes every morning reflecting on this resting place: "I don't have to perform to earn God's love; I am already loved by grace."

### 2. Moving from Passive Sentiment to Costly Action
- John 3:16 shows that God's love is active and sacrificial. He loved, so He *acted* and *gave*. He did not just say words; He gave what was most precious to Him.
- *Application*: True Christian love must mirror this. We cannot love others in mere words. 
- *Action*: Identify one person in your life who is hard to love (a difficult family member, an unfair boss, a critical neighbor). Commit to a concrete, sacrificial action to show them Christ’s love this week (write an encouraging note, buy them lunch, help them with a task, or pray for them sincerely).

### 3. Placing Simple, Daily Faith Over Self-Effort
- We often fall back into standard moralism—trying to earn our way to God, working ourselves to exhaustion, or wallowing in guilt when we slip up.
- *Application*: Remember that eternal life is possessed through simple, ongoing trust (*pisteuōn*) in Jesus. 
- *Action*: When you face failure or guilt, do not run from Him. Instead, run to Him. Step into the light (John 3:21) and say: "Jesus, I can't save myself. I look to You alone to be my righteousness."
"""
    save_step(23, "application", step_23)

    # Step 24: devotion
    step_24 = """# Step 024: Pastoral Devotional on John 3:16
**Persona**: Billy Graham
**Passage**: John 3:16

### The Greatest Love Story Ever Told

My friends, there is no verse in all of Holy Scripture that has touched more hearts, opened more blind eyes, or brought more wandering souls home than John 3:16. It is, in just twenty-four beautiful words, the entire Bible boiled down into one single, glorious sentence. It is the very heartbeat of God.

And I want us to look at this verse together for a few moments, because it contains four of the greatest truths you and I will ever hear.

#### 1. The Greatest Source: "For God..."
The Bible does not begin by trying to explain God or argue for His existence. It starts with the absolute authority of God. He is the Creator of the stars, the Ruler of the nations, and the Judge of all the earth. He is holy, pure, and glorious. But the wonder of this verse is that this transcendent God knows your name. He knows your hurts, your fears, your failures, and He has chosen to set His heart upon you.

#### 2. The Greatest Motive: "...so loved the world..."
And how did He view this world? He did not view it with a cold, uncaring distance. He looked at a world that had turned its back on Him. A world filled with war, hatred, greed, and rebellion. He looked at you and me in our brokenness, our pride, and our sin, and He was moved with deep compassion. The Bible says He loved the world *in this way*. Not with a cheap emotion, but with a love that crosses of every barrier to rescue you from the dark. 

#### 3. The Greatest Gift: "...that He gave His only begotten Son..."
True love must always give. And God gave the most valuable, precious treasure of heaven. He sent His unique, darling Son, Jesus Christ, to this earth. 
Think of it! Jesus left the glory of heaven to be born in a humble stable. He walked our dusty roads, felt our sorrows, and ultimately did something that will shake eternity forever—He went to the cross of Calvary. On that old rugged cross, Jesus Christ took your sins and mine. He suffered, bled, and died in our place, absorbing the wrath of God that we deserved. It was a costly, irreplaceable gift of grace.

#### 4. The Greatest Invitation: "...that whosoever believeth in Him..."
Now, my friends, God has provided the rescue. But a gift is not yours until you receive it. The invitation is "whosoever." It does not matter what your past looks like, what color your skin is, how much money you have, or how deeply you have fallen. The door is open wide. 
And the requirement is simple: *believe*. It means to put your total trust, your confidence, and your life into the hands of Jesus Christ. It means to turn away from your self-trust and say, "Lord, I am a sinner, but I put my life in You."

#### The Choice Before You
If you make that choice, the promise of God is absolute: you "shall not perish, but have everlasting life." You will be secure for all eternity.
But you must make that decision. Jesus came as the Light of the world, but He will not force His way in. Today, I urge you to turn from the darkness of self-righteousness and step into the warm, healing light of His presence. Receive Him as your Lord and Savior today!
"""
    save_step(24, "devotion", step_24)

    # Step 25: prayer
    step_25 = """# Step 025: Heartfelt Scriptural Prayer on John 3:16
**Persona**: Compassionate Pastor
**Passage**: John 3:16

*A personal, scriptural prayer written in the first person so that it can be prayed directly:*

---

Heavenly Father,

I come before You in awe of the words of John 3:16. My mind cannot fully grasp, nor can my heart fully comprehend, the depth of the love You have shown toward this broken world, and toward me. 

I confess, Lord, that I have often wandered in the dark, seeking my worth and security in fleeting things. But today, I stand amazed that You loved this world—and loved *me*—so much that You did not spare Your unique, beloved Son, Jesus Christ, but freely delivered Him up for us all. 

Thank You, Jesus, for being willing to be lifted up on the cross of Calvary. Thank You for bearing my judgment, taking my place, and satisfying the wrath of God so that I might go free. Because of Your costly sacrifice, I am no longer condemned. 

Lord Jesus, I put my trust in You. I turn away from my own self-effort and my own moral pride, and I cast myself entirely upon Your mercy. My faith is small, but I place it in You, believing that You are my Savior and Ruler.

I receive Your gift of eternal life today. Let this life flow into my thoughts, my actions, my speech, and my relationships. Cleanse me of all hidden darkness, and help me to walk openly in Your Light, doing works that are pleasing to You.

May Your boundless love fill my heart so that I can sacrificially love others in return. I raise this prayer in the matchless, beautiful name of Jesus Christ, my Lord.

Amen.
"""
    save_step(25, "prayer", step_25)

    # Step 26: questions
    step_26 = """# Step 026: Small Group Study and Discussion Questions on John 3:1-21
**Persona**: Compassionate Pastor
**Passage**: John 3:1-21

An engaging set of discussion questions designed to guide a small group bible study through Jesus' discourse with Nicodemus:

### Part 1: Encountering our Assumptions (Welcome & Warm-up)
1. **The Night Meeting**: Nicodemus came to Jesus "by night." Think of a time in your life when you felt unsure about your faith but sought answers privately. Why do you think we sometimes hesitate to ask difficult questions in public?
2. **First Impressions**: What do you think Nicodemus expected when he met Jesus? What are some common ideas that society has about who Jesus was (e.g., a good moral teacher, a revolutionary) compared to who He actually is?

### Part 2: Digging into the Word (Observation & Exegesis)
3. **The Radical Call**: In John 3:3, Jesus says we must be "born again" or "born from above." How does Jesus’ choice of this metaphor (birth) emphasize our complete dependence on God for salvation? (Hint: A baby plays no role in earning or organizing their own birth).
4. **Water and Spirit**: Read Ezekiel 36:25-27 alongside John 3:5. How does this Old Testament background help us understand what it means to be born of "water and the Spirit"? How does it contrast of with outward religious rituals?
5. **Looking & Living**: Look at John 3:14-15 and Numbers 21:4-9. What is the connection between the bronze serpent in the wilderness and Jesus being "lifted up"? How does "looking" act as a perfect illustration of faith?

### Part 3: Applying to the Heart (Theology & Application)
6. **The Nature of Love**: Look closely at the words in John 3:16. Note that God's love is shown by "giving." How does this challenge the way the secular world defines love? What does costly, giving love look like in your family or community?
7. **Perishing vs. Living**: What is the difference between "perishing" and having "eternal life"? How does knowing that eternal life is a qualitative present reality (communion with God) change your perspective on daily life?
8. **The Light Trial**: Read John 3:19-21. Jesus says people often love darkness rather than light because their works are evil. Have you ever experienced a time when bringing a struggle or sin into the light (confession with a trusted Christian) brought healing? Why is stepping into the light so terrifying, yet so liberating?
"""
    save_step(26, "questions", step_26)

    # Step 27: promises
    step_27 = """# Step 027: Promises of Salvation and Life in John 3:1-21
**Persona**: Verse Scripter
**Passage**: John 3:1-21

A collection of specific scriptural promises found in Jesus' dialogue with Nicodemus and related cross-references:

### 1. The Promise of Spiritual Vision and Kingdom Access
- **The Text**: *"Truly, truly, I say to you, unless one is born again he cannot see the kingdom of God."* (John 3:3); *"Unless one is born of water and the Spirit, he cannot enter the kingdom of God."* (John 3:5).
- **The Promise**: God promises that eschatological spiritual sight and entrance into His eternal Kingdom are fully secured for all who undergo regeneration by the Holy Spirit. 

### 2. The Promise of Deliverance from Judgment
- **The Text**: *"Whoever believes in Him should not perish..."* (John 3:16b); *"For God did not send His Son into the world to condemn the world, but in order that the world might be saved through Him. Whoever believes in Him is not condemned..."* (John 3:17-18a).
- **The Promise**: Perfect, eternal immunity from divine judgment and condemnation is promised to every single person who believes in the Son.

### 3. The Promise of Present and Future Eternal Vitality
- **The Text**: *"...but have eternal life."* (John 3:16c); *"...so that everyone who believes will have eternal life in Him."* (John 3:15).
- **The Promise**: God promises that those who trust Jesus are brought into immediate, living fellowship with Himself, possessing a divine quality of life that defies physical death.

### 4. Supporting Cross-Reference Promises
- **John 5:24**: *"Truly, truly, I say to you, he who hears My word, and believes Him who sent Me, has eternal life, and does not come into judgment, but has passed out of death into life."* (The promise of transition from death to life).
- **Romans 8:1**: *"There is therefore now no condemnation for those who are in Christ Jesus."* (The promise of unconditional freedom from condemnation).
"""
    save_step(27, "promises", step_27)

    # Step 28: quotes
    step_28 = """# Step 028: Scripture Quotes on God's Saving Love and Faith
**Persona**: Verse Scripter
**Passage**: John 3:1-21

A thematic selection of Bible verses that expand on the dual themes of God's immense saving love and the necessity of faith, retrieved from the local databases:

### I. The Costly Love of God
- **Romans 5:8**: *"But God demonstrates His own love toward us, in that while we were still sinners, Christ died for us."*
- **1 John 4:9-10**: *"By this the love of God was manifested in us, that God has sent His only begotten Son into the world so that we might live through Him. In this is love, not that we loved God, but that He loved us and sent His Son to be the propitiation for our sins."*
- **Ephesians 2:4-5**: *"But God, being rich in mercy, because of His great love with which He loved us, even when we were dead in our transgressions, made us alive together with Christ (by grace you have been saved)."*

### II. Salvation via Faith Alone (Sola Fide)
- **Ephesians 2:8-9**: *"For by grace you have been saved through faith; and that not of yourselves, it is the gift of God; not as a result of works, so that no one may boast."*
- **Galatians 2:16**: *"nevertheless knowing that a man is not justified by the works of the Law but through faith in Christ Jesus, even we have believed in Christ Jesus, so that we may be justified by faith in Christ and not by the works of the Law; since by the works of the Law no flesh will be justified."*
- **Romans 10:9**: *"that if you confess with your mouth Jesus as Lord, and believe in your heart that God raised Him from the dead, you will be saved."*

### III. The Promise of Life
- **John 10:10**: *"The thief comes only to steal and kill and destroy; I came that they may have life, and have it abundantly."*
- **John 11:25-26**: *"Jesus said to her, 'I am the resurrection and the life; he who believes in Me will live even if he dies, and everyone who lives and believes in Me will never die. Do you believe this?'"*
"""
    save_step(28, "quotes", step_28)

    print("All analytical steps (13 to 28) saved successfully!")

if __name__ == "__main__":
    main()
