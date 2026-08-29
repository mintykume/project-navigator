> This is the full design philosophy behind Project Navigator -- why it exists, what it optimizes for, and the taxonomy it uses to avoid AI-generated project slop. It's written for humans reading the repo, not loaded into a running conversation: the operational rules an agent actually follows live in [`prompts/core-policy.md`](prompts/core-policy.md) and [`prompts/stages/`](prompts/stages/), which distill the ideas below into something small enough to fit in context. For install and quick usage, see [README.md](README.md) and [QUICKSTART.md](QUICKSTART.md).

---

# Project Navigator

**An LLM skill for deciding what to build, research, learn, contribute to, publish, or pursue next.**

Project Navigator helps people use AI to make **better technical decisions**, not merely generate more project ideas.

It connects a person's existing capabilities, trajectory, preferences, constraints, and goals with the changing outside world: real problems, research, datasets, open-source work, career paths, scholarships, competitions, grants, organizations, local opportunities, and emerging technologies.

Its central question is:

> **Given who you are, what you can already do, where you want to go, what the world currently needs, and what constraints you have, what is the most rational thing to do next?**

The skill is designed to reduce **AI-generated project slop**: duplicated projects, generic tutorials, unnecessary technology choices, abandoned repositories, shallow portfolio pieces, and work that looks productive without creating meaningful value.

---

# Why Project Navigator Exists

AI has made implementation dramatically cheaper.

A person can now ask an LLM to:

* generate an application,
* reproduce a paper,
* create a visualization,
* write an API,
* make a website,
* explain a technology,
* produce a GitHub repository,
* write a social post,
* or turn an idea into a prototype.

This creates a new problem.

The bottleneck is increasingly not:

> **"Can I build this?"**

It is:

> **"Should I build this?"**

And after that:

> **"Is this the best use of my time?"**

> **"Does this already exist?"**

> **"Would anyone benefit from another version?"**

> **"Does this move me toward the career I actually want?"**

> **"Should I be building, researching, learning, earning money, networking, or simply understanding the problem better?"**

Project Navigator is designed around these decisions.

---

# The Core Philosophy

Project Navigator follows:

## Find -> Understand -> Match -> Test -> Build -> Verify -> Connect -> Compound

### Find

Find real problems, research questions, opportunities, technologies, organizations, datasets, and unmet needs.

### Understand

Understand the problem before immediately proposing an implementation.

Sometimes the correct first step is:

* reading a paper,
* examining an existing repository,
* interviewing someone,
* studying a regulation,
* looking at a map,
* understanding a social or economic mechanism,
* examining historical context,
* or learning the relevant domain.

### Match

Determine whether the problem actually fits the person's:

* technical abilities,
* demonstrated experience,
* trajectory,
* interests,
* preferred working style,
* available resources,
* location,
* time,
* financial constraints,
* and current priorities.

### Test

Before committing to a large project, identify the cheapest experiment that can determine whether the direction is worth pursuing.

### Build

Use AI to accelerate implementation once the direction has earned the investment.

### Verify

Determine whether the resulting work actually works and whether it is worth presenting publicly.

### Connect

Identify what the finished work could connect to:

* research,
* open source,
* organizations,
* communities,
* scholarships,
* competitions,
* grants,
* jobs,
* customers,
* collaborators,
* or future projects.

### Compound

Prefer actions that create reusable capabilities, evidence, relationships, assets, knowledge, or opportunities for future work.

---

# What Project Navigator Is NOT

Project Navigator is deliberately **not**:

* a generic project-idea generator;
* a random list of hackathon ideas;
* a motivational productivity bot;
* a portfolio spam generator;
* a social-media content generator;
* a startup-idea generator;
* a career quiz;
* a replacement for domain experts;
* an algorithm that pretends to know the objectively optimal life decision.

It should be willing to tell the user:

> **"Don't build this."**

It should also be willing to say:

> **"This already exists. Don't recreate it; study it, contribute to it, extend it, or find the remaining gap."**

And sometimes:

> **"Don't code yet. You don't understand the problem sufficiently."**

---

# 1. Existing-Project Awareness

One of the most important rules is:

> **Do not recommend building something merely because it sounds like a good project. First determine whether it already exists.**

The skill should search for:

* GitHub repositories;
* existing applications;
* research projects;
* papers;
* datasets;
* APIs;
* commercial products;
* open-source alternatives;
* previous hackathon projects;
* university projects;
* standards;
* existing implementations.

It should distinguish between:

### Exists and is already good

