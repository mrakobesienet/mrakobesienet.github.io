(function () {
	"use strict";

	var MOBILE_MAX = 959;

	function isMobile() {
		return window.innerWidth <= MOBILE_MAX;
	}

	function setupMenuToggle() {
		var menu = document.getElementById("menu");
		if (!menu || menu.querySelector(".mobile-menu-toggle")) {
			return;
		}

		var button = document.createElement("button");
		button.type = "button";
		button.className = "mobile-menu-toggle";
		button.setAttribute("aria-expanded", "false");
		button.setAttribute("aria-controls", "nav");
		button.textContent = "Меню";

		button.addEventListener("click", function () {
			var open = menu.classList.toggle("mobile-menu-open");
			button.setAttribute("aria-expanded", open ? "true" : "false");
		});

		menu.parentNode.insertBefore(button, menu);
	}

	function setupCollapsibleWidgets() {
		var widgets = document.querySelectorAll("#preFooter .widget");
		widgets.forEach(function (widget) {
			var heading = widget.querySelector(":scope > h2");
			var list = widget.querySelector(":scope > ul");
			if (!heading || !list || widget.dataset.collapsibleReady) {
				return;
			}

			widget.dataset.collapsibleReady = "1";

			heading.addEventListener("click", function () {
				if (!isMobile()) {
					return;
				}
				var expanded = widget.classList.toggle("mobile-expanded");
				widget.classList.toggle("mobile-collapsed", !expanded);
			});
		});
	}

	function syncCollapsibleState() {
		var widgets = document.querySelectorAll("#preFooter .widget");
		widgets.forEach(function (widget) {
			if (!widget.querySelector(":scope > ul")) {
				return;
			}
			if (isMobile()) {
				if (
					!widget.classList.contains("mobile-expanded") &&
					!widget.classList.contains("mobile-collapsed")
				) {
					widget.classList.add("mobile-collapsed");
				}
			} else {
				widget.classList.remove("mobile-collapsed", "mobile-expanded");
			}
		});
	}

	function init() {
		setupMenuToggle();
		setupCollapsibleWidgets();
		syncCollapsibleState();
	}

	if (document.readyState === "loading") {
		document.addEventListener("DOMContentLoaded", init);
	} else {
		init();
	}

	window.addEventListener("resize", syncCollapsibleState);
})();
