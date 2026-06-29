"""Translate a legacy ``js_instrument_settings`` config into an equivalent flat,
non-recursive ``stealth_js_instrument_settings`` config.

The stealth JavaScript instrument (``Extension/src/stealth``) cannot honour the
legacy ``recursive`` flag — recursion requires mutating the page's in-page object
graph, which is incompatible with stealth's isolated compartment (see
``docs/developers/Stealth-Instrumentation.rst``). A stealth surface that sets
``recursive: true`` is therefore rejected at config-validation time
(``openwpm/config.py``).

This module turns that rejection into an actionable step. Given a researcher's
legacy settings list — including ``recursive`` entries — it launches a
lightweight Firefox, replays **exactly** the legacy descent
(``instrumentObject`` in ``Extension/src/lib/js-instruments.ts``) over the live
object graph, and emits a flat list of stealth entries that cover the same API
surface without recursion.

Each reached node becomes one stealth entry ``{object, instrumentedName, depth,
logSettings}`` where ``object`` is the node's ``constructor.name`` (the bare
global name stealth resolves against the page scope) and ``instrumentedName`` is
the legacy symbol path.

Coverage: what is representable, and what is surfaced as untranslatable
-----------------------------------------------------------------------
Every legacy member is accounted for: a member is EITHER represented in the new
stealth config OR surfaced as an :class:`UntranslatedEntry` (the second element
of the returned tuple). Nothing is dropped silently. Members fall into three
classes:

1. **Untranslatable node** — a node whose ``constructor.name`` is ``Object``/
   ``Array``/falsy has no global interface prototype to hook, so the whole node
   cannot be expressed as a stealth entry (e.g. ``navigator.languages``, a plain
   ``Array``). Surfaced as an :class:`UntranslatedEntry`.

2. **Universal-prototype inherited members** — legacy's
   ``Object.getPropertyNames(instance)`` instruments the instance's own names
   PLUS the entire prototype chain to ``null``. The leaf stealth entry uses
   ``depth: 0``, so ``getPropertyNamesPerDepth(proto, 0)`` (stealth
   ``instrument.ts``) covers only the LEAF interface prototype's OWN names.
   Inherited members owned by a UNIVERSAL prototype (``Object.prototype``,
   ``Function.prototype``, ``Array.prototype`` — e.g. ``toString``, ``valueOf``,
   ``hasOwnProperty``) are deliberately left uninstrumented: hooking such a member
   would fire on virtually every receiver on the page, flooding the log with
   noise. Each is surfaced as an :class:`UntranslatedEntry` with an explanatory
   reason.

   Inherited members owned by a REAL global interface prototype (e.g.
   ``EventTarget.prototype.addEventListener``) ARE representable — see
   "interface-attributed shared-prototype capture" below.

3. **Resolution failures** — a legacy ``object`` string that does not ``eval``
   to a live node (``undefined``/``null``/throws) is surfaced as an
   :class:`UntranslatedEntry` too, and makes the CLI exit non-zero.

Interface-attributed shared-prototype capture
---------------------------------------------
Inherited members owned by a REAL global interface prototype (e.g.
``addEventListener`` on ``EventTarget.prototype``, reached via
``navigator.permissions`` / a DOM element / ``XMLHttpRequest`` / …) ARE
representable in the new stealth config. For each owner interface the sweep emits a SINGLE
shared-prototype stealth entry whose ``propertiesToInstrument`` lists every
inherited method of that owner (e.g. ``EventTarget`` →
``["addEventListener", "removeEventListener", "dispatchEvent", …]``), hooked once
each on the owner's prototype, carrying ``receiverInterfaces`` — the set of LEAF
interface names that reached it. One entry per owner (not per member) is required
for correctness: the stealth instrument gates instrumentation on
``needsWrapper(prototypeObject)``, so several entries sharing one owner prototype
would leave all-but-the-first member unhooked (see ``_shared_prototype_entries``).
At call time the stealth instrument reads the receiver's
interface name (its ``constructor.name``, read through the Xray so a hostile page
cannot fool it; see ``Extension/src/stealth/instrument.ts``) and records the call
only when that interface is in ``receiverInterfaces``. The recorded ``symbol``
stays the static shared-prototype method (e.g. ``EventTarget.addEventListener``);
the concrete receiver interface is written to the dedicated ``receiver`` column
of the ``javascript`` table. This is a content-script-side filter — calls on
other interfaces are dropped before any record is emitted — and attribution is
interface-level (it does not distinguish two instances of the same interface),
which is exactly the granularity researchers filter by in post-processing.

Conversely, the swept (``recursive: false``) stealth config is a strict
**superset** of the legacy recursive surface for object-VALUED properties:
legacy suppresses the plain ``get`` of an object-valued property while it
recurses into it, but the flat stealth entry — having no recursion to suppress —
logs that ``get``. See ``docs/developers/Stealth-Instrumentation.rst``.

CLI::

    python -m openwpm.utilities.js_settings_migrator LEGACY_CONFIG.json \\
        [--output STEALTH_CONFIG.json]

``LEGACY_CONFIG.json`` is a JSON file containing the legacy settings list exactly
as it would be assigned to ``browser_params.js_instrument_settings`` (the same
shorthand/collection forms ``clean_js_instrumentation_settings`` accepts). The
generated stealth list is printed to stdout (or written to ``--output``) and is
ready to assign to ``browser_params.stealth_js_instrument_settings``.
"""

import argparse
import importlib.resources
import json
import logging
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service

