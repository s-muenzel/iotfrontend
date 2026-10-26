"use strict";

(function () {
  function schemaFor(form, field) {
    const schemas = JSON.parse(form.dataset.typeSchemas || "{}");
    const selector = document.getElementById(field.dataset.typeSelectorId);
    const selectedType = selector.value;
    return (schemas[selectedType] &&
      schemas[selectedType][field.dataset.parameter]) ||
      { input: "text" };
  }

  function displayValue(canonicalValue, schema) {
    if (schema.input !== "time" || canonicalValue === "") {
      return canonicalValue;
    }

    const totalSeconds = Number(canonicalValue);
    if (!Number.isFinite(totalSeconds) || totalSeconds < 0) {
      return "";
    }
    const hours = Math.floor(totalSeconds / 3600);
    const minutes = Math.floor((totalSeconds % 3600) / 60);
    return String(hours).padStart(2, "0") + ":" +
      String(minutes).padStart(2, "0");
  }

  function canonicalValue(displayedValue, schema) {
    if (schema.input !== "time" || displayedValue === "") {
      return displayedValue;
    }

    const [hours, minutes] = displayedValue.split(":").map(Number);
    return String(hours * 3600 + minutes * 60);
  }

  function updateField(form, field) {
    const schema = schemaFor(form, field);
    const canonical = field.querySelector("[data-canonical-value]");
    const activeLabel = field.querySelector(
      '[data-typed-control="' + schema.input + '"]'
    );

    field.querySelectorAll("[data-typed-control]").forEach(function (label) {
      const active = label === activeLabel;
      label.hidden = !active;
      const input = label.querySelector("[data-value-control]");
      input.disabled = !active || canonical.disabled;
      input.min = schema.min === undefined ? "" : schema.min;
      input.max = schema.max === undefined ? "" : schema.max;
      input.step = schema.step === undefined ? "any" : schema.step;
      if (active) {
        input.value = displayValue(canonical.value, schema);
      }
    });
  }

  function synchronizeField(field) {
    const form = document.getElementById(
      field.querySelector("[data-canonical-value]").getAttribute("form")
    );
    const schema = schemaFor(form, field);
    const activeInput = field.querySelector(
      '[data-typed-control="' + schema.input + '"] [data-value-control]'
    );
    if (activeInput) {
      field.querySelector("[data-canonical-value]").value =
        canonicalValue(activeInput.value, schema);
    }
  }

  function setFormEnabled(form, enabled) {
    form.querySelectorAll("[data-canonical-value]").forEach(function (input) {
      input.disabled = !enabled;
    });
    form.querySelectorAll("[data-value-control]").forEach(function (input) {
      const label = input.closest("[data-typed-control]");
      input.disabled = !enabled || label.hidden;
    });
    form.querySelectorAll("[data-form-control]").forEach(function (input) {
      input.disabled = !enabled;
    });
    form.dataset.editing = enabled ? "true" : "false";
    form.querySelectorAll("[data-save-button]").forEach(function (button) {
      button.hidden = !enabled;
    });
    form.querySelectorAll("[data-edit-button]").forEach(function (button) {
      button.hidden = enabled;
    });
    form.querySelectorAll("[data-cancel-button]").forEach(function (button) {
      button.hidden = !enabled;
    });
  }

  document.querySelectorAll("[data-typed-form]").forEach(function (form) {
    const fields = form.querySelectorAll(".typed-value");

    fields.forEach(function (field) {
      updateField(form, field);
      field.querySelectorAll("[data-value-control]").forEach(function (input) {
        input.addEventListener("input", function () {
          synchronizeField(field);
        });
        input.addEventListener("change", function () {
          synchronizeField(field);
        });
      });
    });

    form.querySelectorAll("[data-type-selector]").forEach(function (selector) {
      const relatedFields = Array.from(fields).filter(function (field) {
        return field.dataset.typeSelectorId === selector.id;
      });
      function updateRelatedFields() {
        relatedFields.forEach(function (field) {
          updateField(form, field);
        });
      }
      selector.addEventListener("input", updateRelatedFields);
      selector.addEventListener("change", updateRelatedFields);
    });

    form.addEventListener("submit", function () {
      fields.forEach(synchronizeField);
    });
  });

  document.querySelectorAll("[data-record-form]").forEach(function (form) {
    form.querySelectorAll("[data-form-control], [data-canonical-value]")
      .forEach(function (input) {
        input.dataset.originalValue = input.value;
      });
    setFormEnabled(form, false);
    form.querySelectorAll("[data-edit-button]").forEach(function (button) {
      button.addEventListener("click", function () {
        setFormEnabled(form, true);
      });
    });
    form.querySelectorAll("[data-cancel-button]").forEach(function (button) {
      button.addEventListener("click", function () {
        form.querySelectorAll("[data-form-control], [data-canonical-value]")
          .forEach(function (input) {
            input.value = input.dataset.originalValue;
          });
        form.querySelectorAll(".typed-value").forEach(function (field) {
          updateField(form, field);
        });
        setFormEnabled(form, false);
      });
    });
  });

  document.querySelectorAll("[data-create-form]").forEach(function (form) {
    setFormEnabled(form, true);
  });

  document.querySelectorAll("[data-add-condition-button]").forEach(
    function (button) {
      button.addEventListener("click", function () {
        const form = document.getElementById(button.dataset.formId);
        form.hidden = false;
        setFormEnabled(form, true);
        button.hidden = true;
      });
    }
  );
})();
