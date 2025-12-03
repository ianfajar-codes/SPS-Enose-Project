// src/server.rs
use crate::data_process::{SensorData, StatusMessage};
use serde_json;
use tokio::io::AsyncWriteExt;
use tokio::net::{TcpListener, TcpStream};
use tokio::sync::broadcast;

#[derive(Clone, Debug)]
pub enum Message {
    SensorData(SensorData),
    Status(StatusMessage),
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
                        println!("✓ Client connected: {}", addr);
                        let rx = tx.subscribe();
                        tokio::spawn(handle_client(socket, rx));
                    }
                    Err(e) => {
                        eprintln!("Connection error: {}", e);
                    }
                }
            }
        });

        Ok(())
    }

    pub fn broadcast(&self, msg: Message) {
        let _ = self.tx.send(msg);
    }

    // ✅ TAMBAHKAN METHOD INI
    pub fn get_sender(&self) -> broadcast::Sender<Message> {
        self.tx.clone()
    }
}

async fn handle_client(
    socket: TcpStream,
    mut rx: broadcast::Receiver<Message>,
) {
    let (_, mut writer) = socket.into_split();

    while let Ok(msg) = rx.recv().await {
        let packet = match msg {
            Message::SensorData(data) => {
                if let Ok(json) = serde_json::to_string(&data) {
                    format!("DATA:{}\n", json)
                } else {
                    continue;
                }
            }
            Message::Status(status) => {
                if let Ok(json) = serde_json::to_string(&status) {
                    format!("STATUS:{}\n", json)
                } else {
                    continue;
                }
            }
        };

        if writer.write_all(packet.as_bytes()).await.is_err() {
            break;
        }
    }

    println!("✗ Client disconnected");
}