from ..js_instrumentation import clean_js_instrumentation_settings
from .platform_utils import get_firefox_binary_path

logger = logging.getLogger("openwpm")

# ``constructor.name`` values that do NOT correspond to a global interface whose
# prototype the stealth instrument can hook. A node reaching one of these is a
# plain container the page built, not a DOM/Web interface, so there is no
# ``window[<name>].prototype`` carrying native accessors to redefine. These nodes
# are surfaced as untranslatable entries. (Legacy can still instrument them
# because it walks the live instance in the page compartment; stealth cannot,
# which is exactly the documented recursive ceiling.)
#
# INTENTIONAL ASYMMETRY vs ``UNIVERSAL_PROTOTYPE_CONSTRUCTORS`` below: that set
# adds ``Function``, this one does NOT — and the two MUST NOT be harmonized. A
# node whose OWN ``constructor.name`` is ``Function`` is a real callable with a
# real ``Function.prototype`` to hook for its own names, so it is NOT
# untranslatable. ``Function`` only matters for the inherited-member
# classification (call/apply/bind are universal-prototype members), which is the
# other set's job. Adding ``Function`` here would wrongly mark every function
# node untranslatable.
UNTRANSLATABLE_CONSTRUCTORS = {"Object", "Array"}

# ``constructor.name`` values of the UNIVERSAL prototypes every object inherits
# from (``Object``/``Function``/``Array``.prototype). Members owned by these
# (``toString``, ``valueOf``, ``hasOwnProperty``, ``call``, ``bind``, …) are, by
# default, surfaced as :class:`UntranslatedEntry` rather than instrumented:
# hooking such a member fires on virtually every receiver page-wide for zero
# tracking signal. The opt-in ``capture_universal_prototype_members`` flag routes
# the METHOD members here into the interface-attributed shared-prototype path
# instead. These owners are matched by
# NAME, not object identity: the sweep walk straddles the content-script/page
# Xray boundary, where the two realms' ``Object.prototype`` objects are distinct,
# so an identity check is unreliable (whereas ``window[owner].prototype`` — the
# real-interface test — resolves the page realm and so correctly identifies them).
#
# INTENTIONAL ASYMMETRY vs ``UNTRANSLATABLE_CONSTRUCTORS`` above: ``Function`` is
# present HERE but absent THERE, and the two sets MUST NOT be harmonized.
# ``Function`` being universal-for-inherited-members (call/apply/bind surfaced as
# untranslated by default) is independent of a Function NODE being translatable
# (it has its own ``Function.prototype`` to hook). Dropping ``Function`` from THIS
# set would silently re-arm the bug where call/apply/bind are captured page-wide
# instead of surfaced as untranslated; the
# ``test_function_prototype_members_untranslated_by_default`` test guards it.
UNIVERSAL_PROTOTYPE_CONSTRUCTORS = {"Object", "Function", "Array"}


@dataclass(frozen=True)
class UntranslatedEntry:
    """One legacy symbol path the swept stealth config does NOT cover.

    ``path`` is the legacy ``instrumentedName`` symbol path (e.g.
    ``window.navigator.languages`` for an untranslatable node, or
    ``window.navigator.permissions.toString`` for an inherited-chain member).
    ``reason`` explains, in source-grounded terms, why stealth cannot cover it.

    These are the second element of ``legacy_settings_to_stealth``'s return
    tuple. Every legacy member not representable in the swept stealth config is
    surfaced here — nothing is dropped silently.
    """

    path: str
    reason: str

    def __str__(self) -> str:
        return f"{self.path} — {self.reason}"


# The walker is a self-contained JavaScript program executed in a clean page via
# ``execute_script``. It mirrors the LEGACY descent in
# ``Extension/src/lib/js-instruments.ts`` exactly:
#
#   * ``getPropertyNames`` (lib/js-instruments.ts ~74-86): own + ENTIRE
#     prototype-chain property names. Used when ``propertiesToInstrument`` is
#     empty, matching ``instrumentObject`` (~668-674).
#   * ``isObject`` (lib/js-instruments.ts ~418-430): ``typeof object[prop] ===
#     "object"`` and not null, guarded against throwing getters.
#   * The recursion gate (lib/js-instruments.ts ~681-696):
#     ``recursive && depth > 0 && isObject(object, prop) && prop !== "__proto__"``
#     recurses into ``object[prop]`` with ``depth - 1``, ``propertiesToInstrument
#     = []`` (→ all names), and ``instrumentedName = `${name}.${prop}` ``.
#   * The ``object`` STRING is resolved with ``eval`` (lib/js-instruments.ts
#     ~761), exactly as the legacy instrument does, so e.g. ``"window.navigator"``
#     and ``"window['CanvasRenderingContext2D'].prototype"`` resolve identically.
#
# For each REACHED node it records the symbol path (``instrumentedName``), the
# node's ``constructor && constructor.name`` (→ the stealth ``object``), and the
# instrumented property names at that node. A node is "reached" both at the top
# level (the resolved ``object``) and at every recursion step.
# Loaded from ``walker.js`` (shipped as package data) so the program is a real,
# lintable/highlightable JavaScript file rather than an inline Python string.
_WALKER_JS = (
    importlib.resources.files("openwpm.utilities")
    .joinpath("walker.js")
    .read_text(encoding="utf-8")
)


