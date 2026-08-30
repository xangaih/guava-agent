# **Concierge — Voice-First Agentic Travel Planner**

## **1\. Product Overview**

**Concierge** is a voice-first, multimodal travel planning agent that learns how a user likes to travel and coordinates specialized agents across hotels, restaurants, transportation, and experiences to build a personalized, feasible itinerary in real time.

Unlike traditional travel planners that return disconnected lists of recommendations, Concierge maintains two persistent objects:

1. A **Traveler Profile** representing how the user likes to travel.  
2. A **Trip Plan** representing the current trip, including its itinerary, participants, reservations, constraints, and budget.

As the user speaks, specialist agents call tools to search travel inventory, reason about constraints, and propose or modify plans. Simultaneously, an interactive dashboard populates with hotel and restaurant cards, images, links, transportation options, experiences, maps, costs, and the evolving day-by-day itinerary.

The core product principle is:

> **The user tells Concierge what kind of trip they want. Concierge handles the complexity of making the entire trip fit together.**

---

# **2\. User Experience**

## **Phase 1 — Conversational Travel Profile**

Every new user begins with a short conversational discovery process.

This should feel like speaking with a great human travel advisor, **not completing a questionnaire**. The agent should extract multiple preferences from each response and only ask follow-up questions for important missing information.

Concierge should establish:

### **Party**

* How many people are traveling?  
* Are there children or other relevant party considerations?  
* Will everyone participate in every activity?  
* Should Concierge support splitting the group for some activities and reconvening later?

### **Budget**

* What is the total trip budget?  
* What is excluded from that budget, e.g. international flights?  
* How flexible is the budget?

### **Spending Priorities**

Concierge should explicitly ask:

> “When you travel, what do you actually enjoy spending money on — food, hotels, experiences, shopping, convenience?”

For example:

> “Definitely food. I don't care about fancy hotels. I'll spend on experiences if they're genuinely special.”

becomes:

`food_spend_priority = high`  
`hotel_spend_priority = low`  
`experience_spend_priority = medium/high`

### **Pace & Spacing**

Concierge asks something like:

> “Do you like a relaxed trip with time to wander, or are you a ‘pack everything in and see as much as possible’ traveler?”

It should establish:

* Relaxed vs. packed itinerary  
* Preferred number of scheduled activities per day  
* Desired buffer between activities  
* Amount of unstructured/free time

### **Daily Rhythm**

* How early will the user realistically start?  
* How late do they like staying out?  
* Do they prefer late dinners?  
* Are early-morning activities acceptable?

### **Interests**

Examples:

* Food  
* Architecture  
* Art  
* History  
* Museums  
* Nature  
* Nightlife  
* Shopping  
* Design  
* Neighborhood exploration  
* Adventure  
* Wellness  
* Local/cultural experiences

### **Food Preferences**

* Dietary restrictions  
* Favorite cuisines  
* Adventurousness  
* Fine dining vs. casual/local  
* Interest in bars/nightlife

### **Accommodation Preferences**

* Save vs. splurge  
* Boutique vs. large hotel  
* Luxury vs. functional  
* Neighborhood preferences  
* Amenities that matter

### **Transportation Preferences**

* Cheapest  
* Fastest  
* Most comfortable  
* Scenic  
* Minimal transfers  
* Walkability preference

The resulting **Traveler Profile is persisted in Supabase** and continuously refined through conversation and UI behavior.

---

# **3\. Traveler Profile**

The Traveler Profile persists beyond an individual trip.

Example:

{  
  "travel\_style": {  
    "pace": "relaxed",  
    "preferred\_activity\_buffer\_minutes": 45,  
    "day\_start": "09:00",  
    "day\_end": "23:00",  
    "tourist\_tolerance": "low"  
  },

  "interests": {  
    "food": 0.95,  
    "architecture": 0.85,  
    "design": 0.8,  
    "history": 0.5,  
    "nightlife": 0.3  
  },

  "spending\_preferences": {  
    "food": "splurge",  
    "hotels": "save",  
    "experiences": "moderate",  
    "transport": "efficient"  
  },

  "accommodation": {  
    "preferred\_styles": \["boutique", "local"\],  
    "avoid": \["large\_chain"\]  
  },

  "food": {  
    "adventurousness": 0.9,  
    "dietary\_restrictions": \[\]  
  }  
}

Concierge should also learn from behavior.

If a user repeatedly rejects luxury towers and selects small design hotels, those interactions become preference signals that influence future recommendations.

---

# **4\. Trip Plan & Constraint Engine**

Once sufficient information has been collected, Concierge creates a structured **Trip Plan**.

The Trip Plan contains:

* Destination(s)  
* Dates  
* Travelers  
* Participant availability  
* Total budget  
* Category budget targets  
* Hard constraints  
* Daily schedule  
* Proposed itinerary items  
* Confirmed reservations  
* Remaining budget

## **Hard Budget Constraint**

The total trip budget is enforced programmatically rather than left to LLM judgment.

Before adding an itinerary item:

`committed spend + proposed spend + new item ≤ total trip budget`

Concierge **cannot knowingly construct a plan exceeding the user's hard budget.**

Individual category budgets are soft optimization targets.

For example, for a food-focused traveler with a $4,000 budget:

* Hotels — $1,200  
* Food — $900  
* Transportation — $600  
* Experiences — $700  
* Flexible buffer — $600

If the user wants a $400 omakase, Concierge may reduce hotel spending or draw from the flexible budget rather than exceeding $4,000.

The agent should explain relevant tradeoffs conversationally:

> “That ryokan would put us $140 over budget. Since you've told me food matters much more to you than hotels, I'd keep the omakase and choose the $290 ryokan instead.”

## **Schedule Constraints**

Every itinerary item contains:

* Start time  
* End time  
* Location  
* Participants  
* Cost  
* Travel time  
* Required buffer  
* Reservation status  
* Dependencies

The itinerary validator checks:

* Schedule conflicts  
* Geographic feasibility  
* Required travel time  
* User's preferred spacing between activities  
* Daily start/end preferences  
* Participant conflicts  
* Budget  
* Reservation availability

A relaxed traveler might receive 45–60 minutes between major activities, while a “see everything” traveler may tolerate 15-minute transitions.

The system should also support **split-party itineraries**. Two travelers could visit a museum while two others shop, with everyone reconvening for dinner.

---

# **5\. Multi-Agent Architecture**

A central **Travel Orchestrator** owns the overall Trip Plan.

Its responsibilities are to:

1. Understand user intent.  
2. Read the Traveler Profile.  
3. Read current Trip Plan state.  
4. Determine which specialist agent(s) are needed.  
5. Sequence dependent actions.  
6. Detect downstream consequences.  
7. Request user confirmation when necessary.  
8. Validate the resulting itinerary.  
9. Update the live UI.

