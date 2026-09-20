const form = document.getElementById("analysisForm");
const claim = document.getElementById("claim");
const counter = document.getElementById("counter");
const loading = document.getElementById("loading");
const results = document.getElementById("results");

const photo = document.getElementById("photo");
const video = document.getElementById("video");
const photoName = document.getElementById("photoName");
const videoName = document.getElementById("videoName");
const previewArea = document.getElementById("previewArea");
const photoPreview = document.getElementById("photoPreview");
const videoPreview = document.getElementById("videoPreview");

claim.addEventListener("input", () => {
    counter.textContent = claim.value.length;
});

document.querySelectorAll(".example-btn").forEach(button => {
    button.addEventListener("click", () => {
        claim.value = button.dataset.example;
        counter.textContent = claim.value.length;
    });
});

photo.addEventListener("change", () => {
    photoName.textContent = photo.files[0]?.name || "No photo selected";

    if (photo.files[0]) {
        photoPreview.src = URL.createObjectURL(photo.files[0]);
        photoPreview.classList.remove("hidden");
        previewArea.classList.remove("hidden");
    }
});

video.addEventListener("change", () => {
    videoName.textContent = video.files[0]?.name || "No video selected";

    if (video.files[0]) {
        videoPreview.src = URL.createObjectURL(video.files[0]);
        videoPreview.classList.remove("hidden");
        previewArea.classList.remove("hidden");
    }
});

form.addEventListener("submit", async (event) => {
    event.preventDefault();

    if (!claim.value.trim() && !document.getElementById("brand").value.trim()
        && !photo.files.length && !video.files.length) {
        alert("Please enter a brand, claim, photo, or video.");
        return;
    }

    loading.classList.remove("hidden");
    results.classList.add("hidden");

    try {
        const response = await fetch("/analyze", {
            method: "POST",
            body: new FormData(form)
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.details || data.error || "Analysis failed");
        }

        showResults(data);
    } catch (error) {
        alert(error.message);
        console.error(error);
    } finally {
        loading.classList.add("hidden");
    }
});

function showResults(data) {
    results.classList.remove("hidden");

    document.getElementById("score").textContent = data.score ?? 0;
    document.getElementById("scoreFill").style.width = `${data.score ?? 0}%`;
    document.getElementById("riskText").textContent = data.risk || "Uncertain";
    document.getElementById("summary").textContent = data.summary || "";

    fillList("highlights", data.highlights);
    fillList("evidence", data.evidence);
    fillList("limitations", data.limitations);

    const redFlags = document.getElementById("redFlags");
    redFlags.innerHTML = "";

    if (!data.red_flags || data.red_flags.length === 0) {
        redFlags.innerHTML = "<p class='summary'>No specific warning phrase was returned. This does not mean the claim is verified.</p>";
    } else {
        data.red_flags.forEach(flag => {
            const item = document.createElement("div");
            item.className = "flag-item";

            const phrase = document.createElement("div");
            phrase.className = "flag-phrase";
            phrase.textContent = flag.phrase || "Unspecified phrase";

            const reason = document.createElement("p");
            reason.textContent = flag.reason || "";

            item.appendChild(phrase);
            item.appendChild(reason);
            redFlags.appendChild(item);
        });
    }

    document.getElementById("rewrite").textContent = data.rewrite || "No rewrite generated.";
    results.scrollIntoView({ behavior: "smooth", block: "start" });
}

function fillList(id, values) {
    const element = document.getElementById(id);
    element.innerHTML = "";

    (values || []).forEach(value => {
        const li = document.createElement("li");
        li.textContent = value;
        element.appendChild(li);
    });

    if (!values || values.length === 0) {
        const li = document.createElement("li");
        li.textContent = "No information returned.";
        element.appendChild(li);
    }
}

document.getElementById("newBtn").addEventListener("click", () => {
    results.classList.add("hidden");
    window.scrollTo({ top: 0, behavior: "smooth" });
});
