// Claude Code-only (CLI >= 2.1.287; earlier CLIs load it only with CLAUDE_CODE_ENABLE_FUNCTION_HOOKS=1).
// Constant text: identical bytes in every conversation keep the prompt cache stable.
// Pointers, not rules: the named files and the plugin's hooks stay the authority.
const NAME = "graphPowersRouting";
const TEXT = [
  "Graph Powers is installed. In the main session, take the one existing command or skill whose description fits the request, sized by the plugin's references/shared/020-complexity-routing.md (L1-L2: edit directly; in doubt, take the lower tier).",
  "When asked to do the work, carry it to its acceptance criteria and verify it; a plan alone is the deliverable only when a plan was asked for.",
  "Add no workflow, review or agent the tier does not call for.",
  "A subagent or teammate follows the task it was given.",
  "Approval gates, the plugin's references/execution-floor.md and its hooks remain the authority; this block adds no rule.",
].join("\n");

export function register(on) {
  on("prompt.context", async ($, e, next) => {
    const context = await next(e);
    if (context.blocks.some((block) => block.name === NAME)) return context;
    return { ...context, blocks: [...context.blocks, { name: NAME, text: TEXT }] };
  });
}
