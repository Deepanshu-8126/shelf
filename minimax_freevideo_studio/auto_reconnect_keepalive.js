// =====================================================================
// ⚡ GOOGLE COLAB 24/7 AUTO-RECONNECT & ANTI-DISCONNECT KEEPALIVE SCRIPT
// =====================================================================
// Kaise use karein:
// 1. Google Colab notebook tab par F12 (Inspect / Developer Tools) dabayein.
// 2. "Console" tab par click karein.
// 3. Neeche diya gaya code paste karein aur Enter dabayein!
// =====================================================================

function KeepColabAlive() {
    console.log("⚡ [Anti-Disconnect] Heartbeat ping checking Colab status...");
    
    // Auto-click connect button if disconnected
    let connectBtn = document.querySelector("#top-toolbar > colab-connect-button");
    if (connectBtn) {
        connectBtn.shadowRoot.querySelector("#connect").click();
        console.log("🔄 [Anti-Disconnect] Reconnecting session button clicked!");
    }
    
    // Auto-click reconnect popups
    let okBtn = document.querySelector("#ok");
    if (okBtn) {
        okBtn.click();
        console.log("🔄 [Anti-Disconnect] Dismissed idle dialog!");
    }
}

// Har 60 second (1 minute) me heartbeat bhejega
let keepAliveTimer = setInterval(KeepColabAlive, 60000);
console.log("✅ Colab KeepAlive Active! Session will not auto-disconnect.");
