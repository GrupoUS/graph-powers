/** Controller integration: real ledger/checks, fake provider and native dispatch only. */
import assert from "node:assert/strict";
import { mkdtempSync, mkdirSync, readFileSync, writeFileSync, rmSync, unlinkSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { spawnSync } from "node:child_process";
import { coordinate } from "../codex/coordinate.mjs";

const actor = { requesterRole: "parent", depth: 0 };
const capabilities = ["high", "medium"].map((reasoningEffort) => ({
  model: reasoningEffort === "high" ? "gpt-6-astra" : "gpt-6-luna",
  reasoningEffort,
  status: "SUPPORTED",
  evidence: "synthetic account capability fixture",
}));
function fixture(name) {
  const root = mkdtempSync(join(tmpdir(), "gp-coordinate-"));
  mkdirSync(join(root, ".graph-powers"));
  writeFileSync(
    join(root, ".graph-powers/config.json"),
    JSON.stringify({ codex: { evaluation: { enabled: true } } }),
  );
  assert.equal(spawnSync("git", ["init", "-q"], { cwd: root }).status, 0);
  const settings = { projectDir: root, sessionId: name, env: { AI_GATEWAY_API_KEY: "fixture" } };
  const input = {
    ...actor,
    request: "Produce the requested verified result",
    taskId: "T1",
    owns: ["result.txt"],
    checks: [
      {
        name: "result",
        argv: [
          process.execPath,
          "-e",
          'if(require("node:fs").readFileSync("result.txt","utf8")!=="ok")process.exit(1)',
        ],
      },
    ],
  };
  return { root, settings, input, cleanup: () => rmSync(root, { recursive: true, force: true }) };
}
const handoff = () => ({
  status: "COMPLETED",
  confidence: 4,
  artifacts: [{ path: "result.txt", lines: "1", action: "modified" }],
  qualityGates: [{ name: "result", status: "PASS", evidence: "worker claim, main must verify" }],
  decisions: [],
  risks: [],
  nextAgent: "NONE",
  resumeHint: "Verify result",
});
function provider(choose, count) {
  return async (_url, init) => {
    count.calls++;
    const body = JSON.parse(init.body);
    const ids = Object.keys(body.questions.route.criteria);
    const choice = choose(ids, body);
    assert(ids.includes(choice));
    return new Response(
      JSON.stringify({
        model: "typesafe-ai/jev",
        answers: {
          route: {
            type: "choice",
            choice,
            probabilities: Object.fromEntries(ids.map((id) => [id, id === choice ? 1 : 0])),
          },
        },
      }),
      { status: 200 },
    );
  };
}

const cycleFixture = fixture("cycle");
try {
  const start = await coordinate("init", cycleFixture.input, cycleFixture.settings);
  assert.equal(start.status, "READY");
  assert(start.contextPath && readFileSync(join(cycleFixture.root, start.contextPath), "utf8"));
  const count = { calls: 0 };
  const settings = {
    ...cycleFixture.settings,
    fetchImpl: provider(
      (ids) => (ids.includes("finish") ? "finish" : "agent:frontend-specialist"),
      count,
    ),
  };
  const request = {
    ...actor,
    capabilities,
    allowed: ["agent:debugger", "agent:frontend-specialist"],
  };
  const action = await coordinate("next", request, settings);
  assert.equal(action.status, "PENDING");
  assert.equal(action.executionAuthorized, true);
  assert.equal(action.action.candidate.role, "frontend-specialist");
  assert(
    action.handoff.prompt.includes("## TASK") && action.handoff.prompt.includes("## RETURN FORMAT"),
  );
  assert(
    action.handoff.methods.some(
      (method) => method.name === "debugger" && method.content.includes("# Debugger"),
    ),
  );
  assert.equal(count.calls, 1, "same-model specialists must still reach Jev");
  const pending = await coordinate("next", request, settings);
  assert.equal(pending.executionAuthorized, false);
  assert.equal(count.calls, 1);
  // Simulates the parent's native dispatch callback using the prepared handoff.
  writeFileSync(join(cycleFixture.root, "result.txt"), "ok");
  const returned = await coordinate(
    "return",
    { ...actor, ticket: action.action.ticket, handoff: handoff() },
    settings,
  );
  assert.equal(returned.status, "RETURNED");
  assert.equal(returned.handoffs.at(-1).verification.passed, true);
  const finished = await coordinate("next", request, settings);
  assert.equal(finished.status, "COMPLETED");
  assert.equal(finished.executionAuthorized, false);
  const replay = await coordinate("next", request, {
    ...settings,
    env: {},
    fetchImpl: () => {
      throw Error("no network");
    },
  });
  assert.equal(replay.status, "COMPLETED");
  assert.equal(count.calls, 2);
} finally {
  cycleFixture.cleanup();
}

await Promise.all(
  ["failed-check", "outside-owner", "stale", "bad-handoff"].map(async (scenario) => {
    const scenarioFixture = fixture(scenario);
    try {
      await coordinate("init", scenarioFixture.input, scenarioFixture.settings);
      const settings = {
        ...scenarioFixture.settings,
        fetchImpl: provider((ids) => ids[0], { calls: 0 }),
      };
      const request = {
        ...actor,
        capabilities,
        allowed: ["agent:debugger", "agent:frontend-specialist"],
      };
      const action = await coordinate("next", request, settings);
      writeFileSync(
        join(scenarioFixture.root, "result.txt"),
        scenario === "failed-check" ? "bad" : "ok",
      );
      if (scenario === "outside-owner")
        writeFileSync(join(scenarioFixture.root, "unowned.txt"), "not allowed");
      const result = await coordinate(
        "return",
        {
          ...actor,
          ticket: action.action.ticket,
          handoff: scenario === "bad-handoff" ? { status: "COMPLETED" } : handoff(),
        },
        settings,
      );
      if (scenario === "bad-handoff") {
        assert.equal(result.status, "BLOCKED");
        return;
      }
      if (scenario !== "stale") assert.equal(result.handoffs.at(-1).verification.passed, false);
      else writeFileSync(join(scenarioFixture.root, "result.txt"), "changed after proof");
      let finishOffered = false;
      await coordinate("next", request, {
        ...settings,
        fetchImpl: provider(
          (ids) => {
            finishOffered = ids.includes("finish");
            return ids[0];
          },
          { calls: 0 },
        ),
      });
      assert.equal(finishOffered, false, scenario);
    } finally {
      scenarioFixture.cleanup();
    }
  }),
);

await Promise.all(
  ["command:design", "skill:designer", "agent:verification"].map(async (target) => {
    const targetFixture = fixture(target.replace(":", "-"));
    try {
      await coordinate("init", targetFixture.input, targetFixture.settings);
      const action = await coordinate(
        "next",
        { ...actor, capabilities, allowed: [target, "agent:frontend-specialist"] },
        { ...targetFixture.settings, fetchImpl: provider(() => target, { calls: 0 }) },
      );
      assert.equal(action.executionAuthorized, true);
      assert(action.handoff.methods.length > 0);
      if (target === "agent:verification") {
        assert(action.handoff.methods.some((item) => item.name === "webapp-testing"));
        assert(action.handoff.prompt.includes("browser"));
      } else assert.equal(action.action.candidate.role, "main");
    } finally {
      targetFixture.cleanup();
    }
  }),
);
const fRace = fixture("decision-race");
try {
  await coordinate("init", fRace.input, fRace.settings);
  const request = {
    ...actor,
    capabilities,
    allowed: ["agent:debugger", "agent:frontend-specialist"],
  };
  const action = await coordinate("next", request, {
    ...fRace.settings,
    fetchImpl: provider((ids) => ids[0], { calls: 0 }),
  });
  writeFileSync(join(fRace.root, "result.txt"), "ok");
  const returned = handoff();
  returned.decisions = [{ what: "UI flow verified", why: "browser evidence exists" }];
  returned.risks = [{ desc: "remaining keyboard check", mitigation: "verify focus" }];
  returned.resumeHint = "Review the keyboard result before finishing";
  await coordinate(
    "return",
    { ...actor, ticket: action.action.ticket, handoff: returned },
    fRace.settings,
  );
  let feedback;
  const stale = await coordinate("next", request, {
    ...fRace.settings,
    fetchImpl: provider(
      (ids, body) => {
        feedback = body.state.verification;
        writeFileSync(join(fRace.root, "result.txt"), "changed during request");
        return "finish";
      },
      { calls: 0 },
    ),
  });
  assert.equal(feedback.decisions[0].what, returned.decisions[0].what);
  assert.equal(feedback.risks[0].desc, returned.risks[0].desc);
  assert.equal(feedback.resumeHint, returned.resumeHint);
  assert.equal(stale.status, "BLOCKED");
  assert.equal(stale.reason, "STALE_DECISION");
  const status = await coordinate("status", actor, fRace.settings);
  assert.equal(status.status, "RETURNED");
  // A changed snapshot gets a new bounded decision key, without replaying stale finish.
  const corrected = await coordinate("next", request, {
    ...fRace.settings,
    fetchImpl: provider(
      (ids) => {
        assert(!ids.includes("finish"));
        return ids[0];
      },
      { calls: 0 },
    ),
  });
  assert.equal(corrected.status, "PENDING");
} finally {
  fRace.cleanup();
}

const fRemoved = fixture("removed-artifact");
try {
  writeFileSync(join(fRemoved.root, "result.txt"), "old");
  fRemoved.input.checks = [
    {
      name: "removed",
      argv: [
        process.execPath,
        "-e",
        'if(require("node:fs").existsSync("result.txt"))process.exit(1)',
      ],
    },
  ];
  await coordinate("init", fRemoved.input, fRemoved.settings);
  const request = {
    ...actor,
    capabilities,
    allowed: ["agent:debugger", "agent:frontend-specialist"],
  };
  const settings = {
    ...fRemoved.settings,
    fetchImpl: provider((ids) => (ids.includes("finish") ? "finish" : ids[0]), { calls: 0 }),
  };
  const action = await coordinate("next", request, settings);
  unlinkSync(join(fRemoved.root, "result.txt"));
  const result = handoff();
  result.artifacts[0].action = "removed";
  result.qualityGates = [{ name: "removed", status: "PASS", evidence: "absence" }];
  const returned = await coordinate(
    "return",
    { ...actor, ticket: action.action.ticket, handoff: result },
    settings,
  );
  assert.equal(returned.status, "RETURNED");
  assert.equal(returned.handoffs.at(-1).verification.artifacts[0].sha256, "MISSING");
  assert.equal((await coordinate("next", request, settings)).status, "COMPLETED");
} finally {
  fRemoved.cleanup();
}

async function checkLinkedPlanScenario(completion) {
  const fPlan = fixture(`linked-${completion}`);
  try {
    const checked = completion !== "pending" ? "x" : " ";
    const plan = `# Plan

**Tier:** L4

## Phase 1 — Work [SEQUENTIAL]

- [${checked}] **T1.1** — Produce result
  Owns: result.txt
  Needs: none
  Acceptance: Result is ok
  Agent: graph-powers:debugger · Skill: none · Effort: mechanical
  TDD: not-applicable (fixture)
  Steps:
    1. Check result
  CHECK: bun check.mjs
  EXPECT: ok
  EVIDENCE: ${completion}

- [${checked}] **G1.1** — Gate
  CHECK: bun check.mjs
  EXPECT: ok
  EVIDENCE: ${completion}
`;
    writeFileSync(join(fPlan.root, "PLAN.md"), plan);
    await coordinate("init", fPlan.input, fPlan.settings);
    const linked = await coordinate("link-plan", { ...actor, planPath: "PLAN.md" }, fPlan.settings);
    assert.equal(linked.context.planPath, "PLAN.md");
    assert.equal(
      (await coordinate("init", fPlan.input, fPlan.settings)).context.planPath,
      "PLAN.md",
    );
    const request = {
      ...actor,
      capabilities,
      allowed: ["agent:debugger", "agent:frontend-specialist"],
    };
    const action = await coordinate("next", request, {
      ...fPlan.settings,
      fetchImpl: provider((ids) => ids[0], { calls: 0 }),
    });
    writeFileSync(join(fPlan.root, "result.txt"), "ok");
    await coordinate(
      "return",
      { ...actor, ticket: action.action.ticket, handoff: handoff() },
      fPlan.settings,
    );
    const result = await coordinate("next", request, {
      ...fPlan.settings,
      fetchImpl: provider(
        (ids) => {
          assert.equal(ids.includes("finish"), completion === "verified");
          return completion === "verified" ? "finish" : ids[0];
        },
        { calls: 0 },
      ),
    });
    assert.equal(result.status, completion === "verified" ? "COMPLETED" : "PENDING");
  } finally {
    fPlan.cleanup();
  }
}

await checkLinkedPlanScenario("pending");
await checkLinkedPlanScenario("todo");
await checkLinkedPlanScenario("verified");

console.log(
  "jev-coordination: routing, methods, handoff, fresh checks, resume and browser lane passed",
);
