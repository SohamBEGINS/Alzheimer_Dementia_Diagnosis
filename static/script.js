document.getElementById('loginBtn').addEventListener('click', function() {
    window.location.href = '/login';
});

document.getElementById('signupBtn').addEventListener('click', function() {
    window.location.href = '/sign_up';
});

document.getElementById('googleSignInBtn').addEventListener('click', function() {
    window.location.href = '/login/google';
});



document.getElementById("tryButton").addEventListener("click", function () {
    // Slide up and fade out the intro content (previous text)
    document.querySelector(".intro-content").style.transform = "translateY(-50px)";
    document.querySelector(".intro-content").style.opacity = 0;

    // Delay to hide intro content and show description
    setTimeout(function () {
        // Hide the intro content and show the description
        document.querySelector(".intro-content").style.display = "none";
        document.querySelector(".description-content").style.display = "block";

        // Trigger the smooth slide-up and fade-in effect for the new text
        setTimeout(function () {
            document.querySelector(".description-content").style.opacity = 1;
            document.querySelector(".description-content").style.transform = "translateY(0)"; // Slide in
        }, 50); // Short delay for smoother transition
    }, 1500); // Time for intro text to fade out and slide up

    // Add glitter effect
    setTimeout(function () {
        const glitterContainer = document.createElement("div");
        glitterContainer.id = "glitter-container";
        document.body.appendChild(glitterContainer);

        // Gradually add stars
        let starCount = 0;
        const maxStars = 500;

        const addStar = () => {
            if (starCount >= maxStars) return;

            const star = document.createElement("div");
            star.className = "star";

            // Random position and size
            const x = Math.random() * window.innerWidth;
            const y = Math.random() * window.innerHeight;
            const size = Math.random() * 3 + 2; // Between 2px and 5px

            star.style.width = `${size}px`;
            star.style.height = `${size}px`;
            star.style.left = `${x}px`;
            star.style.top = `${y}px`;

            // Random color generation for each star
            const randomColor = `hsl(${Math.random() * 360}, 100%, 75%)`; // Random color in HSL format
            star.style.backgroundColor = randomColor; // Apply random color

            // Gradually make the star visible
            setTimeout(() => {
                star.style.opacity = 1;
            }, 100);

            // Random animation delay
            const delay = Math.random() * 6; // Between 0 and 6 seconds
            star.style.animationDelay = `${delay}s`;

            glitterContainer.appendChild(star);

            starCount++;
            setTimeout(addStar, 20); // Add a star every 500ms
        };

        addStar();
    }, 1000); // Slight delay for smoother transition
});



document.getElementById("sendBtn").addEventListener("click", function () {
    const userMessage = document.getElementById("userInput").value;
    const chatDisplay = document.getElementById("chat-display");

    if (userMessage.trim() === "") {
        return; // Do nothing if the input is empty
    }

    // Display user message
    const userBubble = document.createElement("div");
    userBubble.className = "user-message";
    userBubble.textContent = userMessage;
    chatDisplay.appendChild(userBubble);

    // Clear input field
    document.getElementById("userInput").value = "";

    // Call the backend API
    fetch("/api/chat", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ message: userMessage })
    })
        .then(response => response.json())
        .then(data => {
            // Display bot response
            const botBubble = document.createElement("div");
            botBubble.className = "bot-message";
            botBubble.textContent = data.reply;
            chatDisplay.appendChild(botBubble);
        })
        .catch(error => {
            console.error("Error:", error);
            const errorBubble = document.createElement("div");
            errorBubble.className = "error-message";
            errorBubble.textContent = "There was an error connecting to the API.";
            chatDisplay.appendChild(errorBubble);
        });
});
