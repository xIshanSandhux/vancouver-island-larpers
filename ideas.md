# LarpHacks ideas

Theme: **create a product to help you LARP as someone you are not.**
Rubric (5 pts each, 30 total): working product, usefulness, theme, creativity, ease of use, demo.
Demo is 2 minutes plus 2 minutes of questions. Hard submission at 6:00 PM.

Each idea targets a different audience and is scoped so a team of two (a bank intern and a software engineer) can get it working in about 7 hours.

## Sponsor cheat sheet (from research)

- **Render Workflows**: you turn functions into tasks with their own retry behaviour, chain them, and fan them out in parallel. `ctx.step()` makes inline work durable, so a retried task skips steps that already finished. Put side effects in a child task with an idempotency key. SDKs for TypeScript and Python. Deploys from a Git repo as a Workflow service, and you trigger it from your app or the Render API.
  - Rule of thumb: **use it for the fan-out and the slow part, not the live chat loop.**
- **ElevenLabs**: text to speech (v3 for emotion, Flash v2.5 for low latency), voice changer (speech to speech), sound effects from a text prompt, music from a prompt, Scribe speech to text (including a real-time variant), and Conversational Agents.
  - The demo has to show the voice feature working.
- **Agentboxd**: real email inboxes for agents through an API. Create inboxes, send, reply, draft and search mail, with AI-applied labels such as urgency or phishing risk. Python SDK, JS SDK and an MCP server (`npx @agentboxd/mcp`). Free Builder plan with code `LARPHACKS-2026`.
  - The demo has to show the working inbox.
- **Other prizes**: Sportiner (tennis and pickleball tools), PostHog (analytics), Sentry, ConfigCat (feature flags).

Caveat: I could only read third-party listings for Agentboxd and found nothing on past LarpHacks winners. Check <https://agentboxd.com/docs/api> before depending on specific endpoints.

## At a glance

| # | Idea | Audience | Render | ElevenLabs | Agentboxd | Difficulty |
|---|------|----------|:---:|:---:|:---:|:---:|
| 1 | Thought Leadr | LinkedIn larpers | yes | yes | yes | easy |
| 2 | Margaret | Scam victims, fraud teams | yes | yes | yes | medium |
| 3 | Babel | Engineers and business people | yes | yes | yes | medium |
| 4 | Court Larper | Pickleball and tennis beginners | yes | yes | | medium |
| 5 | Sommelier Larp | Date-night diners | | yes | | easy |
| 6 | Local Larp | Travellers | yes | yes | | medium |
| 7 | Streamer Larp | Aspiring streamers | | yes | | easy |
| 8 | Did The Reading | Students | yes | yes | yes | easy |
| 9 | Founder Kit | Student entrepreneurs | yes | yes | yes | medium |
| 10 | Bedtime Larp | Parents and kids | | yes | | easy |
| 11 | Phone Anxiety Larp | Gen Z, people who hate calls | yes | yes | yes | medium |
| 12 | Native Larp | Language learners | yes | yes | | medium |
| 13 | Staff Engineer Larp | Developers | yes | yes | | easy |
| 14 | Wingman | Dating | | yes | | easy |
| 15 | Larp Master | Tabletop and LARP groups | yes | yes | yes | hard |

---

## 1. Thought Leadr: for LinkedIn larpers

You type something boring ("I went to a meeting and got a coffee"). It turns it into a hustle-culture post: a one-line hook, a lesson, a "Agree?" ending, and an audio version read like a TED keynote.

- **Demo moment:** a mundane sentence becomes a 12-line post and a dramatic voiceover in seconds.
- **Render:** fans out 20 post variants in parallel and ranks them.
- **ElevenLabs:** keynote voice, with applause from a sound effect.
- **Agentboxd:** an inbox where fake recruiter messages arrive and "you" replies in persona.
- **Why 5s:** theme is literal, it's very funny, and judges have all seen these posts.