The Orchestrator routes work to specialist agents.

### **Hotel Agent**

Searches accommodations based on price, neighborhood, style, availability, amenities, and user preferences.

Example tools:

`search_hotels()`  
`get_hotel_details()`  
`check_room_availability()`  
`hold_room()`  
`book_hotel()`  
`modify_hotel()`  
`cancel_hotel()`

### **Dining Agent**

Searches restaurants based on cuisine, location, budget, availability, dietary requirements, and Traveler Profile.

`search_restaurants()`  
`get_restaurant_details()`  
`check_reservation()`  
`reserve_table()`  
`modify_reservation()`  
`cancel_reservation()`

### **Transit Agent**

Handles trains, flights, and other intercity transportation.

`search_trains()`  
`search_flights()`  
`get_route()`  
`check_schedule()`  
`hold_ticket()`  
`book_ticket()`  
`change_ticket()`

### **Experience Agent**

Finds tours, museums, attractions, activities, and other experiences.

`search_experiences()`  
`get_experience_details()`  
`check_availability()`  
`book_experience()`  
`cancel_experience()`

### **Local / Logistics Agent**

Handles geographic and contextual reasoning.

`calculate_travel_time()`  
`find_nearby()`  
`get_neighborhood()`  
`get_weather()`  
`check_geographic_feasibility()`

Agents should interact with the system through **structured tool calls** rather than directly modifying shared state.

---

# **6\. Live Multimodal Trip Dashboard**

The defining UI is a **live trip canvas that builds itself during the conversation**.

The screen contains two primary surfaces:

### **Conversation**

The user speaks naturally with Concierge through Guava.

### **Live Trip Board**

As agents work, the dashboard progressively renders:

* Day-by-day itinerary  
* Hotel cards  
* Hotel images  
* Restaurant cards  
* Food imagery  
* Train/flight options  
* Tours and experiences  
* Maps  
* External links  
* Reservation confirmations  
* Trip costs  
* Budget utilization  
* Remaining budget  
* Schedule conflicts

For example:

**SATURDAY — KYOTO**

9:30 AM — Breakfast  
11:00 AM — Kiyomizu-dera  
1:30 PM — Lunch  
3:30 PM — Architecture Tour  
5:30–7:30 PM — Wander / Free Time  
8:00 PM — Omakase

**Budget: $2,840 / $4,000 · $1,160 remaining**

When Concierge says:

> “I've found three boutique hotels I think you'd like…”

the Hotel Agent calls a UI tool and three rich hotel cards immediately appear with:

* Image  
* Name  
* Neighborhood  
* Price  
* Relevant tags  
* External link  
* Selection action

The user can interact with these cards while continuing the voice conversation.

UI interactions also become **preference signals** that update the Traveler Profile.

---

# **7\. Tool Architecture**

Tools fall into several categories.

### **Discovery**

`update_traveler_profile()`  
`record_preference_signal()`  
`create_trip()`

### **Search**

`search_hotels()`  
`search_restaurants()`  
`search_transit()`  
`search_experiences()`

### **Planning**

`add_itinerary_item()`  
`modify_itinerary_item()`  
`remove_itinerary_item()`  
`calculate_travel_time()`

### **Validation**

`check_budget()`  
`validate_schedule()`  
`validate_participants()`  
`validate_itinerary()`

### **Execution**

`reserve()`  
`modify_reservation()`  
`cancel_reservation()`

### **Multimodal / UI**

`show_hotel_options()`  
`show_restaurant_options()`  
`show_transit_options()`  
`show_experience_options()`  
`render_itinerary()`  
`render_budget()`  
`render_map()`  
`highlight_item()`  
`show_conflict()`  
`show_confirmation()`

Search, reasoning, and rendering tools can execute autonomously.

Consequential actions such as booking, cancellation, payment, or reservation modification require explicit user confirmation.

---

# **8\. Dynamic Replanning**

The system must understand that travel reservations are **interdependent**.

Example:

The existing itinerary contains:

**5:00 PM — Arrive Kyoto**  
**7:30 PM — Dinner reservation**

The user says:

> “Actually, my meeting moved. We can't leave Tokyo until after five.”

The system:

1. Identifies the Tokyo → Kyoto train as affected.  
2. Routes the request to the Transit Agent.  
3. Finds a 5:48 PM train arriving at 8:01 PM.  
4. Updates the proposed Trip Plan.  
5. Runs `validate_itinerary()`.  
6. Detects that the 7:30 dinner is now impossible.  
7. Routes the downstream conflict to the Dining Agent.  
8. Searches for similar restaurants near the hotel with availability after 8:30.  
9. Displays replacement restaurant cards.  
10. Asks:

> “I can move you to the 5:48 train, but that breaks our dinner reservation. I found a similar restaurant seven minutes from your hotel with an 8:45 table. Want me to switch both?”

After confirmation:

`change_ticket()`  
→ `modify_restaurant_reservation()`  
→ `validate_itinerary()`  
→ `render_itinerary()`

The dashboard updates immediately.

This **change → detect dependencies → replan → validate → render** loop is the primary demonstration of agentic behavior.

---

# **9\. Supabase Data Model**

Core tables:

`users`  
`traveler_profiles`  
`preference_signals`

`trips`  
`trip_participants`  
`trip_budgets`  
`trip_destinations`

`itinerary_items`

`hotels`  
`hotel_availability`

`restaurants`  
`restaurant_availability`

`trains`  
`train_availability`

`experiences`  
`experience_availability`

`reservations`

`agent_runs`  
`tool_calls`

Travel listings should contain structured multimodal fields including:

`name`  
`description`  
`image_url`  
`external_url`  
`latitude`  
`longitude`  
`price`  
`tags[]`

`agent_runs` and `tool_calls` provide a trace of agent behavior that can optionally be surfaced during the hackathon demo.

---

# **10\. Call Conclusion — “Your Trip as an Anime”**

Once planning is complete, Concierge should end with a memorable celebratory moment rather than simply terminating the conversation.

The Orchestrator runs:

`validate_itinerary()`

The trip must satisfy:

**✓ Budget constraint**  
**✓ Schedule feasibility**  
**✓ Geographic feasibility**  
**✓ Participant constraints**  
**✓ No unresolved conflicts**

The dashboard then transitions from **Planning Mode** into a polished **Final Trip View**.

Concierge gives a short personalized recap:

> “We're done — eight days, two cities, comfortably under budget, lots of incredible food, and plenty of time to wander.”

Then:

> “And I made you one last thing…”

Concierge calls:

`generate_trip_comic(trip_id)`

The image-generation tool receives structured context from the completed trip:

* Travelers  
* Destinations  
* Major activities  
* Restaurants/food  
* Neighborhoods  
* Transportation  
* Landmarks  
* Travel style  
* Overall trip vibe

It generates a playful **anime-inspired comic/poster depicting the trip that was just planned**.

For example, the Japan trip might show several illustrated panels:

**Panel 1:** Travelers riding the Shinkansen toward Kyoto  
**Panel 2:** Wandering through atmospheric Kyoto streets  
**Panel 3:** Eating omakase at the special dinner  
**Panel 4:** Visiting temples and architecture  
**Panel 5:** Drinks at a tiny neighborhood bar

The generated comic appears directly inside the final trip dashboard under:

### **🎉 Your Trip as an Anime**

The final screen contains:

* Complete itinerary  
* Reservation summary  
* Route/map  
* Final budget  
* **Generated trip comic**  
* Save/share trip actions

Final tool sequence:

`validate_itinerary()`  
→ `render_final_itinerary()`  
→ `generate_trip_comic()`  
→ `render_trip_comic()`  
→ `save_trip()`

The comic is a **delight feature**, not part of the core planning logic. It provides an emotional conclusion, demonstrates multimodal tool use, and creates a personalized, shareable artifact.

---

# **11\. MVP Success Criteria**

A successful hackathon demo demonstrates that Concierge can:

1. Learn a nuanced Traveler Profile through natural voice conversation.  
2. Understand what the user likes spending money on.  
3. Understand pace, spacing, daily rhythm, and party composition.  
4. Translate those preferences into actual planning decisions.  
5. Coordinate multiple specialist agents.  
6. Make meaningful sequential tool calls.  
7. Maintain a hard total-trip budget.  
8. Respect time, geography, spacing, and participant constraints.  
9. Populate a rich multimodal itinerary UI live while the user speaks.  
10. React when one change breaks another part of the trip.  
11. Autonomously find feasible alternatives.  
12. Execute approved changes and update the dashboard.  
13. Conclude by generating a personalized anime-style trip comic.

## **North Star**

**The user should feel like they are talking to a great human travel concierge who learns how they like to travel, understands the entire trip at once, handles the logistical complexity for them, and leaves them with something they're genuinely excited to experience.**

## **Constraint Conflicts, Tradeoffs & User Overrides**

Concierge should treat constraints as a mechanism for **helping users make tradeoffs**, not automatically rejecting requests that conflict with their existing preferences.

When a requested action conflicts with the Traveler Profile or Trip Plan, the system should identify the conflict, explain it conversationally, and—where safe and feasible—allow the user to explicitly override the preference.

### **Constraint Hierarchy**

Every constraint should be classified as one of three types:

**1\. Hard Constraints**

Cannot be violated unless the user explicitly changes the constraint itself.

Examples:

* Total trip budget  
* Traveler availability  
* Reservation availability  
* Physical impossibility, such as overlapping activities  
* Explicit accessibility requirements

Example:

> “That would bring the trip to $4,280, above the $4,000 budget you gave me. If this restaurant is worth splurging on, I can either find $280 of savings elsewhere or raise the trip budget. Which would you prefer?”

The system should **not simply reject the restaurant**.

Instead, it should help the user understand what would need to change.

---

**2\. Soft Preferences**

These represent how the user generally prefers to travel but can be overridden for individual activities.

Examples:

* 60 minutes between activities  
* Starting after 9 AM  
* Avoiding tourist-heavy attractions  
* Preferring boutique hotels  
* Avoiding long transit times  
* Maintaining a relaxed pace  
* Category spending targets

Example:

User:

> “Add the 8 AM fish market tour.”

Concierge knows the Traveler Profile says:

`preferred_day_start = 09:30`

Rather than rejecting it:

> “You normally prefer not to start before 9:30, and this one means leaving the hotel around 7:15. It does look like a great fit for how food-focused this trip is, though. Want to make an exception for this day?”

If yes, the exception applies only to that activity/day unless the user indicates their general preference has changed.

---

**3\. Optimization Preferences**

These guide ranking but generally do not require explicit approval to violate.

Examples:

* Prefer walking over taxis  
* Prefer direct trains  
* Prefer local restaurants  
* Prefer particular neighborhoods  
* Prefer cheaper transportation

The agent should optimize for these when possible but may choose a slightly less-preferred option when it creates a substantially better overall itinerary.

---

## **Conflict Resolution Flow**

When the user requests something contradictory, Concierge should follow:

`REQUEST`

→ `CHECK CONSTRAINTS`

→ **No conflict:** proceed normally

→ **Conflict detected:** classify conflict

→ Explain the conflict and consequence

→ Generate feasible tradeoffs

→ Ask user which preference/constraint they want to relax

→ Record explicit override

→ Replan affected itinerary

→ Validate entire Trip Plan

→ Render updated itinerary

The goal is to behave like an excellent human travel advisor:

> **“We can absolutely do that. Here's what we'd have to give up.”**

rather than:

> **“That violates your preferences.”**

---

## **Tradeoff Generation**

Where possible, Concierge should proactively generate options rather than asking an open-ended question.

For example:

> “That ryokan would put us $320 over budget. We have three ways to make it work:

> **Keep the ryokan** and switch to the simpler Tokyo hotel I showed you, saving $350.

> **Keep both hotels** and replace the $240 food tour with the self-guided market morning.

> **Increase the trip budget** from $4,000 to $4,320.

> Since you told me hotels aren't where you like spending money, I'd recommend the first option.”

The UI should simultaneously display the alternatives and their effects on the trip.

---

## **Explicit Overrides**

Overrides should be stored separately from the underlying Traveler Profile.

Example:

{  
  "constraint": "preferred\_day\_start",  
  "profile\_value": "09:30",  
  "override\_value": "07:15",  
  "scope": "2026-10-14",  
  "reason": "Tsukiji food tour",  
  "user\_confirmed": true  
}

This prevents one exception from accidentally rewriting the user's entire profile.

If the user repeatedly makes the same override, Concierge can ask:

> “You've chosen early starts three times on this trip. Should I update your travel style to say you're okay with early mornings when the activity is worth it?”

---

## **Contradictory User Preferences**

Users may also express preferences that are inherently difficult to satisfy simultaneously.

For example:

> “I want to see as much as possible, but I hate feeling rushed.”

Concierge should recognize the tension rather than arbitrarily selecting one interpretation.

It can respond:

> “Those can pull in opposite directions a little. I can optimize for seeing a lot while keeping the important parts relaxed—for example, two anchor activities each day with smaller things nearby that we can treat as optional. Does that sound right?”

The resulting Trip Plan might distinguish:

**Anchor activities** — important, scheduled  
**Optional activities** — suggested if time/energy permits  
**Free time** — intentionally protected

