function Werte_Init_Strom() {
	Resize_Strom();
	HoleWerte_Strom();
}

function Resize_Strom() {
	let width = window.innerWidth || document.documentElement.clientWidth || document.body.clientWidth;
	document.getElementById("stromSvg").width.baseVal.value = width * 0.8;
	document.getElementById("stromSvg").height.baseVal.value = width * 0.8 * 0.75;
	document.getElementById("scale_group").setAttribute(
		"transform",
		"scale(" + document.getElementById("stromSvg").width.baseVal.value / 800 + ")"
	);
}

function HoleWerte_Strom() {
	fetch('/status_s')
		.then(response => {
			if (!response.ok) {
				throw new Error("Power status request failed: " + response.status);
			}
			return response.json();
		})
		.then(UpdatePfeile_Strom)
		.catch(error => console.error('Error fetching power status:', error));
}

function ErzeugePText_Strom(power) {
	if (power >= 1000 || power <= -1000) {
		return (power / 1000).toPrecision(3) + "kW";
	}
	return Math.round(power) + " W";
}

function UpdatePfeile_Strom(data) {
	document.getElementById("battery_per").textContent = data.soc + "%";
	document.getElementById("battery_fill").setAttribute("height", 70 * (data.soc / 100));
	document.getElementById("battery_fill").setAttribute("y", 10 + 70 * (1 - data.soc / 100));
	document.getElementById("battery_p").textContent = ErzeugePText_Strom(data.p_battery);
	document.getElementById("battery_arrow_lade").setAttribute(
		"fill", data.p_battery > 0 ? "green" : "none"
	);
	document.getElementById("battery_arrow_entlade").setAttribute(
		"fill", data.p_battery < 0 ? "red" : "none"
	);
	document.getElementById("solar_p").textContent = ErzeugePText_Strom(data.p_solar);
	document.getElementById("solar_arrow_lade").setAttribute(
		"fill", data.p_solar > 0 ? "green" : "none"
	);
	document.getElementById("haus_p").textContent = ErzeugePText_Strom(data.p_haus);
	document.getElementById("haus_arrow_lade").setAttribute(
		"fill", data.p_haus > 0 ? "red" : "none"
	);
	document.getElementById("grid_p").textContent = ErzeugePText_Strom(data.p_grid);
	document.getElementById("grid_arrow_lade").setAttribute(
		"fill", data.p_grid > 0 ? "red" : "none"
	);
	document.getElementById("grid_arrow_entlade").setAttribute(
		"fill", data.p_grid < 0 ? "green" : "none"
	);
}
