use std::process::{Command, Stdio};
use std::thread;
use std::time::Duration;

fn launch_backend() {
    let backend_process = Command::new("eco-backend.exe")
        .current_dir("resources/eco-backend")
        .stdout(Stdio::null())      // Redirigir stdout (sin consola)
        .stderr(Stdio::null())      // Redirigir stderr (sin consola)
        .stdin(Stdio::null())       // Redirigir stdin
        .spawn()
        .expect("Failed to start backend");
    
    // Guardar el PID si lo necesitas, o dejarlo correr
    thread::sleep(Duration::from_secs(3));
}

fn main() {
    launch_backend();
    
    tauri::Builder::default()
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}