def _launch_browser(firefox_binary: Union[str, Path]) -> webdriver.Firefox:
    """Launch a lightweight headless Firefox for the walk.

    No extension is loaded — the walk only inspects the native object graph of a
    clean ``about:blank`` page, which is exactly the surface the legacy instrument
    descends at ``document_start``. ``-remote-allow-system-access`` matches how
    OpenWPM launches Firefox (see ``deploy_browsers``).

    Resolves geckodriver explicitly, the same way ``deploy_firefox`` does, so the
    two stay in sync (single source of truth).
    """
    options = Options()
    options.binary_location = str(firefox_binary)
    options.add_argument("--headless")
    options.add_argument("-remote-allow-system-access")
    # shutil.which returns None when geckodriver is absent, so the explicit guard
    # below fires with actionable guidance. subprocess.check_output("which …")
    # would instead raise an opaque CalledProcessError before the guard is reached.
    geckodriver_path = shutil.which("geckodriver")
    if not geckodriver_path:
        raise RuntimeError(
            "geckodriver not found on PATH; cannot launch Firefox for the walk"
        )
    return webdriver.Firefox(
        options=options,
        service=Service(executable_path=geckodriver_path),
    )


def _stealth_entry_from_node(
    node: Dict[str, Any], log_settings: Dict[str, Any]
) -> Dict[str, Any]:
    """Build one stealth entry from a reached legacy node.

    ``object`` is the node's ``constructor.name`` — the bare global name stealth
    resolves via ``context.wrappedJSObject[object]`` then ``.prototype`` (see
    ``getContextualPrototypeFromString`` in ``Extension/src/stealth/instrument.ts``
    and the "object naming convention" section in
    ``docs/developers/Stealth-Instrumentation.rst``). For a constructor that
    resolution lands directly on its ``.prototype`` (where the native accessors
    live), so the top-level ``depth`` is 0.

    ``logSettings`` is the legacy node's settings with ``recursive`` forced off
    and ``propertiesToInstrument`` set to the explicit list of REQUESTED own
    names — the names legacy instruments at this node
    (``node["propertyNames"]``) intersected with the resolved prototype's own
    names (``node["stealthOwnNames"]``). Under stealth an empty
    ``propertiesToInstrument`` means "instrument EVERY own member of the resolved
    prototype", so a narrow legacy request (e.g. ``{"window.navigator":
    ["userAgent"]}``) must NOT be emitted as ``[]`` — that would silently widen
    it to all ~35 ``Navigator.prototype`` members. Emitting the explicit
    intersection keeps narrow requests narrow while preserving the
    instrument-everything case: when legacy reached this node via the "instrument
    every name" path, ``node["propertyNames"]`` is the full ``getPropertyNames``
    chain, so the intersection equals the ENTIRE leaf own set — every own member
    is still listed, just explicitly instead of via ``[]``.

    ``depth`` is kept at 0 deliberately. At depth 0 the stealth instrument covers
    only the resolved prototype's OWN names
    (``getPropertyNamesPerDepth(proto, 0)`` →
    ``Object.getOwnPropertyNames(proto)``), whereas legacy covers the entire
    prototype chain. Raising ``depth`` to cover the inherited members would
    instrument shared prototypes (``Object.prototype``, ``EventTarget.prototype``)
    under this one recursive path, mis-attributing methods that belong to every
    interface. Instead the inherited members are handled separately: those owned
    by a real global interface prototype become interface-attributed
    shared-prototype entries (``_shared_prototype_entries``), and those owned by a
    universal prototype are surfaced as untranslated (``_inherited_members_of_node``
    + the main loop).
    """
    flat_log_settings = dict(log_settings)
    flat_log_settings["recursive"] = False
    # preventSets is dropped on translation (see legacy_settings_to_stealth):
    # write-blocking distorts the measured behaviour, so the swept config always
    # observes the page's real writes. The caller warns once per requesting path.
    flat_log_settings["preventSets"] = False
    # Emit the EXPLICIT set of requested own names rather than [] (which stealth
    # reads as "instrument every own member of the resolved prototype"). The
    # requested own names are the names legacy instruments at this node
    # (node["propertyNames"]) intersected with the resolved prototype's own names
    # (node["stealthOwnNames"]) — narrow legacy requests stay narrow, while an
    # "instrument everything" node (whose propertyNames is the full chain) still
    # yields every own name. stealthOwnNames is None only when the constructor did
    # not resolve to a hookable prototype; such nodes are surfaced as
    # untranslatable by the caller and never reach here, but guard defensively.
    own_names = set(node.get("stealthOwnNames") or [])
    requested_own = sorted(own_names.intersection(node.get("propertyNames", [])))
    flat_log_settings["propertiesToInstrument"] = requested_own
    # overwrittenProperties is a stealth-only field; default it so the emitted
    # entry validates against the shared schema.
    flat_log_settings.setdefault("overwrittenProperties", [])
    return {
        "object": node["constructorName"],
        "instrumentedName": node["instrumentedName"],
        "depth": 0,
        "logSettings": flat_log_settings,
    }


