function Rollo_Hoch(zimmer_url) {
	fahre_Rollo(zimmer_url, 100);
}

function Rollo_Runter(zimmer_url) {
	fahre_Rollo(zimmer_url, 0);
}

function Rollo_Wert(zimmer, zimmer_url) {
	wert = document.getElementById("rollo_" + zimmer + "_wert").value;
	fahre_Rollo(zimmer_url, wert);
	Rollo_Img(zimmer); // auf aktive RÃ¼ckmeldung warten...
}

function fahre_Rollo(rollo_url, pos) {
	var xhttp = new XMLHttpRequest();
	xhttp.onreadystatechange = function () { };
	xhttp.open("GET", rollo_url + 'roller/0?go=to_pos&roller_pos=' + pos, true);
	xhttp.send();
}

function Rollo_Img(zimmer) {
	wert = document.getElementById("rollo_" + zimmer + "_wert").value;
	if (wert > 90) {
		document.getElementById("rollo_" + zimmer).style.backgroundImage = 'url(static/shutter-0.png)';
	} else if (wert > 80) {
		document.getElementById("rollo_" + zimmer).style.backgroundImage = 'url(static/shutter-10.png)';
	} else if (wert > 70) {
		document.getElementById("rollo_" + zimmer).style.backgroundImage = 'url(static/shutter-20.png)';
	} else if (wert > 60) {
		document.getElementById("rollo_" + zimmer).style.backgroundImage = 'url(static/shutter-30.png)';
	} else if (wert > 50) {
		document.getElementById("rollo_" + zimmer).style.backgroundImage = 'url(static/shutter-40.png)';
	} else if (wert > 40) {
		document.getElementById("rollo_" + zimmer).style.backgroundImage = 'url(static/shutter-50.png)';
	} else if (wert > 30) {
		document.getElementById("rollo_" + zimmer).style.backgroundImage = 'url(static/shutter-60.png)';
	} else if (wert > 20) {
		document.getElementById("rollo_" + zimmer).style.backgroundImage = 'url(static/shutter-70.png)';
	} else if (wert > 10) {
		document.getElementById("rollo_" + zimmer).style.backgroundImage = 'url(static/shutter-80.png)';
	} else if (wert > 0) {
		document.getElementById("rollo_" + zimmer).style.backgroundImage = 'url(static/shutter-90.png)';
	} else {
		document.getElementById("rollo_" + zimmer).style.backgroundImage = 'url(static/shutter-100.png)';
	}
}

function Werte_Init_Rollo() {
	var xhttp_rollo = new XMLHttpRequest();
	xhttp_rollo.onreadystatechange = function () {
		if (this.readyState == 4 && this.status == 200) {
			var obj = JSON.parse(this.responseText);
			document.getElementById("rollo_tim_wert").value = obj.rollo_tim;
			Rollo_Img("tim");
			document.getElementById("rollo_eva_wert").value = obj.rollo_eva;
			Rollo_Img("eva");
			document.getElementById("rollo_sz_wert").value = obj.rollo_sz;
			Rollo_Img("sz");
			document.getElementById("rollo_bad_wert").value = obj.rollo_bad;
			Rollo_Img("bad");
		}
	}
	xhttp_rollo.open("GET", "status_r", true);
	xhttp_rollo.send();
}
