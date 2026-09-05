# Five specialized Mawkingbird entry pages

These are proposed additions to mawkingbird.com, not implemented app routes. Keep the existing home entry intact: a live preview with an immediate sign-in or anonymous choice. The directory's current calls to action continue to use https://mawkingbird.com/ until specialized destinations exist.

## 1. Browse Mastodon without an account

**Proposed path:** /browse-without-an-account

**Search intent:** “browse Mastodon without an account”, “read Mastodon anonymously”.

**Objection:** “I don't want another account just to see what this is.”

**Headline:** “Look around. Join when you’re ready.”

**Supporting copy:** “Explore public conversations and find things worth reading before creating an account. Sign in when you want to post or reply.”

**First screen:** A working public-feed preview. Two actions: **Start reading** and **I already have an account**. The first action should complete the anonymous choice and dismiss the entry overlay immediately. Explain anonymous browsing as signed-out use; do not imply network anonymity or promise access to private content.

**Proof below the first screen:** Three examples of useful anonymous activities, a starter-kit preview, and a short answer about what needs sign-in. Keep extra detail optional.

**Success:** Anonymous choice completed, then a meaningful reading action. Do not make signup the only conversion.

## 2. Miss Twitter before it changed?

**Proposed path:** /old-twitter-feel

**Search intent:** “Mastodon client like old Twitter”, “Twitter 2018 interface alternative”.

**Objection:** “I don't want to learn a completely different interface.”

**Headline:** “Miss the Twitter you knew?”

**Supporting copy:** “A familiar, 2018-inspired design for finding people, reading conversations and joining in. Meet Mawkingbird.”

**First screen:** The actual Mawkingbird timeline preview. A short caption points out familiar navigation, without obscuring it. Actions: **Take a look** and **Sign in**.

**Proof below:** Real screenshots of the timeline and conversation view, followed by concise explanations of the differences users will notice. Show the interface instead of making nostalgic claims about a social network's culture.

**Success:** Enter the preview, open a conversation, return to the feed.

## 3. Build a feed worth opening on day one

**Proposed path:** /find-your-feed

**Search intent:** “who to follow on Mastodon”, “Mastodon starter kits”, “Mastodon feed empty”.

**Objection:** “I tried Mastodon and there was nothing in my feed.”

**Headline:** “Your interests. Your first feed.”

**Supporting copy:** “Start with a starter kit and discover people and sources around the things you care about.”

**First screen:** A small set of real starter-kit topics, with a preview of what each contains. Actions: **Preview this kit** and **Browse all starter kits**. Let a visitor inspect a kit before applying it; distinguish local reading setup from account follows.

**Proof below:** What a kit changes, what can be undone, and how to refine it later. Keep the benefit visible: a reading experience the visitor shaped themselves.

**Success:** Kit preview → deliberate kit selection → reading the resulting feed. Account creation is optional where supported.

## 4. Mastodon, Bluesky and RSS in one reading routine

**Proposed path:** /mastodon-bluesky-rss

**Search intent:** “Mastodon Bluesky RSS client”, “read social feeds and RSS together”.

**Objection:** “My people and reading are spread across too many places.”

**Headline:** “Keep up with more of your world.”

**Supporting copy:** “Bring Mastodon, Bluesky and RSS into your reading routine with Mawkingbird.”

**First screen:** A real preview demonstrating the supported source types, with clear source labels. Actions: **Explore the reader** and **Choose your sources**. The source picker must reflect the app's actual capabilities; avoid promising universal cross-posting or a merged feed unless that exact behavior is supported.

**Proof below:** A concrete reading scenario, RSS starter-kit example, and a short explanation of which actions need a network account.

**Success:** Explore a second source type or deliberately add a reading source.

## 5. What stays free?

**Proposed path:** /free-with-optional-plus (keep /plans as the detailed reference)

**Search intent:** “is Mawkingbird free”, “Mawkingbird Plus”, “Mawkingbird free limits”.

**Objection:** “Is this a trial that becomes unusable unless I pay?”

**Headline:** “Start free. Stay free. Add Plus when it suits you.”

**Supporting copy:** “Anonymous browsing and a free signed-in experience are ongoing ways to use Mawkingbird. Plus adds more convenience when you want it.”

**First screen:** The live preview alongside two short promises: **Free: read and build your setup in this browser. Plus: take your setup across devices and read more articles here.** Actions: **Continue free** and **See what Plus adds**.

**Proof below:** Three direct answers: “Is this a 30-day trial?” “What does Plus add?” “What happens if I stop paying?” Pull current limits, price and cancellation behavior from the app's existing plan sources. Do not duplicate limits as new hard-coded marketing constants.

**Success:** Enter the free experience after understanding it; separately measure Plus-detail visits and upgrades. A free choice is a successful conversion.

## Shared implementation notes

- Keep each page's substantive introduction, answers, title, canonical URL and links available in HTML before the preview starts. The public explanatory pages should be indexable independently of Angular's entry routing.
- Preserve signed-in and returning-anonymous state. A campaign entry must not reset someone to anonymous or re-ask a settled choice.
- The first action should do what its label says. Carry the intended destination through sign-in when necessary.
- Use actual screenshots and live content, with graceful fallbacks for unavailable preview servers.
- Track page, CTA and completed action without recording feed content, account names or reading histories. No analytics integration is included in this directory pass.
- Each page should answer a distinct situation with substantive content. Google recommends useful original content and a clear crawlable structure for search and AI features. [Google Search guidance](https://developers.google.com/search/docs/fundamentals/ai-optimization-guide)

## App sources inspected

- mastodon_mock/ui/src/app/pages/entry/entry.ts: existing preview dispatch and returning-user behavior.
- mastodon_mock/ui/src/app/pages/anonymous-entry/anonymous-entry.ts: explicit anonymous entry and server availability handling.
- mastodon_mock/ui/src/app/plus-benefits.ts: free/Plus benefits and shared plan values.
- mastodon_mock/ui/src/app/pages/plans/plans.html: reading, device and cancellation explanations.
- mastodon_mock/ui/src/app/pages/bundled-starter-kits/ and pages/rss/: starter kits and RSS support.