**Don't rebuild it.**

Possible actions:

* analyze the repository;
* reproduce its results;
* contribute;
* fix an issue;
* improve documentation;
* benchmark it;
* create an extension;
* build an integration;
* study its architecture.

### Exists but has an obvious limitation

**Build the missing piece.**

### Exists but is abandoned

Investigate whether the problem is still valuable before reviving it.

### Exists as research but not as a practical tool

Potentially build the implementation.

### Exists commercially but not openly

Potentially investigate an open alternative, integration, or complementary tool.

### Does not appear to exist

This is particularly interesting, but **absence of a search result is not proof of novelty**.

The skill should communicate uncertainty rather than declaring:

> "Nobody has built this."

---

# 2. Basic Projects Should Be Treated Differently

A beginner does not necessarily need an original invention.

For a basic-level user, an existing project can be extremely valuable.

Instead of:

> "Build another weather application."

Project Navigator might say:

> "Three strong weather applications already exist. Rebuilding one from scratch has low novelty. However, analyzing repository X with AI and reproducing its data pipeline would teach you APIs, data processing, testing, and visualization. Then modify one component."

This creates a progression:

**Study -> Reproduce -> Modify -> Extend -> Create**

The system therefore does **not** confuse originality with learning value.

A project can be worthwhile because it teaches a capability.

---

# 3. Novelty and Social Value

When the user is sufficiently advanced, the system should increasingly prioritize:

> **"What useful thing is missing?"**

A candidate project should be evaluated against:

* existing solutions;
* unmet needs;
* number and type of beneficiaries;
* accessibility of the problem;
* technical feasibility;
* potential differentiation;
* evidence of demand;
* maintenance requirements;
* opportunity cost;
* potential downstream uses.

The ideal recommendation is not:

> "Nobody has done this."

It is:

> **"There appears to be a meaningful gap, here is the evidence, here is why this user is unusually suited to address it, and here is the smallest experiment that can determine whether the gap is real."**

---

# 4. User Capability and Trajectory

Project Navigator should not treat a user as a static list of programming languages.

It should distinguish:

### Demonstrated capabilities

Things supported by actual evidence:

* repositories;
* code;
* projects;
* papers;
* contributions;
* experiments;
* deployed applications;
* coursework;
* documented work.

### Claimed capabilities

Things the user says they know but that may not yet have strong evidence.

### Emerging capabilities

Things they are currently learning.

### Missing capabilities

Things required by a desired direction.

### Transferable capabilities

Mental models and technical abilities that can move between fields.

---

# 5. Career Trajectory Matching

The skill should consider not only:

> "What technology does this project use?"

but:

> **"What career path rewards the capabilities this project develops?"**

For example, the same project might be evaluated differently for someone pursuing:

* ML engineering;
* research;
* scientific computing;
* robotics;
* data engineering;
* climate technology;
* product engineering;
* UX engineering;
* technical entrepreneurship;
* computational social science;
* visualization;
* systems engineering.

The skill should look for **career paths that value the relevant capability combinations and working patterns**.

It should also identify when a project would be useful because it demonstrates a transferable mental model rather than merely another programming language.

---

# 6. Technical Depth vs. Big-Picture Understanding

Project Navigator should recognize that becoming better technically is not always the correct next move.

Sometimes the user needs to go deeper:

> Learn the algorithm.
> Understand the architecture.
> Implement the system.
> Benchmark it.
> Read the relevant papers.

Other times the user needs to step back:

> Who is affected?
> What incentives exist?
> What regulation applies?
> What economic mechanism causes this?
> What historical context matters?
> What behavior are we actually trying to change?
> Who benefits and who pays?

This is particularly important for projects involving:

* climate;
* sustainability;
* healthcare;
* education;
* government;
* economics;
* public policy;
* communities;
* human behavior.

A technically impressive solution can still solve the wrong problem.

The skill should therefore recommend **humanities, social-science, policy, economic, historical, or ethical investigation when those disciplines materially affect the problem**.

---

# 7. The Skill-Progression Map

Sometimes the correct answer is not another project.

The user may need to see their current capability map.

Project Navigator can suggest creating a progression map showing:

```text
Current capabilities
       |
Missing capabilities
       |
Possible career directions
       |
Projects that demonstrate them
       |
Research opportunities
       |
Organizations / communities
       |
Higher-level opportunities
```

The map should only be generated when it provides useful decision-making information.

It should not force users into a giant skills tree every time they ask a simple question.

---

# 8. Clarification Before Computation

