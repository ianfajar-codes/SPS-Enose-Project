mod arduino;
mod data_process;
mod server;

use arduino::start_arduino_receiver;
use data_process::{StatusMessage};
use server::{TcpServer, Message};
use std::env;
use std::time::{SystemTime, UNIX_EPOCH};

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    println!("╔══════════════════════════════════════════════════════════════╗");
    println!("║                Electronic Nose Backend (Rust)                ║");
    println!("║                         WiFi Mode                            ║");
    println!("╚══════════════════════════════════════════════════════════════╝\n");

    let args: Vec<String> = env::args().collect();
    let mode = if args.len() > 1 { args[1].as_str() } else { "normal" };

    match mode {
        "dummy" => {
            println!("⚠️  DUMMY MODE - Structured Data Generation\n");
            run_dummy_mode().await?;
        }
        _ => {
            println!("📡 NORMAL MODE - Real Arduino WiFi Data\n");
            run_normal_mode().await?;
        }
    }

    Ok(())
}

// ============================================================================
// MODE 1: DUMMY - Structured Data with Manual Sample Type Change
// ============================================================================
async fn run_dummy_mode() -> Result<(), Box<dyn std::error::Error>> {
    let (server, _rx) = TcpServer::new();
    server.start("127.0.0.1:8080").await?;
    
    println!("✓ TCP Server listening on 127.0.0.1:8080");
    println!("✓ Structured dummy data generation");
    println!("⚠️  Change sample type manually in main.rs");
    println!("✓ Press Ctrl+C to stop\n");
    println!("{:-<70}\n", "");

    // ══════════════════════════════════════════════════════════════
    // GANTI SAMPLE TYPE DI SINI:
    let current_sample = "Daun Pandan";  // ← UBAH INI UNTUK GANTI SAMPLE
    // Options: "Daun Kari", "Daun Kemangi", "Daun Jeruk", "Daun Seledri"
    // ══════════════════════════════════════════════════════════════
    
    let mut counter = 0_i32;
    let mut m1_step = 0_usize;

    // Motor speeds
    let m1_speeds = vec![20, 40, 60, 80, 100];
    let m2_speed = 50;
    
    loop {
        tokio::time::sleep(tokio::time::Duration::from_secs(2)).await;
        
        counter += 1;
        let current_m1_speed = m1_speeds[m1_step];
        
        // Generate structured dummy data
        let dummy_data = generate_structured_dummy_data(
            counter,
            current_sample,
            current_m1_speed,
            m2_speed
        );
        
        println!(
            "📊 #{:03} | {:15} | M1:{:3}% M2:{:3}% | CO:{:5.2} ETH:{:5.2} VOC:{:5.2}", 
            counter,
            current_sample,
            current_m1_speed,
            m2_speed,
            dummy_data.co_m, 
            dummy_data.eth_m, 
            dummy_data.voc_m
        );
        
        // Broadcast sensor data
        server.broadcast(Message::SensorData(dummy_data));
        
        // Send motor status every 5 samples
        if counter % 5 == 0 {
            send_dummy_motor_status(&server, current_m1_speed, m2_speed);
        }
        
        // Cycle M1 speed every 10 samples
        if counter % 10 == 0 {
            m1_step = (m1_step + 1) % m1_speeds.len();
            let next_speed = m1_speeds[m1_step];
            println!("⚙️  M1 cycle → {}% | M2 remains {}%", next_speed, m2_speed);
        }
        
        // Calibration simulation at start
        if counter == 1 {
            send_dummy_calib_progress(&server, 5, 10);
        }
        if counter == 2 {
            send_dummy_calib_progress(&server, 10, 10);
        }
    }
}

