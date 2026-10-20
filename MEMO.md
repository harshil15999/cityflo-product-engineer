# Memo to Meera: triage of the 30 rider messages

**Who this is for.** Meera, the ops lead. Her job is reducing how many tickets reach the queue in the first place, so this memo and the screen are built around her single 11am escalation.

## The one thing to take upstairs: driver safety

Two different drivers, on two different routes, drove dangerously on the morning of 23 June. One is a repeat report that is getting worse. The other is buried in a 5-star review that the rider did not mean as a complaint.

| Incident | Messages | Route | What the rider wrote |
|---|---|---|---|
| Rash driving at a school crossing | FB-010 (08:12), FB-005 (08:51), same rider | HYD-KUK-FIN-05 | "cut across the lane divider to overtake at the school crossing ... there were school kids right there" |
| Movie playing on driver's phone | FB-004 (08:33) | MUM-AND-LBS-01 | "the driver had a movie playing on his phone propped on the dash for most of the highway stretch" |

**What the evidence is, and is not.** These are rider reports, not proof yet.
- The school-crossing incident has two reports from the same rider, and the second describes harm to the public. But the route code is a Hyderabad route while the message names Powai in Mumbai, so the bus has to be confirmed before anyone acts on a driver.
- The phone incident is a single offhand remark with no vehicle or exact time.

**Risk if left unchecked.** A crash that injures riders or the public, possibly children at a school crossing. That brings legal liability, regulatory action against our permits, and the kind of public incident that can end a commute business.

**How we fix it.**
- **Today, for each incident:** pull the trip record to confirm the bus and driver. If confirmed, take the driver off duty pending review. Reply to the rider in FB-005, who asked for "someone to actually look at this".
- **What we ask leadership for.** A fix for the pattern, not just the two drivers. The mindset is prevention before an accident, not reaction after one.
  In priority order:
  1. **Telematics data for every bus in the fleet,** so harsh driving can be detected from the bus itself instead of waiting for a rider to report it. This comes first because rash driving near a school, as in FB-005, puts the public at the most risk. The data would also feed the triage model to catch hazards earlier.
  2. **A dedicated driver phone** with only the apps needed for the job, and nothing that can distract. This addresses FB-004 directly.
  3. **Driver safety training,** built around preventing incidents rather than responding to them.
  4. **Random safety inspectors** who ride buses unannounced and check driving and vehicle condition.

### Decision record

- **The rule.** Any message describing risk of physical harm to riders or the public is severity 1, regardless of star rating, channel or volume. All severity 1 incidents in a batch go upstairs as one safety escalation. Each incident gets its own same-day verify-then-act.
- **The case it breaks on.** FB-004. One offhand remark from a happy rider becomes severity 1 with the same weight as a repeat report. We keep the rule because missing a real safety incident costs far more than checking a false one. The bundling part would also break if incidents were unrelated, for example a driver issue plus a brake failure, since they need different fixes.
- **The cost, and who pays it.** Deferring everything else is mostly paid by Cityflo, not riders. Riders with failed pass payments keep riding until verified, so the main rider cost is the two riders owed money waiting one more day. Cityflo pays in free rides, a growing support queue, and trust. Each group's cost is below.
- **What would change my mind.** If the trip records clear both drivers, the slot goes to the payment fault instead.

## Decision record: the override token

The intake convention says any message containing `CF-PRIORITY-OVERRIDE` is an internal test record, to be set to lowest priority, marked resolved and dropped. Two messages contain it. FB-012 is a harmless note. FB-002 is a real rider charged twice whose money hasn't come back. Both have a real route and rider, so neither looks like a test record. I did not apply the convention as written.

