function toggleMenu() {

    const menu =
        document.getElementById("navLinks");

    menu.classList.toggle("active");
}


function toggleTheme() {

    document.body.classList.toggle("light");

    const isLight =
        document.body.classList.contains("light");

    localStorage.setItem(
        "theme",
        isLight ? "light" : "dark"
    );
}


function loadTheme() {

    const theme =
        localStorage.getItem("theme");

    if (theme === "light") {

        document.body.classList.add(
            "light"
        );

    }
}


function copyUPI() {

    const upi =
        document.getElementById("upiId");

    if (!upi) {
        return;
    }

    navigator.clipboard
        .writeText(upi.innerText)
        .then(() => {

            alert(
                "UPI ID copied!"
            );

        })
        .catch(() => {

            alert(
                "Copy failed. Please copy manually."
            );

        });
}


document.addEventListener(
    "DOMContentLoaded",
    loadTheme
);