def legacy_settings_to_stealth(
    legacy_settings: List[Any],
    firefox_binary: Optional[Union[str, Path]] = None,
    capture_universal_prototype_members: bool = False,
) -> Tuple[List[Dict[str, Any]], List[UntranslatedEntry]]:
    """Expand a legacy ``js_instrument_settings`` list into a flat stealth list.

    Parameters
    ----------
    legacy_settings:
        The legacy settings list, in any of the shorthand/collection forms
        ``clean_js_instrumentation_settings`` accepts (strings, collections,
        ``{object: {...logSettings...}}`` dicts, including ``recursive: true``).
    firefox_binary:
        Path to the Firefox binary to drive the walk. Defaults to
        ``get_firefox_binary_path()`` (``FIREFOX_BINARY`` env var or the bundled
        ``firefox-bin``).
    capture_universal_prototype_members:
        Opt-in flag, **OFF by default**. When ``False`` (the default), inherited
        METHODS owned by a universal prototype (``Object.prototype``,
        ``Function.prototype``, ``Array.prototype`` — ``toString``, ``valueOf``,
        ``hasOwnProperty``, …) are surfaced as :class:`UntranslatedEntry` and NOT
        instrumented. When ``True``, those universal methods are instead captured
        via the same interface-attributed shared-prototype mechanism used for real
        interfaces: a single ``{object: "Object"/"Function"/"Array", …}`` entry is
        emitted carrying ``receiverInterfaces`` covering every leaf interface that
        reached the member.

        .. warning::
           This instruments BASE-PROTOTYPE methods such as
           ``Object.prototype.toString``. Because virtually every object on a page
           inherits from these prototypes, the wrapper fires on EVERY object's
           ``toString()`` / ``valueOf()`` / … call across the whole page — you are
           wrapping every ``toString``. That is a very high-overhead, very-high-
           volume capture for essentially zero tracking signal, and it is rarely
           what you want. Enable it ONLY when you specifically need strict parity
           with legacy ``recursive`` instrumentation (which walked the full
           prototype chain and so did hook these). Non-method universal members
           (accessors) stay :class:`UntranslatedEntry` regardless of this flag,
           because the receiver-interface filter only applies to methods at call
           time.

    Returns
    -------
    (stealth_settings, untranslated):
        ``stealth_settings`` is the flat, non-recursive list ready for
        ``browser_params.stealth_js_instrument_settings``. It includes
        interface-attributed shared-prototype entries (see the module docstring):
        inherited members owned by a real global interface prototype (e.g.
        ``EventTarget.prototype.addEventListener``) become a single entry carrying
        ``receiverInterfaces``. ``untranslated`` is the second element: the legacy
        members NOT representable in the stealth config, each surfaced as an
        :class:`UntranslatedEntry` with a source-grounded reason — so nothing is
        dropped silently. The three untranslatable classes (see the module
        docstring) are:

        * **untranslatable node** — ``constructor.name`` is ``Object``/``Array``/
          falsy, so the whole node has no global interface prototype to hook;
        * **universal-prototype inherited member** — an inherited member owned by
          ``Object``/``Function``/``Array`` ``.prototype`` (``toString``,
          ``valueOf``, …); by default left uninstrumented because hooking it would
          fire on virtually every receiver. Pass
          ``capture_universal_prototype_members=True`` to instead capture the
          METHOD members here via a shared-prototype entry (accessors stay
          untranslated) — see that parameter's warning;
        * **resolution failure** — the legacy ``object`` string did not ``eval``
          to a live node.
    """
    if firefox_binary is None:
        firefox_binary = get_firefox_binary_path()

    # Step A: expand shorthand/collections to full legacy entries
    # {object, instrumentedName, logSettings}.
    cleaned = clean_js_instrumentation_settings(legacy_settings)

    # ``preventSets`` is deliberately NOT carried over to the swept stealth config.
    # Unlike ``recursive`` (which stealth CANNOT honour), stealth can technically
    # implement preventSets — but doing so is measurement-distorting rather than
    # impossible: blocking a page's writes to an instrumented property suppresses
    # behaviour the measurement is meant to OBSERVE (e.g. a polyfill overwriting a
    # native API), so the recorded data no longer reflects what the page actually
    # did. The sweep therefore drops it (forced off in ``_stealth_entry_from_node``)
    # and warns once, naming the legacy paths that requested it, so the researcher
    # knows their captured behaviour is unmodified rather than write-blocked.
    prevent_sets_paths = sorted(
        entry["instrumentedName"]
        for entry in cleaned
        if entry.get("logSettings", {}).get("preventSets")
    )
    if prevent_sets_paths:
        logger.warning(
            "stealth sweep: dropping preventSets (no longer supported) requested "
            "by %d legacy path(s): %s. Blocking page writes distorts the measured "
            "behaviour, so stealth observes the page's real writes instead.",
            len(prevent_sets_paths),
            ", ".join(prevent_sets_paths),
        )

    # Map instrumentedName -> the legacy logSettings of the TOP-LEVEL entry that
    # reached it, so non-recursively-reached children inherit their parent's flags
    # (logCallStack, logFunctionsAsStrings, ...). The walker keys nodes by
    # instrumentedName; a child's path is prefixed by its root's instrumentedName.
    cleaned_by_name = {entry["instrumentedName"]: entry for entry in cleaned}

    # Step B/C: drive a clean Firefox and replay the legacy descent.
    driver = _launch_browser(firefox_binary)
    try:
        driver.get("about:blank")
        raw = driver.execute_script(_WALKER_JS, cleaned)
    finally:
        driver.quit()

    result = json.loads(raw)

    # Step D/E: assemble stealth entries; collect untranslated members.
    stealth_settings: List[Dict[str, Any]] = []
    untranslated: List[UntranslatedEntry] = []

    # Resolution failures: a legacy object string that did not eval to a live
    # node. Surfaced as untranslated (symmetric with the other classes) so the
    # caller — and the CLI exit code — can see the translation was not complete.
    for err in result["errors"]:
        untranslated.append(
            UntranslatedEntry(
                path=err["object"],
                reason=(
                    "could not be resolved (eval of the legacy object string "
                    f"failed: {err['error']}); not instrumented under stealth"
                ),
            )
        )

    # Interface-attributed shared-prototype capture (B′). An inherited member
    # reached from a REAL-interface shared prototype (e.g.
    # ``EventTarget.prototype.addEventListener``) is instrumented ONCE on that
    # shared prototype, recording the call only when its receiver interface is one
    # of the leaf interfaces that reached it. Aggregate, across all reached nodes,
    # per (owner interface, member): the set of leaf interfaces whose receivers
    # should be recorded. ``shared[(owner, member)]`` → set of leaf interface
    # names → becomes ``receiverInterfaces`` on the emitted shared-prototype
    # entry.
    shared: Dict[Tuple[str, str], "set[str]"] = {}
    # Preserve a stable order of (owner, member) first-seen for deterministic
    # output independent of dict iteration.
    shared_order: List[Tuple[str, str]] = []

    for node in result["reached"]:
        name = node["instrumentedName"]
        ctor = node["constructorName"]
        if not ctor or ctor in UNTRANSLATABLE_CONSTRUCTORS:
            # The whole node has no global interface prototype to hook.
            untranslated.append(
                UntranslatedEntry(
                    path=name,
                    reason=(
                        f"constructor is {ctor!r} (Object/Array/unknown); no "
                        "global interface prototype for stealth to hook, so the "
                        "node cannot be expressed as a stealth entry"
                    ),
                )
            )
            continue
        # Inherit the logSettings of the root entry whose path is the prefix of
        # this node's path (the longest matching root). The walker prefixes child
        # paths with the root's instrumentedName.
        root = cleaned_by_name.get(name)
        if root is None:
            root = _root_for(name, cleaned_by_name)
        log_settings = root["logSettings"] if root else {}
        leaf_entry = _stealth_entry_from_node(node, log_settings)
        stealth_settings.append(leaf_entry)

        # Inherited-chain members: legacy instruments node.propertyNames (own +
        # the ENTIRE prototype chain, getPropertyNames); the emitted leaf stealth
        # entry (depth 0) covers only node.stealthOwnNames (the resolved
        # prototype's OWN names). The DIFFERENCE is the inherited members legacy
        # covers but stealth's leaf entry does not. We split them:
        #   * a METHOD owned by a REAL global interface prototype →
        #     interface-attributed shared-prototype capture: aggregate
        #     (owner, member) → leaf ctor, emitted as a shared-prototype entry
        #     with receiverInterfaces (filtered+attributed at call time).
        #   * everything else (members owned by a UNIVERSAL prototype, members of
        #     unknown ownership, OR non-method members — inherited accessors/data
        #     properties, whose call-time receiver cannot be filtered) →
        #     surfaced as untranslated.
        #
        # Non-existing properties (nonExistingPropertiesToInstrument) are absent
        # from the live prototype chain BY DESIGN, so the walk reports owner=None
        # for them. But they are NOT a coverage gap: the emitted leaf entry carries
        # the same nonExistingPropertiesToInstrument, and the stealth instrument
        # synthesizes a native-looking accessor for each (proven by
        # test_non_existing_property_captured_and_native). Surfacing them as
        # untranslated would double-classify a captured member as uncovered and so
        # lie in the honesty report — exclude them from the absent-member branch.
        #
        # Scope the suppression to the non-existing set THIS node's own leaf entry
        # will synthesize (leaf_entry's nonExistingPropertiesToInstrument), NOT a
        # raw root-level set. Both currently coincide, but reading the per-node leaf
        # entry keeps the suppression node-local: a genuinely-absent inherited
        # member of one node can never be silently swallowed by a non-existing name
        # that belongs only to a different (e.g. parent/sibling) node's entry.
        non_existing_props = set(
            leaf_entry["logSettings"].get("nonExistingPropertiesToInstrument", [])
        )
        for member, owner, real_interface, is_function in _inherited_members_of_node(
            node
        ):
            is_universal = owner in UNIVERSAL_PROTOTYPE_CONSTRUCTORS
            if owner is None and member in non_existing_props:
                # Intentionally instrumented as a non-existing property despite
                # being absent from the live chain; the leaf entry captures it.
                continue
            if is_function and real_interface and owner and not is_universal:
                # Real global-interface method (e.g. EventTarget.addEventListener)
                # → interface-attributed shared-prototype capture, in BOTH flag
                # states. A method owned by a UNIVERSAL prototype
                # (Object/Function/Array.prototype) is excluded here by ``not
                # is_universal`` — all three universal constructors fall through to
                # the flag-gated branch below, so Function.prototype methods
                # (``call``/``apply``/``bind``) are governed by
                # capture_universal_prototype_members exactly like Object/Array
                # rather than being silently captured regardless of the flag.
                key = (owner, member)
                if key not in shared:
                    shared[key] = set()
                    shared_order.append(key)
                shared[key].add(ctor)
            elif (
                capture_universal_prototype_members
                and is_universal
                and is_function
                and real_interface
                and owner
            ):
                # Opt-in (OFF by default): route a METHOD owned by a universal
                # prototype (Object/Function/Array.prototype — toString, valueOf,
                # hasOwnProperty, …) into the SAME interface-attributed
                # shared-prototype capture path used for real interfaces. The
                # member is hooked ONCE on the universal prototype (object=owner,
                # which the stealth instrument resolves via
                # ``wrappedJSObject["Object"|"Function"|"Array"].prototype``) and,
                # at call time, the receiver-interface filter records only the leaf
                # interfaces that reached it. This restores strict legacy-recursive
                # parity for universal methods at the cost of wrapping a base
                # prototype method that fires on virtually every receiver page-wide
                # (see the warning on ``capture_universal_prototype_members``).
                # ``real_interface`` is required so we only attempt this for a
                # universal owner whose prototype the stealth instrument can
                # actually resolve (``window[owner].prototype`` matched in the
                # walk); for a universal owner the bare global name IS the hookable
                # prototype, so all three (Object/Function/Array) route here.
                # Non-method universal members (accessors) cannot be filtered by
                # receiver at call time and stay untranslated regardless of the
                # flag.
                key = (owner, member)
                if key not in shared:
                    shared[key] = set()
                    shared_order.append(key)
                shared[key].add(ctor)
            elif real_interface and owner and not is_universal:
                # Inherited accessor/data member on a real interface prototype.
                # The receiver-interface filter only applies to methods (call
                # time), so we cannot attribute this without instrumenting the
                # shared accessor for every receiver — surface it as untranslated.
                untranslated.append(
                    UntranslatedEntry(
                        path=f"{name}.{member}",
                        reason=(
                            f"inherited (non-method) member of {owner!r}.prototype; "
                            "not instrumented (interface-attributed shared-prototype "
                            "capture filters by receiver at CALL time and so applies "
                            "to methods only, not accessor/data members)"
                        ),
                    )
                )
            elif owner is None:
                # The member was requested by legacy but could not be located on
                # the object's live prototype chain (no owning prototype found in
                # the walk). It is genuinely absent from the live object — not an
                # inherited member of any prototype — so stealth has nothing to
                # hook for it.
                untranslated.append(
                    UntranslatedEntry(
                        path=f"{name}.{member}",
                        reason=(
                            "not present on the live object's prototype chain "
                            "(no owning prototype found in the walk); the member "
                            "is absent from the object, so stealth has nothing to "
                            "instrument"
                        ),
                    )
                )
            else:
                untranslated.append(
                    UntranslatedEntry(
                        path=f"{name}.{member}",
                        reason=(
                            f"inherited from {owner!r} (a universal/unknown "
                            f"prototype, not a hookable global interface); not "
                            "instrumented (instrumenting a universal-prototype "
                            "member would fire on virtually every receiver)"
                        ),
                    )
                )

    # Emit one shared-prototype entry per (owner interface, member), instrumenting
    # the member once on the owner's prototype and filtering+attributing by
    # receiver interface at call time. receiverInterfaces is the sorted set of leaf
    # interfaces that reached this member, so the content-script filter records a
    # call only when invoked on one of them, under the static symbol
    # "<owner>.<member>" with the receiver interface in the dedicated receiver
    # column.
    stealth_settings.extend(
        _shared_prototype_entries(
            shared, shared_order, cleaned_by_name, result, untranslated
        )
    )

    if untranslated:
        # One-line summary for library callers; the full per-path detail is the
        # returned ``untranslated`` list (and the CLI logs it in full). Logging
        # both the summary here and the full list in ``_main`` would double-print
        # on the CLI, so keep the library-side log terse.
        logger.warning(
            "stealth sweep: %d legacy symbol path(s) are NOT representable in the "
            "generated stealth config; see the returned untranslated list",
            len(untranslated),
        )

    return stealth_settings, untranslated


