document.addEventListener("DOMContentLoaded", function () {

    // Toast auto hide
    const toasts = document.querySelectorAll(".toast");

    toasts.forEach(function (toast) {
        setTimeout(function () {
            toast.style.opacity = "0";
            toast.style.transform = "translateY(-10px)";

            setTimeout(function () {
                toast.remove();
            }, 400);

        }, 3500);
    });


    // Smooth button click animation
    const buttons = document.querySelectorAll(
        ".primary-btn, .buy-btn, .hero-button"
    );

    buttons.forEach(function (button) {

        button.addEventListener("click", function () {

            button.style.transform = "scale(0.96)";

            setTimeout(function () {
                button.style.transform = "";
            }, 150);

        });

    });


    // Product cards animation
    const cards = document.querySelectorAll(".product-card");

    cards.forEach(function (card, index) {

        card.style.opacity = "0";
        card.style.transform = "translateY(20px)";

        setTimeout(function () {

            card.style.transition =
                "opacity 0.5s ease, transform 0.5s ease";

            card.style.opacity = "1";
            card.style.transform = "translateY(0)";

        }, index * 80);

    });


    // Demo notification only
    const notification = document.createElement("div");

    notification.id = "demo-notification";

    notification.innerHTML = `
        <div class="demo-icon">🛍️</div>

        <div>
            <b>Store Activity</b>
            <p>Welcome! Browse available products.</p>
        </div>
    `;

    document.body.appendChild(notification);


    setTimeout(function () {

        notification.classList.add("show");

        setTimeout(function () {

            notification.classList.remove("show");

        }, 4000);

    }, 5000);

});
