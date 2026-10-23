function Garage_Img(wert) {
	if (wert == 0) {
		document.getElementById("garage_tor").style.backgroundImage = 'url(static/offen.png)';
	} else if (wert == 1) {
		document.getElementById("garage_tor").style.backgroundImage = 'url(static/zu.png)';
	} else {
		document.getElementById("garage_tor").style.backgroundImage = 'url(static/unklar.png)';
	}
}

function fahre_Garagentor(wert) {
	var xhttp = new XMLHttpRequest();
	xhttp.onreadystatechange = function () { };
	xhttp.open("GET", "http://192.168.2.97/" + wert, true);
	xhttp.send();
}

function Werte_Init_Garage() {
	var xhttp_garage = new XMLHttpRequest();
	xhttp_garage.onreadystatechange = function () {
		if (this.readyState == 4 && this.status == 200) {
			var obj = JSON.parse(this.responseText);
			Garage_Img(obj.garage_tor);
		}
	}
	xhttp_garage.open("GET", "status_g", true);
	xhttp_garage.send();
}