def _inherited_members_of_node(
    node: Dict[str, Any],
) -> List[Tuple[str, Optional[str], bool, bool]]:
    """The inherited-chain members legacy instruments at a translatable node.

    Legacy covers ``node["propertyNames"]`` (own + entire prototype chain, via
    ``getPropertyNames``). The emitted leaf stealth entry (``depth: 0``) covers
    only ``node["stealthOwnNames"]`` (``Object.getOwnPropertyNames`` of the leaf
    interface's ``.prototype``). Every legacy-covered name NOT in that own set is
    an inherited member the leaf entry misses.

    For each such member, return ``(member, owner, real_interface, is_function)``
    where ``owner`` is the ``constructor.name`` of the prototype that owns it
    (from the walker's live ``inheritedOwners`` map), ``real_interface`` is
    ``True`` iff that prototype is a hookable global interface prototype
    (``EventTarget`` etc., resolved via ``window[owner].prototype``), and
    ``is_function`` is ``True`` iff the member is a plain method (data property
    holding a function) — only methods are interface-attributable, since the
    receiver filter runs at call time. Members whose owner could not be located on
    the live chain are returned with ``(member, None, False, False)`` so the
    caller surfaces them as untranslated.

    Whether an owner is a UNIVERSAL prototype (``Object``/``Function``/``Array``
    ``.prototype``) is decided by the caller from ``owner`` against
    ``UNIVERSAL_PROTOTYPE_CONSTRUCTORS`` — not by object identity in the walk: the
    walk runs across the content-script/page Xray boundary, where the page's
    ``Object.prototype`` and the content script's ``Object.prototype`` are
    DISTINCT objects, so an identity check is unreliable. ``window[owner].prototype
    === proto`` (the ``real_interface`` test) DOES hold for the universal owners
    because ``window`` resolves the page realm, which is exactly why
    ``{object: "Object"}`` resolves to the right prototype at instrument time.
    """
    own = node.get("stealthOwnNames")
    if own is None:
        # The constructor did not resolve to a hookable prototype in the walk
        # environment; the node-level untranslatable entry (handled by the
        # caller) already records that the whole node is uncovered.
        return []
    own_set = set(own)
    # owner/real_interface/is_function per inherited member, from the live walk.
    owners_by_member: Dict[str, Tuple[Optional[str], bool, bool]] = {
        o["member"]: (
            o.get("owner"),
            bool(o.get("realInterface")),
            bool(o.get("isFunction")),
        )
        for o in node.get("inheritedOwners", [])
    }
    out: List[Tuple[str, Optional[str], bool, bool]] = []
    for prop in node["propertyNames"]:
        if prop in own_set:
            continue
        owner, real_interface, is_function = owners_by_member.get(
            prop, (None, False, False)
        )
        out.append((prop, owner, real_interface, is_function))
    return out