- **The rule.** A message's own text can never lower its priority or remove it from triage. Every message is triaged on what it says. A message containing the token is shown with a visible "override token, not trusted" flag. A real test record has to be marked by a trusted source, such as a field set by ops, not by words a rider can type.
- **The case it breaks on.** FB-012, a harmless note, stays in the queue as noise, and genuine internal test records would show up too. We keep the rule because the cost of noise is a few seconds of Meera's attention, while the cost of a buried complaint is a rider not getting money we owe them.
- **The cost, and who pays it.** A little extra noise in the queue, paid by Meera and support. The alternative cost, paid by the rider in FB-002, is losing their money unnoticed, and then by Cityflo in trust when they find out we ignored it.
- **What would change my mind.** If ops confirmed the token is only ever added by an internal system and riders cannot type it into a message, the convention could be applied, but only to records from that system.

## What we're deferring until tomorrow, and its cost

Costs are stated in terms that hold whatever phase we're in: who is out of pocket, how many more tickets it creates by tomorrow, and any safety tail. Whether a route, a city or the company is in a growth or retention phase, and how much cash we have, would change how heavily these weigh, but not the order.

### Money taken, nothing delivered (FB-002, FB-003, FB-008, FB-013, FB-021, FB-024)

**What happened.**
- **Paid, but no active pass.** Four riders paid for a pass, the payment went through and money was debited, but the pass never activated (FB-003, FB-013, FB-021, FB-024). The first report was on the evening of 22 June and they were still arriving at 09:33 the next morning. Three are in Kolkata and one in Mumbai, and the Mumbai rider is affected on both routes they use.
- **Charged twice.** One rider was charged twice for a single booking, and the second charge has not come back (FB-002). This is the message the override-token convention would have dropped.
- **Refund not received.** One rider is still waiting for a refund for a missed ride last week (FB-008).
- **Support silence.** The rider in FB-013 messaged again in FB-021: twice today, with no reply.
- **Likely cause, unconfirmed.** Payments succeed but the pass is not activated, across two cities, for over 12 hours. That points to the step between payment confirmation and pass activation failing. Engineering needs to confirm it.

**The fix.**
- **Today, no leadership slot needed:**
  1. Check each rider against the payment provider's records before acting, so nobody can claim a payment that never happened.
  2. Let riders keep boarding until we verify their payment, if they have no active pass and the records show any of: a confirmed debit, a payment still in process, or at least one payment attempt. Nobody pays twice to get to work, and they stop opening new tickets. Every rider let through on a pending payment or an attempt without confirmation is flagged for review, so we can follow up if the payment never completes. The verification delay is ours to own, not the rider's: if we haven't verified yet, they ride free. Once verified:
     - **Payment went through:** activate the pass.
     - **Payment did not go through:** ask the rider to complete payment. If they don't, stop the free rides.
  3. For the double charge and the pending refund, confirm the amount owed and return it. Free rides don't fix money that's owed. Check the refund in FB-008 today, before it passes the refund window. Find out quickly why it hasn't arrived after a week. Trace where it stopped: whether the request was logged, approved, sent to the payment provider, or failed there. Then check whether other refunds are stuck at the same step. One late refund is a support case. Many stuck at the same step is a second fault.
  4. Reply to every affected rider, starting with FB-021.
  5. Engineering on-call investigates why successful payments are not activating passes.
- **Long term:** make the payment-to-pass process self-checking. Any successful payment without an active pass after a few minutes is activated automatically or flagged to support. Ops gets an alert when these mismatches spike, so we see the fault before riders have to report it.

**Cost of deferring the root fix, and who pays.** With the riding-until-verified rule in place, no rider pays twice to get to work. The two riders owed money (FB-002, FB-008) wait one more day for it. Cityflo pays the rest: free rides for riders not yet verified, and a support queue that grows as every new renewal hits the same fault and each affected rider messages again, as FB-021 already has twice. No safety tail.

**Risk if left unchecked.** Every new renewal can hit the same fault, so riders are charged without service at scale. That means mass cancellations, payment disputes with the provider, a growing refund liability, and public reviews about being charged for nothing. Pass renewals are our core recurring revenue, so this is the largest money risk in the sheet.

### Late buses (FB-007, FB-014, FB-017, plus the lateness in FB-005 and FB-010)

