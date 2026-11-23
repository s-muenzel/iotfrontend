function w3_open() {
	document.getElementById("mySidebar").style.display = "block";
	document.getElementById("myOverlay").style.display = "block";
}

function w3_close() {
	document.getElementById("mySidebar").style.display = "none";
	document.getElementById("myOverlay").style.display = "none";
}

window.addEventListener("scroll", function () {
	const top = document.getElementById("myTop");
	const intro = document.getElementById("myIntro");
	if (!top || !intro) return;
	if (document.body.scrollTop > 80 || document.documentElement.scrollTop > 80) {
		top.classList.add("w3-card-4", "w3-animate-opacity");
		intro.classList.add("w3-show-inline-block");
	} else {
		intro.classList.remove("w3-show-inline-block");
		top.classList.remove("w3-card-4", "w3-animate-opacity");
	}
});

function initializeDataTable(table) {
	const controls = document.querySelector(
		'[data-controls-for="' + table.id + '"]'
	);
	const filterRow = table.querySelector(".filter-row");
	const filterToggle = controls.querySelector("[data-filter-toggle]");
	const filterVisibilityToggle = controls.querySelector(
		"[data-filter-visibility-toggle]"
	);
	const viewOptions = controls.querySelectorAll("[data-table-view]");
	let filtersEnabled = false;
	let filterControlsVisible = false;
	let filterStorageAvailable = true;
	let sortedColumn = -1;
	let ascending = true;
	const filterStorageKey = "iotfrontend:table-filters:"
		+ window.location.pathname + ":" + table.id;

	function readSavedFilterState() {
		let serializedState;
		try {
			serializedState = window.localStorage.getItem(filterStorageKey);
		} catch (error) {
			filterStorageAvailable = false;
			console.error("Could not read saved table filters.", error);
			return null;
		}
		if (serializedState === null) return null;

		let savedState;
		try {
			savedState = JSON.parse(serializedState);
		} catch (error) {
			console.error("Could not parse saved table filters.", error);
			return null;
		}

		const isRecord = function (value) {
			return value !== null && typeof value === "object"
				&& !Array.isArray(value);
		};
		if (!isRecord(savedState)
			|| savedState.version !== 1
			|| typeof savedState.filtersEnabled !== "boolean"
			|| typeof savedState.filterControlsVisible !== "boolean"
			|| !isRecord(savedState.textFilters)
			|| !isRecord(savedState.selectedValues)) {
			console.error("Ignoring invalid saved table filters.");
			return null;
		}

		return savedState;
	}

	function saveFilterState() {
		if (!filterStorageAvailable) return;

		const textFilters = {};
		table.querySelectorAll(".filter-text").forEach(function (input) {
			textFilters[input.dataset.filterColumn] = input.value;
		});
		const selectedValues = {};
		table.querySelectorAll(".filter-options").forEach(function (container) {
			selectedValues[container.dataset.filterColumn] = Array.from(
				container.querySelectorAll("input:checked")
			).map(function (checkbox) { return checkbox.value; });
		});

		const savedState = {
			version: 1,
			filtersEnabled: filtersEnabled,
			filterControlsVisible: filterControlsVisible,
			textFilters: textFilters,
			selectedValues: selectedValues
		};
		try {
			window.localStorage.setItem(
				filterStorageKey, JSON.stringify(savedState)
			);
		} catch (error) {
			filterStorageAvailable = false;
			console.error("Could not save table filters.", error);
		}
	}

	function updateFilterVisibility() {
		filterRow.hidden = !filterControlsVisible;
		filterVisibilityToggle.setAttribute(
			"aria-expanded", String(filterControlsVisible)
		);
		const label = filterControlsVisible
			? "Filterbereich ausblenden"
			: "Filterbereich anzeigen";
		filterVisibilityToggle.setAttribute("aria-label", label);
		filterVisibilityToggle.title = label;
		const icon = filterVisibilityToggle.querySelector("i");
		icon.classList.toggle("fa-eye", filterControlsVisible);
		icon.classList.toggle("fa-eye-slash", !filterControlsVisible);
	}

	function updateFilterToggle() {
		filterToggle.classList.toggle("filter-active", filtersEnabled);
		filterToggle.setAttribute("aria-pressed", String(filtersEnabled));
		const label = filtersEnabled
			? "Filter deaktivieren"
			: "Filter aktivieren";
		filterToggle.setAttribute("aria-label", label);
		filterToggle.title = label;
		filterVisibilityToggle.hidden = !filtersEnabled;
	}

	function applyFilters() {
		const rows = Array.from(table.tBodies[0].rows);
		if (!filtersEnabled) {
			rows.forEach(function (row) { row.style.display = ""; });
			return;
		}

		rows.forEach(function (row) {
			let matches = true;
			table.querySelectorAll(".filter-options").forEach(function (container) {
				if (!matches) return;
				const column = Number(container.dataset.filterColumn);
				const selectedValues = Array.from(
					container.querySelectorAll("input:checked")
				).map(function (checkbox) { return checkbox.value; });
				if (!selectedValues.length) return;

				const cell = row.cells[column];
				const value = cell.dataset.filterValue !== undefined
					? cell.dataset.filterValue
					: (cell.dataset.sort !== undefined
						? cell.dataset.sort : cell.textContent.trim());
				if (selectedValues.indexOf(value) === -1) matches = false;
			});

			table.querySelectorAll(".filter-text").forEach(function (input) {
				if (!matches || !input.value.trim()) return;
				const column = Number(input.dataset.filterColumn);
				const text = row.cells[column].textContent.toLocaleLowerCase("de");
				if (text.indexOf(input.value.trim().toLocaleLowerCase("de")) === -1) {
					matches = false;
				}
			});

			row.style.display = matches ? "" : "none";
		});
	}

	table.querySelectorAll(".filter-options").forEach(function (container) {
		const column = Number(container.dataset.filterColumn);
		const values = new Map();
		Array.from(table.tBodies[0].rows).forEach(function (row) {
			const cell = row.cells[column];
			const value = cell.dataset.filterValue !== undefined
				? cell.dataset.filterValue
				: (cell.dataset.sort !== undefined
					? cell.dataset.sort : cell.textContent.trim());
			if (!values.has(value)) {
				values.set(value, cell.dataset.filterLabel || (value || "(leer)"));
			}
		});

		Array.from(values.keys()).sort(function (a, b) {
			return a.localeCompare(b, "de", {
				sensitivity: "base", numeric: true
			});
		}).forEach(function (value) {
			const label = document.createElement("label");
			label.className = "filter-option";
			const checkbox = document.createElement("input");
			checkbox.type = "checkbox";
			checkbox.value = value;
			checkbox.addEventListener("change", function () {
				applyFilters();
				saveFilterState();
			});
			label.appendChild(checkbox);
			label.appendChild(document.createTextNode(
				" " + values.get(value)
			));
			container.appendChild(label);
		});
	});

	const savedFilterState = readSavedFilterState();
	if (savedFilterState) {
		filtersEnabled = savedFilterState.filtersEnabled;
		filterControlsVisible = filtersEnabled
			&& savedFilterState.filterControlsVisible;
		table.querySelectorAll(".filter-text").forEach(function (input) {
			const value = savedFilterState.textFilters[input.dataset.filterColumn];
			if (value !== undefined) input.value = value;
		});
		table.querySelectorAll(".filter-options").forEach(function (container) {
			const values =
				savedFilterState.selectedValues[container.dataset.filterColumn];
			if (!Array.isArray(values)) return;
			container.querySelectorAll("input[type=checkbox]").forEach(
				function (checkbox) {
					checkbox.checked = values.indexOf(checkbox.value) !== -1;
				}
			);
		});
	}

	table.querySelectorAll(".filter-text").forEach(function (input) {
		input.addEventListener("input", function () {
			applyFilters();
			saveFilterState();
		});
	});

	filterToggle.addEventListener("click", function () {
		filtersEnabled = !filtersEnabled;
		filterControlsVisible = filtersEnabled;
		updateFilterToggle();
		updateFilterVisibility();
		applyFilters();
		saveFilterState();
	});

	filterVisibilityToggle.addEventListener("click", function () {
		if (!filtersEnabled) return;
		filterControlsVisible = !filterControlsVisible;
		updateFilterVisibility();
		saveFilterState();
	});

	function setTableView(view) {
		const showAllColumns = view === "complete";
		table.classList.toggle("show-optional-columns", showAllColumns);
		viewOptions.forEach(function (option) {
			const selected = option.dataset.tableView === view;
			option.classList.toggle("is-selected", selected);
			option.setAttribute("aria-pressed", String(selected));
		});
	}

	viewOptions.forEach(function (option) {
		option.addEventListener("click", function () {
			setTableView(option.dataset.tableView);
		});
	});

	table.querySelectorAll("th[data-sort-column]").forEach(function (header) {
		function sort() {
			const column = Number(header.dataset.sortColumn);
			if (sortedColumn === column) {
				ascending = !ascending;
			} else {
				sortedColumn = column;
				ascending = true;
			}

			table.querySelectorAll("th[aria-sort]").forEach(function (item) {
				const indicator = item.querySelector(".sort-indicator");
				const current = Number(item.dataset.sortColumn) === column;
				item.setAttribute(
					"aria-sort",
					current ? (ascending ? "ascending" : "descending") : "none"
				);
				indicator.classList.remove(
					"fa-sort", "fa-sort-asc", "fa-sort-desc"
				);
				if (current) {
					indicator.classList.add(
						ascending ? "fa-sort-asc" : "fa-sort-desc"
					);
				} else {
					indicator.classList.add("fa-sort");
				}
			});

			const tbody = table.tBodies[0];
			const rows = Array.from(tbody.rows);
			rows.sort(function (a, b) {
				const aCell = a.cells[column];
				const bCell = b.cells[column];
				const aValue = aCell.dataset.sort !== undefined
					? aCell.dataset.sort : aCell.textContent.trim();
				const bValue = bCell.dataset.sort !== undefined
					? bCell.dataset.sort : bCell.textContent.trim();
				const comparison = aValue.localeCompare(bValue, "de", {
					numeric: true, sensitivity: "base"
				});
				return ascending ? comparison : -comparison;
			});
			rows.forEach(function (row) { tbody.appendChild(row); });
		}

		header.addEventListener("click", function (event) {
			if (event.target.closest("button")) return;
			sort();
		});
		header.addEventListener("keydown", function (event) {
			if (event.target !== header) return;
			if (event.key === "Enter" || event.key === " ") {
				event.preventDefault();
				sort();
			}
		});
	});

	updateFilterToggle();
	updateFilterVisibility();
	applyFilters();
}

document.querySelectorAll("table[data-sortable-filterable]").forEach(
	initializeDataTable
);
