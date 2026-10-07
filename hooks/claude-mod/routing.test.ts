import { expect, test } from "claude-code/testing";

const ENGINE = { name: "claudeMd", text: "Project instructions." };

test("appends one routing block after the engine block, keeping instruction files", async ($, on) => {
  on("prompt.context", ($, e) => ({ blocks: e.blocks }));
  const context = await $.prompt.context({
    blocks: [ENGINE],
    instructionFiles: [
      { path: "/fixture/AGENTS.md", kind: "project", content: "Project instructions." },
    ],
  });
  expect(context.blocks[0]).toEqual(ENGINE);
  expect(context.blocks.map((block) => block.name)).toEqual(["claudeMd", "graphPowersRouting"]);
  expect(context.instructionFiles).toEqual([
    { path: "/fixture/AGENTS.md", kind: "project", content: "Project instructions." },
  ]);
});

test("keeps the routing text byte-identical across conversations", async ($, on) => {
  on("prompt.context", ($, e) => ({ blocks: e.blocks }));
  const first = await $.prompt.context({ blocks: [ENGINE] });
  const second = await $.prompt.context({ blocks: [] });
  const firstRouting = first.blocks.find((block) => block.name === "graphPowersRouting");
  const secondRouting = second.blocks.find((block) => block.name === "graphPowersRouting");
  expect(firstRouting).toBeDefined();
  expect(secondRouting).toBeDefined();
  expect(secondRouting?.text).toBe(firstRouting?.text);
});

test("leaves an existing routing block unchanged without adding a duplicate", async ($, on) => {
  on("prompt.context", ($, e) => ({ blocks: e.blocks }));
  const blocks = [ENGINE, { name: "graphPowersRouting", text: "already composed" }];
  const context = await $.prompt.context({ blocks });
  expect(context.blocks).toEqual(blocks);
  expect(context.blocks.filter((block) => block.name === "graphPowersRouting").length).toBe(1);
});

test("names both routing authorities instead of copying their rules", async ($, on) => {
  on("prompt.context", ($, e) => ({ blocks: e.blocks }));
  const context = await $.prompt.context({ blocks: [] });
  const routing = context.blocks.find((block) => block.name === "graphPowersRouting");
  expect(routing?.text).toContain("references/shared/020-complexity-routing.md");
  expect(routing?.text).toContain("references/execution-floor.md");
});

test("passes a typed prompt through unchanged", async ($, on) => {
  on("prompt.submit", ($, e) => ({ text: e.text }));
  const submitted = await $.prompt.submit({ text: "fix the typo in README" });
  expect(submitted.text).toBe("fix the typo in README");
});
