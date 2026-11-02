# Example interactions

Short chats showing rational behavior (not "always invent a project").

---

### 1) Insufficient information -- clarify only

**User:** Using project-navigator, what's the best project to build next?

**Agent:** (runs preflight on empty/missing profile)  
I need a few constraints before recommending anything:

1. Are you optimizing for learning, portfolio evidence, income, or research right now?
2. What time window do you have this week or month?
3. What can you already show with evidence (repos, papers, shipped work)?

*(Stops. No project list.)*

---

### 2) Generic / saturated idea -- don't rebuild

**User:** Profile attached. Should I build a climate dashboard for my portfolio?

**Agent:** (preflight may offer quick vs deep; user picks quick)  
**Action: study** -- Don't build another generic climate dashboard; they're saturated.  

First experiment: spend 45 minutes on one existing open-source dashboard, run one data fetch, write what breaks. Continue only if you find a concrete local/data gap.

---

### 3) Immediate money -- earn beats prestige project

**User:** Rent is due in two weeks. I was going to build an open-source analytics platform for my portfolio. What should I do?

**Agent:**  
**Action: earn** -- An unpaid platform does not meet your constraint. Prefer short paid automation / freelance cleanup using skills you already have.  

Trade-off: less portfolio theater this month. Protect 1-2 evenings later for a smaller trajectory-aligned experiment once rent is covered.

---

### 4) Beginner learning -- study then reproduce

**User:** I'm a beginner. Project idea: todo app with AI features.

**Agent:**  
**Action: dont** (as greenfield portfolio) / **study** -- AI-todo apps are low-signal.  

Better path: pick one small existing app, reproduce its API or data path, then change one component. That teaches more than shipping another wrapper.

---

### 5) Build claim + deep mode -- check prior art first

**User:** Deep mode. Should I build a new ETL framework?

**Agent:** (S4 search + normalize)  
Several mature toolkits already cover batch ETL.  

**Action: contribute** -- Reproduce an upstream quickstart this week; open a docs/bug PR if you hit a sharp edge. Build a new framework only if you can name a gap those tools miss.

---

### 6) Conflicting preferences -- make conflict explicit

**User:** I need an AI product-eng job soon, but I'll only use Haskell and I refuse all cloud vendors. Plan my project.

**Agent:**  
Those constraints conflict with the usual evidence bar for that role (and with "soon").  

**Action: wait** or **dont** (as currently framed) -- Resolve which constraint moves: role target, stack, cloud, or timeline. A Haskell-only no-cloud "AI product" app is unlikely to be the rational unlock.