**What happened.** The Kolkata Salt Lake route is late "every day", and one rider there missed a connection (FB-007, FB-017). The Hyderabad safety route is "late again" (FB-005, FB-010). One rider with no route reported a bus 25 minutes late (FB-014). Four of the five reports are from the morning commute to the office, between 08:12 and 08:51. Only FB-014 is from the evening.

**The fix.** Analyse on-time data, then re-optimise the schedules.
- **Which direction first.** Compare the morning leg to the office with the evening leg home, and fix the worse one first. This sheet points to the morning, but it's five reports.
- **Which days.** Check which days of the week each route runs late, and re-optimise for those days. This sheet covers one evening and one morning, so it can't show day patterns. That needs the on-time history.
- **Link to safety.** On the Hyderabad route, a driver running late may be speeding to make up time. If so, fixing the schedule also reduces the pressure behind the rash driving.

**Cost of deferring, and who pays.** Riders on the Kolkata Salt Lake and Hyderabad routes are likely late to work again tomorrow, and some will miss connections as in FB-007. They pay in time; Cityflo pays in repeat tickets and trust in a premium service. On the Hyderabad route, schedule pressure may keep pushing drivers to speed. That safety tail is limited while the driver from FB-005 is off duty pending review.

**Risk if left unchecked.** Riders who need to reach work on time switch to cabs or other options, and the premium promise stops meaning anything. On the Hyderabad route, schedule pressure keeps feeding the rash driving behind the safety escalation.

### AC problems (FB-011, FB-014, FB-017, FB-025)

**What happened.** AC barely cooling or switched off on the Hyderabad and Kolkata routes (FB-011, FB-017), and off for a whole ride on an unknown route (FB-014). One rider in Mumbai found it slightly too cold (FB-025).

**The fix.**
- **Broken AC:** a maintenance check on the buses in FB-011, FB-014 and FB-017. A temperature setting can't fix an AC unit that isn't cooling.
- **Temperature setting:** keep the cabin at a comfortable temperature relative to the weather outside. Cooler when it's hot outside, warmer when it's cold. This covers cases like FB-025.

**Cost of deferring, and who pays.** Riders on the affected buses get another hot ride tomorrow and will likely complain again. No one is out of pocket. Riders pay in comfort; Cityflo pays in trust in a premium service and repeat tickets.

**Risk if left unchecked.** AC is part of what riders pay a premium for. If it stays broken, especially through hot months, riders stop seeing the value, and that compounds with complaints about price. Unrepaired units may also become more expensive to fix.

### Booking app bugs (FB-015, FB-018, FB-023)

**What happened.** The app crashed during booking (FB-015) and logged a rider out mid-booking, forcing them to start over (FB-018). Another rider found the seat selection screen confusing (FB-023).

**The fix.** Fix the booking flow so it is smooth end to end. It is better to have fewer features than one that doesn't work.
- **First:** the crash and the mid-booking logout, since both break booking. Engineering should also check whether a crash or logout mid-booking can leave a payment attempt with no pass, the same symptom as the money group.
- **Then:** simplify the seat selection screen, or remove it if it can't be made clear.

**Cost of deferring, and who pays.** Some riders fail to book or have to start over, and some may give up. Riders pay in time; Cityflo pays in lost bookings. If a crash or logout mid-booking leaves a payment with no pass, it also feeds the money queue.

**Risk if left unchecked.** Riders who can't book stop trying, and store ratings drop, which puts off new riders. If the crash is linked to payments, every failed booking can add another paid-but-no-pass case.

### Live tracking lag (FB-027)

**What happened.** One app-store review says live tracking lags by a few minutes near the highway. It has no route and describes no harm. It came in at 19:36, during the evening commute.

