function Lampe_Wert(zimmer, zimmer_url) {
	wert = document.getElementById("lampe_" + zimmer + "_wert").value;
	setze_Lampe(zimmer_url, wert);
	Lampe_Img(zimmer);
}

function setze_Lampe(lampe_url, wert) {
	var xhttp = new XMLHttpRequest();
	xhttp.onreadystatechange = function () { };
	xhttp.open("GET", lampe_url + 'SetzeWert?Wert=' + wert, true);
	xhttp.send();
}

function anaus_Lampe(zimmer, lampe_url) {
	var xhttp = new XMLHttpRequest();
	xhttp.onreadystatechange = function () { };
	xhttp.open("GET", lampe_url + "Wechsel", true);
	xhttp.send();
}

function Lampe_Img(zimmer) {
	wert = document.getElementById("lampe_" + zimmer + "_wert").value;
	if (wert > 0) {
		document.getElementById("lampe_" + zimmer + "_schalter").style.color = "red";
	} else {
		document.getElementById("lampe_" + zimmer + "_schalter").style.color = "black";
	}
}

function Werte_Init_Leuchte() {
	var xhttp_lampe = new XMLHttpRequest();
	xhttp_lampe.onreadystatechange = function () {
		if (this.readyState == 4 && this.status == 200) {
			var obj = JSON.parse(this.responseText);
			Lampe_Img(obj.wz_lampe);
		}
	}
	xhttp_lampe.open("GET", "status_l", true);
	xhttp_lampe.send();
}
