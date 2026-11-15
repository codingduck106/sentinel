import { TopBar } from "@/components/TopBar";
import { TerminalCheck } from "@/components/TerminalCheck";
import type { TacticId } from "@/lib/api";

const TRICKS: { t: TacticId; name: string; what: string; example: string }[] = [
  { t: "urgency", name: "Urgency", what: "It pushes you to act right now, so you don’t stop to think.", example: "Act within 24 hours or lose access" },
  { t: "fear", name: "Fear", what: "It warns of a loss or threat so you feel you must respond.", example: "Your account has been suspended" },
  { t: "authority_impersonation", name: "Pretending to be official", what: "It poses as your bank, a delivery firm or the government.", example: "HSBC Fraud Team" },
  { t: "reward", name: "Too-good-to-be-true reward", what: "It dangles a prize or refund to make you click first.", example: "You have won a £1000 gift card" },
];

export default function Home() {
  return (
    <div className="frame">
      <TopBar />
      <main>
        <section className="hero" aria-labelledby="hero-h">
          <h1 id="hero-h">Scam text checker.</h1>
          <p className="hero-sub">
            Paste a text you&rsquo;re not sure about. Sentinel flags the pressure words and rates the risk.
          </p>
          <TerminalCheck />
        </section>

        <section className="section" id="how" aria-labelledby="tricks-h">
          <h2 id="tricks-h">Four tricks scam texts use</h2>
          <dl className="tricks">
            {TRICKS.map((x) => (
              <div key={x.t} className={`trick c-${x.t}`}>
                <dt><span className="dot" aria-hidden />{x.name}</dt>
                <dd>
                  <p className="soft">{x.what}</p>
                  <p className="example"><mark className={`hl hl-${x.t}`} style={{ color: "inherit" }}>{x.example}</mark></p>
                </dd>
              </div>
            ))}
          </dl>
        </section>

        <section className="section" aria-labelledby="decide-h">
          <h2 id="decide-h">How Sentinel decides</h2>
          <p className="soft flow-lede">Two separate checks read your message. Neither decides on its own.</p>
          <figure className="flow" aria-label="Your message goes through two checks, a spam pattern check and a pressure tactic check. A risk decision combines them into a verdict, the highlighted words, and what to do.">
            <div className="flow-node flow-start">Your message</div>
            <div className="flow-split" aria-hidden />
            <div className="flow-pair">
              <div className="flow-node">
                <h3>Spam pattern check</h3>
                <p className="soft">A machine-learning model compares the wording with patterns learned from 3,610 real UK text messages from 2011, 450 of them spam.</p>
                <p className="flow-out">Gives a spam score</p>
              </div>
              <div className="flow-node">
                <h3>Pressure tactic check</h3>
                <p className="soft">Rules look for urgency, fear, fake authority and too-good-to-be-true rewards.</p>
                <p className="flow-out">Finds the exact words</p>
              </div>
            </div>
            <div className="flow-join" aria-hidden />
            <div className="flow-node flow-decide">
              <h3>Risk decision</h3>
              <p className="soft">High risk needs two signals: spam-like wording plus a pressure tactic, or two tactics. One signal alone means &ldquo;could be a scam&rdquo;.</p>
            </div>
            <div className="flow-split" aria-hidden />
            <ul className="flow-outs">
              <li>The verdict</li>
              <li>Why: the words highlighted</li>
              <li>What to do next</li>
            </ul>
          </figure>
        </section>

        <section className="section" id="limits" aria-labelledby="limits-h">
          <h2 id="limits-h">What Sentinel can and can&rsquo;t tell you</h2>
          <div className="cando">
            <div>
              <h3>What it can do</h3>
              <p className="soft">
                It spots the pressure tactics (urgency, fear, fake authority and too-good-to-be-true rewards), checks the wording against
                patterns common in spam, then shows you the exact words doing the pushing.
              </p>
            </div>
            <div>
              <h3>What it can&rsquo;t do</h3>
              <p className="soft">
                It can&rsquo;t confirm who really sent a message, and it can be wrong. Treat it as a second opinion, not the final word.
              </p>
            </div>
          </div>
          <p className="closing">If in doubt, contact the company using a number you already trust.</p>
        </section>
      </main>
      <footer className="footer">We don&rsquo;t store the messages you check.</footer>
    </div>
  );
}