fn generate_structured_dummy_data(
    counter: i32,
    sample: &str,
    m1_speed: i32,
    m2_speed: i32
) -> data_process::SensorData {
    use rand::Rng;
    let mut rng = rand::thread_rng();
    
    // Base sensor values per sample type
    let (base_co, base_eth, base_voc, base_no2) = match sample {
        "Daun Kari" => (45.0, 25.0, 60.0, 5.0),
        "Daun Kemangi" => (38.0, 32.0, 55.0, 6.5),
        "Daun Jeruk" => (52.0, 20.0, 70.0, 4.2),
        "Daun Serai" => (40.0, 28.0, 65.0, 5.8),
        _ => (45.0, 25.0, 60.0, 5.0),
    };
    
    // Motor influence
    let m1_factor = (m1_speed as f32) / 100.0;
    let m2_factor = (m2_speed as f32) / 100.0;
    let combined_factor = m1_factor * 0.6 + m2_factor * 0.4;
    
    // Time-based noise
    let noise = (counter as f32 * 0.03).sin() * 1.5;
    
    data_process::SensorData {
        timestamp: SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .unwrap()
            .as_millis() as u64,
        sample: sample.to_string(),
        co_m: base_co * (0.6 + combined_factor * 0.6) + rng.gen_range(-2.5..2.5) + noise,
        eth_m: base_eth * (0.6 + combined_factor * 0.6) + rng.gen_range(-1.8..1.8) + noise * 0.5,
        voc_m: base_voc * (0.6 + combined_factor * 0.6) + rng.gen_range(-4.0..4.0) + noise * 0.7,
        no2: base_no2 * (0.7 + combined_factor * 0.4) + rng.gen_range(-0.8..0.8),
        eth_gm: (base_eth * 1.35) * (0.6 + combined_factor * 0.6) + rng.gen_range(-2.2..2.2),
        voc_gm: (base_voc * 0.92) * (0.6 + combined_factor * 0.6) + rng.gen_range(-3.5..3.5),
        co_gm: (base_co * 1.12) * (0.6 + combined_factor * 0.6) + rng.gen_range(-2.8..2.8),
    }
}

// ============================================================================
// MODE 2: NORMAL (Real Arduino WiFi data)
// ============================================================================
async fn run_normal_mode() -> Result<(), Box<dyn std::error::Error>> {
    println!("🌐 Setting up WiFi receiver for Arduino...\n");

    let (server, _rx) = TcpServer::new();
    
    // Start GUI broadcast server on port 8080
    server.start("0.0.0.0:8080").await?;
    println!("✓ GUI Server listening on 0.0.0.0:8080");
    
    // Start Arduino WiFi receiver on port 8081
    let tx = server.get_sender();  
    println!("✓ Arduino WiFi Receiver listening on 0.0.0.0:8081");
    println!("✓ Waiting for Arduino connection...\n");
    println!("{:-<70}\n", "");
    
    // This will run indefinitely, receiving data from Arduino
    start_arduino_receiver("0.0.0.0:8081", tx).await?;
    
    Ok(())
}

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

fn send_dummy_motor_status(server: &TcpServer, m1_speed: i32, m2_speed: i32) {
    let motor_msg_m1 = StatusMessage {
        msg_type: "motor".to_string(),
        status: None,
        message: None,
        motor: Some("M1".to_string()),
        speed: Some(m1_speed),
        current: None,
        total: None,
    };
    server.broadcast(Message::Status(motor_msg_m1));
    
    let motor_msg_m2 = StatusMessage {
        msg_type: "motor".to_string(),
        status: None,
        message: None,
        motor: Some("M2".to_string()),
        speed: Some(m2_speed),
        current: None,
        total: None,
    };
    server.broadcast(Message::Status(motor_msg_m2));
}

fn send_dummy_calib_progress(server: &TcpServer, current: i32, total: i32) {
    let calib_msg = StatusMessage {
        msg_type: "calib_progress".to_string(),
        status: None,
        message: None,
        motor: None,
        speed: None,
        current: Some(current),
        total: Some(total),
    };
    
    println!("🔧 Calibration progress: {}/{}", current, total);
    server.broadcast(Message::Status(calib_msg));
}
