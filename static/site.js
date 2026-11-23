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
	if (document.body.scrollTop > 80 || document.documentElement.scrollTop > 80) {
		top.classList.add("w3-card-4", "w3-animate-opacity");
		intro.classList.add("w3-show-inline-block");
	} else {
		intro.classList.remove("w3-show-inline-block");
		top.classList.remove("w3-card-4", "w3-animate-opacity");
	}
});