## 2. Margaret: scam-baiting grandma

An agent plays a chatty, confused retiree and keeps phone and email scammers talking. It extracts their scripts, accounts and wallets into a fraud report.

- **Demo moment:** your teammate plays the scammer live, and a "scammer time wasted" counter climbs.
- **Render:** each conversation is a durable workflow, so many run at once, with parallel extraction after.
- **ElevenLabs:** Margaret's voice. **Agentboxd:** phishing emails land in her inbox and she replies.
- **Bank angle:** the intern knows what fraud teams need in a report.
- **Safety:** all details she gives out are clearly fake. Use browser voice in the demo instead of real phone lines.

## 3. Babel: tech and business each LARP as the other

A voice translator: the engineer says "idempotent retry queue" and the banker hears "you'll never be charged twice", and the reverse.

- **Demo moment:** you and your teammate speak live, and each hears the other's language.
- **Render:** after the meeting, parallel tasks produce tickets for the tech side and an executive summary for the business side.
- **Agentboxd:** each side gets its own email. **ElevenLabs:** a distinct voice per side.
- **Both audiences:** it bridges them by design.

## 4. Court Larper: pass as a pickleball regular

A beginner gets a courtside voice coach who whispers the rules, etiquette ("call the score before serving") and confident trash talk, and a hype mode for the mid-game.

- **Demo moment:** point a phone at a rally and the coach talks you through a point.
- **Render:** organizers get round-robin and ladder scheduling run as a workflow.
- **ElevenLabs:** coach voice and crowd sound effects.
- **Extra prize:** targets the Sportiner challenge as well (useful for players, coaches or organizers).

## 5. Sommelier Larp: fake being a wine snob

Photograph a menu or a bottle, and the app gives you three pompous tasting notes plus one safe, correct pairing, with a voice that sounds like a sommelier.

- **Demo moment:** a $14 bottle gets described as "a brooding, slate-forward vintage".
- **ElevenLabs:** persona voice, spoken privately into one earbud.
- **Why 5s:** it's low-risk to build, very funny on stage, and the theme is on the nose.
- **Note:** keep the pairing logic grounded so the product is actually useful, not just a joke.

## 6. Local Larp: pass as a local in a city you just landed in

Gives travellers the phrases, slang, ordering etiquette and walking-pace tips for a city, with accent coaching so they don't give themselves away.

- **Demo moment:** say a phrase badly, hear a native-sounding one, then repeat it back and get scored.
- **Render:** a pre-trip workflow builds a personalised "local cheat sheet" in parallel (food, transit, etiquette).
- **ElevenLabs:** native voices and voice changer for shadowing practice.

## 7. Streamer Larp: fake a 10,000-viewer stream

Aspiring streamers get a simulated audience: a chat full of distinct characters, text-to-speech donations, and crowd reactions that respond to what you actually say.

- **Demo moment:** you say something mildly funny and the "chat" erupts with voices and sound effects.
- **ElevenLabs:** many voices plus sound effects for hype, gasps and donations.
- **Why 5s:** very visual, Gen Z audience, and it doubles as practice for speaking to a live crowd.

## 8. Did The Reading: LARP as the student who prepared

Drop in the assigned reading. You get a 60-second spoken brief, three smart-sounding comments with the page references, and a likely-question list.

- **Demo moment:** a dense PDF becomes a spoken brief and three comments in under 30 seconds.
- **Render:** parallel chapter summaries, then a merge step.
- **Agentboxd:** the full study pack arrives in your inbox.
- **Guardrail:** make it a study aid that points to the source text, not a way to fabricate quotes.

## 9. Founder Kit: LARP as a founder in 60 seconds

Enter a startup idea and get a name, tagline, landing page, pitch script in a confident voice, and an inbox for investor-style replies.

