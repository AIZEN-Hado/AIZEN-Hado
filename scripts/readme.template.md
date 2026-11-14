<!-- Template for README.md. Run `python3 scripts/build.py` after editing.
     Write images as plain <img src="assets/NAME.svg">. The build expands each into a <picture> that
     picks the -dark/-light variant for the GitHub theme and the frozen assets/static/ twin for
     prefers-reduced-motion. -->
<a href="https://portfoliio-jet.vercel.app/"><img src="assets/cosmic-hero.svg" width="100%" alt="Yashsingh Chauhan, AI engineer working on LLM systems. Engineering intelligence that can be trained, tested, and trusted. Focus: fine-tuning infrastructure, agent evaluation, full-stack AI."></a>

<img src="assets/band-01-identity.svg" width="100%" alt="01. Identity">

I work on the layer that decides whether an LLM system survives contact with production: **how models are adapted, how agents are evaluated, and how both run as dependable software.** Right now that means LoRA fine-tuning infrastructure for open-weight models, a statistical CI gate for LLM agents, and the Python and TypeScript services around them.

Working rule across every project below: *if a number was not measured, it is not shown.*

<sub>BHOPAL, INDIA &nbsp;·&nbsp; VELLORE INSTITUTE OF TECHNOLOGY &nbsp;·&nbsp; OPEN TO AI ENGINEERING ROLES</sub>

<img src="assets/band-02-exploring.svg" width="100%" alt="02. Currently exploring">

<img src="assets/research-grid.svg" width="100%" alt="Four research vectors. V.01 Agent evaluation: pass^k sampling, McNemar's test, judge calibration. V.02 Parameter-efficient fine-tuning: LoRA, supervised fine-tuning, open-weight models. V.03 Tool-using agents: agent loops, MCP, Claude skills. V.04 Retrieval and graph reasoning: RAG, GraphRAG, knowledge graphs.">

<img src="assets/band-03-arsenal.svg" width="100%" alt="03. Engineering arsenal">

<img src="assets/arsenal.svg" width="100%" alt="Stack manifest. AI and ML: PyTorch, Transformers, PEFT and LoRA, TRL, LiteLLM, scikit-learn. Languages: Python, TypeScript, JavaScript, Java, SQL. Frameworks: FastAPI, Next.js, React, Spring Boot, Express, React Native. Infrastructure: PostgreSQL, Redis, MongoDB, SQLite, Docker, RunPod GPUs. Tooling: OpenTelemetry, GitHub Actions, uv, Turborepo, pytest, Supabase.">

<img src="assets/band-04-work.svg" width="100%" alt="04. Selected work">

{{work}}

<img src="assets/band-05-telemetry.svg" width="100%" alt="05. Development telemetry">

<img src="assets/telemetry.svg" width="100%" alt="Development telemetry from the GitHub GraphQL API, refreshed daily: public contributions over the last 12 months, active days, longest streak, public repositories, weekly activity, a daily contribution field and the language mix of public repositories.">

<img src="assets/band-06-frontier.svg" width="100%" alt="06. The research frontier">

> **Q.01 &nbsp;Regression, or noise?**<br>
> An agent changes: a prompt edit, a model version, a tool schema, a refactored loop. Its outputs are stochastic and multi-turn, so one run proves nothing either way. Which differences are real, and which layer caused them?<br>
> <sub>WORKING ANSWER · pass^k sampling, McNemar's exact test as a merge gate, trajectory diffs to locate the change &nbsp;·&nbsp; INSTRUMENT · Fisherman</sub>

> **Q.02 &nbsp;When is a judge allowed to judge?**<br>
> LLM-as-judge is cheap and scales, but a lenient judge quietly lets regressions through. How much agreement with human labels is enough before a judge may block a merge, and which deterministic checks must sit underneath it?<br>
> <sub>WORKING ANSWER · calibrate against a golden set (κ, FPR, FNR), back the judge with rule assertions &nbsp;·&nbsp; INSTRUMENT · Fisherman</sub>

> **Q.03 &nbsp;What does an adapter actually learn?**<br>
> LoRA trains a low-rank update on a frozen model. Separating a genuine domain gain from memorised formatting needs base and adapter evaluated on the same held-out examples, with provenance for both.<br>
> <sub>WORKING ANSWER · base-versus-adapter evaluation on held-out data, verified artifacts only &nbsp;·&nbsp; INSTRUMENT · fine-tuning platform (private, in development)</sub>

> **Q.04 &nbsp;Can structure define a unit of work?**<br>
> Time and line counts are weak proxies for "this feature is done". Can syntax-tree changes, weighted by depth, spread and confidence, recognise a meaningful milestone without asking the developer?<br>
> <sub>WORKING ANSWER · weighted milestone scoring over AST diffs &nbsp;·&nbsp; INSTRUMENT · SemiGit</sub>

<img src="assets/band-07-contact.svg" width="100%" alt="07. Establish connection">

<img src="assets/contact-terminal.svg" width="100%" alt="Uplink open. Open to AI engineering roles and research collaborations. Transmitting from Bhopal, India.">

<a href="https://portfoliio-jet.vercel.app/"><img src="assets/channel-1-portfolio.svg" width="100%" alt="Channel 1, Portfolio: portfoliio-jet.vercel.app"></a><br>
<a href="https://www.linkedin.com/in/yashsinghchauhan29"><img src="assets/channel-2-linkedin.svg" width="100%" alt="Channel 2, LinkedIn: in/yashsinghchauhan29"></a><br>
<a href="mailto:yashchauhan2905@gmail.com"><img src="assets/channel-3-email.svg" width="100%" alt="Channel 3, Email: yashchauhan2905@gmail.com"></a><br>
<a href="https://wa.me/918962125787"><img src="assets/channel-4-whatsapp.svg" width="100%" alt="Channel 4, WhatsApp: direct message"></a>

<img src="assets/footer.svg" width="100%" alt="End of transmission">