def _shared_prototype_entries(
    shared: Dict[Tuple[str, str], "set[str]"],
    shared_order: List[Tuple[str, str]],
    cleaned_by_name: Dict[str, Dict[str, Any]],
    walk_result: Dict[str, Any],
    untranslated: List[UntranslatedEntry],
) -> List[Dict[str, Any]]:
    """Build the interface-attributed shared-prototype stealth entries.

    ``shared`` maps ``(owner_interface, member)`` to the set of LEAF interface
    names whose receivers should be recorded for that member. All members owned by
    one prototype are emitted as a SINGLE entry per owner:

        {object: owner, instrumentedName: owner, depth: 0,
         logSettings: {propertiesToInstrument: [member1, member2, ...],
                       recursive: False,
                       receiverInterfaces: [sorted leaf interfaces], ...}}

    One entry per owner is REQUIRED for correctness, not just tidiness. The stealth
    instrument gates each instrumentation collection element on
    ``needsWrapper(prototypeObject)`` (a WeakSet keyed on the prototype object, see
    ``startInstrument`` in ``Extension/src/stealth/instrument.ts``). Emitting one
    entry PER (owner, member) produces several entries all resolving to the SAME
    owner prototype; the first wraps it and the rest are silently skipped — so only
    one member per owner would actually be hooked. Consolidating every member of an
    owner into one entry means a single ``needsWrapper(owner.prototype)`` covers
    all of them.

    The stealth instrument hooks each ``owner.prototype.member`` once and, at call
    time, records the call only when the receiver's interface is in
    ``receiverInterfaces``, under the static symbol ``<owner>.<member>`` with the
    concrete receiver interface in the dedicated ``receiver`` column (see
    ``Extension/src/stealth/instrument.ts``). Attribution is interface-level, not
    instance-level, by design.

    ``receiverInterfaces`` is carried at the ENTRY (owner) level, so it applies to
    every member of that owner. When a config requests the FULL inherited set of a
    prototype (the ``propertiesToInstrument: []`` / recursive case), prototype
    inheritance is all-or-nothing — any leaf inheriting ``owner.prototype``
    inherits ALL its members — so every member is reached by the same leaf set and
    the per-owner ``receiverInterfaces`` is exact.

    A NARROW legacy config, however, records only the members it explicitly
    requested (``_inherited_members_of_node`` iterates the requested
    ``propertyNames``, not the owner's full member set). Two leaves that share one
    prototype can therefore request DISJOINT members — e.g.
    ``[{"window.document": ["addEventListener"]}, {"window.document.body":
    ["dispatchEvent"]}]`` yields ``(EventTarget, addEventListener) -> {HTMLDocument}``
    and ``(EventTarget, dispatchEvent) -> {HTMLBodyElement}``. The members'
    leaf-sets legitimately differ, so a single per-owner entry cannot filter each
    member by its own reaching interface (the stealth instrument applies
    ``receiverInterfaces`` to the whole entry, and the per-prototype
    ``needsWrapper`` gate forbids a second entry on the same prototype). The
    consolidation therefore UNIONS the members' leaf-sets into one
    ``receiverInterfaces`` so nothing requested is dropped, and — when the per-member
    sets differ — records an honest UntranslatedEntry note for the resulting
    interface-level OVER-capture (e.g. ``addEventListener`` will now also be recorded on
    ``HTMLBodyElement``). This is the same superset-not-subset direction the module
    already takes for object-valued gets, and keeps the contract "nothing is
    dropped silently" intact instead of crashing a legitimate narrow config.

    ``logSettings`` flags (logCallStack, logFunctionsAsStrings, …) are inherited
    from the legacy root entry that reached the member, so per-study flags carry
    over. When several roots reach the same shared member their flags are OR-ed
    conservatively (a member is recorded with a stack if ANY reaching root asked
    for one).
    """
    # Map each leaf interface back to a reaching root's logSettings so the shared
    # entry inherits sensible flags. Build leaf-interface → list of roots.
    leaf_to_roots: Dict[str, List[Dict[str, Any]]] = {}
    for node in walk_result["reached"]:
        ctor = node.get("constructorName")
        if not ctor:
            continue
        name = node["instrumentedName"]
        root = cleaned_by_name.get(name) or _root_for(name, cleaned_by_name)
        if root is None:
            continue
        leaf_to_roots.setdefault(ctor, []).append(root)

    # Group members by owner, preserving first-seen order for both owners and the
    # members within each owner, so the consolidated output is deterministic.
    owner_order: List[str] = []
    members_by_owner: Dict[str, List[str]] = {}
    for owner, member in shared_order:
        if owner not in members_by_owner:
            members_by_owner[owner] = []
            owner_order.append(owner)
        members_by_owner[owner].append(member)

    entries: List[Dict[str, Any]] = []
    for owner in owner_order:
        members = members_by_owner[owner]

        # receiverInterfaces is carried once per ENTRY (owner). For a full-chain
        # request every member shares one leaf-set (prototype inheritance is
        # all-or-nothing). A NARROW request can give members DISJOINT leaf-sets,
        # which a single per-owner entry cannot filter per-member — so union the
        # sets (capture everything requested, never crash) and, when they differ,
        # record an honest UntranslatedEntry note for the interface-level over-capture.
        leaf_sets = {member: shared[(owner, member)] for member in members}
        distinct = {frozenset(s) for s in leaf_sets.values()}
        union: "set[str]" = set()
        for s in leaf_sets.values():
            union |= s
        leaves = sorted(union)
        if len(distinct) != 1:
            detail = ", ".join(f"{m}->{sorted(leaf_sets[m])}" for m in members)
            untranslated.append(
                UntranslatedEntry(
                    path=f"{owner}.<shared-prototype>",
                    reason=(
                        "Your legacy config asked to instrument different members "
                        f"on objects that share the {owner} prototype ({detail}). "
                        "The stealth instrument can't instrument them separately, "
                        f"so it instruments all of them together ({leaves}). Every "
                        "member you asked for is still captured — but some calls "
                        "may also be recorded under an interface that only another "
                        "member needed (over-capture). To recover exactly the "
                        "members you requested, filter the results by (symbol, "
                        "receiver) in post-processing."
                    ),
                )
            )
        # OR the boolean flags across every root that reached any of these leaves.
        log_call_stack = False
        log_functions_as_strings = False
        for leaf in leaves:
            for root in leaf_to_roots.get(leaf, []):
                ls = root.get("logSettings", {})
                log_call_stack = log_call_stack or bool(ls.get("logCallStack"))
                log_functions_as_strings = log_functions_as_strings or bool(
                    ls.get("logFunctionsAsStrings")
                )
        entries.append(
            {
                "object": owner,
                "instrumentedName": owner,
                "depth": 0,
                "logSettings": {
                    "propertiesToInstrument": list(members),
                    "nonExistingPropertiesToInstrument": [],
                    "excludedProperties": [],
                    "overwrittenProperties": [],
                    "logCallStack": log_call_stack,
                    "logFunctionsAsStrings": log_functions_as_strings,
                    "logFunctionGets": False,
                    "preventSets": False,
                    "recursive": False,
                    # depth is inert with recursive=False (no child walk); carried
                    # only to match the legacy logSettings shape the schema expects.
                    "depth": 5,
                    "receiverInterfaces": leaves,
                },
            }
        )
    return entries