Another example:

> “I want incredible restaurants but don't want to spend much on food.”

Concierge might ask:

> “Would you rather have one or two expensive standout meals and eat cheaply the rest of the trip, or keep every meal moderately priced?”

The system turns contradictory preferences into **explicit planning strategies**.

---

## **Confirmation Threshold**

Concierge should not ask for confirmation constantly.

Confirmation is required when:

* A hard constraint must change  
* A consequential reservation will be booked/cancelled/modified  
* A meaningful existing plan must be sacrificed  
* A significant soft preference will be violated  
* Multiple viable tradeoffs exist and choosing one materially changes the trip

Minor optimization decisions can happen autonomously.

The intended behavior is:

**Notice contradictions → understand the tradeoff → offer intelligent alternatives → let the user decide → remember the decision → replan.**

Concierge should optimize for the user's **actual intent**, not blindly enforce preferences collected earlier in the conversation.

**MASTER PROMPT — Concierge (Voice-First Travel Planner)**

Paste everything below the line into Claude Code. This translates the team's full product spec into what's actually buildable tonight, using Guava for voice and Supabase for data \+ live dashboard updates. **The full spec is preserved at the bottom as a roadmap — nothing is deleted, just deferred.**

---

## **SCOPE REALITY CHECK — read this before writing any code**

The original spec describes a production travel platform: five specialist agents, \~40 tools, real hotel/flight/restaurant search integrations, a general-purpose itinerary replanner that detects arbitrary downstream conflicts, split-party scheduling, a 15+ table normalized schema with availability/reservation/agent-trace tables, and a live multimodal dashboard rendering many card types. That is weeks of work, not a hackathon build window.

Tonight's build cuts, in priority order (highest-risk-to-attempt first):

1. **No real search APIs.** Hotels/restaurants/experiences are seeded mock data in Supabase, not live calls to Amadeus/Google Places/etc. Auth, rate limits, and unfamiliar API shapes are exactly the kind of thing that eats an hour and leaves you with nothing. Mock data that looks real is indistinguishable to a judge watching a 2-minute demo.  
2. **One agent, not five.** Implement a single `guava.Agent` with well-organized internal Python functions that mirror the "specialist agent" concept (a `hotels.py`, `restaurants.py`, `experiences.py` module each with search/propose functions). This produces the same observable behavior — the caller sees hotel proposals, restaurant proposals, etc. — without building an actual multi-agent orchestration framework from scratch under time pressure.  
3. **One rehearsed replanning moment, not a general solver.** Build the exact Tokyo→Kyoto train/dinner conflict scenario from the spec as real, working code (it calls real functions, checks real budget/schedule state) but don't try to build a generic dependency-graph engine that detects arbitrary conflicts. Scope the demo conversation to walk into this scenario naturally.  
4. **Trimmed schema.** 9 tables instead of 15+. No `agent_runs`/`tool_calls` tracing tables, no per-item availability tables, no participant-level tables. See schema below — it still supports everything the demo needs.  
5. **No split-party itineraries.** Single unified itinerary for the whole party. Cut entirely for tonight.  
6. **Qualitative preferences, not numeric weights.** The spec's `interests: {food: 0.95, architecture: 0.85, ...}` model is not something you can reliably extract and verify live in a 2-minute demo. Capture a short list of stated interests and spend priorities as plain text/tags, not confidence-scored weights. This is a real product feature for later, not a hackathon deliverable.  
7. **No generic contradiction detection.** The spec's example — "I want to see as much as possible but I hate feeling rushed" — describes the agent recognizing tension between arbitrary stated preferences. That's a real reasoning capability, not something you code a detector for. Tonight, rely on Guava's own LLM reasoning (guided by the profile context and objective text you give it) to handle this conversationally when it comes up naturally; don't build explicit tension-detection logic. Same treatment for "you've chosen early starts three times, should I update your profile" — that requires counting overrides across a call and a secondary confirmation flow. Real feature, not tonight's.

**Kept, deliberately, because they're cheap and high-payoff:**

* The hard total-budget constraint (`committed + proposed ≤ total_budget`) — this is a simple arithmetic check, genuinely differentiates the demo from "just a chatbot," and is exactly the kind of thing judges remember.  
* **Tradeoff generation on a hard-constraint conflict** (see "Constraint Hierarchy & Tradeoffs" below) — when a request would break the budget, generate 2-3 concrete alternatives instead of flatly rejecting. This is mechanical code (compare costs, suggest a cheaper same-category swap, suggest removing an optional item, suggest raising the budget by the overage) sitting right next to the budget check you're already building, and it's arguably the single clearest demonstration of the spec's stated goal — "here's what we'd have to give up" instead of "that violates your preferences" — so it's worth the modest extra scope.  
* One soft-constraint example, built for real: checking a new activity's start time against the traveler's stated `day_start` preference and offering a one-time, scoped exception instead of silently allowing or blocking it. One concrete example, not a generic soft-preference engine.  
* The anime trip comic finale — one API call to an image-gen model at the end of the call. Cheap, visually strong, and the spec itself correctly frames it as "delight, not core logic," so it's low-risk to keep.  
* The live dashboard, via Supabase Realtime (see below) — this is less work than it sounds because Supabase gives you live-updating UI for free off table changes, no custom WebSocket/polling backend needed.

**A note on demo time**: these additions mean the build now has three possible "conflict" moments — the budget tradeoff, the soft day-start exception, and the transit replanning scenario — but the judge demo is still only 2 minutes. Pick **one** as the rehearsed centerpiece (the budget tradeoff is the strongest choice — see Demo Script below) and treat the other two as real, working features you can show if judges ask a follow-up during Q\&A, not things you try to cram into the timed demo.

