// MkDocs Material 9.7.x uses the nearest ancestor ID as a code block ID.
// Multiple code blocks inside an anchored container (such as an admonition)
// therefore receive the same ID and all copy buttons target the first block.
const repairDuplicateCodeCopyTargets = () => {
  const codeBlocks = [...document.querySelectorAll("pre[id]")];
  const idCounts = new Map();

  for (const codeBlock of codeBlocks) {
    idCounts.set(codeBlock.id, (idCounts.get(codeBlock.id) ?? 0) + 1);
  }

  const usedIds = new Set(
    [...document.querySelectorAll("[id]")].map((element) => element.id)
  );
  let sequence = 0;

  for (const codeBlock of codeBlocks) {
    if (idCounts.get(codeBlock.id) === 1) {
      continue;
    }

    const copyButton = codeBlock.querySelector(
      ':scope > .md-code__nav [data-md-type="copy"]'
    );
    if (!copyButton) {
      continue;
    }

    let id;
    do {
      id = `__linux201_code_${sequence++}`;
    } while (usedIds.has(id));

    usedIds.add(id);
    codeBlock.id = id;
    copyButton.dataset.clipboardTarget = `#${id} > code`;
  }
};

const scheduleCodeCopyRepair = () => {
  requestAnimationFrame(repairDuplicateCodeCopyTargets);
};

if (typeof document$ !== "undefined") {
  document$.subscribe(scheduleCodeCopyRepair);
} else if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", scheduleCodeCopyRepair);
} else {
  scheduleCodeCopyRepair();
}
