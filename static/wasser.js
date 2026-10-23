function Werte_Init() {
	Werte_Init_Zisterne();
}

function Werte_Init_Zisterne() {
	let p = Number(document.querySelector("[data-water-level]").dataset.waterLevel);
	document.getElementById("zisterne_per").textContent = p + "%";
	if (!Number.isFinite(p) || p < 0 || p > 100) {
		p = 80;
		document.getElementById("zisterne_per").textContent = "??? %";
		document.getElementById("zisterne_fill").setAttribute("fill", "red");
		document.getElementById("zisterne_welle").setAttribute("stroke", "red");
	}
	document.getElementById("zisterne_fill").setAttribute("height", p * 1.7);
	document.getElementById("zisterne_fill").setAttribute("y", 190 - p * 1.7);
	document.getElementById("zisterne_welle").setAttribute(
		"transform",
		"translate(4 " + (185 - p * 1.7) + ")"
	);
}
