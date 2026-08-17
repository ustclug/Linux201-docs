const detailsTargetClass = "admonition-anchor-target";

const setDetailsTarget = (details) => {
  document
    .querySelectorAll(`details.${detailsTargetClass}`)
    .forEach((element) => element.classList.remove(detailsTargetClass));

  details?.classList.add(detailsTargetClass);
};

const syncDetailsTarget = () => {
  let anchorId;

  try {
    anchorId = decodeURIComponent(window.location.hash.slice(1));
  } catch {
    setDetailsTarget();
    return;
  }

  const target = document.getElementById(anchorId);
  setDetailsTarget(target?.tagName === "DETAILS" ? target : undefined);
};

document.addEventListener("click", (event) => {
  const summary = event.target.closest("summary");
  const details = summary?.parentElement;

  if (
    details?.tagName !== "DETAILS" ||
    !details.id ||
    !details.closest(".md-typeset")
  ) {
    return;
  }

  const permalink = event.target.closest("a.headerlink");
  const interactive = event.target.closest(
    "a, button, input, select, textarea"
  );

  if (interactive && interactive !== permalink) {
    return;
  }

  if (permalink) {
    if (
      event.button !== 0 ||
      event.altKey ||
      event.ctrlKey ||
      event.metaKey ||
      event.shiftKey
    ) {
      return;
    }

    event.preventDefault();
    details.open = !details.open;
  }

  const url = new URL(window.location.href);
  url.hash = details.id;
  window.history.replaceState(window.history.state, "", url);
  setDetailsTarget(details);
});

window.addEventListener("hashchange", syncDetailsTarget);
window.addEventListener("popstate", syncDetailsTarget);
syncDetailsTarget();