- **Demo moment:** "idea to landing page and pitch voice" on stage, in front of judges.
- **Render:** logo, copy, page and pitch generated as parallel tasks, with a retry if one fails.
- **ElevenLabs:** the pitch voice. **Agentboxd:** the "hello@" inbox is live and answers.
- **Note:** label it as a satire and prototyping tool so it can't be mistaken for a real company.

## 10. Bedtime Larp: be a dragon for your kid

A parent reads a story and the app turns their voice into a dragon, a knight or a sleepy owl as they go, with matching sound effects for storms and footsteps.

- **Demo moment:** the voice changes character mid-sentence, and a judge's reaction is the proof.
- **ElevenLabs:** voice changer plus sound effects. This one is almost all ElevenLabs.
- **Audience:** non-technical parents and kids, which sets it apart from the rest of the list.

## 11. Phone Anxiety Larp: LARP as the person who just makes the call

An agent phones to book the dentist or cancel a subscription in a calm, confident voice, then emails you the confirmation.

- **Demo moment:** it "calls" a mock receptionist played by your teammate and books a slot.
- **Render:** a durable workflow handles the call, retries a busy line, and sends the follow-up.
- **Agentboxd:** the inbox that receives the confirmation and handles reschedules.
- **Why 5s:** funny, relatable, and genuinely useful.

## 12. Native Larp: pass as a native speaker

A language-learning coach for shadowing: you hear a native line, repeat it, and get feedback on rhythm and sounds, then hear your own sentence in a native-sounding voice.

- **Demo moment:** your own sentence played back in a native voice, side by side with your attempt.
- **ElevenLabs:** voice changer, TTS and Scribe for scoring. **Render:** a nightly workflow builds a personal practice plan.
- **Audience:** learners, immigrants, and anyone preparing for interviews or exams.

## 13. Staff Engineer Larp: review code like a principal

It reads your diff and leaves review comments in the calm, vague-but-wise tone of a staff engineer ("Have we considered the blast radius?"), plus a spoken summary. A hidden toggle shows the real, specific feedback.

- **Demo moment:** a messy PR gets a confident review read aloud.
- **Render:** parallel reviewers (security, performance, naming, tests) merge into one voice.
- **Audience:** developers, and your teammate can wire up the GitHub side quickly.

## 14. Wingman: rehearse being smooth

Practise a first date or networking chat against a voice agent that plays a realistic, slightly awkward person. It scores your openers and listening, and gives a gentle debrief.

- **Demo moment:** a short live conversation with real-time feedback beside it.
- **ElevenLabs:** conversational agent with emotional range.
- **Safety:** all characters are fictional and the tone is encouraging, not manipulative.

## 15. Larp Master: an AI game master for real LARPers and D&D tables

A voice game master that runs NPCs with distinct voices, plays ambient sound (tavern, storm, battle), tracks quest state, and emails each player a session recap.

- **Demo moment:** a judge plays a short scene and the world answers back in character with sound.
- **Render:** a long-running workflow holds the campaign state and generates recaps in parallel.
- **Agentboxd:** every NPC has an inbox, so players can write to them between sessions.
- **Why 5s:** it's literally the hackathon's namesake. It's the hardest to build, so only pick it if you scope tightly.

---

## Suggested shortlist for your team

1. **Margaret** — best sponsor coverage and the intern's fraud knowledge makes it credible.
2. **Babel** — your two backgrounds are the demo, and it speaks to tech and non-tech people at once.
3. **Thought Leadr** — easiest to finish, and the funniest if you want a safe win.

Whichever you choose, decide the first 30 seconds of the demo before you write code, and rehearse it with scripted lines so latency can't surprise you.

## Sources

- Render Workflows: <https://render.com/blog/durability-as-code-introducing-render-workflows> and <https://render.com/articles/render-vs-trigger>
- Agentboxd: <https://pypi.org/project/agentboxd/> and <https://jentic.com/apis/agentboxd.com/agentboxd.md>
- ElevenLabs: <https://elevenlabs.io/developers> and <https://elevenlabs.io/docs/overview/intro.md>
