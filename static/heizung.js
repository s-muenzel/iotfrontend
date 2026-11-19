function Werte_Init_Heizung() {
	fetch('/heizung/status')
		.then(response => {
			if (!response.ok) {
				throw new Error("Heating status request failed: " + response.status);
			}
			return response.json();
		})
		.then(data => {
			document.querySelectorAll("[data-heating-room]").forEach(roomElement => {
				const temperature =
					data.rooms[roomElement.dataset.heatingRoom];
				roomElement.querySelector(".heating-actual").textContent =
					temperature && temperature.actual !== null
						? temperature.actual.toFixed(1) + " °C"
						: "Nicht verfügbar";
				const targetInput = roomElement.querySelector('[name="target"]');
				if (!targetInput.dataset.userEdited) {
					targetInput.value =
						temperature && temperature.target !== null
							? temperature.target
							: "";
				}
			});
		})
		.catch(error => {
			console.error('Error fetching heating status:', error);
			Fehlermeldung("Heizungsdaten konnten nicht geladen werden.");
		});
}