The skill should avoid wasting:

* tokens;
* API calls;
* web searches;
* computation;
* context window;
* user attention.

If an important piece of information is missing, it should ask a concise clarifying question before performing an expensive analysis.

For example:

> "Are you optimizing for income within the next month, or long-term career leverage?"

That single answer can radically change the recommendation.

Similarly:

> "Do you have time for a 2-week project, or do you need something you can finish this weekend?"

The system should prefer **cheap clarification over expensive incorrect analysis**.

---

# 9. The "Wait or Analyze Now?" Decision

Sometimes the user wants an answer immediately.

Sometimes a better answer requires:

* searching current information;
* comparing existing projects;
* examining papers;
* checking opportunities;
* mapping a career path;
* analyzing the user's repositories.

Project Navigator should be able to say:

> **Quick answer:** I can give you a useful answer now.

or:

> **Better answer:** I can do a deeper search and comparison, but it will take more processing and external information. Is that worth doing for this decision?

This makes resource usage itself part of the decision system.

---

# 10. Leverage and Compounding

Project Navigator should explicitly look for **high-leverage actions**.

Relevant concepts include:

* leverage;
* compounding;
* optionality;
* reuse;
* distribution;
* network effects;
* learning value;
* information value;
* credibility;
* automation;
* ownership;
* defensibility;
* transferability;
* time-to-value;
* opportunity cost.

But these should **not become fake numerical scores**.

The system should explain the reasoning.

For example:

> "This project has low immediate financial value but creates a reusable dataset pipeline, demonstrates geospatial engineering, and opens three research directions. Its main value is option creation rather than direct income."

---

# 11. Immediate Money vs. Long-Term Leverage

High-leverage work is not always the correct decision.

The system must account for the user's actual circumstances.

If someone needs money immediately, a lower-leverage action can be rational.

For example:

```text
Immediate objective:
Earn money this month.

Action A:
Small automation job -> EUR100 this week.

Action B:
Research project -> potentially valuable career asset in 6 months.
```

The skill should not automatically choose B because it sounds more ambitious.

Instead it should explain:

> "B has stronger long-term compounding value, but A better satisfies your immediate constraint. If you choose A, here is how to prevent it from consuming the time needed for your longer-term trajectory."

The goal is **rational prioritization**, not prestige maximization.

---

# 12. The Rationality Filter

Before recommending a significant activity, Project Navigator should challenge its own recommendation.

Questions include:

1. Does this solve a real problem?
2. Does the user actually need it?
3. Does something equivalent already exist?
4. Why would another implementation matter?
5. Is there evidence of demand?
6. Does it fit the user's trajectory?
7. Does it fit their current constraints?
8. What is the opportunity cost?
9. What could the user learn instead?
10. Is there a smaller experiment?
11. Does it create meaningful evidence?
12. Could it create future opportunities?
13. Is there a simpler way to achieve the same outcome?
14. Would this still be rational if AI had not made implementation cheap?
15. Is the recommendation being generated merely because it sounds impressive?

If the answer is weak, the skill should downgrade or reject the recommendation.

---

# 13. Avoiding "AI Slop"

Project Navigator should actively avoid encouraging:

* generic AI wrappers;
* duplicate dashboards;
* trivial CRUD applications;
* shallow chatbots;
* tutorial clones;
* automatically generated content farms;
* meaningless social-media posts;
* projects created only because they are easy to generate.

AI should be treated as an **execution multiplier**, not as a reason to manufacture more objects.

The system should ask:

> **"What is scarce here?"**

If implementation is no longer scarce, the answer might be:

* domain knowledge;
* original data;
* research;
* experimentation;
* users;
* distribution;
* trust;
* integration;
* judgment;
* relationships.

---

# 14. Research Support

Project Navigator can recommend research paths when appropriate.

A research path might include:

1. Find the relevant literature.
2. Identify an unresolved question.
3. Reproduce an existing result.
4. Obtain the relevant dataset.
5. Build the smallest experimental pipeline.
6. Visualize the result.
7. Compare against existing methods.
8. Identify unexpected findings.
9. Decide whether deeper research is justified.
10. Identify researchers, labs, competitions, conferences, or programs relevant to the result.

The system can also help turn technical experiments into useful visualizations and explanations.

---

# 15. Visualization as a First-Class Capability

Some problems are better understood visually.

The skill should consider:

* maps;
* time-series plots;
* network graphs;
* geospatial visualizations;
* interactive dashboards;
* scientific figures;
* system diagrams;
* animations;
* before/after comparisons.

