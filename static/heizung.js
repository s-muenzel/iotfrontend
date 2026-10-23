function Werte_Init_Heizung() {
	fetch('/heizung/status')
		.then(response => {
			if (!response.ok) {
				throw new Error("Heating status request failed: " + response.status);
			}
			return response.json();
		})
		.then(data => {
			Object.entries(data.rooms).forEach(([room, temperature]) => {
				const roomElement = document.querySelector(
					'[data-heating-room="' + room + '"]'
				);
				if (!roomElement) {
					return;
				}
				roomElement.querySelector(".heating-actual").textContent =
					temperature ? temperature.actual.toFixed(1) + " °C" : "Nicht verfügbar";
				roomElement.querySelector(".heating-target").textContent =
					temperature ? temperature.target + " °C" : "Nicht verfügbar";
				const targetInput = roomElement.querySelector('[name="target"]');
				if (!targetInput.dataset.userEdited) {
					targetInput.value = temperature ? temperature.target : "";
				}
			});
		})
		.catch(error => {
			console.error('Error fetching heating status:', error);
			Fehlermeldung("Heizungsdaten konnten nicht geladen werden.");
		});
}
