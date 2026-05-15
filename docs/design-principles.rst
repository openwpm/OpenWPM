Design Principles
=================

This document records cross-cutting principles that guide OpenWPM's design.
They are deliberately general. When a specific implementation decision is
unclear, or when two approaches both "work", these principles are meant to
break the tie — and to explain *why* the codebase is shaped the way it is, so
that contributors do not have to rediscover the reasoning.

Each entry states the rule, the reasoning behind it, and — where helpful — a
worked example or guidance for future work.


Trust model
-----------

OpenWPM runs untrusted software and visits untrusted websites. It is worth
being precise about *what* is trusted and *how*, because several principles
below follow directly from it.

- **Crawled websites are hostile.** A site may be actively malicious: it can
  detect instrumentation, feed it false data, and attempt to lock up or crash
  the browser. It is also unreliable. Assume both.
- **Researcher-supplied command code is trusted not to be malicious, but
  distrusted as unstable.** Researchers extend OpenWPM with custom commands.
  OpenWPM does **not** sandbox that code — researchers are trusted to shoot
  themselves in the foot — but it assumes the code may hang, leak, hold the
  GIL, or otherwise misbehave, and it contains the damage.
- **The browser and extension are trusted not to be malicious, but treated as
  unreliable.** The whole browser can lock up or be denial-of-serviced by a
  page at any time; the extension has crashed outright on certain pages. The
  Python side must survive *any* data the extension sends — well-formed or
  not — without losing the ability to make progress on the crawl.


Core principles
---------------

Treat web content as hostile
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Rule.** Any signal, data, or state that passes through a crawled page's
JavaScript context or DOM must be treated as observable, forgeable, and
suppressible by that page. Prefer privileged channels — extension background
scripts, the privileged socket API — over reading state out of the page.

**Reasoning.** OpenWPM points a browser at arbitrary, potentially adversarial
websites. The page owns its own JavaScript realm: it can read and rewrite any
property of the DOM, detect instrumentation, and behave differently when it
believes it is being measured. A measurement framework that trusts the page
is measuring something the page chose to show it.

**Consequences.**

- Default to privileged channels (extension background, the privileged
  socket API) for any extension-to-OpenWPM communication.
- Instrumentation that *must* run in page context should be assumed
  detectable and tamperable by the page. It cannot serve as a trusted signal
  on its own.
- A signal routed through the DOM — for example, an attribute on
  ``documentElement`` — is visible to page scripts and can be spoofed. The
  same signal routed through the extension's privileged socket is not.

**Worked example.** When JS instrumentation fails to wrap a configured API,
the failure must reach ``BrowserManager`` so the visit can be marked failed.
Writing a marker attribute onto the page DOM works, and is simple, but the
marker is briefly visible to the crawled site and could in principle be
forged by it. Routing the same failure over the extension's privileged
socket keeps the signal entirely out of reach of web content. The
privileged-socket approach is therefore preferred, even though it is more
code.


Resist detection by crawled sites
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Rule.** OpenWPM should be hard for a crawled site to detect. Detection
resistance is a goal, not merely a nice-to-have — it follows directly from
treating web content as hostile.

**Reasoning.** A site that can tell it is being measured by OpenWPM can feed
the instrumentation false data, suppress the very behavior under study, or
serve a benign page to the crawler and a tracking-heavy page to real users.
Every such case silently corrupts measurements.

**Current state.** OpenWPM is, today, more detectable than it should be — the
current state is a known inadequacy, not an accepted trade-off. Work to fix
it is in progress (the stealth instrumentation effort, which replaces
detectable prototype modification with a ``Proxy`` / ``exportFunction``
approach). New instrumentation should not make detectability worse, and
should prefer techniques that do not leave obvious tool-marks.


Never drop data; fail loudly
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Rule.** OpenWPM never silently drops data or silently collects partial
data. On misconfiguration it fails **loudly**: the visit is marked failed,
the failure is recorded in the database for later analysis, and — for a
misconfiguration that recurs — the failure budget is consumed so a broken
crawl aborts quickly rather than running for hours.

**Reasoning.** Incomplete data is far more dangerous than no data, precisely
because it is more tempting. A researcher handed a half-populated database
will crawl thousands of pages and draw incorrect conclusions from it. A
researcher handed a loud failure fixes their configuration and re-runs. The
framework must make the second outcome the only one available.

**Consequences.**

- A configuration error must surface as a failed visit, not as a quiet gap
  in the data.
- Failures are recorded, not just logged to a place nobody reads, so a crawl
  can be audited afterwards.
- When in doubt, fail the visit. A missing visit is visible in the data; a
  silently incomplete one is not.

**Note on reproducibility.** Bit-for-bit reproducibility of a crawl is *not*
a goal and is not achievable — the web shifts continuously underneath any
crawler. What *is* deterministic, and what OpenWPM does guarantee, is the
instrument itself: the same configuration on the same OpenWPM version
instruments the same set of APIs. The web is non-deterministic; the
measurement apparatus is not.