If the user prefers visual work, Project Navigator should explicitly prioritize projects where visualization is a meaningful part of the value rather than merely decorating a technical project.

---

# 16. Opportunities Beyond GitHub

A project should not automatically end with:

> "Upload it to GitHub."

Depending on the work, the skill can suggest:

* open-source contribution;
* research collaboration;
* university laboratories;
* scholarships;
* fellowships;
* hackathons;
* competitions;
* grants;
* sustainability programs;
* civic-tech organizations;
* local events;
* conferences;
* community projects;
* internships;
* freelance opportunities;
* potential customers;
* relevant companies.

The skill should search for **actual current opportunities** rather than inventing generic categories.

---

# 17. Opportunity Unlocking

A particularly important capability is recognizing that:

> **Project X may be valuable because it makes Opportunity Y accessible.**

For example:

```text
Build sustainability data tool
        |
demonstrates geospatial + data skills
        |
relevant research program
        |
application / collaboration
```

Or:

```text
Open-source contribution
        |
demonstrated domain expertise
        |
maintainer relationship
        |
research / internship / job opportunity
```

The skill should therefore ask:

> **"What doors does this work open?"**

rather than only:

> "Is this project impressive?"

---

# 18. GitHub and Distribution Assistance

When the user has produced meaningful work, Project Navigator should proactively help package it.

It can assist with:

* repository structure;
* README;
* installation instructions;
* examples;
* tests;
* screenshots;
* demonstrations;
* documentation;
* license selection;
* issue templates;
* contribution guidelines;
* release notes;
* project descriptions;
* technical writeups;
* visual explanations;
* portfolio entries;
* social posts.

The skill should also determine **whether something is worth posting at all**.

Not every experiment deserves public distribution.

---

# 19. Proof Before Promotion

Before recommending:

> "Post this."

the skill should inspect whether there is something worth showing.

Evidence can include:

* working implementation;
* reproducible setup;
* meaningful experiment;
* real dataset;
* benchmark;
* comparison;
* visualization;
* user feedback;
* documented limitation;
* research finding;
* useful contribution.

A README and passing tests alone do not make a project valuable.

The system should evaluate:

> **Does this artifact contain an actual signal worth communicating?**

---

# 20. Monetization

Monetization is treated as **one possible downstream path**, not the default goal.

The skill can investigate:

* direct customer demand;
* B2B applications;
* developer tooling;
* APIs;
* paid integrations;
* consulting;
* freelance work;
* grants;
* competitions;
* sponsorship;
* licensing;
* research funding;
* open-source sustainability.

It should distinguish:

### Immediate monetization

> Can this reasonably generate money soon?

### Strategic monetization

> Could this become a product or service?

### Indirect economic value

> Does this materially increase access to better opportunities?

### Non-monetary value

> Is the project worth doing even if it never earns money?

This prevents the system from forcing every interesting technical project into a startup.

---

# 21. Sustainability and Climate Projects

For sustainability-oriented work, the skill should go beyond:

> "Build a climate dashboard."

It should investigate:

* actual environmental problems;
* available datasets;
* scientific literature;
* existing organizations;
* municipal initiatives;
* policy context;
* local conditions;
* relevant researchers;
* active open-source projects;
* grants;
* scholarships;
* competitions;
* fellowships;
* sustainability programs;
* organizations that could benefit from the work.

A project can therefore become a bridge between:

**technical capability -> environmental problem -> evidence -> organization -> opportunity.**

This is the domain `examples/sample-recommendation.md` and `examples/interactions.md` #2 both use to demonstrate the skill end-to-end -- it's a flagship worked example precisely because it forces the "understand and check prior art before building" discipline this whole document argues for. It is not a required lens the skill applies to every recommendation; the same rigor applies to whatever domain the user's own profile and question point to.

---

# 22. Local and Offline Opportunities

Location can materially change what is useful.

Project Navigator can search for relevant:

* hackathons;
* university laboratories;
* technology communities;
* civic-tech initiatives;
* environmental organizations;
* maker spaces;
* conferences;
* workshops;
* public datasets;
* research programs;
* local companies;
* volunteer technical projects.

It should distinguish:

**online opportunity**

from

**something the user can realistically participate in locally.**

---

# 23. Personal Rules and Preferences

Recommendations should respect the user's stated:

* interests;
* preferred technologies;
* desired career direction;
* working style;
* risk tolerance;
* time constraints;
* financial goals;
* location;
* willingness to collaborate;
* preference for research vs. implementation;
* preference for visual vs. abstract work;
* preferred project size;
* ethical boundaries.

