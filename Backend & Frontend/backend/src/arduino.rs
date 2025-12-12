use tokio::net::TcpListener;
use tokio::io::{AsyncBufReadExt, BufReader};
use tokio::sync::broadcast;
use crate::server::Message;
use crate::data_process::DataProcessor;

pub async fn start_arduino_receiver(
    addr: &str,
    tx: broadcast::Sender<Message>,
) -> Result<(), Box<dyn std::error::Error>> {
    let listener = TcpListener::bind(addr).await?;
    println!("🎧 Arduino WiFi Receiver listening on {}", addr);

    loop {
        let (socket, addr) = listener.accept().await?;
        println!("📱 Arduino connected from: {}", addr);
        
        let tx_clone = tx.clone();
        tokio::spawn(async move {
            if let Err(e) = handle_arduino(socket, tx_clone).await {
                eprintln!("❌ Error handling Arduino {}: {}", addr, e);
            }
            println!("📱 Arduino {} disconnected", addr);
        });
    }
}

async fn handle_arduino(
    socket: tokio::net::TcpStream,
    tx: broadcast::Sender<Message>,
) -> Result<(), Box<dyn std::error::Error>> {
    let reader = BufReader::new(socket);
    let mut lines = reader.lines();
    let mut processor = DataProcessor::new(3); // Moving average window size 3

    while let Some(line) = lines.next_line().await? {
        if line.is_empty() {
            continue;
        }

        // DEBUG: Print raw data
        println!("🔍 RAW: {}", line);

        // Parse JSON menggunakan DataProcessor yang sudah ada
        match processor.parse_arduino_json(&line) {
            Ok((msg_type, json_value)) => {
                match msg_type.as_str() {
                    "data" => {
                        if let Some(sensor_data) = processor.process_sensor_data(&json_value) {
                            println!(
                                "📊 [WiFi] {:15} | CO:{:5.2} ETH:{:5.2} VOC:{:5.2} NO2:{:4.2}", 
                                sensor_data.sample,
                                sensor_data.co_m,
                                sensor_data.eth_m, 
                                sensor_data.voc_m,
                                sensor_data.no2
                            );
                            
                            // Simpan ke CSV (optional)
                            save_to_csv(&sensor_data);
                            
                            // Broadcast ke GUI clients
                            let _ = tx.send(Message::SensorData(sensor_data));
                        }
                    }
                    "status" | "motor" | "calib_progress" => {
                        let status_msg = processor.process_status_message(&json_value, &msg_type);
                        
                        if let Some(ref msg) = status_msg.message {
                            println!("ℹ️  Status: {}", msg);
                        }
                        if let (Some(ref motor), Some(speed)) = (&status_msg.motor, status_msg.speed) {
                            println!("⚙️  Motor {} = {}%", motor, speed);
                        }
                        if let (Some(current), Some(total)) = (status_msg.current, status_msg.total) {
                            println!("🔧 Calibration progress: {}/{}", current, total);
                        }
                        
                        // Broadcast status ke GUI clients
                        let _ = tx.send(Message::Status(status_msg));
                    }
                    _ => {
                        println!("❓ Unknown message type: {}", msg_type);
                    }
                }
            }
            Err(e) => {
                eprintln!("✗ JSON Parse error: {}", e);
                eprintln!("   Line: {}", line);
            }
        }
    }

    Ok(())
}

// Optional: Simpan ke CSV untuk logging
fn save_to_csv(data: &crate::data_process::SensorData) {
    use std::fs::OpenOptions;
    use std::io::Write;
    
    let file_result = OpenOptions::new()
        .create(true)
        .append(true)
        .open("sensor_data.csv");
    
    if let Ok(mut file) = file_result {
        let csv_line = format!(
            "{},{},{:.2},{:.2},{:.2},{:.2},{:.2},{:.2},{:.2}\n",
            data.timestamp,
            data.sample,
            data.co_m,
            data.eth_m,
            data.voc_m,
            data.no2,
            data.eth_gm,
            data.voc_gm,
            data.co_gm
        );
        
        let _ = file.write_all(csv_line.as_bytes());
    }
}
