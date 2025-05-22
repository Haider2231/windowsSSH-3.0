// Haz term global para que window.handle_output pueda accederla
window.term = new Terminal();
const fitAddon = new FitAddon.FitAddon();
window.term.loadAddon(fitAddon);
window.term.open(document.getElementById('terminal'));
fitAddon.fit();

// Define window.handle_output antes de cualquier posible uso
window.handle_output = function(data) {
    if (window.term && typeof window.term.write === "function") {
        window.term.write(data);
    } else {
        console.log("SSH Output:", data);
    }
};

// Redimensiona el terminal al cambiar el tamaño de la ventana
window.addEventListener('resize', () => {
    fitAddon.fit();
    try {
        let size_dim = 'cols:' + window.term.cols + '::rows:' + window.term.rows;
        if (window.backend && window.backend.set_pty_size) {
            window.backend.set_pty_size(size_dim);
        }
    } catch (error) {
        console.error(error);
        console.log("Channel may not be up yet!");
    }
});

// Cuando el usuario escribe, envía los datos al backend
window.term.onData(e => {
    if (window.backend && window.backend.write_data) {
        window.backend.write_data(e);
    }
});

// Establece la conexión con el backend de Qt
new QWebChannel(qt.webChannelTransport, function(channel) {
    window.backend = channel.objects.backend;
});

window.onload = function() {
    window.term.focus();
    window.term.setOption('theme', {
        background: '#141414'
    });
    let style = document.createElement('style');
    style.innerHTML = `
.xterm-viewport::-webkit-scrollbar {
    width: 12px;
}
.xterm-viewport::-webkit-scrollbar-track {
    background: #212121;
}
.xterm-viewport::-webkit-scrollbar-thumb {
    background: #888;
}
.xterm-viewport::-webkit-scrollbar-thumb:hover {
    background: #555;
}`;
    document.head.appendChild(style);
    // window.term.write("Press Enter To Begin...");
};
