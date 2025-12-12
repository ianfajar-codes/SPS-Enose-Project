use serde::{Deserialize, Serialize};
use serde_json::Value;
use std::collections::VecDeque;

// ============================================================================
// DATA STRUCTURES
// ============================================================================

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct SensorData {
    #[serde(alias = "timestamp")]
    pub timestamp: u64,
    pub sample: String,
    pub co_m: f32,
    pub eth_m: f32,
    pub voc_m: f32,
    pub no2: f32,
    pub eth_gm: f32,
    pub voc_gm: f32,
    pub co_gm: f32,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct StatusMessage {
    #[serde(rename = "msg_type")]
    pub msg_type: String,
    
    #[serde(skip_serializing_if = "Option::is_none")]
    pub status: Option<String>,
    
    #[serde(skip_serializing_if = "Option::is_none")]
    pub message: Option<String>,
    
    #[serde(skip_serializing_if = "Option::is_none")]
    pub motor: Option<String>,
    
    #[serde(skip_serializing_if = "Option::is_none")]
    pub speed: Option<i32>,
    
    #[serde(skip_serializing_if = "Option::is_none")]
    pub current: Option<i32>,
    
    #[serde(skip_serializing_if = "Option::is_none")]
    pub total: Option<i32>,
}

// ============================================================================
// DATA PROCESSOR
// ============================================================================

pub struct DataProcessor {
    window_size: usize,
    buffers: SensorBuffers,
}

struct SensorBuffers {
    co_m: VecDeque<f32>,
    eth_m: VecDeque<f32>,
    voc_m: VecDeque<f32>,
    no2: VecDeque<f32>,
    eth_gm: VecDeque<f32>,
    voc_gm: VecDeque<f32>,
    co_gm: VecDeque<f32>,
}

impl DataProcessor {
    pub fn new(window_size: usize) -> Self {
        Self {
            window_size,
            buffers: SensorBuffers {
                co_m: VecDeque::with_capacity(window_size),
                eth_m: VecDeque::with_capacity(window_size),
                voc_m: VecDeque::with_capacity(window_size),
                no2: VecDeque::with_capacity(window_size),
                eth_gm: VecDeque::with_capacity(window_size),
                voc_gm: VecDeque::with_capacity(window_size),
                co_gm: VecDeque::with_capacity(window_size),
            },
        }
    }

    pub fn parse_arduino_json(&self, line: &str) -> Result<(String, Value), String> {
        let json_value: Value = serde_json::from_str(line)
            .map_err(|e| format!("JSON parse error: {}", e))?;

        let msg_type = json_value
            .get("type")
            .and_then(|v| v.as_str())
            .ok_or_else(|| "Missing 'type' field".to_string())?
            .to_string();

        Ok((msg_type, json_value))
    }

    pub fn process_sensor_data(&mut self, json_value: &Value) -> Option<SensorData> {
        match serde_json::from_value::<SensorData>(json_value.clone()) {
            Ok(mut raw_data) => {
                // NORMALIZE SAMPLE NAME (FIX CASE)
                raw_data.sample = Self::normalize_sample_name(&raw_data.sample);
                
                // Apply moving average
                let smoothed = self.apply_moving_average(&raw_data);
                Some(smoothed)
            }
            Err(e) => {
                eprintln!("Error parsing sensor data: {}", e);
                eprintln!("JSON: {:?}", json_value);
                None
            }
        }
    }

    fn normalize_sample_name(name: &str) -> String {
        match name.trim().to_lowercase().as_str() {
            "kari" | "daun kari" => "Daun Kari".to_string(),
            "kemangi" | "daun kemangi" => "Daun Kemangi".to_string(),
            "jeruk" | "daun jeruk" => "Daun Jeruk".to_string(),
            "serai" | "daun serai" => "Daun Serai".to_string(),
            _ => {
                // Capitalize first letter of each word
                name.split_whitespace()
                    .map(|word| {
                        let mut chars = word.chars();
                        match chars.next() {
                            None => String::new(),
                            Some(first) => first.to_uppercase().collect::<String>() + chars.as_str(),
                        }
                    })
                    .collect::<Vec<_>>()
                    .join(" ")
            }
        }
    }

    fn apply_moving_average(&mut self, data: &SensorData) -> SensorData {
        // Update buffers (static method)
        Self::update_buffer(&mut self.buffers.co_m, data.co_m, self.window_size);
        Self::update_buffer(&mut self.buffers.eth_m, data.eth_m, self.window_size);
        Self::update_buffer(&mut self.buffers.voc_m, data.voc_m, self.window_size);
        Self::update_buffer(&mut self.buffers.no2, data.no2, self.window_size);
        Self::update_buffer(&mut self.buffers.eth_gm, data.eth_gm, self.window_size);
        Self::update_buffer(&mut self.buffers.voc_gm, data.voc_gm, self.window_size);
        Self::update_buffer(&mut self.buffers.co_gm, data.co_gm, self.window_size);

        // Calculate averages (static method)
        SensorData {
            timestamp: data.timestamp,
            sample: data.sample.clone(),
            co_m: Self::calculate_average(&self.buffers.co_m),
            eth_m: Self::calculate_average(&self.buffers.eth_m),
            voc_m: Self::calculate_average(&self.buffers.voc_m),
            no2: Self::calculate_average(&self.buffers.no2),
            eth_gm: Self::calculate_average(&self.buffers.eth_gm),
            voc_gm: Self::calculate_average(&self.buffers.voc_gm),
            co_gm: Self::calculate_average(&self.buffers.co_gm),
        }
    }

    fn update_buffer(buffer: &mut VecDeque<f32>, value: f32, window_size: usize) {
        if buffer.len() >= window_size {
            buffer.pop_front();
        }
        buffer.push_back(value);
    }

    fn calculate_average(buffer: &VecDeque<f32>) -> f32 {
        if buffer.is_empty() {
            return 0.0;
        }
        let sum: f32 = buffer.iter().sum();
        sum / buffer.len() as f32
    }

    pub fn process_status_message(&self, json_value: &Value, msg_type: &str) -> StatusMessage {
        let mut status_msg = StatusMessage {
            msg_type: msg_type.to_string(),
            status: None,
            message: None,
            motor: None,
            speed: None,
            current: None,
            total: None,
        };

        match msg_type {
            "status" => {
                status_msg.status = json_value
                    .get("status")
                    .and_then(|v| v.as_str())
                    .map(|s| s.to_string());
                
                status_msg.message = json_value
                    .get("msg")
                    .and_then(|v| v.as_str())
                    .map(|s| s.to_string());
            }
            "motor" => {
                status_msg.motor = json_value
                    .get("motor")
                    .and_then(|v| v.as_str())
                    .map(|s| s.to_string());
                
                status_msg.speed = json_value
                    .get("speed")
                    .and_then(|v| v.as_i64())
                    .map(|i| i as i32);
            }
            "calib_progress" => {
                status_msg.current = json_value
                    .get("current")
                    .and_then(|v| v.as_i64())
                    .map(|i| i as i32);
                
                status_msg.total = json_value
                    .get("total")
                    .and_then(|v| v.as_i64())
                    .map(|i| i as i32);
            }
            _ => {}
        }

        status_msg
    }
}

// ============================================================================
// TESTS
// ============================================================================

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_normalize_sample_name() {
        assert_eq!(DataProcessor::normalize_sample_name("kari"), "Daun Kari");
        assert_eq!(DataProcessor::normalize_sample_name("KARI"), "Daun Kari");
        assert_eq!(DataProcessor::normalize_sample_name("Kari"), "Daun Kari");
        assert_eq!(DataProcessor::normalize_sample_name("daun kari"), "Daun Kari");
        assert_eq!(DataProcessor::normalize_sample_name("kemangi"), "Daun Kemangi");
        assert_eq!(DataProcessor::normalize_sample_name("jeruk"), "Daun Jeruk");
        assert_eq!(DataProcessor::normalize_sample_name("serai"), "Daun Serai");
    }

    #[test]
    fn test_parse_sensor_data() {
        let json_str = r#"{"type":"data","ts":1496921,"sample":"kari","co_m":2.56,"eth_m":1.68,"voc_m":0.73,"no2":0.80,"eth_gm":0.74,"voc_gm":0.31,"co_gm":0.04}"#;
        
        let mut processor = DataProcessor::new(3);
        let (msg_type, json_value) = processor.parse_arduino_json(json_str).unwrap();
        
        assert_eq!(msg_type, "data");
        
        let sensor_data = processor.process_sensor_data(&json_value).unwrap();
        assert_eq!(sensor_data.sample, "Daun Kari");
        assert_eq!(sensor_data.co_m, 2.56);
    }
}
