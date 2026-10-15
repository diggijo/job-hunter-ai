document.querySelectorAll(".status-button").forEach(button => {
    button.addEventListener("click", async () => {
        const jobId = button.dataset.jobId;
        const status = button.dataset.status;

        if (status === "not_interested") {
            if (!confirm("Hide this job and exclude it from future AI evaluations?")) {
                return;
            }
        }

        button.disabled = true;

        try {
            const response = await fetch(
                `/jobs/${jobId}/application-status`,
                {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({ status })
                }
            );

            if (!response.ok) {
                throw new Error("Could not save job status");
            }

            button.closest(".job-card").remove();

            const count = document.getElementById("job-count");
            if (count) {
                count.textContent = document.querySelectorAll(".job-card").length;
            }
        } catch (error) {
            alert("Failed to save job status. Please try again.");
            button.disabled = false;
        }
    });
});
