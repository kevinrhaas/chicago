# SPDX-License-Identifier: GPL-3.0-or-later
"""T-3553: the words of the two adults jaunts (read by adults.py): what is new beside the
students' telling. Every quotation is the eyewitness's own words as Kirkland (1893) prints them,
carried in a claim here or already in the students' jaunt; Kirkland's own editorial voice is not
quoted. A stop not named here keeps the students' text.
"""
KIRKLAND = 'kirkland_1893_chicago_massacre'
PG = 'Project Gutenberg eBook #59624 plain text'


def words(text):
    return len(text.split())


def stop(text, evidence):
    return {'text': text, 'read_s': round(words(text) / 3.5), 'evidence': evidence}


WARNING_BATTLE = ("18+. Graphic violence from the eyewitness accounts: men and women shot, stabbed and struck down "
                  "with tomahawks and the dead scalped, staged in the scenes; the worst mutilations described in the narration. "
                  "No child is shown being killed.")
WARNING_LALIME = ("18+. A killing staged as the witnesses described it: a pistol fired at close range and a man "
                  "stabbed to death with a knife.")

BATTLE = {
    'id': 'battle-of-fort-dearborn-adults',
    'title': 'The Battle of Fort Dearborn (18+)',
    'grade_band': '6-8',
    'content_warning': WARNING_BATTLE,
    'premise': ("18+: 6 April to 16 August 1812 in thirteen stops, with the killings at Lee's Place, the attack "
                "on the beach and the death of Captain Wells staged as the witnesses described them."),
    'opening': ("JAUNT: THE BATTLE OF FORT DEARBORN, 18+. Spring 1812, where the Chicago River meets Lake Michigan. "
                "The nearest American post is Fort Wayne, far to the south-east; Detroit, where the general commands, is "
                "farther still. War with Britain is coming, and every report that reaches the fort makes it feel smaller "
                "and farther from help.\n\n"
                "This telling is 18+. It walks the same thirteen stops as the students' jaunt, but at Lee's Place, "
                "on the beach and on the prairie the killing is staged as the people who lived through it described it: "
                "shots fired, knives and tomahawks used, men and women struck down, the dead scalped, and soldiers fighting "
                "back with the bayonet. The worst of what was done to the bodies is told, not shown, and no child is shown "
                "being harmed.\n\n"
                "Thirteen stops in date order, with the time of day and the season set for each. Long rides go Instantly; "
                "every place keeps its stop.\n\n"
                "The story begins with the fort, on the afternoon of 6 April 1812."),
    'stops': {
        'hardscrabble': stop(
            "6 April 1812, a little before sunset, at Lee's Place, later called Hardscrabble, up the South Branch. Eleven armed men walk into the log house and sit down; Captain Heald wrote that they were 'supposed "
            "to be Winnebagoes'. The soldier and Lee's young son slip across the river and run. Behind them comes 'the "
            "discharge of two guns successively.' Liberty White and the Canadian hand are shot down. Heald's letter lists "
            "what was done to White: 'two balls through his body, nine stabs with a knife in his breast, and one in his "
            "hip, his throat was cut from ear to ear, his nose and lips were taken off in one piece, and his head was "
            "skinned'. The Frenchman 'was only shot through the neck and scalped.' That night a soldier found the body, "
            "and 'The faithful dog of the murdered man stood guarding the remains of his master.'",
            ['white-wounds', 'lee-place-night']),
        'the-bank': stop(
            "About ten, two miles down the beach. Wells comes 'riding furiously back', shouting 'They are "
            "about to attack us!' Mrs. Helm remembered: 'Scarcely were the words uttered when a volley was showered from "
            "among the sand-hills.' The company fires one round and charges up the bank; 'One man, a veteran of seventy "
            "winters, fell as they ascended.' Sergeant Hays, shot 'through the body', drives his bayonet into "
            "Nau-non-gee as the chief comes at him with a tomahawk: 'They fell together.' A tomahawk meant for Mrs. Helm's skull 'alighted on my shoulder', she said, "
            "before Black Partridge dragged her into the lake. At the wagons the militia are 'cut down to a man', and a "
            "young warrior climbs into the baggage wagon and 'tomahawked the children of the entire group.' The dead "
            "are scalped; a soldier's daughter later 'saw her father's scalp in the hands of an Indian afterward.'",
            ['volley', 'hays-naunongee', 'helm-on-the-field', 'wagon-children', 'cooper-scalp']),
        'cottonwoods': stop(
            "About half past ten. Wells, 'shot through the lungs', reaches his niece, Mrs. Heald, and takes her hand: "
            "'Farewell my child.' She saw 'the blood oozing through his nose and mouth.' Pinned when his horse falls, he "
            "'took aim and fired, killing one of them.' Warned that a gun was pointed at his head, he cried 'Shoot away!' "
            "A warrior fired, 'the shot being fatal.' He was scalped, and they 'cut his body open' and 'took out his "
            "heart'. Mrs. Heald "
            "was 'wounded in six places'. Heald gathers his last men on 'a small elevation in the open prarie'. Black "
            "Bird comes out and asks him to surrender, 'promising to spare the lives of all the prisoners.' His count: "
            "'twenty-six regulars and all the militia were killed in the action, with two women and twelve children.'",
            ['wells-death', 'heald-wounds', 'wells-scalp']),
    },
    'evidence': [
        {'id': 'white-wounds', 'confidence': 'attested', 'sources': [KIRKLAND],
         'text': ("Captain Heald's letter from Chicago, 15 April 1812, as Kirkland prints it: 'White received two balls "
                  "through his body, nine stabs with a knife in his breast, and one in his hip, his throat was cut from "
                  "ear to ear, his nose and lips were taken off in one piece, and his head was skinned almost as far "
                  "round as they could find any hair. The Frenchman was only shot through the neck and scalped.'"),
         'locator': f"ch. II, Building of the First Fort Dearborn, Captain Heald's letter of 15 April 1812, {PG} lines 2305-2319"},
        {'id': 'lee-place-night', 'confidence': 'attested', 'sources': [KIRKLAND],
         'text': ("Mrs. Kinzie's narrative of the attack at Lee's place, as Kirkland condenses it: the soldier and the boy "
                  "'had run a quarter of a mile when they heard the discharge of two guns successively.' That night the "
                  "fishing party stopped to warn the house: 'as the corporal jumped over the small enclosure he placed his "
                  "hand on the dead body of a man. By the sense of touch he soon ascertained that the head was without a "
                  "scalp and was otherwise mutilated. The faithful dog of the murdered man stood guarding the remains of "
                  "his master.'"),
         'locator': f"ch. II, Building of the First Fort Dearborn, the condensation of Mrs. Kinzie's narrative, {PG} lines 2255-2300"},
        {'id': 'volley', 'confidence': 'attested', 'sources': [KIRKLAND],
         'text': ("Margaret Helm's story (Wau-Bun), as Kirkland reprints it: 'Captain Wells, who had kept somewhat in "
                  "advance of his Miamis, came riding furiously back. \"They are about to attack us!\" he shouted. \"Form "
                  "instantly and charge upon them.\" Scarcely were the words uttered when a volley was showered from among "
                  "the sand-hills. The troops were hastily brought into line and charged up the bank. One man, a veteran "
                  "of seventy winters, fell as they ascended.' 'The troops behaved most gallantly. They were but a handful, "
                  "but they seemed resolved to sell their lives as dearly as possible.'"),
         'locator': f"Part I, Margaret Helm's Story, {PG} lines 764-790"},
        {'id': 'hays-naunongee', 'confidence': 'attested', 'sources': [KIRKLAND],
         'text': ("Wau-Bun's account of Nau-non-gee, a chief of the Calumet village, as Kirkland reprints it: 'During the "
                  "battle of the 15th of August, the chief object of his attack was one Sergeant Hays, a man from whom he "
                  "had received many acts of kindness. After Hays had received a ball through the body, this Indian ran up "
                  "to tomahawk him, when the Sergeant, collecting his remaining strength, pierced him through the body "
                  "with his bayonet. They fell together. Other Indians running up soon dispatched Hays, and it was not "
                  "until then that his bayonet was extracted from the body of his adversary.' The wounded chief was "
                  "carried to his village on the Calumet and survived several days."),
         'locator': f"ch. V, Fate of the Fugitives, {PG} lines 3315-3330"},
        {'id': 'helm-on-the-field', 'confidence': 'attested', 'sources': [KIRKLAND],
         'text': ("Margaret Helm's story (Wau-Bun), as Kirkland reprints it: the surgeon 'was badly wounded. His horse was "
                  "shot under him and he had received a ball in his leg.' 'I pointed to Ensign Ronan, who, though mortally "
                  "wounded and nearly down, was still fighting with desperation on one knee.' 'At this moment a young "
                  "Indian raised his tomahawk at me. By springing aside I avoided the blow, which was intended for my "
                  "skull, but which alighted on my shoulder. I seized him around the neck, and while exerting my utmost "
                  "efforts to get possession of his scalping-knife, which hung in a scabbard over his breast, I was "
                  "dragged from his grasp by another and an older Indian. The latter bore me struggling and resisting "
                  "toward the lake.' She passed 'the remains of the unfortunate surgeon. Some murderous tomahawk had "
                  "stretched him upon the very spot where I had last seen him.' 'I was immediately plunged into the "
                  "water and held there with a forcible hand'; her captor kept her head above water, and she knew him, "
                  "'in spite of the paint with which he was disguised', as The Black Partridge."),
         'locator': f"Part I, Margaret Helm's Story, {PG} lines 795-850"},
        {'id': 'wagon-children', 'confidence': 'attested', 'sources': [KIRKLAND],
         'text': ("Margaret Helm's story (Wau-Bun), as Kirkland reprints it: 'But in the meantime, a horrible scene had been "
                  "enacted. One young savage, climbing into the baggage-wagon containing the children of the white "
                  "families, twelve in number, tomahawked the children of the entire group.' Kirkland takes it as "
                  "confirmed by Heald's count of the dead, 'two women and twelve children'."),
         'locator': f"Part I, after Rebekah Heald's Story, {PG} lines 1280-1295"},
        {'id': 'wells-death', 'confidence': 'attested', 'sources': [KIRKLAND],
         'text': ("Rebekah Heald's story, taken down by Kirkland from her son Darius Heald in 1892: 'Captain Wells, who was "
                  "shot through the lungs, rode up and took her hand, saying: \"Farewell my child.\"' 'He told her he was "
                  "shot through the lungs, and she saw the blood oozing through his nose and mouth.' 'His horse, which had "
                  "been shot just behind the girth, then fell and caught Captain Wells' leg under him. As he did so, "
                  "Captain Wells turned and saw six or seven Indians approaching them. He took aim and fired, killing one "
                  "of them.' 'Mrs. Heald said to him: \"Uncle, there is an Indian pointing right at the back of your "
                  "head.\" Captain Wells put his hand back and held up his head that better aim might be taken, and then "
                  "cried \"Shoot away!\" The Indian fired, the shot being fatal. They then pulled him out from under his "
                  "horse (Mrs. Heald still seated on her horse near by) and cut his body open, the gashes being in the "
                  "shape of a cross. They took out his heart'."),
         'locator': f"Part I, Death of Captain Wells, {PG} lines 1043-1070"},
        {'id': 'cooper-scalp', 'confidence': 'attested', 'sources': [KIRKLAND],
         'text': ("A. H. Edwards to John Wentworth, 24 May 1891, from what a survivor told him, a soldier's daughter who "
                  "rode in the wagons: she 'had been scalped'. 'She said a young Indian came to the wagon where she was "
                  "and grabbed her by the hair and pulled her out of the wagon, and she fought him the best she knew how, "
                  "scratching and biting, till finally he threw her down and scalped her.' 'I do not know the first name "
                  "of Cooper. He was killed and the girl said she saw her father's scalp in the hands of an Indian "
                  "afterward.'"),
         'locator': f"Appendix G, Important Reminiscences of an Old Settler (A. H. Edwards), {PG} lines 6585-6700"},
        {'id': 'wells-scalp', 'confidence': 'attested', 'sources': [KIRKLAND],
         'text': ("Margaret Helm's story (Wau-Bun), as Kirkland reprints it: led from the lake, she was 'Supported partly by "
                  "my kind conductor, Black Partridge, and partly by another Indian, Pee-so-tum, who held dangling in his "
                  "hand a scalp which, by the black ribbon around the queue, I recognized as that of Captain Wells'."),
         'locator': f"Part I, Margaret Helm's Story, {PG} lines 884-892"},
        {'id': 'heald-wounds', 'confidence': 'attested', 'sources': [KIRKLAND],
         'text': ("Rebekah Heald's story, through her son Darius: 'Just before the surrender, she got up in range of the "
                  "bullets coming from Indians on both sides of her. She did not know whether the Indians aimed at her or "
                  "not, but she was wounded in six places, one hand being rendered helpless, the ball passing between the "
                  "two bones of her arm.'"),
         'locator': f"Part I, Rebekah Heald's Story, {PG} lines 1026-1034"},
    ],
}

