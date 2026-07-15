const FaceCapture = (() => {
    async function startCamera(video, statusEl) {
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            throw new Error("Browser tidak mendukung akses kamera.");
        }

        const stream = await navigator.mediaDevices.getUserMedia({
            video: {
                facingMode: "user",
                width: { ideal: 640 },
                height: { ideal: 480 }
            },
            audio: false
        });

        video.srcObject = stream;
        statusEl.textContent = "Kamera aktif.";
        return stream;
    }

    function capture(video, canvas) {
        const context = canvas.getContext("2d");

        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;

        context.drawImage(
            video,
            0,
            0,
            canvas.width,
            canvas.height
        );
        return canvas.toDataURL("image/jpeg", 0.95);
    }

    function setResult(resultEl, message, state) {
        resultEl.textContent = message;
        resultEl.className = `result-box ${state || ""}`.trim();
    }

    async function postJSON(endpoint, payload) {
        const response = await fetch(endpoint, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(payload)
        });

        const data = await response.json().catch(() => ({}));

        if (!response.ok || data.ok === false) {
            throw new Error(data.message || "Permintaan gagal diproses.");
        }

        return data;
    }

    function mountFaceRegistration(options) {

        const video = document.getElementById(options.videoId);
        const canvas = document.getElementById(options.canvasId);
        const statusEl = document.getElementById(options.statusId);
        const startButton = document.getElementById(options.startButtonId);
        const captureButton = document.getElementById(options.captureButtonId);
        const resultEl = document.getElementById(options.resultId);
        const sampleCount = document.getElementById(options.sampleCountId);
        const sampleBar = document.getElementById(options.sampleBarId);

        let stream = null;

        // jumlah sampel
        const TOTAL_SAMPLES = 3;

        // penyimpanan sampel
        let samples = [];
        let currentSample = 0;

        startButton.addEventListener("click", async () => {
            try {
                stream = stream || await startCamera(video, statusEl);

                // Tunggu kamera stabil
                await new Promise(resolve => setTimeout(resolve, 500));

                samples = [];
                currentSample = 0;

                sampleCount.textContent = `0/${TOTAL_SAMPLES} sampel`;
                sampleBar.style.width = "0%";

                captureButton.textContent = "Ambil Sampel 1";
                captureButton.disabled = false;

                startButton.disabled = true;

            } catch (error) {
                setResult(resultEl, error.message, "error");
            }
        });

        captureButton.addEventListener("click", async () => {

            captureButton.disabled = true;

            // Tunggu kamera stabil sebentar
            await new Promise(resolve => setTimeout(resolve, 200));

            // Ambil satu gambar
            samples.push(capture(video, canvas));

            currentSample++;

            sampleCount.textContent =
                `${currentSample}/${TOTAL_SAMPLES} sampel`;

            sampleBar.style.width =
                `${(currentSample / TOTAL_SAMPLES) * 100}%`;

            if (currentSample < TOTAL_SAMPLES) {

                captureButton.textContent =
                    `Ambil Sampel ${currentSample + 1}`;
                
                captureButton.disabled = false;
                
                setResult(
                    resultEl,
                    `Sampel ${currentSample} berhasil diambil.`,
                    "info"
                );

                return;
            }

            captureButton.disabled = true;

            setResult(
                resultEl,
                "Memproses registrasi wajah...",
                "info"
            );

            try {

                const data = await postJSON(
                    options.endpoint,
                    {
                        images: samples
                    }
                );

                setResult(resultEl, data.message, "success");

                // Reset
                samples = [];
                currentSample = 0;

                sampleCount.textContent = `0/${TOTAL_SAMPLES} sampel`;
                sampleBar.style.width = "0%";

                captureButton.textContent = "Ambil Sampel 1";

                captureButton.disabled = false;

            } catch (error) {

                setResult(resultEl, error.message, "error");

                samples = [];
                currentSample = 0;

                sampleCount.textContent = `0/${TOTAL_SAMPLES} sampel`;
                sampleBar.style.width = "0%";

                captureButton.textContent = "Ambil Sampel 1";
                captureButton.disabled = false;
            }

        });
    }

    function mountAttendance(options) {
        const video = document.getElementById(options.videoId);
        const canvas = document.getElementById(options.canvasId);
        const statusEl = document.getElementById(options.statusId);
        const startButton = document.getElementById(options.startButtonId);
        const submitButton = document.getElementById(options.submitButtonId);
        const resultEl = document.getElementById(options.resultId);
        const sessionSelect = document.getElementById(options.sessionSelectId);

        let stream = null;

        startButton.addEventListener("click", async () => {
            try {

                stream = stream || await startCamera(video, statusEl);

                startButton.disabled = true;

                if (sessionSelect && sessionSelect.value) {
                    submitButton.disabled = false;
                }

            } catch (error) {
                setResult(resultEl, error.message, "error");
            }
        });

        submitButton.addEventListener("click", async () => {

            if (!sessionSelect || !sessionSelect.value) {
                setResult(resultEl, "Pilih sesi presensi.", "error");
                return;
            }

            submitButton.disabled = true;

            setResult(resultEl, "Mencocokkan wajah...", "info");

            try {

                const image = capture(video, canvas);

                const data = await postJSON(
                    options.endpoint,
                    {
                        session_id: sessionSelect.value,
                        image
                    }
                );

                const confidence =
                    data.confidence
                        ? ` Kecocokan ${Math.round(data.confidence * 1000) / 10}%.`
                        : "";

                // jika sudah presensi
                const state = data.message.toLowerCase().includes("sudah presensi")
                    ? "warning"
                    : "success";

                setResult(
                    resultEl,
                    `${data.message}${confidence}`,
                    state
                );

            } catch (error) {

                setResult(resultEl, error.message, "error");

                submitButton.disabled = false;
            }
        });
    }

    return {
        mountFaceRegistration,
        mountAttendance
    };

})();