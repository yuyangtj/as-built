# Design Story

A short record of what this project is and why it looks the way it does. Not a spec — the *reasoning* behind the spec, kept here so future-me and anyone reading the repo can see the shape of the thinking.

## What it is

An opinionated, modern, multi-component data platform that happens to be operated by agents. The platform is the protagonist; agents are the medium through which a viewer encounters its biography. Components — starting with a schema registry, growing toward a semantic layer and beyond — are the substance. The whole thing runs as a continuous campaign on a VPS, with a curated replay viewer on GitHub Pages as the first-impression surface.

This is a portfolio project. Its job is to make my taste in data platform design legible to a hiring manager in 30 seconds, and to my reasoning legible to one who reads further.

## Why campaign mode, not episodic runs

The original instinct was to run discrete experiments with resets between them — clean attribution of "did the agent learn." That's the right shape for a research instrument, not for a portfolio piece showing realistic operation. Real data platforms have one continuous biography. Resets erase the thing worth watching. Campaign mode: one platform, one clock, work arriving as a stream, no resets.

## Why a real consequence engine, not scripted bugs

A simulation is only as honest as its failures. If bugs are described rather than caused, agents role-play handling them and learn nothing. The consequence engine tracks latent conditions the agent's own past actions created, and fires tickets when those conditions become active — symptoms only, never causes. The agent diagnoses blind, exactly as in real work. The world hurts the agent independently of what the agent believes.

## Why two work sources, not one

Endogenous-only would just *harden* the platform — consequences are parasitic on prior construction. Exogenous-only would never produce the platform creating its own future work, which is most of what makes real platforms hard. Both sources are required, and they meet at one object: the ticket. The team can't tell whether a ticket came from outside the platform or from the platform's own past — and shouldn't be able to.

## Why a sealed ticket half

A ticket carries two halves: a visible half the team works against (symptoms, asks) and a sealed half (origin, causal trace, resolution_hook) the team never sees. The seal preserves the asymmetry that makes diagnosis meaningful — solved in the dark, graded in the light. Without it, the agent could cheat by reading the answer key, and the whole project becomes theater.

## Why per-broken-model granularity

For consequence rules with set-valued conditions (over-long columns landing in a Spectrum table; an upstream drift breaking multiple downstream models), the choice was one ticket per offending member or one ticket per affected entity. Per-entity (per Spectrum table, per broken model) keeps the symptom binary at the entity level — it builds or it doesn't — and avoids modeling partial-resolution states. It also produces a binding shape that generalized cleanly across three structurally different rules, which is how we knew the schema was locked.

## Why an upfront briefing for the agent's platform contract

A human engineer has years of tacit competence about a dbt project — what's authoritative vs derived, what's expensive vs cheap, what's safe to touch. An agent has none of that. The upfront briefing is that tacit competence made machine-readable. In v0, the briefing is rich. As the platform adopts components (schema registry, then catalog, then semantic layer), those components become queryable sources of truth, and the briefing shrinks. The briefing's shrinkage *is* the platform's maturity made visible — which becomes a demo moment.

## Why simplified memory

The original lesson schema was eight fields with confidence updates and evidence logs — built to make learning measurable. With the pivot to a component-centered showcase rather than a learning instrument, that complexity stopped earning its cost. Simplified memory is four fields with semantic retrieval and free-form tags. Enough to make the agent's behavior plausible and visible; no more.

## Why one step per tick

The orchestrator gives each active worker one action per tick, not run-to-completion. This naturally spaces reasoning steps along the timeline so the replay viewer can render them as visible thinking rather than collapsed execution. The cost is that complex tickets take many ticks to resolve — which, on a slow-tick live deployment, is exactly the rhythm a real team has.

## Why a replay viewer plus live VPS, not one or the other

A live deployment will be in a broken or quiet state when a hiring manager visits — base rate. A replay viewer can be curated to always show the system at its best. Both serve different roles: the replay is the always-working first impression; the live deployment is operational credibility ("this isn't a toy"). The replay is shielded from the live system's health. The same event log feeds both.

## Why schema registry as the first component

Semantic layer was tempting as the headliner, but a real semantic layer presumes a schema discipline that doesn't yet exist on the bare v0 platform. A schema registry is the foundation — it's what makes upstream drift detectable, contract violations visible, and the semantic layer possible later. Starting here also lets the campaign tell a coherent story: bare platform → painful schema-drift incident → agents reason about adopting a registry → registry becomes the foundation of everything that follows.

## What this project does *not* try to be

Not a research instrument for measuring agent learning. Not a multi-agent coordination playground. Not a benchmark. Not a production framework. It's a platform with a biography, operated by agents whose work is visible enough to be a demo. The discipline of saying no to the adjacent projects is what makes this one shippable.