LALIME = {
    'id': 'killing-of-jean-lalime-adults',
    'title': "Chicago's First Murder (18+)",
    'grade_band': '6-8',
    'content_warning': WARNING_LALIME,
    'premise': ("18+: 17 June 1812, sunset, the fort gate: Chicago's first recorded murder, with the pistol shot and "
                "the knife staged as the witnesses described them. The victim, interpreter Jean Lalime. The killer, John "
                "Kinzie, 'The Father of Chicago'. Nine stops."),
    'opening': None,   # the students' opening, with the line for adults put in (adults.py)
    'opening_add': ("This telling is 18+: outside the gate, the pistol shot and the knife are staged as the "
                    "witnesses described them."),
    'stops': {
        'cold-open': stop(
            "17 June 1812, sunset, outside the gate of Fort Dearborn. Jean Lalime, the fort's interpreter, lies dead in "
            "the dust, stabbed. The man walking away, 'covered with blood', is John Kinzie, the trader who sells to the "
            "garrison, the man later histories would call 'The Father of Chicago'. Who did it has never been in doubt. "
            "Why, and whether it was murder, depends on whom you believe. To see how it came to this, go back eight "
            "years, across the river, to the best house in Chicago.",
            ['hubbard']),
        'the-gate': stop(
            "17 June, sunset, outside the main gate. Victoire Porthier, a girl inside the fort, remembered: 'It was "
            "sunset, when they used to shut the gates of the fort.' She heard Helm call out to Kinzie to look out for "
            "Lalime, 'as he had a pistol.' 'Quick we saw the men come together. We heard the pistol go off and saw the "
            "smoke.' The ball struck Kinzie, 'cutting the side of his neck', his family said; 'Blood was running from his "
            "shoulder', said Porthier. 'After Lalime shot him and Kinzie got his arms around him, he (Lalime) pulled out "
            "his dirk, and as they fell he was stabbed with his own knife.' Kinzie, 'closing with Lalime, stabbed him'. "
            "Irwin, the factor, saw it all from twenty or thirty yards. Van Voorhis wrote that 'it was a perfect "
            "assassination and can be proven to be such'. The Kinzie family called it self-defence.",
            ['porthier-knife']),
    },
    'evidence': [
        {'id': 'porthier-knife', 'confidence': 'attested', 'sources': [KIRKLAND],
         'text': ("Victoire Porthier went on, as Andreas printed her and Kirkland reprints: 'You see, Kinzie wasn't to "
                  "blame at all. He didn't have any pistol nor knife--nothing. After Lalime shot him and Kinzie got his "
                  "arms around him, he (Lalime) pulled out his dirk, and as they fell he was stabbed with his own knife. "
                  "That is what they all said. I didn't see the knife at all.'"),
         'locator': f"Appendix F, The Bones of John Lalime, Mrs. Porthier's statement, {PG} lines 6283-6298"},
    ],
}
