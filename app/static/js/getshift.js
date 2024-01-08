        function getfesti() {
            fetch("/getshift", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({"get": true}),
            })
            .then(response => response.json())  // Parse the JSON from the response
            .then(data => {
                console.log("RESULT:", data);
                // Process the data as needed
            })
            .catch(error => {
                console.error("ERROR:", error);
            });
        }
window.onload = getfesti();