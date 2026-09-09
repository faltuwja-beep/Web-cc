document.addEventListener(
    "DOMContentLoaded",
    function () {

        // Toast auto hide

        const toasts =
            document.querySelectorAll(
                ".toast"
            );

        toasts.forEach(
            function (toast) {

                setTimeout(
                    function () {

                        toast.style.opacity = "0";

                        setTimeout(
                            function () {

                                toast.remove();

                            },
                            400
                        );

                    },
                    3500
                );

            }
        );


        // Product animation

        const cards =
            document.querySelectorAll(
                ".product-card"
            );

        cards.forEach(
            function (card, index) {

                card.style.opacity = "0";

                card.style.transform =
                    "translateY(20px)";

                setTimeout(
                    function () {

                        card.style.transition =
                            "0.5s ease";

                        card.style.opacity =
                            "1";

                        card.style.transform =
                            "translateY(0)";

                    },
                    index * 80
                );

            }
        );


        // Button animation

        const buttons =
            document.querySelectorAll(
                ".primary-btn, .buy-btn"
            );

        buttons.forEach(
            function (button) {

                button.addEventListener(
                    "click",
                    function () {

                        button.style.transform =
                            "scale(.97)";

                        setTimeout(
                            function () {

                                button.style.transform =
                                    "";

                            },
                            150
                        );

                    }
                );

            }
        );

    }
);