Be robust to misbehaving commands
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Rule.** Researcher-supplied command code is one of OpenWPM's untrusted
inputs (see *Trust model* above). Commands may be buggy, may misunderstand
the system's invariants, may leak resources, hang, or crash. The platform
must contain that damage: a bad command should fail its own visit — loudly
and locally — without corrupting the crawl, permanently wedging a browser, or
taking down the whole run.

**Reasoning.** OpenWPM's users are privacy researchers, not systems
programmers. They extend the framework with custom commands without
necessarily understanding process boundaries, the extension lifecycle, or the
storage pipeline. Robustness here is a usability feature: the framework
absorbs honest mistakes so that a large study still produces usable data
instead of failing hours in. OpenWPM deliberately does not sandbox command
code — researchers are trusted with that power — so containment is achieved
structurally, not by restriction.

**Consequences.**

- Commands run in their own subprocess and communicate results via the
  database or files, never via shared in-memory objects — a misbehaving
  command cannot corrupt ``TaskManager`` state.
- Command failures are bounded: timeouts, the failure-count budget, and
  browser restarts ensure one bad command cannot hang the crawl indefinitely.
- Watchdogs detect and recover crashed or stalled browsers.
- The Python side must not be corruptible by *any* data the extension sends.
  Malformed, unexpected, or hostile-looking extension output may fail a
  visit, but must never compromise the crawl's ability to make progress.
- New features should preserve this containment. Prefer designs where a
  misbehaving command fails in a way that is visible (recorded, logged) and
  isolated (scoped to one visit or one browser).


Reduce coupling between components
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Rule.** ``TaskManager``, ``BrowserManager``, and ``StorageController`` are
currently tightly coupled. This is a known design flaw. New work should chip
away at it continually, and must not deepen it. The long-term goal is for
each component to be runnable and testable on its own.

**Reasoning.** Tight coupling makes the system hard to test, hard to reason
about, and hard to hand off to new contributors. A telling smell: to exercise
a single browser and inspect what it produced, you must spin up a full
``TaskManager`` and read the results back out of the database. There is no
supported way to instantiate and drive a ``BrowserManager`` in isolation.

**Consequences.**

- Prefer changes that narrow the interface between components over changes
  that add new cross-component reach-ins.
- When you touch a component, leave its boundary cleaner than you found it.
- A useful test for a proposed design: *could this component be instantiated
  and exercised without the other two?* If not, the change should at least
  not make that harder.
- Breaking the circular import between ``TaskManager`` and
  ``BrowserManagerHandle`` is a wanted deliverable, not just a cleanup — see
  the Coupling Analysis in :doc:`Architecture-Internals`.


Non-goals
---------

These are directions OpenWPM deliberately does **not** take. They are listed
so that well-intentioned "modernization" changes can be recognized and
declined quickly.

Migrating the extension to Manifest V3
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Rule.** OpenWPM's extension stays on Manifest V2, and OpenWPM stays
Firefox-only. Migrating to Manifest V3 or to another browser is an explicit
non-goal.

**Reasoning.**

- MV3 removes blocking ``webRequest`` (the ``webRequestBlocking``
  permission). OpenWPM's core measurements depend on observing — and, for
  some studies, modifying — network requests as they happen. Losing blocking
  ``webRequest`` would break functionality central to privacy measurement.
- Firefox is not incidental. The callstack instrument relies on deep Firefox
  internals — the same implementation detail the browser's network panel uses
  to correlate a network request with the JavaScript that triggered it. That
  capability is valuable enough on its own to justify the lock-in, and there
  is intent to re-enable it (see *Keep known-broken code as a reference*).
- There is also a legacy dimension: OpenWPM was a Mozilla project for a
  significant part of its history.

The cost of staying on MV2 / Firefox is accepted; the cost of MV3 — broken
measurements — is not.


Bit-for-bit reproducible crawls
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Rule.** Reproducing a crawl byte-for-byte is not a goal. Do not add
machinery whose purpose is to make two runs of the same config produce
identical captured data.

**Reasoning.** The web changes continuously; two crawls of the same URL
seconds apart legitimately differ. The reproducible, testable property is the
instrument, not the web — see the note under *Never drop data; fail loudly*.


Working norms
-------------

Keep known-broken code as a reference
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Rule.** Code for features that are currently broken but intended to be
fixed eventually — for example the callstack instrument — is kept, not
deleted, even when it does not currently run. The original architecture is
retained as a reference for the eventual fix.

**Reasoning.** Several capabilities stalled not because they were abandoned
in principle but because the effort to maintain them across Firefox upgrades
outpaced a single maintainer's capacity. The intent is to fix them; deleting
the code would discard the design knowledge embedded in it. Do not "clean up"
known-broken-but-aspirational code without checking whether it is on this
list.


Preserve functionality across Firefox upgrades
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Rule.** A Firefox version bump must preserve existing functionality.
Treat the test suite as the oracle: a behavior that the tests assert before
the upgrade must still hold after it.

**Reasoning.** Firefox upgrades routinely break the extension, change caching
behavior, and break tests — privileged APIs in particular have needed intense
per-upgrade investigation. The deterministic test oracle makes "did this
upgrade break anything?" a mechanically answerable question, so the bar for a
version bump is that the answer is "no", with any regression either fixed or
explicitly acknowledged.