These preferences are constraints on the decision, not decorations.

If preferences conflict with goals, the system should make the conflict explicit.

---

# 24. Project Progression as a Game-Like System

Project Navigator can model development as progression:

```text
Current capability
        |
Quest
        |
Small experiment
        |
Result
   /         \
works       doesn't work
  |             |
build        learn / pivot
  |
artifact
  |
new capability
  |
new opportunities
```

A project should ideally **change the user's future option set**.

The system should therefore favor projects that:

* reuse existing capabilities;
* introduce strategically useful new capabilities;
* create reusable assets;
* produce credible evidence;
* open multiple future directions.

A useful heuristic is:

> **Use roughly 60-80% familiar capability and 20-40% strategically new capability when the goal is growth.**

This can be adjusted based on the user's level and objective.

---

# 25. Information Value

Sometimes the highest-value action isn't building anything.

A one-hour experiment that determines whether a project deserves another 40 hours can have enormous value.

Project Navigator should therefore search for:

> **The cheapest action that substantially reduces an important uncertainty.**

Examples:

* download the dataset;
* test whether the API works;
* reproduce one paper result;
* interview one potential user;
* benchmark one model;
* inspect one existing repository;
* plot one variable;
* test one hardware component.

This is one of the strongest ways the system applies the 80/20 principle.

---

# 26. The 20/80 Principle

Project Navigator should not interpret 80/20 as:

> "Always do the easiest 20%."

Instead:

> **Find the small number of actions that disproportionately change the value of everything that follows.**

These may be:

* one experiment;
* one conversation;
* one paper;
* one technical capability;
* one dataset;
* one open-source contribution;
* one relationship;
* one architectural decision;
* one distribution channel.

The goal is **high information gain + high option creation + high downstream value**.

---

# 27. The Decision Output

A strong recommendation should look approximately like:

### Recommendation

**Build X**

### Why you

What existing evidence makes this a good fit?

### Why now

What current problem, technology, opportunity, or timing makes it relevant?

### Existing alternatives

What already exists?

### The gap

What is actually missing?

### First experiment

What can you do in ~30-60 minutes?

### Success condition

What result determines whether you continue?

### Capability unlocked

What do you learn or demonstrate?

### Downstream paths

What can this lead to?

* research;
* open source;
* portfolio;
* community;
* career;
* money.

### Trade-off

What are you giving up by doing this?

### Alternative

What would you do instead if the user's priority were different?

### Confidence

What is known, what is inferred, and what remains uncertain?

This maps directly onto [`templates/decision-output.md`](templates/decision-output.md), which is what the skill actually fills in, and onto the lint contract in [`scripts/check_recommendation.py`](scripts/check_recommendation.py).

---

# 28. The Master Decision Loop

The entire system can be summarized as:

```text
                    USER
                     |
        +------------+------------+
        |                         |
   PERSONAL STATE            WORLD STATE
        |                         |
   skills/history            problems
   trajectory                research
   preferences               opportunities
   constraints               technologies
        |                         |
        +------------+------------+
                     |
              EXISTING WORLD
                     |
            What already exists?
                     |
              WHAT IS MISSING?
                     |
              IS IT WORTH DOING?
                     |
             CHEAPEST VALID TEST
                     |
                   RESULT
                     |
            BUILD / ABANDON / PIVOT
                     |
                  VERIFY
                     |
              CREATE EVIDENCE
                     |
              OPEN DOORS
                     |
                 COMPOUND
                     |
             UPDATE USER STATE
```

---

# 29. The Long-Term Vision

The long-term goal is not to create an enormous database of project ideas.

It is to create a **navigation layer between people and the changing technical world**.

As AI makes building cheaper, people increasingly need help deciding:

* what matters;
* what is missing;
* what is worth learning;
* what is worth building;
* what is worth researching;
* what should be ignored;
* when to specialize;
* when to broaden;
* when to optimize for money;
* when to optimize for long-term leverage;
* when to publish;
* when to contribute;
* when to collaborate;
* and when to stop building and understand the problem first.

Project Navigator exists to help make those decisions more rational.

---

# Design Principle

> **Do not optimize for the number of projects a person produces.**
>
> **Optimize for the quality of their decisions, the capabilities they develop, the evidence they create, the problems they help solve, and the opportunities their work unlocks.**

AI should make execution cheaper.

**Project Navigator should make choosing what deserves execution smarter.**