def _root_for(
    name: str, cleaned_by_name: Dict[str, Dict[str, Any]]
) -> Optional[Dict[str, Any]]:
    """Find the root legacy entry whose instrumentedName prefixes ``name``.

    A child reached by recursion has path ``<root>.<prop>[.<prop>...]``; the
    longest matching root supplies the inherited logSettings.
    """
    best: Optional[Dict[str, Any]] = None
    best_len = -1
    for root_name, entry in cleaned_by_name.items():
        if (name == root_name or name.startswith(root_name + ".")) and len(
            root_name
        ) > best_len:
            best = entry
            best_len = len(root_name)
    return best


def _main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m openwpm.utilities.js_settings_migrator",
        description=(
            "Expand a legacy js_instrument_settings config (including recursive "
            "entries) into an equivalent flat, non-recursive "
            "stealth_js_instrument_settings config."
        ),
    )
    parser.add_argument(
        "config",
        type=Path,
        help=(
            "Path to a JSON file holding the legacy settings list (the same value "
            "you would assign to browser_params.js_instrument_settings)."
        ),
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=None,
        help="Write the generated stealth settings here instead of stdout.",
    )
    parser.add_argument(
        "--firefox-binary",
        type=Path,
        default=None,
        help=(
            "Firefox binary to drive the sweep. Defaults to the FIREFOX_BINARY "
            "env var or the bundled firefox-bin."
        ),
    )
    parser.add_argument(
        "--capture-universal-members",
        action="store_true",
        help=(
            "OFF by default. Also capture inherited METHODS owned by a universal "
            "base prototype (Object/Function/Array.prototype — toString, valueOf, "
            "hasOwnProperty, ...) as interface-attributed shared-prototype entries, "
            "instead of surfacing them as untranslated. WARNING: this wraps base-"
            "prototype methods that fire on EVERY object on the page (you are "
            "wrapping every toString) — very high overhead and volume for "
            "essentially zero tracking signal. Enable ONLY for strict parity with "
            "legacy 'recursive' instrumentation. Universal accessors stay "
            "untranslated regardless."
        ),
    )
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    legacy_settings = json.loads(args.config.read_text())
    stealth_settings, untranslated = legacy_settings_to_stealth(
        legacy_settings,
        args.firefox_binary,
        capture_universal_prototype_members=args.capture_universal_members,
    )

    output = json.dumps(stealth_settings, indent=2)
    if args.output is not None:
        args.output.write_text(output + "\n")
        logger.info(
            "wrote %d stealth entries to %s", len(stealth_settings), args.output
        )
    else:
        print(output)

    if untranslated:
        # Symmetric honesty: any legacy symbol path NOT representable in the swept
        # config — untranslatable nodes, inherited-chain members, AND resolution
        # failures — is reported, and the CLI exits non-zero so an automated
        # pipeline cannot mistake an incomplete translation for a clean one.
        logger.warning(
            "%d legacy symbol path(s) are NOT representable in the generated "
            "stealth config:\n%s",
            len(untranslated),
            "\n".join("  - " + str(r) for r in sorted(untranslated, key=str)),
        )
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(_main())