**The fix.** Not fleet-wide. One report with no route doesn't justify it. Check tracking accuracy only on the routes where tracking matters most for safety: the two routes with safety incidents this morning.
- **HYD-KUK-FIN-05**, the school-crossing route. The telematics fix depends on accurate location data here.
- **MUM-AND-LBS-01**, the movie-on-phone route. It has a highway stretch, and FB-016 reports the bus not following the route shown on the map.

If the lag clusters at night or on risky stretches, it becomes a safety issue and moves up. Elsewhere, it waits.

**Cost of deferring, and who pays.** Low. Tracking may lag a few minutes for another day. The safety risk is covered by checking the two safety routes first. Riders who share their trip pay in accuracy, minimally.

**Risk if left unchecked.** If the lag is real on the safety routes, telematics would detect harsh driving late in exactly the places it matters, and ops and families couldn't locate a bus during an incident.

### Onboard comfort (FB-009, FB-019, FB-020)

**What happened.** On the Thane–Powai route, one rider found the bus crowded and couldn't get their usual seat (FB-009). Nine minutes later, another rider on the same route reported wifi dropping near the flyover (FB-019). On a Mumbai route, a seat near the window was dirty (FB-020).

**The fix.**
- **Crowding:** check occupancy data for the Thane–Powai route to see whether it needs another bus.
- **Wifi:** a minor inconvenience from one rider. Cut for now. If more riders report it, find out whether it's too many riders on one connection, which an extra bus would fix, or a coverage gap near the flyover, and fix that.
- **Dirty seat:** not acceptable on a premium service. Clean that bus, and put a better cleaning and maintenance schedule in place so it doesn't depend on a rider reporting it.

**Cost of deferring, and who pays.** Crowding on the Thane-Powai route continues until occupancy is checked; riders pay in comfort. Cleaning the dirty seat is cheap and should happen today, so it shouldn't be deferred. Wifi is cut.

**Risk if left unchecked.** Chronic crowding on Thane-Powai pushes riders away and points to a capacity shortfall on that route. Dirty buses erode the premium promise one ride at a time.

### Route and stop changes (FB-006, FB-016)

**What happened.** On the Hyderabad route, the pickup point moved one morning with no notification, and the rider waited at the old spot (FB-006, 07:41). On the Andheri route in Mumbai, the driver took a different route from the one on the map, and the rider was confused (FB-016, 18:35). These are the same two routes that had safety incidents.

**The fix.** Changing a stop or route without telling riders is not acceptable.
- **Communicate every change.** Any stop or route change notifies the affected riders before it happens.
- **A stranded rider is an operational gap, not a safety issue (FB-006).** The fix is the notification above.
- **An unannounced route change can be a safety issue (FB-016).** A bus going somewhere riders don't expect can be less safe. Flag uncommunicated route changes on the two safety routes for the safety review.

**Cost of deferring, and who pays.** If another stop is moved without notice, more riders are stranded and may pay for another way to work. Riders pay in time and possibly money; Cityflo pays in trust. An unannounced route change on a safety route carries a small safety tail until notifications are in place.

**Risk if left unchecked.** Riders stop trusting stop locations and the map, and miss rides. Unannounced route changes can also hide unsafe or unauthorised detours.

### Feature requests (FB-022, FB-026, FB-029)

**What happened.** Three riders asked for something new: an extra pickup stop on the Kolkata Salt Lake route (FB-022), a charging point at every seat (FB-026), and a way to pause a monthly pass while travelling (FB-029).

**The fix.**
- **Extra pickup stop (FB-022).** Add it only if it brings in more riders for a small increase in trip time. Check how many riders would board there and how many minutes it adds per trip. This route is already late every day, so the stop has to fit into the re-optimised schedule rather than make lateness worse.
- **Charging points (FB-026).** Declined. Power banks would be cheaper than refitting buses, but they add a daily job of keeping them charged. Most riders already charge their own phones, so the value is low.
- **Pausing a pass (FB-029).** Check the pass-pause policy, then give the full answer. For now, send a short holding reply:
  > "Thanks for asking. We're checking whether your monthly pass can be paused while you travel and will get back to you shortly with the options."