**One real risk to flag explicitly**: the dashboard depends on internet connectivity at the venue (Supabase is a hosted service, unlike Guava's local-Expert model which needs no public server). Test venue wifi/cellular early. Have a phone hotspot as backup. This is a new failure mode you didn't have with the previous ClaimLine build.

---

## **SUPABASE SCHEMA — teammates can start here immediately, in parallel**

Run this in the Supabase SQL editor now. Don't wait on the rest of this document — data seeding and voice-agent build happen in parallel.

```sql
-- Travelers & profile (one row per demo user; keep it simple, no auth needed tonight)
create table travelers (
  id uuid primary key default gen_random_uuid(),
  name text,
  phone text,
  created_at timestamptz default now()
);

create table traveler_profiles (
  traveler_id uuid primary key references travelers(id),
  pace text,                          -- 'relaxed' | 'balanced' | 'packed'
  day_start text,                     -- e.g. '09:00'
  day_end text,                       -- e.g. '23:00'
  interests text[],                   -- plain tags, e.g. {'food','architecture'}
  spend_priorities text,              -- free text, e.g. "food and experiences over hotels"
  dietary_restrictions text[],
  notes text,                         -- anything else worth remembering, free text
  updated_at timestamptz default now()
);

-- Trip shell
create table trips (
  id uuid primary key default gen_random_uuid(),
  traveler_id uuid references travelers(id),
  destination text,                   -- keep to ONE destination string tonight, e.g. "Kyoto, Japan"
  start_date date,
  end_date date,
  total_budget numeric,
  status text default 'planning',     -- 'planning' | 'finalized'
  created_at timestamptz default now()
);

-- Soft category budget targets (auto-generated on trip creation, adjustable)
create table category_budgets (
  id uuid primary key default gen_random_uuid(),
  trip_id uuid references trips(id),
  category text,                      -- 'hotels' | 'food' | 'transport' | 'experiences' | 'buffer'
  target_amount numeric
);

-- Mock inventory — SEED THESE with realistic-looking data, this is the main teammate task
create table hotels (
  id uuid primary key default gen_random_uuid(),
  name text, neighborhood text, city text,
  price numeric, image_url text, external_url text,
  tags text[], lat numeric, lng numeric
);

create table restaurants (
  id uuid primary key default gen_random_uuid(),
  name text, neighborhood text, city text, cuisine text,
  price_tier text,                    -- '$' | '$$' | '$$$' | '$$$$'
  image_url text, external_url text,
  tags text[], lat numeric, lng numeric
);

create table experiences (
  id uuid primary key default gen_random_uuid(),
  name text, city text, category text,
  price numeric, duration_minutes int,
  image_url text, external_url text, tags text[]
);

-- The itinerary itself — this is what the dashboard renders live
create table itinerary_items (
  id uuid primary key default gen_random_uuid(),
  trip_id uuid references trips(id),
  day_date date,
  start_time text, end_time text,     -- store as 'HH:MM' text, skip timezone complexity tonight
  item_type text,                     -- 'hotel' | 'restaurant' | 'experience' | 'transit' | 'free_time'
  ref_id uuid,                        -- points into hotels/restaurants/experiences depending on item_type
  title text, location text,
  cost numeric,
  priority text default 'anchor',     -- 'anchor' | 'optional' — see Constraint Hierarchy section
  status text default 'proposed',     -- 'proposed' | 'confirmed' | 'removed'
  notes text,
  created_at timestamptz default now()
);

-- Explicit constraint overrides — kept separate from traveler_profiles so one
-- exception never silently rewrites the user's general preferences
create table constraint_overrides (
  id uuid primary key default gen_random_uuid(),
  trip_id uuid references trips(id),
  constraint_name text,               -- e.g. 'day_start', 'total_budget'
  profile_value text,                 -- the value on file before the override
  override_value text,                -- the value the caller agreed to for this scope
  scope text,                         -- a date, an itinerary_item id, or 'trip' for the whole trip
  reason text,                        -- short free text, e.g. "Tsukiji food tour"
  user_confirmed boolean default true,
  created_at timestamptz default now()
);

-- Finale artifact
create table trip_comics (
  id uuid primary key default gen_random_uuid(),
  trip_id uuid references trips(id),
  image_url text,
  created_at timestamptz default now()
);

-- Tonight only: disable RLS for speed. NOT production-safe — re-enable before this
-- touches any real user data. This is a deliberate, explicit shortcut for a 2-hour build.
alter table travelers disable row level security;
alter table traveler_profiles disable row level security;
alter table trips disable row level security;
alter table category_budgets disable row level security;
alter table hotels disable row level security;
alter table restaurants disable row level security;
alter table experiences disable row level security;
alter table itinerary_items disable row level security;
alter table constraint_overrides disable row level security;
alter table trip_comics disable row level security;

-- Enable Realtime so the dashboard updates live without any custom backend
alter publication supabase_realtime add table itinerary_items;
alter publication supabase_realtime add table trips;
alter publication supabase_realtime add table trip_comics;
```

### **Seed data — ready to run, not just examples**

Destination locked to **Kyoto, Japan** for tonight (per above — one destination keeps the data coherent and gives the finale comic a clean scene to work from).

Photos are not a priority right now — every row below uses `picsum.photos/seed/<name>/600/400`, which deterministically generates a real (if generic) photo from the seed string with zero API key and zero curation time. It renders fine on the dashboard today. Swap in real travel photography later if there's time, but don't spend tonight's build time on it.

This is a complete, working seed set — run it as-is and you have enough data for the whole demo (intake, proposals, budget tradeoffs, the day\_start exception, and the transit replanning scenario) without needing to author more rows first:

```sql
insert into hotels (name, neighborhood, city, price, image_url, external_url, tags) values
('Nishiki Machiya Inn', 'Nakagyo', 'Kyoto', 145, 'https://picsum.photos/seed/nishiki-machiya/600/400', '#', array['boutique','local','traditional']),
('Gion Ryokan Sora', 'Higashiyama', 'Kyoto', 290, 'https://picsum.photos/seed/gion-ryokan-sora/600/400', '#', array['boutique','traditional','romantic']),
('Kyoto Grand Tower', 'Shimogyo', 'Kyoto', 310, 'https://picsum.photos/seed/kyoto-grand-tower/600/400', '#', array['large_chain','central']),
('Arashiyama Riverside Hotel', 'Arashiyama', 'Kyoto', 210, 'https://picsum.photos/seed/arashiyama-riverside/600/400', '#', array['central','scenic']),
('Kyoto Central Business Hotel', 'Shimogyo', 'Kyoto', 95, 'https://picsum.photos/seed/kyoto-central-business/600/400', '#', array['large_chain','budget']),
('Machiya Stay Kamigyo', 'Kamigyo', 'Kyoto', 160, 'https://picsum.photos/seed/machiya-kamigyo/600/400', '#', array['boutique','local']),
('The Kamogawa Ritz', 'Kamogawa', 'Kyoto', 650, 'https://picsum.photos/seed/kamogawa-ritz/600/400', '#', array['luxury','central']),
('Guesthouse Sakura', 'Fushimi', 'Kyoto', 60, 'https://picsum.photos/seed/guesthouse-sakura/600/400', '#', array['budget','hostel']);

insert into restaurants (name, neighborhood, city, cuisine, price_tier, image_url, external_url, tags) values
('Sushi Kanesaka Annex', 'Gion', 'Kyoto', 'omakase', '$$$$', 'https://picsum.photos/seed/sushi-kanesaka/600/400', '#', array['splurge','special_occasion']),
('Kikunoi', 'Higashiyama', 'Kyoto', 'kaiseki', '$$$$', 'https://picsum.photos/seed/kikunoi/600/400', '#', array['splurge','traditional']),
('Ramen Kokoro', 'Kawaramachi', 'Kyoto', 'ramen', '$', 'https://picsum.photos/seed/ramen-kokoro/600/400', '#', array['casual','local']),
('Nishiki Market Food Stalls', 'Nakagyo', 'Kyoto', 'street food', '$', 'https://picsum.photos/seed/nishiki-stalls/600/400', '#', array['casual','local']),
('Yudofu Sagano', 'Arashiyama', 'Kyoto', 'tofu kaiseki', '$$$', 'https://picsum.photos/seed/yudofu-sagano/600/400', '#', array['traditional','vegetarian_friendly']),
('Pontocho Grill House', 'Pontocho', 'Kyoto', 'yakitori', '$$', 'https://picsum.photos/seed/pontocho-grill/600/400', '#', array['local','nightlife']),
('Kyoto Curry Standing', 'Shimogyo', 'Kyoto', 'curry', '$', 'https://picsum.photos/seed/kyoto-curry/600/400', '#', array['casual','quick']),
('Gion Kappa Sushi Bar', 'Gion', 'Kyoto', 'sushi', '$$', 'https://picsum.photos/seed/gion-kappa/600/400', '#', array['casual']),
('Omen Udon', 'Ginkakuji', 'Kyoto', 'udon', '$$', 'https://picsum.photos/seed/omen-udon/600/400', '#', array['local']),
('Teppanyaki Wa', 'Kamogawa', 'Kyoto', 'teppanyaki', '$$$', 'https://picsum.photos/seed/teppanyaki-wa/600/400', '#', array['splurge']);

insert into experiences (name, city, category, price, duration_minutes, image_url, external_url, tags) values
('Kiyomizu-dera Architecture Walk', 'Kyoto', 'architecture', 45, 90, 'https://picsum.photos/seed/kiyomizu-dera/600/400', '#', array['temple','architecture','walkable']),
('Fushimi Inari Torii Hike', 'Kyoto', 'nature', 0, 120, 'https://picsum.photos/seed/fushimi-inari/600/400', '#', array['nature','adventure','free']),
('Arashiyama Bamboo Grove & Tenryu-ji', 'Kyoto', 'nature', 20, 90, 'https://picsum.photos/seed/arashiyama-bamboo/600/400', '#', array['nature','architecture']),
('Traditional Tea Ceremony', 'Kyoto', 'cultural', 60, 60, 'https://picsum.photos/seed/tea-ceremony/600/400', '#', array['cultural','local']),
('Nishiki Market Food Tour', 'Kyoto', 'food', 85, 120, 'https://picsum.photos/seed/nishiki-food-tour/600/400', '#', array['food','local']),
('Gion Evening District Walk', 'Kyoto', 'cultural', 35, 90, 'https://picsum.photos/seed/gion-evening-walk/600/400', '#', array['cultural','nightlife']),
('Kimono Rental & Photo Walk', 'Kyoto', 'cultural', 70, 180, 'https://picsum.photos/seed/kimono-photo-walk/600/400', '#', array['cultural','design']);
```

This gives you: a clear budget/hotel price spread ($60–$650, so tradeoff generation has real cheaper-swap options to suggest), an obvious omakase splurge item for the budget-tradeoff demo moment, and enough experiences to seed a train/dinner conflict for the transit replanning scenario. If there's spare time later, add more rows or swap in curated photos — but this set alone is enough to run the full demo script end to end tonight.

---

## **VOICE AGENT ARCHITECTURE**

### **File structure**

```
concierge/
├── .env                          # GUAVA_API_KEY, GUAVA_AGENT_NUMBER, SUPABASE_URL, SUPABASE_KEY, IMAGE_GEN_API_KEY
├── app/
│   ├── agent.py                  # guava.Agent(...) instantiation
│   ├── main.py                   # entrypoint, --chat/--local/--webrtc/--phone
│   ├── db.py                     # supabase client + typed helper functions (one per table op)
│   ├── callbacks/
│   │   ├── lifecycle.py          # on_call_start, on_session_end
│   │   ├── profile_intake.py     # set_task: traveler profile + trip shell
│   │   ├── planning_actions.py   # on_action_request/on_action: propose_hotels, propose_restaurants,
│   │   │                         #   propose_experiences, add_to_itinerary, remove_from_itinerary,
│   │   │                         #   check_budget_status, replan_conflict, finalize_trip
│   │   └── questions.py          # on_question: budget status, "what's planned so far", etc.
│   ├── specialists/               # NOT separate agents — plain modules mirroring the spec's "agents"
│   │   ├── hotels.py             # search_hotels(), propose_hotels()
│   │   ├── restaurants.py        # search_restaurants(), propose_restaurants()
│   │   ├── experiences.py        # search_experiences(), propose_experiences()
│   │   └── budget.py             # check_budget(), category_budget_split()
│   └── comic.py                   # generate_trip_comic()
└── dashboard/
    └── index.html                 # single page, Supabase JS client + realtime subscription
```

### **Callback mapping**

**`on_call_start`** → set the initial task, collecting a condensed traveler profile \+ trip shell in one pass:

```py
call.set_task(
    "trip_intake",
    objective="Learn how this traveler likes to travel and get the shape of this trip.",
    checklist=[
        guava.Field(key="destination", field_type="text", description="Where they want to go"),
        guava.Field(key="trip_length_days", field_type="integer", description="How many days"),
        guava.Field(key="party_size", field_type="integer", description="How many people traveling"),
        guava.Field(key="total_budget", field_type="integer", description="Total trip budget in dollars"),
        guava.Field(key="pace", field_type="multiple_choice", choices=["relaxed", "balanced", "packed"],
                    description="Relaxed wandering vs. see-everything pace"),
        guava.Field(key="top_interests", field_type="text",
                    description="What they most enjoy on trips — food, architecture, nightlife, etc."),
        guava.Field(key="spend_priorities", field_type="text",
                    description="What they actually like spending money on vs. don't care about"),
    ],
)
```

**`on_task_complete("trip_intake")`** →

1. Insert `travelers`/`traveler_profiles`/`trips` rows.  
2. Call `budget.category_budget_split(total_budget)` — a fixed, simple percentage split (e.g. hotels 30%, food 25%, transport 15%, experiences 20%, buffer 10%; nudge the split slightly if `spend_priorities` text mentions "food" or "hotels" explicitly — keep this a simple keyword check, not an LLM call, for reliability) and insert `category_budgets` rows.  
3. Call `hotels.propose_hotels()` / `restaurants.propose_restaurants()` / `experiences.propose_experiences()` against the seeded mock data, filtered by destination and budget tier, and insert 2-3 of each as `itinerary_items` with `status='proposed'` — this is what makes cards appear on the dashboard right after intake finishes.  
4. `call.send_instruction(...)` summarizing what was proposed, so the agent describes it naturally ("I've pulled together a few hotel and restaurant options I think you'd like — take a look and tell me what stands out").

**`on_action_request` / `on_action`** — reuse the `IntentRecognizer` pattern from the ClaimLine build:

```py
ACTIONS = {
    "add_to_itinerary": "caller wants to confirm/add a proposed option to the trip",
    "remove_from_itinerary": "caller wants to remove or swap something already planned",
    "budget_status": "caller is asking how much they've spent or have left",
    "replan_conflict": "caller is telling us something changed that affects existing plans (e.g. a time changed)",
    "finalize_trip": "caller is done planning and wants to wrap up",
}
```

Each `on_action(key)` handler calls the matching function in `specialists/` or `budget.py`, checks the hard budget constraint via `budget.check_budget()` before any insert, updates Supabase, and uses `call.send_instruction()` to narrate the result back naturally (per the spec's own example: *"That ryokan would put us $140 over budget... I'd keep the omakase and choose the $290 ryokan instead."*).

### **Constraint hierarchy & tradeoffs (hard / soft / optimization)**

The spec's core philosophy is: notice a conflict → explain it → offer concrete alternatives → let the caller decide → remember the decision → replan. Don't reject requests outright. Tonight's build implements this for exactly two constraint types, done properly, rather than a general three-tier engine attempted for everything:

**Hard constraint (built): total budget.** Extend the `add_to_itinerary` handler:

```py
def add_to_itinerary(trip_id, item):
    ok, remaining = budget.check_budget(trip_id, item["cost"])
    if ok:
        db.insert_itinerary_item(trip_id, item, status="proposed")
        return {"added": True}

    over_amount = item["cost"] - remaining
    tradeoffs = budget.generate_tradeoffs(trip_id, item, over_amount)
    # tradeoffs is a list of up to 3 concrete options, e.g.:
    # [{"type": "swap", "description": "switch to the $290 ryokan", "saves": 140},
    #  {"type": "remove", "description": "drop the food tour", "saves": 240},
    #  {"type": "raise_budget", "description": "raise total budget by $140"}]
    call.send_instruction(
        f"Explain that this would put the trip ${over_amount} over budget, "
        f"then offer these specific options naturally, recommending the one "
        f"that best fits their stated spend priorities: {tradeoffs}"
    )
    return {"added": False, "tradeoffs": tradeoffs}
```

`budget.generate_tradeoffs()` is mechanical, not an LLM call: same-category cheaper swap (query the relevant mock table for a lower-price item with overlapping tags), removal of the most recent `priority='optional'` item, and a raise-budget option showing the new total. When the caller picks one (their next utterance), the following turn's `on_action` applies it and inserts a `constraint_overrides` row if the budget itself was raised.

**Soft constraint (built): `day_start`.** When proposing or adding an `experience`/`restaurant` item, compare its `start_time` against `traveler_profiles.day_start`. If earlier:

```py
call.send_instruction(
    f"Mention they normally don't start before {profile['day_start']}, "
    f"this would mean leaving around {item['start_time']}, but note why it "
    f"might be worth it given their stated interests. Ask if they want to "
    f"make an exception just for this day."
)
```

On confirmation, insert into `itinerary_items` normally and write a `constraint_overrides` row (`constraint_name='day_start'`, `scope=<that day's date>`) — this is what "the exception applies only to that day, not their general profile" actually means in the data.

**Optimization preferences (not explicitly checked): everything else.** Boutique-vs-chain, walking-vs-taxi, neighborhood preference, etc. Don't write a check for each of these. Instead, when `specialists/hotels.py` / `restaurants.py` query mock inventory, sort results by how many of the item's `tags` overlap with the traveler's stated `interests` and `accommodation` notes before picking which 2-3 to propose. That's the entire "optimization tier" implementation tonight — a sort key, not a constraint check.

**Confirmation threshold.** Guava's `on_action_request`/`on_action` flow already lets Guava decide whether to execute a suggested action immediately or confirm with the caller first — you don't need to build this from scratch. Where you do have explicit control (deciding what goes into a `SuggestedAction` and what your handler does before writing to Supabase), match this rule from the spec: auto-apply picks that stay inside an already-agreed category (e.g., swapping which of two already-proposed restaurants to keep), but always narrate-and-wait for a reply before anything in `check_budget`'s tradeoff path, a `day_start` override, or `remove_from_itinerary` on something already `status='confirmed'`.

**`on_question`** — for open questions like "what's my budget looking like" or "what have we planned for Saturday," don't use `DocumentQA` (it's built for static documents, not live changing state). Instead route these through the same `on_action_request`/`budget_status` path, or answer directly from a freshly-queried Supabase read formatted into a sentence.

### **The one rehearsed replanning moment**

Build this as real, working code — not a scripted fake — but design the demo conversation to walk into it on purpose:

1. Seed the itinerary (in Phase 2 of the build, see below) with a Kyoto train arrival \+ a 7:30 PM dinner reservation already in place.  
2. Caller says something like "actually we can't leave until after 5" — this routes to `on_action("replan_conflict")`.  
3. That handler: looks up the existing transit `itinerary_item`, checks whether the linked dinner reservation's `start_time` is now infeasible given a new arrival time (a simple time comparison, not a general solver), and if so, queries `restaurants` for alternatives near the hotel with availability after the new time.  
4. Presents the conflict \+ a specific alternative via `call.send_instruction()`, asks for confirmation, and on confirmation updates both `itinerary_items` rows (`status`, `start_time`) — the dashboard reflects both changes live via the Realtime subscription.

This demonstrates the "change → detect → replan → confirm → update" loop from the spec with real code, scoped to one conflict type instead of a general dependency graph.

### **Finale — trip comic**

`on_action("finalize_trip")`:

1. Run a minimal `validate_itinerary(trip_id)` — check total cost ≤ budget and no two items overlap on the same day. Skip geographic feasibility / travel-time checks tonight (noted in roadmap).  
2. `call.send_instruction()` with a short personalized recap.  
3. Call `comic.generate_trip_comic(trip_id)` — one call to an image-gen API (OpenAI's image endpoint, or whichever provider your team already has a key for) with a prompt built from the trip's destination, top itinerary items, and stated interests. Store the resulting image URL in `trip_comics`.  
4. `call.hangup(final_instructions="Let them know their trip comic is ready on screen.")`

**Gate this behind having an image-gen API key ready within the next five minutes of starting the build.** If it's not readily available, render a static "🎉 Your trip is booked\!" card instead and treat the comic as a stretch item — don't burn build time hunting for API credentials.

---

## **DASHBOARD**

Single `dashboard/index.html`, Supabase JS client loaded via CDN script tag (no build step, no bundler — keep this dead simple to reduce failure surface). Subscribe to `itinerary_items`, `trips`, and `trip_comics` via Supabase Realtime:

```javascript
const supabase = window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

supabase
  .channel('trip-dashboard')
  .on('postgres_changes', { event: '*', schema: 'public', table: 'itinerary_items' }, render)
  .on('postgres_changes', { event: '*', schema: 'public', table: 'trip_comics' }, renderComic)
  .subscribe();
```

Render two card types only tonight (hotel, restaurant — add experience cards only if there's time to spare): image, name, neighborhood, price, tags, a small "proposed / confirmed" badge. Group by `day_date` under a day header, matching the spec's own itinerary format:

```
SATURDAY — KYOTO
9:30 AM — Breakfast
11:00 AM — Kiyomizu-dera
...
Budget: $2,840 / $4,000 · $1,160 remaining
```

Show a budget bar (used / total) computed client-side from the fetched `itinerary_items` \+ `trips.total_budget`, updating live as items are added/removed.

Test this against actual venue wifi as early as possible tonight — it's a new dependency this build has that ClaimLine didn't.

---

## **BUILD PLAN & CUT ORDER**

Work Supabase seeding and voice-agent build in parallel from the start.

1. **Schema \+ seed data (teammate track, starts now, \~10 min)**: run the SQL above as-is — it's a complete working seed set, not just examples to extend. Spend the time saved on testing the actual demo flow against this data instead.  
2. **Agent skeleton \+ intake (\~20 min)**: `agent.py`, `main.py`, `profile_intake.py`. Get `trip_intake` collecting all fields and writing to Supabase via `chat()`.  
3. **Proposals \+ budget (\~25 min)**: `specialists/*.py`, `budget.py`. Verify proposed hotels/restaurants actually show up as rows in `itinerary_items` after intake completes.  
4. **Actions \+ budget tradeoffs (\~30 min)**: wire `planning_actions.py`, including `budget.generate_tradeoffs()`. Test via `chat()` that a caller can accept a proposal, ask about budget, swap something out, and — the important one — get offered concrete alternatives (not a flat rejection) when a request would break the budget.  
5. **Soft constraint: day\_start exception (\~10 min)**: the check in `add_to_itinerary`/proposal flow, plus the `constraint_overrides` insert on confirmation.  
6. **The transit replanning moment (\~15 min, do this after 4 and 5, not before)**: seed the specific train/dinner conflict into a test trip, build and test `replan_conflict` against it specifically.  
7. **Dashboard (\~20 min)**: `index.html`, realtime subscription, card rendering, budget bar. Test against real venue connectivity.  
8. **Finale comic (\~10–15 min, only if time and API key allow)**: `comic.py`, wire `finalize_trip`.  
9. **Real call test \+ demo rehearsal (\~15 min, do not skip or compress)**: place one real `listen_phone()` call end to end, walk the exact demo script below, fix anything that sounds wrong.

**Cut order if time runs short** (drop from the bottom):

1. Finale comic (fall back to a static "trip booked" screen)  
2. Experience cards on dashboard (keep hotel \+ restaurant only)  
3. The transit replanning moment (fall back to: caller can still add/remove items and see budget update live — still a real demo, just without that specific conflict beat)  
4. The `day_start` soft-constraint exception  
5. `budget_status` as a separate on\_question path (fold into `on_action_request` only)

**Never cut**: the hard budget constraint check before any insert, the tradeoff-generation on a budget conflict, and the live dashboard update on at least one item type. Those together are the actual proof of the product's core claim — "here's what we'd have to give up," not "that violates your preferences" — and it's cheap enough that cutting it first to save time would be cutting the wrong thing.

---

## **DEMO SCRIPT (rehearse once before showing judges)**

Only 2 minutes, one rehearsed conflict moment — the budget tradeoff, since it most directly proves the spec's stated goal ("here's what we'd have to give up," not a flat rejection). Keep the transit replanning and `day_start` exception as real, working features to show only if judges ask a follow-up in the 1-minute Q\&A — don't script all three into the timed demo.

1. Call in. Give destination, days, party size, budget, pace, interests, spend priorities — conversationally, not a checklist recitation.  
2. Watch the dashboard populate with hotel \+ restaurant proposals live as the agent talks.  
3. Accept one hotel, then explicitly ask for something that breaks budget — e.g. "let's do the omakase place, that looks amazing" when it would push the trip over. Show the agent explain the overage and offer the 2-3 concrete tradeoffs, then pick one out loud.  
4. Say you're done planning. Show the recap, the finale comic (or the fallback card), and the final budget bar.

If there's time and a judge asks "what if something changes mid-trip," that's the cue to show the transit replanning moment live as a bonus, not something to force into the scripted 2 minutes.

---

## **FULL-VISION ROADMAP (from the original spec — not tonight, preserved for later)**

Everything below is real product scope, deliberately deferred, not forgotten:

* Real hotel/flight/restaurant search integrations (Amadeus, Google Places, etc.) replacing mock data.  
* True multi-agent architecture with independent specialist agents communicating through structured tool-call protocols rather than one agent with internal modules.  
* General-purpose itinerary validator: geographic feasibility, computed travel time between items, arbitrary conflict detection across any change type, not just the one scripted scenario.  
* Split-party itineraries and participant-level constraints/availability.  
* Numeric, confidence-scored interest/preference weights learned over time from both conversation and UI interaction signals (the spec's `interests: {food: 0.95, ...}` model), plus a `preference_signals` table capturing implicit behavioral signals (rejected options, repeated selections) separate from explicit statements.  
* Full 15+ table schema: per-item `*_availability` tables, `trip_participants`, `reservations` as its own table distinct from itinerary item status, and `agent_runs`/`tool_calls` tracing tables for observability into agent behavior.  
* Row-level security properly configured per traveler/trip once this touches real user data.  
* Multiple destinations per trip, multi-city routing.  
* A general three-tier constraint engine covering every stated preference (not just `total_budget` and `day_start`), with per-constraint classification (hard/soft/optimization) instead of two hardcoded checks.  
* Generic contradiction/tension detection between arbitrary stated preferences ("see a lot but don't feel rushed"), including the anchor/optional/free-time planning strategy the spec describes as the resolution — tonight's `priority` column exists but nothing detects the tension automatically or applies the strategy on its own.  
* Counting repeated overrides and proactively offering to update the general Traveler Profile ("you've chosen early starts three times...").  
* Reservation-availability and accessibility as real hard constraints — tonight's mock inventory has no availability limits or accessibility data modeled.  
* Optimization-tier ranking as an actual scored ranking function, not a simple tag-overlap sort.

