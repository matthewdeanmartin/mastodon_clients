# Five Mawkingbird interstitial guides

These are proposed standalone pages on the comparison guide, leading to https://mawkingbird.com/. They answer questions before a visitor enters the app. The app keeps its existing live preview and sign-in/anonymous choice. These guides are optional destinations for “Learn more” links, never a forced step before “Try Mawkingbird”. No interstitial routes have been implemented yet.

## Recommended next step

Build one reusable interstitial template and use it first for **What stays free?**, then **All my friends are scattered**. The first resolves a purchasing objection; the second communicates a distinctive reason to try Mawkingbird.

Each page should have one clear question, a short answer, one real screenshot or concrete example, three supporting points, a few optional FAQs, and an **Open Mawkingbird** action linking to https://mawkingbird.com/. Keep a direct “Try Mawkingbird” action in house ads; add a quieter question link to the relevant guide.

These are normal, shareable HTML pages with their own search titles and canonical URLs. “Interstitial” describes their place in the journey, not a popup, countdown, or blocking overlay.

## 1. Browse Mastodon without an account

**Proposed path:** /meet-mawkingbird/browse-without-an-account/

**Search intent:** “browse Mastodon without an account”, “read Mastodon anonymously”.

**Objection:** “I don't want another account just to see what this is.”

**Headline:** “Look around. Join when you’re ready.”

**Supporting copy:** “Explore public conversations and find things worth reading before creating an account. Sign in when you want to post or reply.”

**First screen:** Explain what visitors can explore without an account, beside a real screenshot of anonymous reading. Action: **Open Mawkingbird**, where the visitor chooses anonymous browsing or sign-in. Explain anonymous browsing as signed-out use, not network anonymity or access to private content.

**Proof below the first screen:** Three examples of useful anonymous activities, a starter-kit preview, and a short answer about what needs sign-in. Keep extra detail optional.

**Success:** Anonymous choice completed, then a meaningful reading action. Do not make signup the only conversion.

## 2. Miss Twitter before it changed?

**Proposed path:** /meet-mawkingbird/old-twitter-feel/

**Search intent:** “Mastodon client like old Twitter”, “Twitter 2018 interface alternative”.

**Objection:** “I don't want to learn a completely different interface.”

**Headline:** “Miss the Twitter you knew?”

**Supporting copy:** “A familiar, 2018-inspired design for finding people, reading conversations and joining in. Meet Mawkingbird.”

**First screen:** A real Mawkingbird timeline screenshot with a short caption pointing out the familiar navigation. Action: **Open Mawkingbird**.

**Proof below:** Real screenshots of the timeline and conversation view, followed by concise explanations of the differences users will notice. Show the interface instead of making nostalgic claims about a social network's culture.

**Success:** Enter the preview, open a conversation, return to the feed.

## 3. Build a feed worth opening on day one

**Proposed path:** /meet-mawkingbird/find-your-feed/

**Search intent:** “who to follow on Mastodon”, “Mastodon starter kits”, “Mastodon feed empty”.

**Objection:** “I tried Mastodon and there was nothing in my feed.”

**Headline:** “Your interests. Your first feed.”

**Supporting copy:** “Start with a starter kit and discover people and sources around the things you care about.”

**First screen:** Show a few real starter-kit topics and examples of what they contain. Explain what choosing a kit does. Action: **Open Mawkingbird**. Distinguish local reading setup from account follows; this explanatory page does not apply kits or modify accounts.

**Proof below:** What a kit changes, what can be undone, and how to refine it later. Keep the benefit visible: a reading experience the visitor shaped themselves.

**Success:** Kit preview → deliberate kit selection → reading the resulting feed. Account creation is optional where supported.

## 4. All my friends are scattered

**Proposed path:** /meet-mawkingbird/all-my-friends-are-scattered/

**Search intent:** “Mastodon Bluesky RSS client”, “read social feeds and RSS together”.

**Objection:** “All my friends are scattered”

**Headline:** “All my friends are scattered”

**Supporting copy:** “Bring Mastodon, Bluesky and RSS into your reading routine with Mawkingbird.”

**First screen:** A concrete example of keeping up with friends on Mastodon and Bluesky, plus the sites you read through RSS. Use real screenshots with clear source labels. Action: **Open Mawkingbird**. Explain the supported reading behavior without promising universal cross-posting or a merged feed unless that exact behavior is supported.

**Proof below:** A concrete reading scenario, RSS starter-kit example, and a short explanation of which actions need a network account.

**Success:** Explore a second source type or deliberately add a reading source.

## 5. What stays free?

**Proposed path:** /meet-mawkingbird/what-stays-free/ (link to mawkingbird.com/plans for current details)

**Search intent:** “is Mawkingbird free”, “Mawkingbird Plus”, “Mawkingbird free limits”.

**Objection:** “Is this a trial that becomes unusable unless I pay?”

**Headline:** “Start free. Stay free. Add Plus when it suits you.”

**Supporting copy:** “Anonymous browsing and a free signed-in experience are ongoing ways to use Mawkingbird. Plus adds more convenience when you want it.”

**First screen:** Two short promises: **Free: read and build your setup in this browser. Plus: take your setup across devices and read more articles here.** Action: **Open Mawkingbird**. A secondary anchor, **See what Plus adds**, reveals the explanation on this guide.

**Proof below:** Three direct answers: “Is this a 30-day trial?” “What does Plus add?” “What happens if I stop paying?” Pull current limits, price and cancellation behavior from the app's existing plan sources. Do not duplicate limits as new hard-coded marketing constants.

**Success:** Enter the free experience after understanding it; separately measure Plus-detail visits and upgrades. A free choice is a successful conversion.

## Shared implementation notes

- Render the complete guide as static HTML on the directory, with its own title, description, canonical URL and internal links. App JavaScript is not needed to read it.
- Link to the existing app entry. Let the app preserve signed-in and returning-anonymous state; the guide never manipulates that state.
- Label the outbound action “Open Mawkingbird” or “Try Mawkingbird”. Do not promise that a link has already chosen anonymous mode, installed a kit or signed someone in.
- Use actual screenshots with useful captions and alt text. The guide should not depend on a live public feed to load.
- Track page, CTA and completed action without recording feed content, account names or reading histories. No analytics integration is included in this directory pass.
- Each page should answer a distinct situation with substantive content. Google recommends useful original content and a clear crawlable structure for search and AI features. [Google Search guidance](https://developers.google.com/search/docs/fundamentals/ai-optimization-guide)

## App sources inspected

- mastodon_mock/ui/src/app/pages/entry/entry.ts: existing preview dispatch and returning-user behavior.
- mastodon_mock/ui/src/app/pages/anonymous-entry/anonymous-entry.ts: explicit anonymous entry and server availability handling.
- mastodon_mock/ui/src/app/plus-benefits.ts: free/Plus benefits and shared plan values.
- mastodon_mock/ui/src/app/pages/plans/plans.html: reading, device and cancellation explanations.
- mastodon_mock/ui/src/app/pages/bundled-starter-kits/ and pages/rss/: starter kits and RSS support.