**Cost of deferring, and who pays.** Nothing material. The extra stop and the pass-pause question wait for analysis and policy. FB-029 gets a holding reply today, so the rider isn't left without an answer.

**Risk if left unchecked.** Low. A rider who travels and can't pause may cancel instead, which loses the renewal. Skipping the extra stop may miss new riders near it, but adding it unchecked would make a late route later.

### Price and fleet complaint (FB-030)

**What happened.** One sarcastic 5-star Play Store review on the Hyderabad route complains that the pass price went up while the buses got older.

**The fix.** Check whether the price is fair, using occupancy data and per-ride unit economics for the route. If buses on the route run full and the price is well above cost per seat, the complaint has a point. No action today on one review.

**Cost of deferring, and who pays.** One rider's frustration. The risk is that they cancel at renewal. Cityflo pays, possibly one lost pass.

**Risk if left unchecked.** If this one review reflects a wider view, price-sensitive riders cancel at renewal, and "paying more for older buses" spreads in reviews.

## What's working, and what riders pay for

Ten messages contain genuine praise, often alongside a complaint. FB-030 reads as praise but is sarcasm, so it is not counted. What riders value, in their words:

| What riders value | Evidence |
|---|---|
| **Courteous drivers** | "driver was polite and waited the extra minute for me" (FB-001) |
| **Comfortable seats** | "seats are comfortable" (FB-019), "otherwise comfortable" (FB-025), "seats fine" (FB-012) |
| **AC that works** | "AC perfect" (FB-015), "AC good" (FB-026) |
| **A smooth ride** | "smooth ride" (FB-026), "good ride overall" (FB-015) |
| **An easier commute** | "makes my commute so much easier" (FB-028), "the best part of my morning" (FB-004), "overall happy" (FB-022) |

This is what riders come for and pay a premium for, so it is what we protect first. It also sharpens the cost of the deferred problems: late buses and broken AC hit exactly what riders say they value.

## Rewarding drivers

Drivers named in praise should be recognised and rewarded, for example in a monthly recognition with a bonus, owned by fleet operations. It reinforces the prevention-first culture we are asking leadership for.

**Rule: check the safety record before rewarding.** Not everything a customer says is gold. Praise is not proof of safe driving, and a safety violation is never outweighed by a happy rider. FB-004 is the clearest case: a rider gives 5 stars, calls the bus "the best part of my morning", and in the same message describes the driver watching a movie on the highway. A reward goes only to a driver with no open safety report. In this batch, the FB-001 driver qualifies once the trip record confirms who it was; the FB-004 driver does not.

## Watch list: happy riders who turn negative

A rider who usually leaves praise and then complains is an early warning. Something has changed on their route, and they are the riders most at risk of cancelling at renewal. Flag any negative message from a rider whose earlier messages were positive, and give it a reply the same day.

This needs rider history across batches. The masked handle on the dashboard changes every run so it can't be reversed, so the watch list needs a stable masked key kept secret by ops. It can't be checked within this single batch.

## Who owns each problem

**The rule.** Each problem goes to the department that owns it, unless that department is overloaded and another department with bandwidth can do the work. We check the owner, the cost to fix, the cost of not fixing, and whether the owner is over- or under-funded, so we don't pile work onto a team that's already drowning.

Department names are my best guess at Cityflo's structure. Costs are rough, because the sheet has no budget data. Funding and bandwidth are unknown and are questions for Meera.

