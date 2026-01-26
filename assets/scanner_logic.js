
// Scanner Logic for Flet App
console.log("Scanner Logic Loaded");

function loadScript(src, callback) {
    var s = document.createElement('script');
    s.src = src;
    s.onload = callback;
    document.head.appendChild(s);
}

function startScanner() {
    console.log("Starting Scanner...");

    // 1. Check if library is loaded
    if (typeof Html5QrcodeScanner === 'undefined') {
        console.log("Library not found, loading...");
        // Intentar cargar desde assets local
        loadScript('/html5-qrcode.min.js', function () {
            console.log("Library loaded via script tag.");
            initScannerUI();
        });
    } else {
        initScannerUI();
    }
}

function initScannerUI() {
    // 2. Create Overlay if not exists
    let overlay = document.getElementById('scanner-overlay');
    if (!overlay) {
        overlay = document.createElement('div');
        overlay.id = 'scanner-overlay';
        overlay.style.position = 'fixed';
        overlay.style.top = '0';
        overlay.style.left = '0';
        overlay.style.width = '100%';
        overlay.style.height = '100%';
        overlay.style.backgroundColor = 'rgba(0,0,0,0.9)';
        overlay.style.zIndex = '9999';
        overlay.style.display = 'flex';
        overlay.style.flexDirection = 'column';
        overlay.style.alignItems = 'center';
        overlay.style.justifyContent = 'center';

        // Reader Box
        let reader = document.createElement('div');
        reader.id = 'reader';
        reader.style.width = '100%';
        reader.style.maxWidth = '500px';
        overlay.appendChild(reader);

        // Close Button
        let closeBtn = document.createElement('button');
        closeBtn.innerText = 'Cerrar / Cancelar';
        closeBtn.style.marginTop = '20px';
        closeBtn.style.padding = '10px 20px';
        closeBtn.style.fontSize = '18px';
        closeBtn.onclick = stopScanner;
        overlay.appendChild(closeBtn);

        document.body.appendChild(overlay);
    } else {
        overlay.style.display = 'flex';
    }

    // 3. Start html5-qrcode
    // Note: We use Html5Qrcode (class) for custom control or Scanner for built-in UI
    // Let's use Html5QrcodeScanner for ease

    // Clean previous instance if any?
    if (window.html5QrcodeScanner) {
        // window.html5QrcodeScanner.clear();
    }

    try {
        window.html5QrcodeScanner = new Html5QrcodeScanner(
            "reader",
            { fps: 10, qrbox: { width: 250, height: 250 } },
            /* verbose= */ false
        );

        window.html5QrcodeScanner.render(onScanSuccess, onScanFailure);
    } catch (e) {
        console.error("Error init scanner", e);
        alert("Error iniciando cámara: " + e);
    }
}

function onScanSuccess(decodedText, decodedResult) {
    // Handle the scanned code
    console.log(`Code matched = ${decodedText}`, decodedResult);

    // Stop scanning
    stopScanner();

    // Send to Flet via Hash
    // We add a timestamp to force change if same code is scanned twice
    window.location.hash = "scan=" + encodeURIComponent(decodedText) + "&ts=" + Date.now();
    // window.location.hash = ""; // Clear it? No, Python cleans it.
}

function onScanFailure(error) {
    // console.warn(`Code scan error = ${error}`);
}

function stopScanner() {
    if (window.html5QrcodeScanner) {
        window.html5QrcodeScanner.clear().then(_ => {
            document.getElementById('scanner-overlay').style.display = 'none';
        }).catch(error => {
            console.error("Failed to clear html5QrcodeScanner. ", error);
            document.getElementById('scanner-overlay').style.display = 'none';
        });
    } else {
        let overlay = document.getElementById('scanner-overlay');
        if (overlay) overlay.style.display = 'none';
    }
}
