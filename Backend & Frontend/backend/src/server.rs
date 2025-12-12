// src/server.rs
use crate::data_process::{SensorData, StatusMessage};
use serde_json;
use tokio::io::{AsyncBufReadExt, AsyncWriteExt, BufReader};
use tokio::net::{TcpListener, TcpStream};
use tokio::sync::broadcast;

#[derive(Clone, Debug)]
pub enum Message {
    SensorData(SensorData),
    Status(StatusMessage),
    Command(String),
}

pub struct TcpServer {
    tx: broadcast::Sender<Message>,
}

impl TcpServer {
    pub fn new() -> (Self, broadcast::Receiver<Message>) {
        let (tx, rx) = broadcast::channel(100);
        (Self { tx }, rx)
    }

    pub async fn start(&self, addr: &str) -> Result<(), Box<dyn std::error::Error>> {
        let listener = TcpListener::bind(addr).await?;
        let tx = self.tx.clone();

        tokio::spawn(async move {
            loop {
                match listener.accept().await {
                    Ok((socket, addr)) => {
                        println!("✅ Client connected: {}", addr);
                        let rx = tx.subscribe();
                        let tx_clone = tx.clone();
                        tokio::spawn(handle_client(socket, rx, tx_clone, addr));
                    }
                    Err(e) => {
                        eprintln!("❌ Connection error: {}", e);
                    }
                }
            }
        });

        Ok(())
    }

    pub fn broadcast(&self, msg: Message) {
        let _ = self.tx.send(msg);
    }

    pub fn get_sender(&self) -> broadcast::Sender<Message> {
        self.tx.clone()
    }
}

async fn handle_client(
    socket: TcpStream,
    mut rx: broadcast::Receiver<Message>,
    tx: broadcast::Sender<Message>,
    addr: std::net::SocketAddr,
) {
    let (reader, mut writer) = socket.into_split();
    let mut reader = BufReader::new(reader);

    // Task untuk MENERIMA command dari client (Python GUI atau Arduino)
    let tx_read = tx.clone();
    let read_handle = tokio::spawn(async move {
        let mut line = String::new();
        loop {
            line.clear();
            match reader.read_line(&mut line).await {
                Ok(0) => break,
                Ok(_) => {
                    let cmd = line.trim().to_string();
                    if !cmd.is_empty() {
                        println!("📥 Command from {}: {}", addr, cmd);
                        let _ = tx_read.send(Message::Command(cmd));
                    }
                }
                Err(_) => break,
            }
        }
    });

    // Task untuk MENGIRIM data ke client
    let write_handle = tokio::spawn(async move {
        while let Ok(msg) = rx.recv().await {
            // ✅ FORMAT YANG MATCH DENGAN PYTHON: "DATA:" atau "STATUS:"
            let packet = match msg {
                Message::SensorData(data) => {
                    if let Ok(json) = serde_json::to_string(&data) {
                        format!("DATA:{}\n", json)  // ✅ Sesuai ekspektasi Python
                    } else {
                        continue;
                    }
                }
                Message::Status(status) => {
                    if let Ok(json) = serde_json::to_string(&status) {
                        format!("STATUS:{}\n", json)  // ✅ Sesuai ekspektasi Python
                    } else {
                        continue;
                    }
                }
                Message::Command(_) => continue,
            };

            if writer.write_all(packet.as_bytes()).await.is_err() {
                break;
            }
        }
    });

    tokio::select! {
        _ = read_handle => {},
        _ = write_handle => {},
    }

    println!("❌ Client disconnected: {}", addr);
}