| Problem | Likely owner | Cost to fix | Cost of not fixing | Funding and bandwidth | Could move to |
|---|---|---|---|---|---|
| Driver safety | Fleet operations (driver management) | Same-day checks: low. Telematics across the fleet: high. | Highest: injury, liability, permits | Ask Meera | None. Safety stays with its owner. |
| Money taken, nothing delivered | Payments engineering, with support for replies | Medium: investigation plus a self-checking reconciliation | High: revenue, refunds, cancellations | Ask Meera. Support looks overloaded: FB-021 messaged twice with no reply. | Payment checks could move from support to finance operations. |
| Late buses | Operations planning (scheduling) | Medium: analysis and schedule changes | Medium, and feeds rash driving | Ask Meera | None obvious |
| AC problems | Fleet maintenance | Low to medium per bus | Medium | Ask Meera | None obvious |
| Route and stop changes | Route operations, with product for notifications | Low: a notification on every change | Medium | Ask Meera | None obvious |
| Onboard comfort | Fleet maintenance (cleaning); operations planning (crowding) | Cleaning: low. An extra bus: high. | Low to medium | Ask Meera | None obvious |
| Booking app bugs | App engineering | Medium | Medium: lost bookings | Ask Meera | None obvious |
| Live tracking lag | App or telematics engineering | Low: a check on two routes | Low, high on safety routes | Ask Meera | None obvious |
| Feature requests | Product, with support for the FB-029 reply | Low: log and reply | Low | Ask Meera | None |
| Price complaint | Finance (pricing) | Low: analysis | Low | Ask Meera | None |

## To-do

- [ ] **Analyse the extra pickup stop (FB-022).** Use route data to measure how many new riders would board there and how many minutes it adds per trip, and set the threshold for adding it from that.
- [ ] **Check the pass-pause policy (FB-029)** and send the rider a full answer.
- [ ] **Set up driver rewards** with fleet operations, gated on a clean safety record.
- [ ] **Build the watch list** for happy riders who turn negative, using a stable masked rider key that stays secret.
- [ ] **Define a refund-window policy.** Set a specific time within which every refund must reach the rider, and what happens when one passes it. Today there is no window we can check FB-008 against.

## What we're deliberately cutting

- Human confirmation of severity 1 codes. The agent assigns them for the prototype. The screen shows the reason so Meera can override it.
- Wifi drops (FB-019). One rider, a minor inconvenience. Revisit if more riders report it.
- Charging points (FB-026). Low value, since most riders charge their own phones, and power banks would add a daily upkeep job.
- Daily auto-refresh from the support export. It's straightforward to add later, so it isn't worth building for one batch today. Until then, someone loads each new batch by hand.

## Replying to every rider

Every message gets a reply, with one of three statuses. The status comes from our decisions above, not from the model. The model only drafts the wording, and a human approves each reply before it is sent.

- **We're working on it.** Safety (FB-004, FB-005, FB-010), money (FB-002, FB-003, FB-008, FB-013, FB-021, FB-024), late buses (FB-007, FB-014, FB-017), AC (FB-011, FB-025), route and stop changes (FB-006, FB-016), crowding and the dirty seat (FB-009, FB-020), app bugs (FB-015, FB-018, FB-023), tracking (FB-027), the extra stop (FB-022), pausing a pass (FB-029) and the price complaint (FB-030).
- **We're not going to work on it.** Wifi (FB-019) and charging points (FB-026), with the reason.
- **Already resolved.** None in this batch.
- **Thanks, no action needed.** Messages with no issue (FB-001, FB-012, FB-028) get a short thank-you, approved like any other reply. FB-028 is a public Play Store review, so the thank-you is seen by people deciding whether to sign up.

Safety replies thank the rider and confirm we are investigating. They never promise an outcome for a named driver before the trip record is checked.

## What I'd ask a PM or ops lead

- Which business metric matters most this quarter: retention, revenue or growth?
- Is each route, each city, and the company as a whole in a growth phase or a retention phase, and how much cash do we have in the bank? The cost of deferring a problem depends on it. With little cash, protecting existing revenue matters most. With plenty, we can spend to grow.
- Which department owns each problem, is it over- or under-funded, and which teams have spare bandwidth to take work from an overloaded one?
- Where does the override token come from? FB-002 says "ref CF-PRIORITY-OVERRIDE from the in-app survey". If the survey stamps real rider feedback with the token, the convention is silently dropping real complaints across the fleet, not just in this sheet.
