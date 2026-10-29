"use strict";

(function () {
  function schemaFor(form, field) {
    const schemas = JSON.parse(form.dataset.typeSchemas || "{}");
    const selector = document.getElementById(field.dataset.typeSelectorId);
    const selectedType = selector.value;
    const argumentMatch = field.dataset.parameter.match(/(?:^a|_arg)([12])$/);
    const schemaArgument = field.dataset.schemaArgument ||
      (argumentMatch ? "arg" + argumentMatch[1] : "");
    return (schemas[selectedType] &&
      schemas[selectedType][schemaArgument]) ||
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

  function rangeError(displayedValue, schema) {
    if (displayedValue === "" || !schema.ranges) {
      return "";
    }

    const value = Number(canonicalValue(displayedValue, schema));
    const allowed = schema.ranges.some(function (range) {
      return value >= range[0] && value <= range[1];
    });
    return allowed ? "" : "Wert liegt außerhalb des erlaubten Typbereichs.";
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
      if (!input) {
        return;
      }
      input.disabled = !active || canonical.disabled;
      input.required = active && schema.input === "tag";
      if (schema.input !== "tag") {
        input.setCustomValidity("");
      }
      if (input instanceof HTMLInputElement) {
        input.min = schema.min === undefined ? "" :
          displayValue(String(schema.min), schema);
        input.max = schema.max === undefined ? "" :
          displayValue(String(schema.max), schema);
        input.step = schema.step === undefined ? "any" : schema.step;
      }
      if (active) {
        if (schema.input === "tag") {
          const mask = Number(canonical.value);
          let selectedMask = 0;
          Array.from(input.options).forEach(function (option) {
            const bit = Number(option.value);
            option.selected = Number.isInteger(mask) && mask > 0 &&
              (mask & bit) === bit;
            if (option.selected) {
              selectedMask |= bit;
            }
          });
          input.title = Array.from(input.selectedOptions)
            .map(function (option) {
              return option.text;
            })
            .join(", ");
          input.setCustomValidity(tagSelectionError(schema, mask, selectedMask));
        } else {
          input.value = displayValue(canonical.value, schema);
          input.setCustomValidity(rangeError(input.value, schema));
        }
      }
    });
  }

  function tagSelectionError(schema, mask, selectedMask) {
    if (!Number.isInteger(mask) || mask <= 0 || selectedMask !== mask) {
      return "Bitte mindestens einen gültigen Tag auswählen.";
    }

    const selectedNames = new Set(
      Object.entries(schema.options || {})
        .filter(function (entry) {
          return (mask & Number(entry[1])) === Number(entry[1]);
        })
        .map(function (entry) {
          return entry[0];
        })
    );
    const incompatible = schema.incompatible || [];
    const hasConflict = incompatible.some(function (combination) {
      return combination.every(function (name) {
        return selectedNames.has(name);
      });
    });
    if (hasConflict) {
      return "Werktag kann nicht mit Wochenende oder Feiertag kombiniert werden.";
    }

    return "";
  }

  function synchronizeField(field) {
    const form = document.getElementById(
      field.querySelector("[data-canonical-value]").getAttribute("form")
    );
    const schema = schemaFor(form, field);
    const activeInput = field.querySelector(
      '[data-typed-control="' + schema.input + '"] [data-value-control]'
    );
    const canonical = field.querySelector("[data-canonical-value]");
    if (schema.input === "none") {
      canonical.value = "";
    } else if (activeInput && schema.input === "tag") {
      const selectedMask = Array.from(activeInput.selectedOptions)
        .reduce(function (mask, option) {
          return mask | Number(option.value);
        }, 0);
      canonical.value = selectedMask ? String(selectedMask) : "";
      activeInput.setCustomValidity(
        tagSelectionError(schema, selectedMask, selectedMask)
      );
    } else if (activeInput) {
      canonical.value = canonicalValue(activeInput.value, schema);
      activeInput.setCustomValidity(rangeError(activeInput.value, schema));
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

  function initializeTypedForm(form) {
    const updateFields = function (selector) {
      form.querySelectorAll(".typed-value").forEach(function (field) {
        if (field.dataset.typeSelectorId === selector.id) {
          updateField(form, field);
        }
      });
    };

    form.querySelectorAll("[data-canonical-value]").forEach(function (input) {
      input.disabled = false;
    });
    form.querySelectorAll(".typed-value").forEach(function (field) {
      updateField(form, field);
    });

    form.addEventListener("focusin", function (event) {
      if (event.target.matches("[data-tag-selector]")) {
        event.target.size = event.target.options.length;
      }
    });
    form.addEventListener("focusout", function (event) {
      if (event.target.matches("[data-tag-selector]")) {
        event.target.size = 1;
      }
    });
    form.addEventListener("input", function (event) {
      if (event.target.matches("[data-value-control]")) {
        synchronizeField(event.target.closest(".typed-value"));
      }
    });
    form.addEventListener("change", function (event) {
      if (event.target.matches("[data-type-selector]")) {
        updateFields(event.target);
      } else if (event.target.matches("[data-value-control]")) {
        synchronizeField(event.target.closest(".typed-value"));
      }
    });
    form.addEventListener("click", function (event) {
      const addButton = event.target.closest("[data-add-row]");
      if (addButton) {
        const category = addButton.dataset.addRow;
        const template = form.querySelector(
          'template[data-row-template="' + category + '"]'
        );
        const rows = form.querySelector('[data-rows="' + category + '"]');
        const fragment = template.content.cloneNode(true);
        const counterName = "next" +
          category.charAt(0).toUpperCase() + category.slice(1) + "Index";
        const index = Number(
          form.dataset[counterName] || rows.querySelectorAll("[data-row]").length
        );
        form.dataset[counterName] = index + 1;
        const walker = document.createTreeWalker(
          fragment,
          NodeFilter.SHOW_ELEMENT
        );
        let element = walker.nextNode();
        while (element) {
          Array.from(element.attributes).forEach(function (attribute) {
            attribute.value = attribute.value.replace(/__INDEX__/g, index);
          });
          element = walker.nextNode();
        }
        rows.appendChild(fragment);
        rows.querySelectorAll(".typed-value").forEach(function (field) {
          if (field.dataset.typeSelectorId.indexOf(
            category + "-" + index + "-"
          ) === 0) {
            field.querySelector("[data-canonical-value]").disabled = false;
            updateField(form, field);
          }
        });
        return;
      }

      const removeButton = event.target.closest("[data-remove-row]");
      if (removeButton) {
        const row = removeButton.closest("[data-row]");
        const rows = row.parentElement;
        if (rows.querySelectorAll("[data-row]").length > 1) {
          row.remove();
        }
      }
    });
    form.addEventListener("submit", function () {
      form.querySelectorAll(".typed-value").forEach(synchronizeField);
    });
  }

  document.querySelectorAll("[data-typed-form]").forEach(function (form) {
    initializeTypedForm(form);
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
