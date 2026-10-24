/**
 * Product Return Risk Intelligence - Client Interaction Script
 * Minimal vanilla JavaScript for dynamic category filtering, demo presets, and form UX.
 */

document.addEventListener("DOMContentLoaded", () => {
  initCategoryFilter();
  initPresetButtons();
  initFormSubmitState();
});

/**
 * Dynamically filter Sub-Category options based on selected Product Category.
 */
function initCategoryFilter() {
  const categorySelect = document.getElementById("product_category");
  const subCategorySelect = document.getElementById("sub_category");

  if (!categorySelect || !subCategorySelect) return;

  // Read taxonomy from embedded data attribute if present, or fallback
  const taxonomyScript = document.getElementById("taxonomy-data");
  let taxonomy = {};
  if (taxonomyScript) {
    try {
      taxonomy = JSON.parse(taxonomyScript.textContent);
    } catch (e) {
      console.warn("Could not parse taxonomy JSON", e);
    }
  }

  function updateSubCategories() {
    const selectedCat = categorySelect.value;
    const currentSub = subCategorySelect.value;
    const allowedSubs = taxonomy[selectedCat] || [];

    if (allowedSubs.length > 0) {
      subCategorySelect.innerHTML = "";
      allowedSubs.forEach((sub) => {
        const opt = document.createElement("option");
        opt.value = sub;
        opt.textContent = sub;
        if (sub === currentSub) {
          opt.selected = true;
        }
        subCategorySelect.appendChild(opt);
      });
      // If currentSub was not in allowedSubs, pick the first
      if (!allowedSubs.includes(currentSub) && allowedSubs.length > 0) {
        subCategorySelect.value = allowedSubs[0];
      }
    }
  }

  categorySelect.addEventListener("change", updateSubCategories);
}

/**
 * Handle instant loading of realistic demonstration presets.
 */
function initPresetButtons() {
  const presetContainer = document.getElementById("preset-container");
  if (!presetContainer) return;

  const presetsScript = document.getElementById("presets-data");
  let presets = {};
  if (presetsScript) {
    try {
      presets = JSON.parse(presetsScript.textContent);
    } catch (e) {
      console.warn("Could not parse presets JSON", e);
      return;
    }
  }

  const buttons = presetContainer.querySelectorAll(".preset-btn");
  buttons.forEach((btn) => {
    btn.addEventListener("click", () => {
      const presetKey = btn.dataset.preset;
      const data = presets[presetKey];
      if (!data) return;

      // Populate form fields
      for (const [key, value] of Object.entries(data)) {
        const field = document.getElementById(key);
        if (field) {
          field.value = value;
          // Trigger change on category to update dependent subcategory dropdown
          if (key === "product_category") {
            const event = new Event("change");
            field.dispatchEvent(event);
          }
        }
      }

      // Re-set subcategory explicitly after category event has refreshed the options
      if (data.sub_category) {
        const subField = document.getElementById("sub_category");
        if (subField) {
          subField.value = data.sub_category;
        }
      }

      // Subtle visual feedback
      btn.style.borderColor = "var(--accent-primary)";
      setTimeout(() => {
        btn.style.borderColor = "";
      }, 500);
    });
  });
}

/**
 * Prevent duplicate form submissions and display loading indicator.
 */
function initFormSubmitState() {
  const form = document.getElementById("prediction-form");
  const submitBtn = document.getElementById("submit-btn");

  if (!form || !submitBtn) return;

  form.addEventListener("submit", (e) => {
    if (form.checkValidity()) {
      submitBtn.disabled = true;
      submitBtn.classList.add("submitting");
      submitBtn.innerHTML = `
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="spinning" style="animation: spin 1s linear infinite;">
          <circle cx="12" cy="12" r="10" stroke-opacity="0.25"></circle>
          <path d="M12 2a10 10 0 0 1 10 10"></path>
        </svg>
        Evaluating Return Risk...
      `;
    }
  });
}

// Add simple spinning keyframe animation inline if not present
const style = document.createElement("style");
style.textContent = `@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }`;
document.head.appendChild(style);
